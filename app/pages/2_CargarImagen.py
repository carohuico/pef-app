import sys, os
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import bootstrap

from config.settings import ALLOWED_EXTENSIONS, TEMP_DIR, STD_DIR
from services.image_preprocess import estandarizar_imagen
import streamlit as st
from PIL import Image

# ---------- CONFIGURACIÓN ----------
st.set_page_config(page_title="Nueva evaluación", layout="wide")

# ---------- CSS (externo) ----------
_css_path = Path(__file__).parent.parent / 'assets' / '2_cargarimagen.css'
try:
    with open(_css_path, 'r', encoding='utf-8') as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
except Exception as _e:
    # Fallback: if file can't be read, inject a minimal link to Google Fonts to keep typography
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

# ---------- SESIÓN ----------
if "show_modal" not in st.session_state:
    st.session_state["show_modal"] = False
if "uploaded_file" not in st.session_state:
    st.session_state["uploaded_file"] = None



# ---------- UI ----------
with st.container():
    st.markdown('<div class="page-header">Nueva evaluación</div>', unsafe_allow_html=True)
    
    # Stepper
    st.markdown("""
    <div class="stepper">
        <div class="step done"><div class="circle"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width:24px; height:24px;">
  <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
</svg>
</div><div class="step-text">Registrar</div></div>
        <div class="step active"><div class="circle">2</div><div class="step-text">Subir dibujo</div></div>
        <div class="step"><div class="circle">3</div><div class="step-text">Resultados</div></div>
        <div class="step"><div class="circle">4</div><div class="step-text">Exportar</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="uploader-mock" id="mock-uploader">
        <div class="uploader-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M37 28V37C37 38.0609 36.5786 39.0783 35.8284 39.8284C35.0783 40.5786 34.0609 41 33 41H15C13.9391 41 12.9217 40.5786 12.1716 39.8284C11.4214 39.0783 11 38.0609 11 37V28" stroke="#888888" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M24 7V29" stroke="#888888" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M16 15L24 7L32 15" stroke="#888888" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
        <p class="uploader-text">Arrastra</p>
        <p class="uploader-text" style="color:#aaa; font-weight:400;">o</p>
        <div class="uploader-button">Elige un archivo</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-container">
        <span>Formatos permitidos: JPG, JPEG, PNG</span>
        <span>Tamaño máximo: 10 MB</span>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state["show_modal"]:
        st.markdown("""
        <div class="modal-overlay">
            <div class="modal-content">
                <h3>✅ Imagen cargada correctamente</h3>
                <p>Tu dibujo se ha estandarizado con éxito.</p>
                <button onclick="window.location.reload()">Continuar</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # --- Footer de navegación (Atrás / Siguiente) ---
    st.markdown(
        """
        <div class="nav-footer">
            <a class="btn btn-back">Atrás</a>
            <a class="btn btn-next">Siguiente</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
    

