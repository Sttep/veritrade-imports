"""pipeline/parquet_io.py — Escritura segura de parquet para silver.py / gold.py."""
from __future__ import annotations
from pathlib import Path
import pandas as pd


def write_parquet_str_safe(df: pd.DataFrame, path: Path) -> None:
    """Escribe df a parquet forzando todas las columnas a string/None.

    Evita pyarrow.ArrowTypeError en columnas de tipo mixto dentro de una
    misma corrida (ej. silver 'potencia': a veces float, a veces '150 HP'
    como string) y mantiene el mismo contrato "todo string, coercionar
    aguas abajo" que build_parquet.py / shared/loader.py ya asumian
    (antes via dtype=str en pd.read_excel).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if df.empty:
        pd.DataFrame(columns=df.columns).to_parquet(path, index=False)
        return
    safe = df.copy()
    for col in safe.columns:
        s = safe[col]
        null_mask = s.isna()
        safe[col] = s.astype(str).where(~null_mask, None)
    safe.to_parquet(path, index=False)
