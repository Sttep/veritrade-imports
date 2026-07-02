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
st.markdown("**Dashboards de importaciones de vehículos comerciales · Perú**")
st.divider()

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
