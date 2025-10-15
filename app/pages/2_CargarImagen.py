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
_css_general = Path(__file__).parent.parent / 'assets' / 'general.css'
_css_registrar = Path(__file__).parent.parent / 'assets' / '1_registrar.css'
_css_cargar = Path(__file__).parent.parent / 'assets' / '2_cargarimagen.css'
try:
    with open(_css_general, 'r', encoding='utf-8') as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
    with open(_css_registrar, 'r', encoding='utf-8') as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
    with open(_css_cargar, 'r', encoding='utf-8') as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
except Exception as _e:
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
        <div class="step active"><div class="circle">1</div><div class="step-text">Registrar</div></div>
        <div class="step"><div class="circle">2</div><div class="step-text">Subir dibujo</div></div>
        <div class="step"><div class="circle">3</div><div class="step-text">Resultados</div></div>
        <div class="step"><div class="circle">4</div><div class="step-text">Exportar</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ---------- COMPONENTES ----------
    def registrar_component():
        # Primera fila: Nombre y Apellido
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Nombre(s) del evaluado <span class="required" style="color: #e74c3c;">*</span></label>', unsafe_allow_html=True)
            nombre = st.text_input("Nombre", key="nombre", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Apellido(s) del evaluado</label>', unsafe_allow_html=True)
            apellido = st.text_input("Apellido", key="apellido", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Segunda fila: Edad y Sexo
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Edad <span class="required" style="color: #e74c3c;">*</span></label>', unsafe_allow_html=True)
            edad = st.number_input("Edad", min_value=18, max_value=100, key="edad", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Sexo <span class="required" style="color: #e74c3c;">*</span></label>', unsafe_allow_html=True)
            sexo = st.selectbox("Sexo", ["Selecciona una opción", "Masculino", "Femenino", "Otro"], key="sexo", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Tercera fila: Estado civil y Escolaridad
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Estado civil</label>', unsafe_allow_html=True)
            estado_civil = st.selectbox("Estado civil", 
                ["Selecciona una opción", "Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a", "Unión libre"], 
                key="estado_civil", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Escolaridad</label>', unsafe_allow_html=True)
            escolaridad = st.selectbox("Escolaridad", 
                ["Selecciona una opción", "Primaria", "Secundaria", "Preparatoria", "Licenciatura", "Posgrado"], 
                key="escolaridad", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Cuarta fila: Ocupación y Grupo
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Ocupación</label>', unsafe_allow_html=True)
            ocupacion = st.selectbox("Ocupación", 
                ["Selecciona una opción", "Estudiante", "Empleado", "Independiente", "Desempleado", "Jubilado", "Otro"], 
                key="ocupacion", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Grupo al que pertenece</label>', unsafe_allow_html=True)
            grupo = st.text_input("Grupo", key="grupo", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    def uploader_component():
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

    # ---------- LÓGICA DE PASOS ----------
    step = 2
    if step == 1:
        registrar_component()
    elif step == 2:
        uploader_component()
    elif step == 3:
        st.write("Componente para el paso 3")
    elif step == 4:
        st.write("Componente para el paso 4")
    
        

    st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
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
    

