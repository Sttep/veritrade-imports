"""Reporte de calidad del pipeline Gold."""

import pandas as pd


def build(df, stats=None):
    metricas = []

    metricas.append({"metrica": "filas_muestra", "valor": float(len(df))})

    campos = ["modelo", "carroceria", "marca", "traccion", "combustible", "clasificacion", "caja"]
    for campo in campos:
        if campo in df.columns:
            pct = df[campo].notna().mean() * 100
            metricas.append({"metrica": f"{campo}_fill_%", "valor": round(pct, 1)})

    if 'marca' in df.columns and 'marca_norm' in df.columns:
        acuerdo = (df['marca'].str.upper() == df['marca_norm'].str.upper()).mean() * 100
        metricas.append({"metrica": "acuerdo_marca_%", "valor": round(acuerdo, 1)})

    if 'marca_in_vocab' in df.columns:
        fuera = (~df['marca_in_vocab']).mean() * 100
        metricas.append({"metrica": "marca_fuera_vocab_%", "valor": round(fuera, 1)})

    if 'modelo_flag' in df.columns:
        try:
            modelo_flag_series = df['modelo_flag'].astype(str)
            for flag, c in modelo_flag_series.value_counts().items():
                metricas.append({"metrica": f"modelo_flag::{flag}", "valor": float(c)})
        except Exception:
            metricas.append({"metrica": "modelo_flag::error", "valor": 0.0})
    else:
        metricas.append({"metrica": "modelo_flag::sin_dato", "valor": float(len(df))})

    if stats:
        for attr in ("requests", "errors", "prompt_tokens", "cached_tokens", "completion_tokens"):
            if hasattr(stats, attr):
                metricas.append({"metrica": attr, "valor": float(getattr(stats, attr))})

        if hasattr(stats, 'prompt_tokens') and hasattr(stats, 'completion_tokens'):
            costo = (stats.prompt_tokens * 0.0000001 + stats.completion_tokens * 0.0000004)
            metricas.append({"metrica": "costo_estimado_usd", "valor": round(costo, 6)})

    return pd.DataFrame(metricas)
