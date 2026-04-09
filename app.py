"""Mithril Capital — Simuladores Financeiros."""

import streamlit as st

st.set_page_config(
    page_title="Mithril Capital — Simuladores",
    page_icon="assets/icon.png",
    layout="wide",
)

pg = st.navigation([
    st.Page("views/calculadora_patrimonial.py", title="Calculadora Patrimonial", icon="📊"),
    st.Page("views/imovel_na_planta.py", title="Imóvel na Planta", icon="🏗️"),
])

pg.run()
