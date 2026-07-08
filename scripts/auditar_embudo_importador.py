"""
scripts/auditar_embudo_importador.py
═════════════════════════════════════
Reconstruye, para cada importador, el camino completo de sus filas por el
pipeline: bronze -> excluidas en silver (por razon) -> validas en silver ->
excluidas en build_parquet (por razon) -> filas finales en camiones.parquet.

Generaliza la investigacion manual que se hizo el 2026-07-08 para Zapler
S.A.C. (ver bd issue/memoria de esa sesion) para que corra sobre TODOS los
importadores sin tener que repetir el analisis a mano cada vez que alguien
pregunta "por que no veo X unidades de tal empresa".

Solo lectura -- no modifica ningun parquet/xlsx.

Uso:
  uv run python scripts/auditar_embudo_importador.py
      -> tabla completa, un renglon por importador, ordenada por
         porcentaje de filas descartadas (los mas sospechosos primero)

  uv run python scripts/auditar_embudo_importador.py --importador "ZAPLER"
      -> detalle completo de un importador puntual, con razones de
         exclusion desglosadas en cada etapa
"""
from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SILVER_DIR = ROOT / "data" / "silver"
GOLD_DIR = ROOT / "data" / "gold"

sys.path.insert(0, str(ROOT))
from pipeline.build_parquet import PARTIDAS_EXCLUIDAS, VANS_EXCLUIDAS  # noqa: E402


def cargar_excluidos_silver() -> pd.DataFrame:
    frames = []
    for f in sorted(glob.glob(str(SILVER_DIR / "*_qa.xlsx"))):
        try:
            df = pd.read_excel(f, sheet_name="_excluidos", dtype=str)
        except Exception:
            continue
        if "importador" not in df.columns:
            continue
        df["razon"] = df.get("razon_exclusion", "desconocida").astype(str).str.split("=").str[0]
        frames.append(df[["importador", "razon"]])
    if not frames:
        return pd.DataFrame(columns=["importador", "razon"])
    return pd.concat(frames, ignore_index=True)


def cargar_gold_normalizado() -> pd.DataFrame:
    frames = []
    for f in sorted(glob.glob(str(GOLD_DIR / "*_normalizado.parquet"))):
        df = pd.read_parquet(f)
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def aplicar_filtros_build_parquet(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Replica pipeline/build_parquet.py: devuelve (sobrevivientes, descartados_con_razon)."""
    descartes = []

    if "partida" in df.columns:
        mask = df["partida"].astype(str).isin(PARTIDAS_EXCLUIDAS)
        d = df[mask].copy()
        d["razon"] = "partida_no_vehicular"
        descartes.append(d)
        df = df[~mask].copy()

    if "marca_norm" in df.columns and "modelo_match" in df.columns:
        marca_up = df["marca_norm"].astype(str).str.upper().str.strip()
        modelo_up = df["modelo_match"].astype(str).str.upper()
        mask_van = pd.Series(False, index=df.index)
        for marca, patrones in VANS_EXCLUIDAS.items():
            m = marca_up == marca
            m2 = modelo_up.str.contains("|".join(patrones), regex=True, na=False)
            mask_van |= (m & m2)
        d = df[mask_van].copy()
        d["razon"] = "van_sobre_partida_liviana"
        descartes.append(d)
        df = df[~mask_van].copy()

    if "dua_dam" in df.columns:
        vin_s = df["vin"] if "vin" in df.columns else pd.Series("", index=df.index)
        chasis_s = df["chasis"] if "chasis" in df.columns else pd.Series("", index=df.index)
        vin_final = vin_s.where(vin_s.notna() & (vin_s.astype(str) != ""), chasis_s)
        key = df["dua_dam"].astype(str) + "|" + vin_final.astype(str)
        mask_dup = key.duplicated(keep="first")
        d = df[mask_dup].copy()
        d["razon"] = "duplicado_dua_vin"
        descartes.append(d)
        df = df[~mask_dup].copy()

    desc_df = pd.concat(descartes, ignore_index=True) if descartes else pd.DataFrame(columns=["importador", "razon"])
    return df, desc_df


def construir_tabla(excl_silver: pd.DataFrame, gold: pd.DataFrame) -> pd.DataFrame:
    finales, excl_build = aplicar_filtros_build_parquet(gold)

    filas = []
    importadores = set(excl_silver["importador"].dropna()) | set(gold.get("importador", pd.Series(dtype=str)).dropna())
    for imp in importadores:
        excl_s = excl_silver[excl_silver["importador"] == imp]
        val_silver = (gold["importador"] == imp).sum() if "importador" in gold.columns else 0
        excl_b = excl_build[excl_build["importador"] == imp] if "importador" in excl_build.columns else excl_build.iloc[0:0]
        final = (finales["importador"] == imp).sum() if "importador" in finales.columns else 0
        bronze_total = len(excl_s) + val_silver

        filas.append({
            "importador": imp,
            "filas_bronze": bronze_total,
            "excluidas_silver": len(excl_s),
            "validas_silver": val_silver,
            "excluidas_build_parquet": len(excl_b),
            "filas_finales": final,
            "pct_descartado": round((bronze_total - final) / bronze_total * 100, 1) if bronze_total else 0.0,
            "razones_silver": ", ".join(f"{r}({n})" for r, n in excl_s["razon"].value_counts().items()),
            "razones_build": ", ".join(f"{r}({n})" for r, n in excl_b["razon"].value_counts().items()) if len(excl_b) else "",
        })

    tabla = pd.DataFrame(filas).sort_values(["pct_descartado", "filas_bronze"], ascending=[False, False])
    return tabla


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--importador", help="Filtrar por un importador puntual (substring, sin distinguir mayusculas)")
    ap.add_argument("--min-filas", type=int, default=5,
                     help="Ignorar importadores con menos de N filas en bronze (default 5, para no llenar la tabla de ruido de 1 fila)")
    args = ap.parse_args()

    print("Cargando datos...")
    excl_silver = cargar_excluidos_silver()
    gold = cargar_gold_normalizado()

    if gold.empty:
        print("No se encontraron *_normalizado.parquet en data/gold/. Correr el pipeline primero.")
        return 1

    tabla = construir_tabla(excl_silver, gold)
    tabla = tabla[tabla["filas_bronze"] >= args.min_filas]

    if args.importador:
        tabla = tabla[tabla["importador"].str.contains(args.importador, case=False, na=False)]
        pd.set_option("display.max_colwidth", None)
        pd.set_option("display.width", 200)
        for _, r in tabla.iterrows():
            print(f"\n=== {r['importador']} ===")
            print(f"  Filas en bronze:              {r['filas_bronze']}")
            print(f"  Excluidas en silver:          {r['excluidas_silver']}  [{r['razones_silver']}]")
            print(f"  Validas post-silver (a gold): {r['validas_silver']}")
            print(f"  Excluidas en build_parquet:   {r['excluidas_build_parquet']}  [{r['razones_build']}]")
            print(f"  Filas finales:                {r['filas_finales']}")
            print(f"  % descartado:                 {r['pct_descartado']}%")
    else:
        pd.set_option("display.max_rows", None)
        pd.set_option("display.width", 220)
        print(f"\n{len(tabla)} importadores (>= {args.min_filas} filas en bronze), ordenados por %% descartado:\n")
        print(tabla[["importador", "filas_bronze", "filas_finales", "pct_descartado", "razones_silver", "razones_build"]].to_string(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
