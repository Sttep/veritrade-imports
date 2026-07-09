"""
scripts/revisar_cuarentena.py
════════════════════════════════
Revisa archivos .xlsx en data/cuarentena/ ANTES de que entren al pipeline (silver → gold →
parquet final). Corre el mismo parser determinístico que pipeline/silver.py (leer_archivo +
procesar_fila + debe_excluir, importados de ahí, no duplicados) pero en modo lectura — no escribe
nada en data/silver/ ni mueve nada de cuarentena a menos que se pida explícitamente.

Motivación (feedback del jefe, 9-jul): algunas descargas por marca ("consolidados amplios")
mezclan importadores/marcas que no se pidieron, o traen partidas de repuestos en vez de camiones
(pasó hoy: un archivo de 1160 filas resultó ser 100% repuestos). Este script CLASIFICA EL RIESGO
de cada archivo antes de moverlo a bronze — no decide por la persona, recomienda con motivo.

Cuatro módulos, siempre presentes en el reporte:
  1. Composición (% partida de camión vs. repuesto/otro) — la que hoy faltó.
  2. Empresas y marcas nuevas (informativo, no es señal de riesgo por sí solo).
  3. Cruce contra huecos de cobertura ya flaggeados (el corazón del script).
  4. % de DUAs genuinamente nuevos vs. ya presentes en camiones.parquet.

Solo lectura sobre data/gold/, configuracion.xlsx y data/cuarentena/ — nunca escribe salvo con
--mover-aprobados explícito (mueve archivos de riesgo bajo a data/bronze/).

Uso:
  uv run python scripts/revisar_cuarentena.py
  uv run python scripts/revisar_cuarentena.py --mover-aprobados
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.silver import (  # noqa: E402
    Config, CONFIG_PATH, PARTIDAS_CAMION, leer_archivo, procesar_fila, debe_excluir,
)
from scripts.validar_continuidad_importador import meses_sospechosos, MESES  # noqa: E402

CUARENTENA_DIR = ROOT / "data" / "cuarentena"
BRONZE_DIR = ROOT / "data" / "bronze"

VOLUMEN_ALTO = 20  # filas de una empresa/marca nueva a partir de las cuales vale la pena revisar
UMBRAL_DUPLICADO = 20  # % de DUAs nuevos por debajo del cual el archivo es mayormente duplicado


# ── Módulo 0: parseo (reusa pipeline/silver.py, no escribe nada) ──────────────

def procesar_archivo_cuarentena(path: Path, cfg: Config) -> pd.DataFrame:
    """Versión de solo lectura de pipeline/silver.py::procesar_archivo() -- mismo parser
    (leer_archivo + procesar_fila + debe_excluir), pero no escribe nada a disco. Devuelve TODAS
    las filas (válidas y excluidas) con su razón, para poder calcular composición camión/repuesto."""
    df_raw, _meta = leer_archivo(path)
    if "_descripcion" not in df_raw.columns:
        return pd.DataFrame()

    registros = []
    for row in df_raw.to_dict("records"):
        rec = procesar_fila(row, cfg)
        excluir, razon = debe_excluir(rec, cfg)
        rec["_excluido"] = excluir
        rec["_razon_exclusion"] = razon if excluir else ""
        registros.append(rec)
    return pd.DataFrame(registros)


# ── Módulo 1: composición ──────────────────────────────────────────────────────

def composicion(df: pd.DataFrame) -> dict:
    total = len(df)
    if total == 0:
        return {"total": 0, "n_camion": 0, "pct_camion": 0.0, "pct_no_camion": 0.0, "top_no_camion": []}
    partida = df["partida"].astype(str)
    es_camion = partida.isin(PARTIDAS_CAMION)
    n_camion = int(es_camion.sum())
    top = partida[~es_camion].value_counts().head(5)
    return {
        "total": total,
        "n_camion": n_camion,
        "pct_camion": round(n_camion / total * 100, 1),
        "pct_no_camion": round((total - n_camion) / total * 100, 1),
        "top_no_camion": [(p, int(n)) for p, n in top.items()],
    }


# ── Módulo 2: empresas y marcas nuevas ─────────────────────────────────────────

def empresas_y_marcas_nuevas(df_ok: pd.DataFrame, vt: pd.DataFrame) -> dict:
    """No es señal de riesgo por sí sola -- se reporta siempre, el riesgo lo decide
    clasificar_riesgo() combinando esto con volumen y huecos (módulo 3)."""
    if df_ok.empty:
        return {"importadores_nuevos": {}, "marcas_nuevas": {}}

    importadores_conocidos = set(vt["importador"].dropna().astype(str)) if "importador" in vt.columns else set()
    marcas_conocidas = set(vt["marca_normalizada"].dropna().astype(str)) if "marca_normalizada" in vt.columns else set()

    importadores_nuevos = {}
    for imp, n in df_ok["importador"].value_counts().items():
        imp_str = str(imp).strip()
        if imp_str and imp_str.upper() not in ("NAN", "NONE") and imp_str not in importadores_conocidos:
            importadores_nuevos[imp_str] = int(n)

    marcas_nuevas = {}
    for marca, n in df_ok["marca_normalizada"].dropna().value_counts().items():
        marca_str = str(marca).strip()
        if marca_str and marca_str.upper() not in ("NAN", "NONE") and marca_str not in marcas_conocidas:
            marcas_nuevas[marca_str] = int(n)

    return {"importadores_nuevos": importadores_nuevos, "marcas_nuevas": marcas_nuevas}


# ── Módulo 3: cruce contra huecos de cobertura (el corazón del script) ────────

def cruce_huecos(df: pd.DataFrame, vt: pd.DataFrame) -> list[dict]:
    """Para cada importador presente en el archivo (usando TODAS sus filas, válidas o excluidas --
    un archivo 100% repuestos también tiene importador, aunque df_ok quede vacío), compara los
    meses REALES de sus filas (no el nombre del archivo) contra los huecos ya flaggeados en el
    histórico (vt) para cada marca que ese importador maneja habitualmente."""
    if df.empty or "fecha_dua" not in df.columns or "importador" not in df.columns or vt.empty:
        return []

    df = df.copy()
    df["_dt"] = pd.to_datetime(df["fecha_dua"], errors="coerce")
    df["_mes"] = df["_dt"].dt.month
    df["_anio"] = df["_dt"].dt.year

    vt = vt.copy()
    vt["_dt"] = pd.to_datetime(vt["fecha_dua"], errors="coerce")

    importadores_archivo = sorted({str(i).strip() for i in df["importador"].dropna() if str(i).strip()})
    if not importadores_archivo:
        return []

    resultados = []
    for imp in importadores_archivo:
        sub = df[df["importador"].astype(str).str.strip() == imp]
        meses_en_archivo = sorted(int(m) for m in sub["_mes"].dropna().unique())
        anios_en_archivo = sorted(int(a) for a in sub["_anio"].dropna().unique())
        if not anios_en_archivo:
            continue
        anio = anios_en_archivo[-1]

        marcas_importador = vt[vt["importador"] == imp]["marca_normalizada"].dropna().unique()
        meses_periodo = list(range(1, 13))
        for marca in marcas_importador:
            vt_hist = vt[(vt["marca_normalizada"] == marca) & (vt["importador"] == imp) & (vt["_dt"].dt.year == anio)]
            por_mes = pd.Series({m: int((vt_hist["_dt"].dt.month == m).sum()) for m in meses_periodo})
            meses_hueco = meses_sospechosos(por_mes, meses_periodo)
            if not meses_hueco:
                continue
            cubre_hueco = bool(set(meses_en_archivo) & set(meses_hueco))
            resultados.append({
                "marca": marca, "importador": imp,
                "meses_en_archivo": meses_en_archivo, "meses_hueco_flaggeados": meses_hueco,
                "cubre_hueco": cubre_hueco,
            })
    return resultados


# ── Módulo 4: duplicados ────────────────────────────────────────────────────────

def duplicados(df_ok: pd.DataFrame, vt: pd.DataFrame) -> dict:
    if df_ok.empty or "dua_dam" not in df_ok.columns or vt.empty:
        return {"total": 0, "duas_nuevos": 0, "duas_existentes": 0, "pct_nuevo": 0.0}
    duas_archivo = set(df_ok["dua_dam"].dropna().astype(str))
    duas_existentes = set(vt["dua_dam"].dropna().astype(str)) if "dua_dam" in vt.columns else set()
    nuevos = duas_archivo - duas_existentes
    total = len(duas_archivo)
    return {
        "total": total,
        "duas_nuevos": len(nuevos),
        "duas_existentes": total - len(nuevos),
        "pct_nuevo": round(len(nuevos) / total * 100, 1) if total else 0.0,
    }


# ── Clasificación de riesgo (recomienda, no decide) ────────────────────────────

def clasificar_riesgo(comp: dict, emp: dict, huecos: list[dict], dup: dict) -> tuple[str, str]:
    if comp["total"] == 0:
        return "RIESGO ALTO", "archivo vacío o sin descripción comercial parseable"

    cubre_algun_hueco = any(h["cubre_hueco"] for h in huecos)
    hay_huecos_flaggeados = any(h["meses_hueco_flaggeados"] for h in huecos)
    rango_incorrecto = hay_huecos_flaggeados and not cubre_algun_hueco

    if comp["pct_camion"] == 0:
        if cubre_algun_hueco:
            return ("BAJO RIESGO (hueco confirmado)",
                    "100% repuestos/no-camión, pero cae en un mes flaggeado como hueco -- "
                    "confirma que el importador genuinamente no trajo camiones ese período. "
                    "Buena noticia, no hay nada que mover a silver.")
        return ("RIESGO MEDIO",
                "100% repuestos/no-camión y no cae en ningún hueco flaggeado -- revisar si el "
                "importador/rango de descarga fue el correcto")

    if rango_incorrecto:
        meses_pedidos = sorted({m for h in huecos for m in h["meses_hueco_flaggeados"]})
        meses_traidos = sorted({m for h in huecos for m in h["meses_en_archivo"]})
        return ("RIESGO MEDIO",
                f"tiene camiones reales pero NO cubre el mes flaggeado como hueco (se necesitaba "
                f"{[MESES[m] for m in meses_pedidos]}, el archivo trae "
                f"{[MESES[m] for m in meses_traidos]}) -- puede que el rango de fecha en Veritrade "
                f"haya sido el equivocado")

    nuevos_alto_volumen = [n for n in list(emp["importadores_nuevos"].values())
                            + list(emp["marcas_nuevas"].values()) if n >= VOLUMEN_ALTO]
    if nuevos_alto_volumen and not huecos:
        return ("RIESGO MEDIO",
                "trae empresa/marca nueva de volumen alto sin relación a ningún hueco flaggeado -- "
                "confirmar que es real, no ruido de un filtro amplio")

    if dup["total"] and dup["pct_nuevo"] < UMBRAL_DUPLICADO:
        return ("RIESGO MEDIO",
                f"solo {dup['pct_nuevo']}% de los DUAs son genuinamente nuevos -- mayormente "
                f"duplicado de lo que ya está en camiones.parquet")

    motivo = f"{comp['pct_camion']}% filas de camión, {dup['pct_nuevo']}% DUAs nuevos"
    if cubre_algun_hueco:
        motivo += ", cubre un hueco flaggeado"
    return "BAJO RIESGO", motivo


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mover-aprobados", action="store_true",
                     help="Mover físicamente los archivos de RIESGO BAJO de data/cuarentena/ a "
                          "data/bronze/ (default apagado -- requiere confirmación humana previa)")
    args = ap.parse_args()

    archivos = sorted(p for p in CUARENTENA_DIR.glob("*.xlsx"))
    if not archivos:
        print(f"\n  Sin archivos en {CUARENTENA_DIR.relative_to(ROOT)}/. Nada que revisar.\n")
        return 0

    cfg = Config(CONFIG_PATH)
    vt_path = ROOT / "data" / "gold" / "camiones.parquet"
    vt = pd.read_parquet(vt_path) if vt_path.exists() else pd.DataFrame()

    print(f"\n{'=' * 70}")
    print(f"  REVISIÓN DE CUARENTENA  —  {len(archivos)} archivo(s)")
    print(f"{'=' * 70}\n")

    resumen = []
    for path in archivos:
        print(f"  ═══ {path.name} ═══")
        df = procesar_archivo_cuarentena(path, cfg)
        df_ok = df[~df["_excluido"]].copy() if not df.empty else df

        comp = composicion(df)
        emp = empresas_y_marcas_nuevas(df_ok, vt)
        huecos = cruce_huecos(df, vt)
        dup = duplicados(df_ok, vt)
        nivel, motivo = clasificar_riesgo(comp, emp, huecos, dup)

        print(f"  1. Composición:      {comp['pct_camion']}% camión / {comp['pct_no_camion']}% "
              f"no-camión (top no-camión: {comp['top_no_camion'][:3]})")
        if emp["importadores_nuevos"]:
            print(f"  2. Empresas nuevas:  {emp['importadores_nuevos']}")
        if emp["marcas_nuevas"]:
            print(f"  2. Marcas nuevas:    {emp['marcas_nuevas']}")
        if not emp["importadores_nuevos"] and not emp["marcas_nuevas"]:
            print("  2. Empresas/marcas nuevas: ninguna")
        if huecos:
            for h in huecos:
                estado = "CUBRE hueco" if h["cubre_hueco"] else "no cubre ningún hueco flaggeado"
                print(f"  3. {h['marca']}/{h['importador']}: meses en archivo "
                      f"{[MESES[m] for m in h['meses_en_archivo']]}, huecos flaggeados "
                      f"{[MESES[m] for m in h['meses_hueco_flaggeados']]} -- {estado}")
        else:
            print("  3. Cruce de huecos: sin combinaciones marca+importador evaluables")
        print(f"  4. Duplicados:       {dup['duas_nuevos']}/{dup['total']} DUAs nuevos ({dup['pct_nuevo']}%)")
        print(f"  >>> {nivel}: {motivo}")
        print()

        resumen.append({"archivo": path, "nivel": nivel, "motivo": motivo})

    print(f"{'=' * 70}")
    print("  RESUMEN")
    print(f"{'=' * 70}")
    for r in resumen:
        print(f"  [{r['nivel']:<28}] {r['archivo'].name}")

    bajo_riesgo = [r for r in resumen if r["nivel"].startswith("BAJO RIESGO")]
    if bajo_riesgo:
        print(f"\n  {len(bajo_riesgo)} archivo(s) de riesgo bajo. Comando sugerido para mover a bronze:")
        for r in bajo_riesgo:
            print(f"    mv \"{r['archivo']}\" \"{BRONZE_DIR / r['archivo'].name}\"")
    else:
        print("\n  Ningún archivo clasificó como riesgo bajo en esta corrida.")

    if args.mover_aprobados:
        if not bajo_riesgo:
            print("\n  --mover-aprobados: nada que mover.")
        for r in bajo_riesgo:
            destino = BRONZE_DIR / r["archivo"].name
            shutil.move(str(r["archivo"]), str(destino))
            print(f"  Movido: {r['archivo'].name} -> data/bronze/")

    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
