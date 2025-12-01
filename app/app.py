import streamlit as st
import logging

# Reduce noisy logs coming from asyncio/tornado (common in websocket disconnects).
# Keep default app logging unchanged but raise threshold for these noisy libraries.
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('tornado').setLevel(logging.WARNING)
logging.getLogger('tornado.websocket').setLevel(logging.WARNING)
from pathlib import Path
from components.sidebar_component import sidebar_component
from components.cargarImagen import cargar_imagen_component 
from components.inicio import inicio
from components.historial import historial
from components.individual import individual
from components.estadisticas import estadisticas
from components.ajustes import ajustes
import services.auth as auth
import components.login_page as login_page

st.set_page_config(page_title="Rainly", layout="wide", initial_sidebar_state="auto")

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

if not auth.is_logged_in():
    st.markdown(
        "<style>#MainMenu, header, footer { visibility: hidden !important; }</style>",
        unsafe_allow_html=True,
    )
    login_page.login_page()
    try:
        st.stop()
    except Exception:
        try:
            st.rerun()
        except Exception:
            pass
        st.stop()
else:
    sidebar_component()


if st.session_state["active_view"] == "inicio":
    inicio()
    
elif st.session_state["active_view"] == "registrar":
    cargar_imagen_component()

elif st.session_state["active_view"] == "historial":
    historial()
    
elif st.session_state["active_view"] == "ajustes":
    ajustes()
    
elif st.session_state["active_view"] == "individual":
    id = st.session_state.get("selected_evaluation_id", None)
    individual(id)

elif st.session_state["active_view"] == "estadisticas":
    estadisticas()

elif st.session_state["active_view"] == "salir":
    auth.logout()


