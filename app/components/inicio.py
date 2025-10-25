import sys, os
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
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
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""<h5>Recientes</h5>""", unsafe_allow_html=True)
        with col2:
            button_label = "Ver todos :material/chevron_forward:"

            if st.button(button_label, key="view_more", type="secondary"):
                st.session_state["active_view"] = "historial"
                st.rerun()

        st.markdown("""
        <div style="border: 1px solid #ccc; border-radius: 10px; padding: 10px; height: 100%;">
            <ul style="list-style-type: none; padding: 0;">
                <li style="margin-bottom: 10px;">nombre<br><small>edad, sexo</small></li>
                <li style="margin-bottom: 10px;">nombre<br><small>edad, sexo</small></li>
                <li style="margin-bottom: 10px;">nombre<br><small>edad, sexo</small></li>
                <li style="margin-bottom: 10px;">nombre<br><small>edad, sexo</small></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
