"""Reporte de calidad del pipeline"""

import pandas as pd

def build(df, stats=None):
    """Construye el reporte de calidad"""
    metricas = []
    
    # 1. Filas de muestra
    metricas.append({"metrica": "filas_muestra", "valor": float(len(df))})
    
    # 2. Porcentaje de llenado de campos
    campos = [
        "modelo", "carroceria", "marca", "traccion", 
        "combustible", "clasificacion", "caja"
    ]
    
    for campo in campos:
        if campo in df.columns:
            pct = df[campo].notna().mean() * 100
            metricas.append({"metrica": f"{campo}_fill_%", "valor": round(pct, 1)})
    
    # 3. Acuerdo con marca
    if 'marca' in df.columns and 'marca_norm' in df.columns:
        acuerdo = (df['marca'].str.upper() == df['marca_norm'].str.upper()).mean() * 100
        metricas.append({"metrica": "acuerdo_marca_%", "valor": round(acuerdo, 1)})
    
    # 4. Marcas fuera de vocabulario
    if 'marca_in_vocab' in df.columns:
        fuera = (~df['marca_in_vocab']).mean() * 100
        metricas.append({"metrica": "marca_fuera_vocab_%", "valor": round(fuera, 1)})
    
    # 5. ✅ CORREGIDO: modelo_flag de forma segura
    if 'modelo_flag' in df.columns:
        try:
            modelo_flag_series = df['modelo_flag'].astype(str)
            for flag, c in modelo_flag_series.value_counts().items():
                metricas.append({"metrica": f"modelo_flag::{flag}", "valor": float(c)})
        except Exception:
            # Si falla, solo ponemos un error y seguimos
            metricas.append({"metrica": "modelo_flag::error", "valor": 0.0})
    else:
        metricas.append({"metrica": "modelo_flag::sin_dato", "valor": float(len(df))})
    
    # 6. Estadísticas del cliente (LLM)
    if stats:
        if hasattr(stats, 'requests'):
            metricas.append({"metrica": "requests", "valor": float(stats.requests)})
        if hasattr(stats, 'errors'):
            metricas.append({"metrica": "errores_batch", "valor": float(stats.errors)})
        if hasattr(stats, 'prompt_tokens'):
            metricas.append({"metrica": "prompt_tokens", "valor": float(stats.prompt_tokens)})
        if hasattr(stats, 'cached_tokens'):
            metricas.append({"metrica": "cached_tokens", "valor": float(stats.cached_tokens)})
        if hasattr(stats, 'completion_tokens'):
            metricas.append({"metrica": "completion_tokens", "valor": float(stats.completion_tokens)})
        
        # Costo estimado
        if hasattr(stats, 'prompt_tokens') and hasattr(stats, 'completion_tokens'):
            costo = (stats.prompt_tokens * 0.0000001 + stats.completion_tokens * 0.0000004)
            metricas.append({"metrica": "costo_estimado_usd", "valor": round(costo, 6)})
    
    return pd.DataFrame(metricas)