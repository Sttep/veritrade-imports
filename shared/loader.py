"""Cargadores de datos centralizados para los dashboards Streamlit.

Lee exclusivamente desde la capa Gold (data/gold/).
Si el parquet no existe, cae al Silver como fallback.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT       = Path(__file__).resolve().parent.parent
GOLD_DIR   = ROOT / "data" / "gold"
SILVER_DIR = ROOT / "data" / "silver"

MESES_NOMBRES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']

MAPEO_COLUMNAS_MAQUINARIA = {
    'marca_norm':       ['marca_norm', 'marca_normalizada'],
    'modelo':           ['modelo_match', 'modelo'],
    'categoria_peso':   ['categoria_peso', 'rango_peso', 'capacidad'],
    'grupo_importador': ['grupo_importador', 'importador_grupo', 'importador'],
    'valor_fob':        ['valor_fob', 'fob', 'fob_usd'],
    'valor_cif':        ['valor_cif', 'cif', 'cif_usd'],
}

MAPEO_COLUMNAS_CAMIONES = {
    'marca_norm':          ['marca_norm', 'marca_normalizada', 'marca_declarada'],
    'modelo':              ['modelo_match', 'modelo', 'modelo_norm'],
    'categoria_maquinaria':['categoria_maquinaria', 'carroceria_normalizada', 'carroceria'],
    'grupo_importador':    ['grupo_importador', 'importador_grupo', 'importador'],
    'valor_fob':           ['valor_fob', 'fob', 'fob_usd'],
    'valor_cif':           ['valor_cif', 'cif', 'cif_usd'],
    'pb':                  ['peso_bruto_desc'],  # kg_bruto_col/kg_bruto es peso NETO, no bruto -- no usar como fallback
}


def _normalizar_columnas(df: pd.DataFrame, mapeo: dict) -> pd.DataFrame:
    df = df.copy()
    for std, posibles in mapeo.items():
        for nombre in posibles:
            if nombre in df.columns:
                if nombre != std:
                    df = df.rename(columns={nombre: std})
                break
    return df


def cargar_maquinaria() -> tuple[pd.DataFrame, float | None, bool]:
    """Carga datos de maquinaria desde Gold → Silver como fallback.

    Returns:
        (df, ultima_actualizacion, falta_columna_fecha)
    """
    ruta_parquet = GOLD_DIR / "maquinaria.parquet"
    if ruta_parquet.exists():
        df = pd.read_parquet(ruta_parquet)
        ultima = ruta_parquet.stat().st_mtime
    else:
        archivos = sorted(GOLD_DIR.glob("*_normalizado.parquet"))
        if not archivos:
            return pd.DataFrame(), None, False
        dfs = []
        for f in archivos:
            try:
                dfs.append(pd.read_parquet(f))
            except Exception:
                pass
        if not dfs:
            return pd.DataFrame(), None, False
        df = pd.concat(dfs)
        ultima = max(f.stat().st_mtime for f in archivos)

    if "fecha_dua" not in df.columns:
        return pd.DataFrame(), None, True

    df["fecha"] = pd.to_datetime(df["fecha_dua"])
    df["año"]   = df["fecha"].dt.year
    df["mes"]   = df["fecha"].dt.month
    df["mes_nombre"] = df["mes"].map({i + 1: m for i, m in enumerate(MESES_NOMBRES)})
    df = _normalizar_columnas(df, MAPEO_COLUMNAS_MAQUINARIA)
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]

    for col in ["categoria_maquinaria", "marca_norm", "modelo", "grupo_importador", "categoria_peso"]:
        if col in df.columns:
            try:
                serie = df[col].iloc[:, 0] if isinstance(df[col], pd.DataFrame) else df[col]
                df[col] = serie.astype(str).str.upper().str.strip()
                df[col] = df[col].replace(["NAN", "NONE", "NULL", "", " "], pd.NA)
            except Exception:
                pass

    for c in ["valor_fob", "valor_cif"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    for col in ["categoria_maquinaria", "marca_norm", "grupo_importador"]:
        if col in df.columns:
            df[col] = df[col].astype("category")

    return df, ultima, False


def cargar_camiones() -> tuple[pd.DataFrame, float | None]:
    """Carga datos de camiones desde Gold → Silver como fallback."""
    ruta_parquet = GOLD_DIR / "camiones.parquet"
    if ruta_parquet.exists():
        df = pd.read_parquet(ruta_parquet)
        ultima = ruta_parquet.stat().st_mtime
    else:
        archivos = sorted(SILVER_DIR.glob("*_fase1.parquet"))
        if not archivos:
            return pd.DataFrame(), None
        frames, ultima = [], 0
        for f in archivos:
            try:
                d = pd.read_parquet(f)
                frames.append(d)
                ultima = max(ultima, f.stat().st_mtime)
            except Exception:
                pass
        if not frames:
            return pd.DataFrame(), None
        df = pd.concat(frames, ignore_index=True)

    if "dua_dam" in df.columns:
        df["_k"] = df.apply(
            lambda r: f"{r.get('dua_dam', '')}|{r.get('vin') or r.get('chasis') or ''}",
            axis=1,
        )
        df = df.drop_duplicates("_k").drop(columns="_k")

    if "fecha_dua" in df.columns:
        df["fecha"]      = pd.to_datetime(df["fecha_dua"], errors="coerce")
        df["año"]        = df["fecha"].dt.year.astype("Int64")
        df["mes"]        = df["fecha"].dt.month.astype("Int64")
        df["mes_nombre"] = df["mes"].map({i + 1: m for i, m in enumerate(MESES_NOMBRES)})

    df = _normalizar_columnas(df, MAPEO_COLUMNAS_CAMIONES)
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]

    if "año" in df.columns:
        df["año"] = df["año"].apply(lambda x: int(x) if pd.notna(x) else pd.NA).astype("Int64")

    for col in ["categoria_maquinaria", "marca_norm", "grupo_importador"]:
        if col in df.columns:
            df[col] = df[col].astype("category")

    return df, ultima
