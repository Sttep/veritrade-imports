"""
scripts/reparar_peso_bruto_invertido.py
═══════════════════════════════════════
Repara las 2 filas detectadas por scripts/validar_calidad_datos.py::
check_coherencia_peso con peso_neto_desc > peso_bruto_desc (físicamente
imposible) en data/gold/camiones.parquet:

- DUA 001876: descripción cruda trae "PB:18,00,PN:7800,CU:10200" -- el
  parser interpretó "18,00" como 18.00 (coma decimal), pero Neto+Carga =
  7800+10200 = 18000, así que el dato de origen quería decir dieciocho
  mil y perdió un cero en el export de Veritrade.
- DUA 234619: descripción cruda trae "PB:41,PN:15720,CU:25780" -- el
  texto crudo corta después de la coma, sin más dígitos. Neto+Carga =
  15720+25780 = 41500.

No es un bug de nuestro parser -- el dato de origen (texto crudo de
Veritrade) viene incompleto en estas 2 filas puntuales. Se reconstruye
el valor correcto con peso_neto_desc + carga_util (ambos ya parseados
correctamente, sin ambigüedad) en vez de intentar generalizar un patrón
de parseo para un caso de 2 filas.

Uso:
  uv run python scripts/reparar_peso_bruto_invertido.py              # dry-run
  uv run python scripts/reparar_peso_bruto_invertido.py --apply       # escribe el fix
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PARQUET_PATH = ROOT / "data" / "gold" / "camiones.parquet"

DUAS_A_REPARAR = ["001876", "234619"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                     help="Escribe el fix en data/gold/camiones.parquet (default: dry-run)")
    args = ap.parse_args()

    df = pd.read_parquet(PARQUET_PATH)
    dua = df["dua_dam"].astype(str)
    mask = dua.str.startswith(tuple(DUAS_A_REPARAR))

    pn = pd.to_numeric(df.loc[mask, "peso_neto_desc"], errors="coerce")
    cu = pd.to_numeric(df.loc[mask, "carga_util"], errors="coerce")
    pb_nuevo = pn + cu

    print(f"Filas a reparar: {int(mask.sum())}")
    for idx in df.loc[mask].index:
        print(f"  DUA {df.loc[idx, 'dua_dam']}: peso_bruto_desc "
              f"{df.loc[idx, 'peso_bruto_desc']} -> {pb_nuevo.loc[idx]} "
              f"(= peso_neto_desc {df.loc[idx, 'peso_neto_desc']} + carga_util {df.loc[idx, 'carga_util']})")

    if not args.apply:
        print("\nDry-run -- no se escribió nada. Volver a correr con --apply para aplicar el fix.")
        return 0

    df.loc[mask, "peso_bruto_desc"] = pb_nuevo.astype("string")
    df.to_parquet(PARQUET_PATH, index=False)
    print(f"\nEscrito: {PARQUET_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
