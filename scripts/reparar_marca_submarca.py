"""
scripts/reparar_marca_submarca.py
═══════════════════════════════════════
Repara retroactivamente la fragmentación de marca en data/gold/camiones.parquet
(ver sección 6 de informe_auditoria_comercial.md), en línea con la consolidación
ya aplicada en configuracion.xlsx (scripts/migrar_config_marcas.py) y
data/vocab_extra.json (scripts/migrar_vocab_marcas.py) para archivos nuevos.

Dos cambios, independientes entre sí:
- `submarca` (columna nueva): copia directa de `marca_declarada` -- el texto
  tal cual lo declaró cada importador, sin normalizar. Reemplaza a
  `submarca_sinotruk` (que mapeaba a un puñado de buckets curados).
- `marca_norm` (remapeo): consolida SINOTRUK/IVECO/PEREYRA. KAMA/KAMAZ NO se
  tocan (decisión de negocio: son marcas distintas).

A diferencia del fix de AÑO (scripts/reparar_anio_modelo.py), acá no hay
riesgo sobre `modelo`/`modelo_match` -- este script solo toca `marca_norm` y
`submarca`.

Uso:
  uv run python scripts/reparar_marca_submarca.py              # dry-run, solo reporta
  uv run python scripts/reparar_marca_submarca.py --apply       # escribe el fix
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PARQUET_PATH = ROOT / "data" / "gold" / "camiones.parquet"

MARCA_REMAP = {
    "HOWO": "SINOTRUK",
    "HOWO MAX": "SINOTRUK",
    "SINOTRUK HOWO": "SINOTRUK",
    "SINOTRUCK HOWO": "SINOTRUK",
    "SITRAK": "SINOTRUK",
    "WANGPAI": "SINOTRUK",
    "SINOTRUK WANGPAI": "SINOTRUK",
    "SINOTRUCK": "SINOTRUK",
    "HOMAN": "SINOTRUK",
    "HONAN": "SINOTRUK",
    "SINOTRUK HONAN": "SINOTRUK",
    "IVECO ASTRA": "IVECO",
    "ASTRA": "IVECO",
    "PEREYRA": "CP PEREYRA",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                     help="Escribe el fix en data/gold/camiones.parquet (default: dry-run)")
    args = ap.parse_args()

    df = pd.read_parquet(PARQUET_PATH)
    marca_norm = df["marca_norm"].astype("string").str.upper().str.strip()

    remap_series = marca_norm.map(MARCA_REMAP)
    afectadas_marca = remap_series.notna()
    n_marca = int(afectadas_marca.sum())

    print("Filas por marca_norm vieja que se van a remapear:")
    print(marca_norm[afectadas_marca].value_counts().to_string())
    print(f"\nTotal filas con marca_norm remapeado: {n_marca:,}")

    tiene_submarca_vieja = "submarca_sinotruk" in df.columns
    n_submarca = int(df["marca_declarada"].notna().sum())
    print(f"Filas con `submarca` a poblar (copia de marca_declarada): {n_submarca:,} de {len(df):,}")
    print(f"Columna vieja `submarca_sinotruk` presente: {tiene_submarca_vieja} (se elimina)")

    if not args.apply:
        print("\nDry-run -- no se escribió nada. Volver a correr con --apply para aplicar el fix.")
        return 0

    df["submarca"] = df["marca_declarada"]
    df.loc[afectadas_marca, "marca_norm"] = remap_series[afectadas_marca]
    if tiene_submarca_vieja:
        df = df.drop(columns=["submarca_sinotruk"])

    df.to_parquet(PARQUET_PATH, index=False)
    print(f"\nEscrito: {PARQUET_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
