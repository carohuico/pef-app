import streamlit as st
from streamlit_cookies_controller import CookieController

st.set_page_config(page_title="Rainly", layout="wide")

# ========================================================
# RESTAURAR TOKEN (solo después de que Streamlit montó el DOM)
# ========================================================

controller = CookieController()

# Leer cookie
if "jwt_token" not in st.session_state:
    token = controller.get("jwt_token")
    if token:
        st.session_state["jwt_token"] = token

# Leer localStorage como backup
if "jwt_token" not in st.session_state:
    from streamlit_js_eval import get_local_storage
    token = get_local_storage("jwt_token")
    if token:
        st.session_state["jwt_token"] = token
        st.rerun()



# 2. Intentar restaurar token desde localStorage (JS) como último recurso
try:
    if "jwt_token" not in st.session_state:
        from streamlit_js_eval import get_local_storage
        token = get_local_storage("jwt_token")
        if token:
            st.session_state["jwt_token"] = token

            # Rerun una vez que ya restauramos el token
            rerun_fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
            if callable(rerun_fn):
                rerun_fn()
except Exception:
    pass


import logging
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

# Cargar CSS
_css_general = Path(__file__).parent / 'assets' / 'general.css'
_css_registrar = Path(__file__).parent / 'assets' / '1_registrar.css'

try:
    with open(_css_general, 'r', encoding='utf-8') as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)

    with open(_css_registrar, 'r', encoding='utf-8') as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
except Exception:
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)


# ======================================================
# CONTROL DE VISTAS
# ======================================================

if "active_view" not in st.session_state:
    st.session_state["active_view"] = "inicio"


# ======================================================
# AUTENTICACIÓN
# ======================================================

if not auth.is_logged_in():

    # Ocultar menú mientras no esté autenticado
    st.markdown(
        "<style>#MainMenu, header, footer { visibility: hidden !important; }</style>",
        unsafe_allow_html=True,
    )

    # Mostrar login
    login_page.login_page()

    # Stop después de mostrar login
    try:
        st.stop()
    except Exception:
        try:
            st.rerun()
        except Exception:
            pass
        st.stop()


# ======================================================
# SI ESTÁ LOGUEADO → MOSTRAR SIDEBAR Y VISTAS
# ======================================================

sidebar_component()

view = st.session_state["active_view"]

if view == "inicio":
    inicio()

elif view == "registrar":
    cargar_imagen_component()

elif view == "historial":
    historial()

elif view == "ajustes":
    ajustes()

elif view == "individual":
    id_e = st.session_state.get("selected_evaluation_id", None)
    individual(id_e)

elif view == "estadisticas":
    estadisticas()

elif view == "salir":
    auth.logout()
