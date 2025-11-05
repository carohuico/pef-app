import sys, os
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from services.queries.q_inicio import GET_RECIENTES
from services.db import fetch_df
import streamlit as st

def inicio():
    # ---------- CONFIGURACIÓN ----------
    st.set_page_config(page_title="Rainly", layout="wide", initial_sidebar_state="auto")
    # ---------- CSS (externo) ----------
    _css_general = Path(__file__).parent.parent / 'assets' / 'general.css'
    _css_sidebar = Path(__file__).parent.parent / 'assets' / 'sidebar_component.css'
    _css_inicio = Path(__file__).parent.parent / 'assets' / 'inicio.css'
    
    try:
        with open(_css_general, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        with open(_css_sidebar, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        with open(_css_inicio, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
    except Exception as _e:
        st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
        """, unsafe_allow_html=True)
        
    # ---------- LAYOUT ----------
    col1, col2 = st.columns([2, 1])
    try:
        if st.session_state.get('created_ok', False):
             st.markdown("""
                <div class="success">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                </svg>
                <span>Evaluado registrado correctamente</span>
                </div>
            """, unsafe_allow_html=True)
        st.session_state['created_ok'] = False
    except Exception:
        pass

    with col1:
        st.markdown('<div class="page-header">Evaluaciones</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])

    with col1:
        c1, c2 = st.columns(2)
        with c1:
                st.markdown("""
                <div style="margin-bottom: 20px;">
                    <h4>01<br>Registrar</h4>
                    <p style="color:  #6c6c6c">Registra los datos de la persona a evaluar.</p><br>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div style="margin-bottom: 20px;">
                    <br>
                    <h4>03<br>Resultados</h4>
                    <p style="color:  #6c6c6c">Descubre los resultados del dibujo que subiste.</p>
                </div>
                """, unsafe_allow_html=True)
        with c2:
                st.markdown("""
                <div style="margin-bottom: 20px; margin-right: 20px;">
                    <h4>02<br>Subir dibujo</h4>
                    <p style="color:  #6c6c6c">Sube tu dibujo como archivo de imagen o desde una cámara.</p><br>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div style="margin-bottom: 20px;">
                    <h4>04<br>Exportar</h4>
                    <p style="color:  #6c6c6c">Descarga tus resultados en un documento CSV o PDF.</p>
                </div>
                """, unsafe_allow_html=True)

    with col2:

        button_label = ":material/add_2: Nueva evaluación"

        if st.button(button_label, key="new_eval", type="primary"):
            st.session_state["active_view"] = "registrar"
            st.rerun()
        
        st.markdown("""<h5>Recientes</h5>""", unsafe_allow_html=True)

        recientes = fetch_df(GET_RECIENTES)

        if recientes.empty:
            st.markdown("<p>No hay evaluaciones recientes.</p>", unsafe_allow_html=True)
        else:
            for _, r in recientes.iterrows():
                id_prueba = r.get('id_prueba')
                id_evaluado = r.get('id_evaluado')
                nombre = r.get('nombre', '')
                apellido = r.get('apellido', '')
                fecha = r.get('fecha', '')

                label = f"**{nombre} {apellido}**  \n{fecha}"
                key = f"recent_btn_{id_prueba}"
                
                if st.button(label, key=key, type="secondary", use_container_width=True):
                    try:
                        st.session_state['open_prueba_id'] = int(id_prueba)
                    except Exception:
                        st.session_state['open_prueba_id'] = id_prueba

                    st.session_state['selected_evaluation_id'] = id_evaluado
                    st.session_state['active_view'] = 'individual'
                    st.rerun()
        
        if st.button("Ver más >", key="view_more", type="secondary", use_container_width=True):
            st.session_state["active_view"] = "historial"
            st.rerun()