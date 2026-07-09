"""
scripts/reparar_carroceria.py
═══════════════════════════════════════
Repara retroactivamente en data/gold/camiones.parquet las 68 filas cuyo
`carroceria_normalizada` estaba fuera del catálogo de configuracion.xlsx
(detectado por scripts/validar_calidad_datos.py::check_carroceria_fuera_catalogo)
-- ya corregido para archivos nuevos vía scripts/migrar_config_carrocerias.py
(hoja "carrocerias" de configuracion.xlsx).

Regresión verificada antes de este script: recalcular normalizar_carroceria()
con la config actualizada contra las 61,160 filas del parquet solo cambia
las 68 filas esperadas -- 0 efectos colaterales sobre el resto.

Uso:
  uv run python scripts/reparar_carroceria.py              # dry-run, solo reporta
  uv run python scripts/reparar_carroceria.py --apply       # escribe el fix
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PARQUET_PATH = ROOT / "data" / "gold" / "camiones.parquet"

sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                     help="Escribe el fix en data/gold/camiones.parquet (default: dry-run)")
    args = ap.parse_args()

    from pipeline.silver import Config, normalizar_carroceria

    cfg = Config()
    df = pd.read_parquet(PARQUET_PATH)

    xl = pd.ExcelFile(ROOT / "configuracion.xlsx").parse("carrocerias", dtype=str)
    validos = set(xl["valor"].dropna().str.upper().str.strip())
    cn = df["carroceria_normalizada"].astype("string").str.upper().str.strip()
    afectadas = cn.notna() & ~cn.isin(validos)

    print(f"Filas con carroceria_normalizada fuera de catálogo: {int(afectadas.sum()):,}")
    print(cn[afectadas].value_counts().to_string())

    nuevo_valor = df.loc[afectadas, "carroceria"].apply(lambda v: normalizar_carroceria(v, cfg))
    n_a_otros = int((nuevo_valor == "OTROS").sum())
    n_otro_resultado = int(afectadas.sum()) - n_a_otros
    print(f"\n-> resuelven a OTROS: {n_a_otros:,}")
    if n_otro_resultado:
        print(f"-> AVISO: {n_otro_resultado} filas no resuelven a OTROS -- revisar antes de aplicar")

    if not args.apply:
        print("\nDry-run -- no se escribió nada. Volver a correr con --apply para aplicar el fix.")
        return 0

    df.loc[afectadas, "carroceria_normalizada"] = nuevo_valor
    df.to_parquet(PARQUET_PATH, index=False)
    print(f"\nEscrito: {PARQUET_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
