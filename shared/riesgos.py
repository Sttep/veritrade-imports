"""Adaptadores cacheados para Streamlit de los scripts de auditoría de riesgo.

Los 3 scripts fuente (scripts/validar_continuidad_importador.py,
scripts/detectar_conflictos_exclusion.py, scripts/auditar_embudo_importador.py)
siguen funcionando standalone por CLI sin cambios de comportamiento -- este
módulo solo envuelve sus funciones ya extraídas con @st.cache_data(ttl=3600)
para que el dashboard (pages/2_Camiones.py, sección "Riesgos") no las
recalcule en cada rerun.

OJO -- disponibilidad de datos por entorno: `detectar_conflictos_exclusion` y
la parte "excluidas_silver" de `auditar_embudo_importador` leen
data/silver/*_qa.xlsx, que NO está versionado en git (.gitignore). En
Streamlit Cloud (solo despliega data/gold/) esos archivos no existen: usar
`hay_qa_silver()` para decidir si mostrar el resultado o un aviso de "no
disponible en este entorno" en vez de un silencioso "sin hallazgos" que se
podría confundir con "todo bien". `obtener_alertas_continuidad()` (basada en
data/gold/camiones.parquet, sí versionado) funciona igual en local y en Cloud.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.auditar_embudo_importador import (  # noqa: E402
    cargar_excluidos_silver, cargar_gold_normalizado, construir_tabla,
)
from scripts.detectar_conflictos_exclusion import (  # noqa: E402
    cargar_excluidos_por_razon_carroceria_marca_texto, construir_tabla_conflictos,
)
from scripts.validar_continuidad_importador import (  # noqa: E402
    construir_hallazgos_continuidad,
)


def hay_qa_silver() -> bool:
    """True si hay al menos un data/silver/*_qa.xlsx en este entorno."""
    return bool(list((ROOT / "data" / "silver").glob("*_qa.xlsx")))


@st.cache_data(ttl=3600)
def obtener_periodo_riesgos() -> tuple[int, int] | None:
    """(año, mes_max) que analizan las tablas de Riesgos -- Ene-mes_max del
    último año con datos en camiones.parquet. Para mostrarlo de forma visible
    en el dashboard (liz-z26.8), ya que es distinto del filtro de fecha global."""
    vt_path = ROOT / "data" / "gold" / "camiones.parquet"
    if not vt_path.exists():
        return None
    vt = pd.read_parquet(vt_path, columns=["fecha_dua"])
    dt = pd.to_datetime(vt["fecha_dua"], errors="coerce")
    anio = int(dt.dt.year.max())
    mes_max = int(dt[dt.dt.year == anio].dt.month.max())
    return anio, mes_max


@st.cache_data(ttl=3600)
def obtener_alertas_continuidad(marcas_filtro: tuple[str, ...] | None = None) -> pd.DataFrame:
    """Ceros sospechosos por importador, período completo disponible en
    camiones.parquet -- NO usa el rango de fechas del filtro global del
    dashboard, siempre analiza Ene-(último mes con datos) del último año.

    Si `marcas_filtro` viene, corre 1 vez por marca (para acotar a la familia
    Sinotruk cuando el dashboard está en modo Vista=Sinotruk)."""
    vt_path = ROOT / "data" / "gold" / "camiones.parquet"
    if not vt_path.exists():
        return pd.DataFrame(columns=["marca", "importador", "filas", "detalle",
                                      "meses_accion", "categoria"])
    vt = pd.read_parquet(vt_path)
    vt["_dt"] = pd.to_datetime(vt["fecha_dua"], errors="coerce")
    anio = int(vt["_dt"].dt.year.max())
    mes_max = int(vt[vt["_dt"].dt.year == anio]["_dt"].dt.month.max())

    if marcas_filtro:
        hallazgos: list[dict] = []
        for marca in marcas_filtro:
            h, _ = construir_hallazgos_continuidad(vt, anio, mes_max, marca_filtro=marca)
            hallazgos.extend(h)
    else:
        hallazgos, _ = construir_hallazgos_continuidad(vt, anio, mes_max)

    if not hallazgos:
        return pd.DataFrame(columns=["marca", "importador", "filas", "detalle",
                                      "meses_accion", "categoria"])
    return pd.DataFrame(hallazgos)


@st.cache_data(ttl=3600)
def obtener_conflictos_exclusion(min_filas: int = 10) -> pd.DataFrame:
    """Términos de exclusión que caen en partidas de camión legítimo.
    Vacío si no hay data/silver/*_qa.xlsx en este entorno -- chequear
    `hay_qa_silver()` antes de mostrar el resultado como "sin hallazgos"."""
    excl = cargar_excluidos_por_razon_carroceria_marca_texto()
    if excl.empty:
        return pd.DataFrame(columns=["tipo", "termino", "filas_excluidas_total",
                                      "filas_en_partida_camion_legitima",
                                      "pct_en_partida_legitima", "partidas_legitimas_afectadas"])
    return construir_tabla_conflictos(excl, min_filas=min_filas)


@st.cache_data(ttl=3600)
def obtener_embudo_importador(min_filas: int = 5) -> pd.DataFrame:
    """Embudo bronze->silver->gold por importador, ordenado por % descartado.
    Sin data/silver/*_qa.xlsx en este entorno, la columna `excluidas_silver`
    queda en 0 para todos (no significa que nada se excluyó ahí) -- chequear
    `hay_qa_silver()` antes de interpretar esa columna."""
    excl_silver = cargar_excluidos_silver()
    gold = cargar_gold_normalizado()
    if gold.empty:
        return pd.DataFrame()
    tabla = construir_tabla(excl_silver, gold)
    return tabla[tabla["filas_bronze"] >= min_filas]
