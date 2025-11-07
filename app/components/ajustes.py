from services.grupos import grupos
import streamlit as st
from pathlib import Path
import pandas as pd

def ajustes():
    # ---------- CONFIGURACIÓN ----------
    st.set_page_config(page_title="Rainly", layout="wide", initial_sidebar_state="auto")
    # ---------- CSS (externo) ----------
    _css_general = Path(__file__).parent.parent / 'assets' / 'general.css'      
    _css_ajustes = Path(__file__).parent.parent / 'assets' / 'ajustes.css'
    
    try:
        with open(_css_general, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        with open(_css_ajustes, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
    except Exception as _e:
        st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
        """, unsafe_allow_html=True)

    st.markdown('<div class="page-header">Ajustes</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Grupos", "Usuarios", "Indicadores"])

    with tab1:
        grupos()
    with tab2:
        st.header("Usuarios")
        st.image("https://static.streamlit.io/examples/dog.jpg", width=200)
    with tab3:
        st.header("Indicadores")
        st.image("https://static.streamlit.io/examples/owl.jpg", width=200)