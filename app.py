"""
app.py — Punto de entrada Veritrade Imports.
Ejecutar con: streamlit run app.py -- redirige directo al dashboard de Camiones
(no hay pages/1_Maquinaria.py todavía, así que una landing con un solo link
era una parada innecesaria -- liz-z26.2).
"""
import streamlit as st

st.switch_page("pages/2_Camiones.py")
