"""pipeline/build_parquet.py — Consolida Gold xlsx → camiones.parquet

Lee todos los *_normalizado.xlsx de data/gold/, los une, deduplica por
DUA+VIN y escribe data/gold/camiones.parquet listo para el dashboard.

Uso:
  python pipeline/build_parquet.py
  python pipeline/build_parquet.py --exclude "EURO MOTORS"
"""
from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT     = Path(__file__).resolve().parent.parent
GOLD_DIR = ROOT / "data" / "gold"

# Partidas no vehiculares (autos/SUV) que a veces se cuelan en los exports de
# Veritrade filtrados por importador/rango — no son camiones, se excluyen.
# Mismo criterio que pipeline/silver.py::PARTIDAS_EXCLUIDAS (aca se aplica de
# nuevo por si el parquet se regenera desde gold/*_normalizado.xlsx ya
# existentes, generados antes de que silver.py filtrara esto en origen).
PARTIDAS_EXCLUIDAS = {"8703229020", "8703210010"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exclude", nargs="*", default=[], metavar="PATRON",
                    help="Excluir archivos cuyo nombre contenga estos patrones")
    args = ap.parse_args()

    archivos = sorted(GOLD_DIR.glob("*_normalizado.xlsx"))
    if args.exclude:
        archivos = [f for f in archivos
                    if not any(p.lower() in f.name.lower() for p in args.exclude)]

    if not archivos:
        print("❌ No se encontraron archivos *_normalizado.xlsx en data/gold/")
        return 1

    print(f"Leyendo {len(archivos)} archivos gold...\n")
    frames = []
    for f in archivos:
        try:
            df = pd.read_excel(f, sheet_name="normalizado_final", dtype=str)
            df["_fuente"] = f.stem
            frames.append(df)
            print(f"  ✓ {f.name}  ({len(df):,} filas)")
        except Exception as e:
            print(f"  ⚠ {f.name}: {e}")

    if not frames:
        print("❌ Ningún archivo pudo leerse.")
        return 1

    out = pd.concat(frames, ignore_index=True)
    print(f"\nTotal antes de dedup: {len(out):,} filas")

    if "partida" in out.columns:
        antes = len(out)
        out = out[~out["partida"].astype(str).isin(PARTIDAS_EXCLUIDAS)].copy()
        excluidas = antes - len(out)
        if excluidas:
            print(f"Excluidas {excluidas:,} filas por partida no vehicular (autos): "
                  f"{sorted(PARTIDAS_EXCLUIDAS)}")

    if "dua_dam" in out.columns:
        vin_col = next((c for c in ("vin", "chasis") if c in out.columns), None)
        key = out["dua_dam"].astype(str) + "|" + (out[vin_col].astype(str) if vin_col else "")
        out = out[~key.duplicated(keep="first")].copy()
        print(f"Total después de dedup: {len(out):,} filas")

    dest = GOLD_DIR / "camiones.parquet"
    if dest.exists():
        bak = GOLD_DIR / f"camiones.parquet.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(dest, bak)
        print(f"\nBackup: {bak.name}")

    out.to_parquet(dest, index=False)
    print(f"✅ Escrito: data/gold/camiones.parquet  ({dest.stat().st_size / 1_048_576:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
