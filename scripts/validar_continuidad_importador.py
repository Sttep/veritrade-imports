"""
scripts/validar_continuidad_importador.py
═══════════════════════════════════════════
Detecta "ceros sospechosos" (mes sin unidades flanqueado por meses con datos)
por importador, para TODAS las marcas relevantes de camiones.parquet — sin
depender de que la cobertura agregada de la marca contra AAP ya haya caído
bajo el umbral de scripts/validar_cobertura.py.

Motivación (feedback del jefe, 9-jul): SINOTRUK está en EXCEPCIONES de
validar_cobertura.py (cobertura agregada ~91% es el techo real, rezago
metodológico esperado) — eso tapa cualquier gap real de un importador puntual
dentro de esa marca (caso Zapler S.A.C., detectado a mano el 2026-07-08, antes
de que existiera este script). detectar_ceros_sospechosos() solo corría hasta
ahora dentro del diagnóstico de validar_cobertura.py, y solo para marcas que
YA habían caído bajo el umbral — este script la aplica siempre, importador
por importador, marca por marca, sin ese filtro previo.

Solo lectura — no modifica ningún parquet/xlsx.

Uso:
  uv run python scripts/validar_continuidad_importador.py
  uv run python scripts/validar_continuidad_importador.py --marca SINOTRUK
  uv run python scripts/validar_continuidad_importador.py --anio 2026 --mes 6
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

MESES = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
         7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}

# Marcas con menos volumen en VT que esto no vale la pena chequearlas mes a mes
# (con pocas unidades, cualquier mes en 0 es ruido, no señal).
MIN_UNIDADES_MARCA = 20
# Importadores con menos filas que esto en el período generan el mismo ruido.
MIN_FILAS_IMPORTADOR = 5


def detectar_ceros_sospechosos(series_mensual: pd.Series) -> bool:
    """Devuelve True si hay meses con 0 flanqueados por meses con datos.

    Extraída de scripts/validar_cobertura.py (2026-07-09) — validar_cobertura.py
    la importa de acá para no duplicar la lógica."""
    vals = list(series_mensual.values)
    for i in range(1, len(vals) - 1):
        if vals[i] == 0 and vals[i - 1] > 0 and vals[i + 1] > 0:
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--marca", help="Filtrar por una marca puntual (substring, sin distinguir mayúsculas)")
    ap.add_argument("--anio", type=int, default=None, help="Año a analizar (default: último en camiones.parquet)")
    ap.add_argument("--mes", type=int, default=None, help="Mes hasta el que analizar (default: último del año elegido)")
    ap.add_argument("--min-unidades-marca", type=int, default=MIN_UNIDADES_MARCA,
                     help=f"Ignorar marcas con menos de N unidades VT en el período (default {MIN_UNIDADES_MARCA})")
    ap.add_argument("--min-filas-importador", type=int, default=MIN_FILAS_IMPORTADOR,
                     help=f"Ignorar importadores con menos de N filas en el período (default {MIN_FILAS_IMPORTADOR})")
    args = ap.parse_args()

    vt_path = ROOT / "data" / "gold" / "camiones.parquet"
    if not vt_path.exists():
        print("ERROR: no se encontro data/gold/camiones.parquet")
        return 1
    vt = pd.read_parquet(vt_path)

    vt["_dt"] = pd.to_datetime(vt["fecha_dua"], errors="coerce")
    anio = args.anio or int(vt["_dt"].dt.year.max())
    mes_max = args.mes or int(vt[vt["_dt"].dt.year == anio]["_dt"].dt.month.max())
    meses_periodo = list(range(1, mes_max + 1))

    vt_per = vt[(vt["_dt"].dt.year == anio) & (vt["_dt"].dt.month <= mes_max)].copy()
    vt_per["mes"] = vt_per["_dt"].dt.month

    print(f"\n{'=' * 65}")
    print(f"  CONTINUIDAD POR IMPORTADOR  —  Ene-{MESES[mes_max]} {anio}")
    print(f"{'=' * 65}")
    print("  Corre SIEMPRE, sin depender del umbral de marca de validar_cobertura.py")
    print("  -- asi se detectan gaps de importador ocultos dentro de marcas con")
    print("  EXCEPCIONES (ej. SINOTRUK -- ver esa constante en validar_cobertura.py).\n")

    marca_tot = vt_per.groupby("marca_normalizada").size()
    marcas = sorted(marca_tot[marca_tot >= args.min_unidades_marca].index)
    if args.marca:
        marcas = [m for m in marcas if args.marca.upper() in str(m).upper()]

    if not marcas:
        print("  Ninguna marca cumple el filtro / umbral de volumen.")
        return 0

    hallazgos = []
    for marca in marcas:
        sub_marca = vt_per[vt_per["marca_normalizada"] == marca]
        imp_tot = sub_marca.groupby("importador").size()
        importadores = imp_tot[imp_tot >= args.min_filas_importador].sort_values(ascending=False)

        for imp, cnt in importadores.items():
            sub = sub_marca[sub_marca["importador"] == imp]
            por_mes = pd.Series({m: int((sub["mes"] == m).sum()) for m in meses_periodo})
            if detectar_ceros_sospechosos(por_mes):
                meses_str = " ".join(f"{MESES[m]}={int(por_mes[m])}" for m in meses_periodo)
                hallazgos.append({"marca": marca, "importador": imp, "filas": int(cnt), "detalle": meses_str})

    print(f"  {len(marcas)} marca(s) analizadas (>= {args.min_unidades_marca} unidades en el período).\n")

    if not hallazgos:
        print("  Sin ceros sospechosos en ningun importador del periodo analizado.")
    else:
        print(f"  {len(hallazgos)} importador(es) con ceros sospechosos")
        print("  (mes con 0 unidades flanqueado por meses con datos):\n")
        for h in sorted(hallazgos, key=lambda h: -h["filas"]):
            print(f"  [ ] {h['marca']:<18} {h['importador']}  ({h['filas']} filas en el período)")
            print(f"       {h['detalle']}")

    print(f"\n{'=' * 65}")
    print(f"  Parquet: {vt_path.name} | período Ene-{MESES[mes_max]} {anio}")
    print(f"{'=' * 65}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
