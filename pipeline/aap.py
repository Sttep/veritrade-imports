"""
pipeline/aap.py  —  ETL de archivos AAP (Asociación Automotriz del Perú)
════════════════════════════════════════════════════════════════════════

Lee los reportes mensuales de la AAP desde refs/*.xlsx,
normaliza marcas para que sean comparables con Veritrade,
y guarda data/gold/aap_camiones.parquet.

Uso:
  python pipeline/aap.py
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pandas as pd

ROOT     = Path(__file__).resolve().parent.parent
REFS_DIR = ROOT / "refs"
GOLD_DIR = ROOT / "data" / "gold"

MESES_ORDEN = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
               "JULIO", "AGOSTO", "SETIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
MESES_NUM   = {m: i + 1 for i, m in enumerate(MESES_ORDEN)}

# Normalización de marcas AAP → nombre canónico comparable con Veritrade
# AAP a veces registra submarcas Sinotruk por separado
MARCA_NORM: dict[str, str] = {
    "HOWO":        "SINOTRUK",
    "SITRAK":      "SINOTRUK",
    "SINOTRUCK":   "SINOTRUK",
    "HONAN":       "SINOTRUK",
    "HOMAN":       "SINOTRUK",
    "MERCEDES BENZ": "MERCEDES-BENZ",
    "MERCEDESBENZ":  "MERCEDES-BENZ",
}

CLASES_CAMIONES = {"CAMIONES Y TRACTO"}


def _detect_year(path: Path) -> int | None:
    """Extrae el año del nombre del archivo (ej. ...-2026-...)."""
    import re
    m = re.search(r"20\d{2}", path.stem)
    return int(m.group()) if m else None


def parse_aap_file(path: Path) -> pd.DataFrame | None:
    """Parsea un archivo AAP y retorna un DataFrame long con columnas:
    año, mes, mes_num, marca_aap, marca_norm, carroceria, categoria, unidades, fuente
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            xl = pd.ExcelFile(path)
        except Exception as e:
            print(f"  ⚠ No se pudo leer {path.name}: {e}")
            return None

    if "BASE" not in xl.sheet_names:
        print(f"  ⚠ Sin hoja BASE en {path.name}")
        return None

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = xl.parse("BASE", header=0)

    year = _detect_year(path)

    # Detectar columnas de meses presentes
    meses_presentes = [m for m in MESES_ORDEN if m in df.columns]
    if not meses_presentes:
        print(f"  ⚠ Sin columnas de mes en {path.name}")
        return None

    # Filtrar camiones nuevos
    mask = (
        df["CLASE AAP"].isin(CLASES_CAMIONES)
        & (df["ESTADO"].str.strip().str.upper() == "NUEVO")
    )
    cam = df[mask].copy()

    if cam.empty:
        print(f"  ⚠ Sin filas de camiones nuevos en {path.name}")
        return None

    # Convertir meses a numérico
    for m in meses_presentes:
        cam[m] = pd.to_numeric(cam[m], errors="coerce").fillna(0)

    # Melt a formato long
    long = cam.melt(
        id_vars=["CLASE AAP", "SUB-CLASE", "CARROCERIA", "MARCA", "MODELO",
                 "CATEGORIA", "COMBUSTIBLE", "ORIGEN"],
        value_vars=meses_presentes,
        var_name="mes_nombre",
        value_name="unidades",
    )
    long = long[long["unidades"] > 0].copy()

    long["mes_num"] = long["mes_nombre"].map(MESES_NUM)
    long["año"]     = year

    # Normalizar marcas
    long["marca_aap"]  = long["MARCA"].str.strip().str.upper()
    long["marca_norm"] = long["marca_aap"].map(
        lambda m: MARCA_NORM.get(m, m)
    )

    long = long.rename(columns={
        "CARROCERIA": "carroceria",
        "CATEGORIA":  "categoria",
        "SUB-CLASE":  "sub_clase",
        "MODELO":     "modelo",
        "COMBUSTIBLE": "combustible",
        "ORIGEN":     "origen",
    })

    long["fuente"] = path.name

    return long[[
        "año", "mes_num", "mes_nombre",
        "marca_aap", "marca_norm",
        "carroceria", "sub_clase", "categoria",
        "modelo", "combustible", "origen",
        "unidades", "fuente",
    ]]


def main() -> int:
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    archivos = sorted(REFS_DIR.glob("*.xlsx"))
    if not archivos:
        print(f"❌ No se encontraron archivos en {REFS_DIR}/")
        return 1

    print("\n" + "=" * 55)
    print("  AAP ETL -> data/gold/aap_camiones.parquet")
    print("=" * 55)
    print(f"  {len(archivos)} archivo(s) encontrado(s)\n")

    frames = []
    for path in archivos:
        print(f"  Procesando: {path.name}")
        df = parse_aap_file(path)
        if df is not None:
            frames.append(df)
            año = df["año"].iloc[0] if "año" in df.columns and df["año"].notna().any() else "?"
            meses = sorted(df["mes_num"].unique())
            print(f"    OK {len(df)} filas | anio {año} | meses {meses}")

    if not frames:
        print("❌ Sin datos para procesar")
        return 1

    out = pd.concat(frames, ignore_index=True)

    # Resumen de totales
    print(f"\n  Total filas long: {len(out):,}")
    totales = (
        out.groupby("marca_norm")["unidades"]
        .sum()
        .sort_values(ascending=False)
        .head(15)
    )
    print("\n  Top 15 marcas (unidades totales):")
    for marca, n in totales.items():
        print(f"    {marca:<25} {n:>6.0f}")

    out_path = GOLD_DIR / "aap_camiones.parquet"
    out.to_parquet(out_path, index=False)
    print(f"\n  OK Escrito -> {out_path.relative_to(ROOT)}")
    print("=" * 55 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
