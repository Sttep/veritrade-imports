"""
scripts/migrar_config_carrocerias.py
═══════════════════════════════════════
Agrega a la hoja "carrocerias" de `configuracion.xlsx` los valores de
`carroceria_normalizada` detectados fuera de catálogo por
scripts/validar_calidad_datos.py::check_carroceria_fuera_catalogo (68 filas,
17 valores únicos, 2026-07-09) -- todos mapeados a "OTROS" por decisión del
usuario:

- Grupo 1 (carrocerías reales sin catalogar): VALORES (camión blindado de
  transporte de valores), CAMIÓN MINERO DE CUERPO ANC[HO], SANITARIO,
  GUNITADORA, FACTORIA, ESPARCIDOR DE ASFALTO, BOMBONA, SPRINKLER TRUCK,
  INTERCAMBIADOR, LANZADOR DE CONCRETO, OTROS USOS ESPECIALES, DERUI DRUK 6,
  ÚNICAMENTE CON MOTOR DE ÉM[BOLO].
- Grupo 2 (texto de clasificación legal por peso que Veritrade puso en el
  campo CA: en vez del nombre de la carrocería -- no es un bug nuestro, es
  el dato de origen): SUPERIOR A 9,3T, - SUPERIOR A 9,3 T,
  - SUPERIOR A 6,2 T, PERO I, DE PESO TOTAL CON CARGA MÁ[XIMA...].

Lee los valores exactos directo de camiones.parquet (no se retipean a mano)
para no corromper acentos/ñ en la escritura al xlsx.

Uso:
  uv run python scripts/migrar_config_carrocerias.py              # dry-run
  uv run python scripts/migrar_config_carrocerias.py --apply       # escribe (con backup)
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "configuracion.xlsx"
PARQUET_PATH = ROOT / "data" / "gold" / "camiones.parquet"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                     help="Escribe los cambios en configuracion.xlsx (default: dry-run)")
    args = ap.parse_args()

    df = pd.read_parquet(PARQUET_PATH)
    xl = pd.ExcelFile(CONFIG_PATH)
    sheets = {name: xl.parse(name, dtype=str) for name in xl.sheet_names}
    carrocerias = sheets["carrocerias"]

    validos = set(carrocerias["valor"].dropna().str.upper().str.strip())
    cn = df["carroceria_normalizada"].astype("string").str.upper().str.strip()
    fuera_de_catalogo = sorted(cn[cn.notna() & ~cn.isin(validos)].unique())

    filas_nuevas = [{"clave": v, "valor": "OTROS"} for v in fuera_de_catalogo
                    if not (carrocerias["clave"].str.upper().str.strip() == v).any()]

    print(f"Valores fuera de catálogo encontrados: {len(fuera_de_catalogo)}")
    print(f"Filas nuevas a agregar (clave -> OTROS): {len(filas_nuevas)}")
    for f in filas_nuevas:
        print(f"  + {f['clave']!r} -> OTROS")

    if not args.apply:
        print("\nDry-run -- no se escribió nada. Volver a correr con --apply para aplicar.")
        return 0

    if filas_nuevas:
        carrocerias = pd.concat([carrocerias, pd.DataFrame(filas_nuevas)], ignore_index=True)

    backup_path = CONFIG_PATH.with_suffix(".xlsx.bak")
    shutil.copy2(CONFIG_PATH, backup_path)
    print(f"\nBackup: {backup_path}")

    sheets["carrocerias"] = carrocerias
    with pd.ExcelWriter(CONFIG_PATH, engine="openpyxl") as xw:
        for name, sheet_df in sheets.items():
            sheet_df.to_excel(xw, sheet_name=name, index=False)

    print(f"Escrito: {CONFIG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
