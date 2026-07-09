"""
scripts/reparar_cc_punto.py
═══════════════════════════════════════
Repara el bug de tokenización de "CC.2771" (punto en vez de ":") en
pipeline/silver.py::CC_PUNTO_PATTERN, corregido el 2026-07-09.

Contexto: CODE_PATTERN exige "[:=]" como frontera de código. Cuando la
descripción cruda trae "NC:4, CC.2771, CO:DIESEL" (punto en vez de ":"
después de CC), el valor de NC (num_cilindros) se extiende greedy hasta
CO: y captura "4, CC.2771"; _convertir() para tipo "int" prioriza el primer
grupo de 4 dígitos, así que num_cilindros termina en 2771 (absurdo) y
cilindrada_cc queda vacío (el dato real se pierde). El fix en silver.py ya
corrige esto para archivos bronze nuevos; esta reparación re-parsea las
filas ya afectadas en data/gold/camiones.parquet usando la misma función
del pipeline (parsear_descripcion), a partir de la columna `_descripcion`
ya persistida -- no hace falta el bronze original.

Uso:
  uv run python scripts/reparar_cc_punto.py              # dry-run, solo reporta
  uv run python scripts/reparar_cc_punto.py --apply       # escribe el fix en camiones.parquet
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.silver import parsear_descripcion  # noqa: E402

PARQUET_PATH = ROOT / "data" / "gold" / "camiones.parquet"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                     help="Escribe el fix en data/gold/camiones.parquet (default: dry-run)")
    args = ap.parse_args()

    df = pd.read_parquet(PARQUET_PATH)
    desc = df["_descripcion"].astype("string")

    afectadas = desc.str.contains(r"CC\.\s*\d", case=False, regex=True, na=False)
    n_afectadas = int(afectadas.sum())
    if n_afectadas == 0:
        print("No se encontraron filas con 'CC.' en `_descripcion`. Nada que reparar.")
        return 0

    reparsed = desc.loc[afectadas].map(parsear_descripcion)
    nc_nuevo = reparsed.map(lambda r: r.get("num_cilindros"))
    cc_nuevo = reparsed.map(lambda r: r.get("cilindrada_cc"))

    nc_actual = pd.to_numeric(df.loc[afectadas, "num_cilindros"], errors="coerce")
    nc_nuevo_num = pd.to_numeric(nc_nuevo, errors="coerce")
    n_nc_cambia = int((nc_actual != nc_nuevo_num).sum())
    n_cc_poblado = int(cc_nuevo.notna().sum())

    print(f"Filas con 'CC.' en la descripción cruda:  {n_afectadas:,}")
    print(f"  -> num_cilindros se corrige:             {n_nc_cambia:,}")
    print(f"  -> cilindrada_cc se completa:             {n_cc_poblado:,}")
    print("\nMuestra (antes -> después):")
    muestra = pd.DataFrame({
        "num_cilindros_antes": df.loc[afectadas, "num_cilindros"],
        "num_cilindros_despues": nc_nuevo,
        "cilindrada_cc_despues": cc_nuevo,
    }).head(10)
    print(muestra.to_string())

    if not args.apply:
        print("\nDry-run -- no se escribió nada. Volver a correr con --apply para aplicar el fix.")
        return 0

    # El parquet persiste ambas columnas como texto en formato "N.0"
    # (write_parquet_str_safe, ver pipeline/parquet_io.py) -- se escribe en
    # el mismo formato para no romper el resto del dataset.
    df.loc[afectadas, "num_cilindros"] = nc_nuevo_num.map(
        lambda x: f"{x:.1f}" if pd.notna(x) else pd.NA
    )
    df.loc[afectadas, "cilindrada_cc"] = pd.to_numeric(cc_nuevo, errors="coerce").map(
        lambda x: f"{x:.1f}" if pd.notna(x) else pd.NA
    )

    df.to_parquet(PARQUET_PATH, index=False)
    print(f"\nEscrito: {PARQUET_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
