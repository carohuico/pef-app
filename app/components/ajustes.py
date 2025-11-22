from components.evaluados import evaluados
from services.usuarios import usuarios
from services.grupos import grupos
from services.indicadores_ajustes import indicadores
import streamlit as st
from pathlib import Path
import pandas as pd
from components.loader import show_loader

def ajustes():
    # ---------- CSS (externo) ----------
    _css_general = Path(__file__).parent.parent / 'assets' / 'general.css'   
    _sidebar = Path(__file__).parent.parent / 'assets' / 'sidebar_component.css'   
    
    try:
        with open(_css_general, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        with open(_sidebar, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
    except Exception as _e:
        st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
        """, unsafe_allow_html=True)

    is_esp = False
    try:
        import services.auth as auth
        is_esp = auth.is_especialista()
    except Exception:
        is_esp = False
        
    if is_esp:
        st.markdown('<div class="page-header">Mis evaluados</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="page-header">Ajustes</div>', unsafe_allow_html=True)

    if is_esp:
        # Obtener id del especialista
        user = st.session_state.get('user', {})
        uid = None
        try:
            uid = int(user.get('id_usuario')) if user.get('id_usuario') is not None else None
        except Exception:
            uid = None

        evaluados(can_delete=False, user_id=uid)
        return

    # Usuario no especialista -> vista completa de ajustes
    tab1, tab2, tab3, tab4 = st.tabs(["Evaluados", "Grupos", "Usuarios", "Indicadores"])

    with tab1:
        evaluados()
    with tab2:
        grupos()
    with tab3:
        usuarios()  
    with tab4:
        indicadores()
    show_loader('show_ajustes_loader', min_seconds=1.0)
    