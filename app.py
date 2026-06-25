"""
app.py — Punto de entrada multi-página Veritrade Imports.
Ejecutar con: streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="Veritrade Imports · Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container { padding: 2rem 2rem !important; max-width: 900px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 📊 Veritrade Imports")
st.markdown("**Dashboards de importaciones de vehículos comerciales y maquinaria pesada · Perú**")
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🚜 Maquinaria Pesada
    Excavadoras, cargadores frontales, bulldozers,
    compactadores, motoniveladoras y retroexcavadoras.

    Análisis de market share, competencia y evolución
    de precios FOB/CIF por marca y segmento.
    """)
    st.page_link("pages/1_Maquinaria.py", label="Abrir Dashboard Maquinaria", icon="🚜")

with col2:
    st.markdown("""
    ### 🚛 Camiones y Vehículos Comerciales
    Tractocamiones, chasis cabina, volquetes,
    hormigoneras, grúas, cisternas y furgones.

    Análisis por carrocería, peso bruto, marca,
    importador y familia Sinotruk/Withmory.
    """)
    st.page_link("pages/2_Camiones.py", label="Abrir Dashboard Camiones", icon="🚛")

st.divider()
st.caption("Fuente: Veritrade · Pipeline: Bronze → Silver → Gold · Arquitectura Medallón")
