"""pipeline/build_parquet.py — Consolida Gold parquet → camiones.parquet

Lee todos los *_normalizado.parquet de data/gold/, los une, deduplica por
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

# Partidas no vehiculares (autos/SUV, maquinaria de construccion, montacargas,
# juguetes a escala) que a veces se cuelan en los exports de Veritrade filtrados
# por importador/rango — no son camiones, se excluyen. Mismo criterio que
# pipeline/silver.py::PARTIDAS_EXCLUIDAS (aca se aplica de nuevo por si el
# parquet se regenera desde gold/*_normalizado.xlsx ya existentes, generados
# antes de que silver.py filtrara esto en origen).
# NOTA: 8716310000 (remolque cisterna) queda afuera a proposito — ver comentario
# en silver.py, esa unica fila es un camion cisterna FAW real mal etiquetado.
PARTIDAS_EXCLUIDAS = {
    "8703229020", "8703210010",
    "8703239020", "8703401000", "8703409020", "8703809020",
    "8703331000", "8703231000", "8703221000", "8703329020",
    "8429520000", "8429510000", "8429590000",
    "8429200000", "8429400000",
    "8427100000", "8427200000", "8428909000",
    "9503003000",
}

# Vans/furgones sobre partidas legitimas de camion liviano — mismo criterio que
# pipeline/silver.py::VANS_EXCLUIDAS, aplicado aca sobre marca_norm/modelo
# (columnas ya normalizadas por el LLM en gold.py).
VANS_EXCLUIDAS: dict[str, list[str]] = {
    "CHEVROLET":     ["N400"],
    "FIAT":          ["FIORINO"],
    "MAXUS":         ["C-100", "C 100", "EV30", "V80", "V90"],
    "DFSK":          ["C35"],
    "WULING":        ["RONGGUANG"],
    "HYUNDAI":       ["STARIA"],
    "TOYOTA":        ["HIACE"],
    "MERCEDES BENZ": ["SPRINTER"],
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exclude", nargs="*", default=[], metavar="PATRON",
                    help="Excluir archivos cuyo nombre contenga estos patrones")
    args = ap.parse_args()

    archivos = sorted(GOLD_DIR.glob("*_normalizado.parquet"))
    if args.exclude:
        archivos = [f for f in archivos
                    if not any(p.lower() in f.name.lower() for p in args.exclude)]

    if not archivos:
        print("❌ No se encontraron archivos *_normalizado.parquet en data/gold/")
        return 1

    print(f"Leyendo {len(archivos)} archivos gold...\n")
    frames = []
    for f in archivos:
        try:
            df = pd.read_parquet(f)
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
            print(f"Excluidas {excluidas:,} filas por partida no vehicular "
                  f"(autos/maquinaria/montacargas/juguetes): {sorted(PARTIDAS_EXCLUIDAS)}")

    if "marca_norm" in out.columns and "modelo" in out.columns:
        marca_up = out["marca_norm"].astype(str).str.upper().str.strip()
        modelo_up = out["modelo"].astype(str).str.upper()
        mask_van = pd.Series(False, index=out.index)
        for marca, patrones in VANS_EXCLUIDAS.items():
            m = marca_up == marca
            m2 = modelo_up.str.contains("|".join(patrones), regex=True, na=False)
            mask_van |= (m & m2)
        if mask_van.any():
            print(f"Excluidas {int(mask_van.sum()):,} filas por van sobre partida de camion liviano")
        out = out[~mask_van].copy()

    if "dua_dam" in out.columns:
        # Coalesce fila por fila: usar chasis solo en las filas donde vin esta vacio,
        # no la columna entera (antes: si la columna "vin" existe se usaba siempre,
        # aunque una fila puntual tuviera vin nulo y chasis con dato real).
        vin_s = out["vin"] if "vin" in out.columns else pd.Series("", index=out.index)
        chasis_s = out["chasis"] if "chasis" in out.columns else pd.Series("", index=out.index)
        vin_final = vin_s.where(vin_s.notna() & (vin_s.astype(str) != ""), chasis_s)
        key = out["dua_dam"].astype(str) + "|" + vin_final.astype(str)
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
