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

# ---------- CSS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
html, body, [class*="st-"] {
    font-family: 'Poppins', sans-serif;
    background-color: #F0F2F6;
    color: #1a1a1a;
}
#MainMenu, header, footer {visibility: hidden;}

.main-container {
    display: flex;
    justify-content: center;
    padding: 2rem;
}
.content-card {
    background-color: #FFFFFF;
    border-radius: 20px;
    padding: 3rem 4rem;
    box-shadow: 0 8px 24px rgba(0,0,0,0.05);
    width: 100%;
    max-width: 850px;
}

/* HEADER */
.header {
    font-size: 2.25rem;
    font-weight: 700;
    margin-bottom: 2.5rem;
}

/* STEPPER */
.stepper {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 3.5rem;
    position: relative;
}
.stepper::before {
    content: '';
    position: absolute;
    top: 20px;
    left: 5%;
    right: 5%;
    height: 2px;
    background-color: #E0E0E0;
    z-index: 0;
}
.step {
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    z-index: 1;
    width: 80px;
}
.circle {
    height: 40px;
    width: 40px;
    border-radius: 50%;
    border: 2px solid #E0E0E0;
    display: flex;
    justify-content: center;
    align-items: center;
    font-weight: 600;
    font-size: 1rem;
    margin-bottom: 0.5rem;
    background-color: #fff;
    color: #A0A0A0;
}
.step-text { font-size: 0.9rem; font-weight: 500; color: #888; }
.step.done .circle { background-color: #000; border-color: #000; color: #FFF; }
.step.active .circle { border-color: #000; color: #000; }
.step.done .step-text, .step.active .step-text { color: #000; }

/* --- MOCK UPLOADER --- */
.uploader-mock {
    border: 2px dashed #D0D0D0;
    border-radius: 12px;
    background-color: #FAFAFA;
    padding: 4rem 2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    transition: all 0.3s;
    cursor: pointer;
}
.uploader-mock:hover {
    border-color: #FFF200;
    background-color: #FFFDF0;
}
.uploader-icon { margin-bottom: 1rem; }
.uploader-text {
    font-weight: 500;
    color: #333;
    font-size: 1rem;
    margin: 0.25rem 0;
}
.uploader-button {
    background-color: #333333;
    color: #FFFFFF;
    border-radius: 8px;
    padding: 0.75rem 1.5rem;
    font-weight: 600;
    cursor: pointer;
    margin-top: 1rem;
}

/* --- INFO --- */
.info-container {
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
    color: #888;
    margin-top: 1rem;
    padding: 0 0.5rem;
}

/* --- BOTONES --- */
.nav-buttons {
    display: flex;
    justify-content: space-between;
    margin-top: 3rem;
    border-top: 1px solid #E0E0E0;
    padding-top: 2rem;
}
.stButton>button {
    border-radius: 10px;
    padding: 0.75rem 0;
    font-weight: 600;
    width: 150px;
    font-size: 1rem;
}
.stButton>button[kind="secondary"] {
    background-color: #FFFFFF;
    color: #333;
    border: 2px solid #E0E0E0;
}
.stButton>button[kind="secondary"]:hover {
    border-color: #333;
}
.stButton>button[kind="primary"] {
    background-color: #FFF200;
    color: #1a1a1a;
    border: none;
}
.stButton>button[kind="primary"]:hover {
    background-color: #E6D900;
}

/* --- MODAL --- */
.modal-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.4);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
}
.modal-content {
    background: #FFFFFF;
    border-radius: 20px;
    padding: 2.5rem 3rem;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    width: 380px;
}
.modal-content h3 { font-size: 22px; font-weight: 600; margin-bottom: 1rem; }
.modal-content p { font-size: 15px; color: #555; margin-bottom: 1.5rem; }
.modal-content button {
    background-color: #FFF200;
    color: #000;
    border: none;
    border-radius: 8px;
    padding: 0.6rem 1.5rem;
    font-weight: 600;
    cursor: pointer;
}
.modal-content button:hover { background-color: #ffeb3b; }
</style>
""", unsafe_allow_html=True)

# ---------- SESIÓN ----------
if "show_modal" not in st.session_state:
    st.session_state["show_modal"] = False
if "uploaded_file" not in st.session_state:
    st.session_state["uploaded_file"] = None

# ---------- UI ----------
st.markdown('<div class="header">Nueva evaluación</div>', unsafe_allow_html=True)

# Stepper
st.markdown("""
<div class="stepper">
    <div class="step done"><div class="circle">✔</div><div class="step-text">Registrar</div></div>
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

# uploader oculto pero funcional
archivo = st.file_uploader("Carga tu archivo", type=ALLOWED_EXTENSIONS, label_visibility="collapsed", key="hidden_uploader")

st.markdown("""
<div class="info-container">
    <span>Formatos permitidos: JPG, JPEG, PNG</span>
    <span>Tamaño máximo: 10 MB</span>
</div>
""", unsafe_allow_html=True)

# Lógica de carga
if archivo:
    st.session_state["uploaded_file"] = archivo
    imagen = Image.open(archivo)
    st.image(imagen, caption="Vista previa del dibujo", use_container_width=True)
    if st.button("Confirmar carga"):
        nombre = archivo.name
        temp_path = Path(TEMP_DIR) / nombre
        std_path = Path(STD_DIR) / nombre
        imagen.save(temp_path)
        estandarizar_imagen(imagen, std_path)
        st.session_state["show_modal"] = True

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

# Botones de navegación
st.markdown('<div class="nav-buttons">', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.button("Atrás", type="secondary", use_container_width=True)
with col2:
    st.button("Siguiente", type="primary", use_container_width=True, disabled=(st.session_state["uploaded_file"] is None))
st.markdown('</div></div></div>', unsafe_allow_html=True)
