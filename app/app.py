import streamlit as st
from pathlib import Path
from components.sidebar_component import sidebar_component
from components.cargarImagen import cargar_imagen_component 
from components.inicio import inicio

_css_general = Path(__file__).parent / 'assets' / 'general.css'
_css_registrar = Path(__file__).parent / 'assets' / '1_registrar.css'
with open(_css_general, encoding="utf-8") as f:
    try:
        with open(_css_general, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        with open(_css_registrar, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        
    except Exception as _e:
        st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
        """, unsafe_allow_html=True)


st.set_page_config(page_title="Persona Bajo la Lluvia", layout="wide")

if "active_view" not in st.session_state:
    st.session_state["active_view"] = "inicio"

sidebar_component()

if st.session_state["active_view"] == "inicio":
    inicio()
    
elif st.session_state["active_view"] == "registrar":
    cargar_imagen_component()

elif st.session_state["active_view"] == "historial":
    st.write("Bienvenido a la vista de Historial")

elif st.session_state["active_view"] == "estadisticas":
    st.write("Bienvenido a la vista de Estadísticas")

elif st.session_state["active_view"] == "salir":
    st.write("Has salido de la aplicación")
