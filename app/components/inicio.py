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
        st.markdown('<div class="title">Nueva evaluación</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<div class="btn-nueva-evaluacion-wrapper">', unsafe_allow_html=True)

       

        if st.button("Nueva evaluación", key="new_eval_start", type="primary"):
            st.session_state["active_view"] == "registrar"
            st.rerun()

        # 3. Cierra el contenedor
        st.markdown('</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
                st.markdown("""
                <div style="margin-bottom: 20px;">
                    <h3>01 Registrar</h3>
                    <p>Registra los datos de la persona a evaluar.</p>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div style="margin-bottom: 20px;">
                    <h3>03 Resultados</h3>
                    <p>Descubre los resultados del dibujo que subiste.</p>
                </div>
                """, unsafe_allow_html=True)
        with c2:
                st.markdown("""
                <div style="margin-bottom: 20px;">
                    <h3>02 Subir dibujo</h3>
                    <p>Sube tu dibujo como archivo de imagen.</p>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div style="margin-bottom: 20px;">
                    <h3>04 Exportar</h3>
                    <p>Descarga tus resultados en un documento CSV o PDF.</p>
                </div>
                """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="border: 1px solid #ccc; border-radius: 10px; padding: 10px;">
            <h3>Recientes</h3>
            <ul style="list-style-type: none; padding: 0;">
                <li style="margin-bottom: 10px;">nombre<br><small>edad, sexo</small></li>
                <li style="margin-bottom: 10px;">nombre<br><small>edad, sexo</small></li>
                <li style="margin-bottom: 10px;">nombre<br><small>edad, sexo</small></li>
                <li style="margin-bottom: 10px;">nombre<br><small>edad, sexo</small></li>
            </ul>
            <a href="#">Ver todos</a>
        </div>
        """, unsafe_allow_html=True)
