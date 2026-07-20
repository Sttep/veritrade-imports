"""Helpers genéricos de UI para los dashboards Streamlit (Camiones, Maquinaria).

Sin dependencias de columnas/constantes específicas de un dominio -- todo lo
que necesita saber sobre "qué es una marca" o "qué es Sinotruk" se le pasa
como parámetro. Extraído de pages/2_Camiones.py (liz-j0k.1).
"""
from __future__ import annotations

import io

import pandas as pd
import streamlit as st
from pandas.io.formats.style import Styler


def pct(parte: float, total: float, decimales: int = 1) -> float:
    """% share con guarda contra división por cero.

    Reemplaza el patrón `round(parte/total*100, N) if total else 0.0`
    repetido inline en ~10 lugares distintos del dashboard de Camiones.
    """
    return round(parte / total * 100, decimales) if total else 0.0


def calc_var(row, col_act, col_ant):
    ant, act = row[col_ant], row[col_act]
    if ant == 0:
        return "+100%" if act > 0 else "0%"
    return f"{((act-ant)/ant*100):+.1f}%"


def vc_reales(serie: pd.Series) -> pd.Series:
    """Igual que serie.value_counts() pero sin las categorías fantasma en 0
    -- columnas dtype 'category' devuelven TODAS las categorías del dataset
    original con conteo 0 para las que no están en un subset filtrado."""
    vc = serie.value_counts()
    return vc[vc > 0]


def safe_selectbox(label, options, key, **kwargs):
    """Igual que st.selectbox pero resetea la selección persistida si ya no
    está en `options` (ej. se angostó el rango de fechas) -- evita el
    StreamlitAPIException que encontró el fuzzer del dashboard."""
    if key in st.session_state and st.session_state[key] not in options:
        del st.session_state[key]
    return st.selectbox(label, options, key=key, **kwargs)


def descargar_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode('utf-8')


@st.cache_data
def excel_bytes(df_tuple, hoja="Datos") -> bytes:
    df = pd.DataFrame(df_tuple)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        df.to_excel(w, sheet_name=hoja, index=False)
    return buf.getvalue()


def fmt_tabla(df_tabla, extra: dict | None = None):
    """Devuelve un Styler con separador de miles ('{:,.0f}') en columnas
    numéricas y '%' con 1 decimal en las que tienen '%' en el nombre --
    evita que las tablas de informe muestren enteros/porcentajes pelados
    (ej. '5934', '100') al lado de tarjetas KPI que sí formatean.

    Acepta tanto un DataFrame como un Styler ya armado (ej. con
    `.style.apply(...)` para resaltar filas), y un `extra` con overrides de
    formato manuales (ej. precios en '${:,.2f}') que no se pisan.
    """
    styler = df_tabla if isinstance(df_tabla, Styler) else df_tabla.style
    base = styler.data
    fmt = dict(extra or {})
    for col in base.columns:
        if col in fmt or not pd.api.types.is_numeric_dtype(base[col]):
            continue
        fmt[col] = '{:.1f}%' if '%' in col else '{:,.0f}'
    return styler.format(fmt) if fmt else styler


def render_bloque(titulo, fig, df_tabla, key, nombre="datos"):
    raw = df_tabla.data if hasattr(df_tabla, 'data') else df_tabla
    c1, c2 = st.columns([6, 1])
    with c1:
        if titulo:
            st.markdown(f'<div class="section-header"><p class="section-title-text">{titulo}</p></div>',
                        unsafe_allow_html=True)
    with c2:
        with st.popover("📥", use_container_width=True):
            cx, cy = st.columns(2)
            with cx:
                try:
                    st.download_button("xlsx", excel_bytes(tuple(raw.itertuples(index=False)), nombre[:30]),
                                        f"{nombre}.xlsx", key=f"xl_{key}", use_container_width=True)
                except Exception:
                    pass
            with cy:
                try:
                    st.download_button("csv", descargar_csv(raw), f"{nombre}.csv",
                                        key=f"csv_{key}", use_container_width=True)
                except Exception:
                    pass
    if fig:
        st.plotly_chart(fig, use_container_width=True,
                        config={'displayModeBar': True, 'displaylogo': False})
    with st.expander("📊 Ver tabla", expanded=False):
        st.dataframe(fmt_tabla(df_tabla), hide_index=True, use_container_width=True)


def render_kpi_cards(kpis: list[dict]):
    """4 tarjetas KPI nativas (st.metric) -- fondo claro por default, sin CSS
    custom. Cada kpi: {"titulo": str, "valor": str, "subtitulo": str (opcional)}."""
    cols = st.columns(min(len(kpis), 4))
    for col, k in zip(cols, kpis[:4]):
        with col:
            st.metric(k['titulo'], k['valor'])
            if k.get('subtitulo'):
                st.caption(k['subtitulo'])


def tabla_dl(df_tabla: pd.DataFrame, key: str, nombre: str = "datos"):
    """Muestra un dataframe con botones de descarga xlsx/csv debajo."""
    st.dataframe(fmt_tabla(df_tabla), hide_index=True, use_container_width=True)
    cx, cy = st.columns(2)
    with cx:
        try:
            st.download_button("📥 xlsx", excel_bytes(tuple(df_tabla.itertuples(index=False)), nombre[:30]),
                                f"{nombre}.xlsx", key=f"xl_{key}", use_container_width=True)
        except Exception:
            pass
    with cy:
        try:
            st.download_button("📥 csv", descargar_csv(df_tabla), f"{nombre}.csv",
                                key=f"csv_{key}", use_container_width=True)
        except Exception:
            pass
