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
if "current_step" not in st.session_state:
    st.session_state["current_step"] = 1



# ---------- UI ----------
with st.container():
    step = st.session_state.get("current_step", 1)
    st.markdown('<div class="page-header">Nueva evaluación</div>', unsafe_allow_html=True)
    
    steps = [
        {"label": "Registrar"},
        {"label": "Subir dibujo"},
        {"label": "Resultados"},
        {"label": "Exportar"},
    ]
    stepper_html = '<div class="stepper">'
    for idx, s in enumerate(steps, start=1):
        active_class = "active" if step == idx else ""
        class_attr = f'step {active_class}'.strip()
        stepper_html += (
            f'<div class="{class_attr}">' \
            f'<div class="circle">{idx}</div>' \
            f'<div class="step-text">{s["label"]}</div>' \
            f'</div>'
        )
    stepper_html += '</div>'
    st.markdown(stepper_html, unsafe_allow_html=True)

    # ---------- COMPONENTES ----------
    def registrar_component():
        # Primera fila: Nombre y Apellido
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Nombre(s) del evaluado <span class="required" style="color: #e74c3c;">*</span></label>', unsafe_allow_html=True)
            st.markdown('<input type="text" class="custom-input" id="nombre"/>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Apellido(s) del evaluado</label>', unsafe_allow_html=True)
            st.markdown('<input type="text" class="custom-input" id="apellido"/>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Segunda fila: Edad y Sexo
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Edad <span class="required" style="color: #e74c3c;">*</span></label>', unsafe_allow_html=True)
            st.markdown('<input type="number" class="custom-input" id="edad" min="18" max="100"/>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Sexo <span class="required" style="color: #e74c3c;">*</span></label>', unsafe_allow_html=True)
            st.markdown(
                '<select class="custom-input" id="sexo">\n'
                '  <option selected>Selecciona una opción</option>\n'
                '  <option class="option">Masculino</option>\n'
                '  <option class="option">Femenino</option>\n'
                '  <option class="option">Otro</option>\n'
                '</select>',
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Tercera fila: Estado civil y Escolaridad
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Estado civil</label>', unsafe_allow_html=True)
            st.markdown(
                '<select class="custom-input" id="estado_civil">\n'
                '  <option selected>Selecciona una opción</option>\n'
                '  <option class="option">Soltero/a</option>\n'
                '  <option class="option">Casado/a</option>\n'
                '  <option class="option">Divorciado/a</option>\n'
                '  <option class="option">Viudo/a</option>\n'
                '  <option class="option">Unión libre</option>\n'
                '</select>',
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Escolaridad</label>', unsafe_allow_html=True)
            st.markdown(
                '<select class="custom-input" id="escolaridad">\n'
                '  <option selected>Selecciona una opción</option>\n'
                '  <option class="option">Primaria</option>\n'
                '  <option class="option">Secundaria</option>\n'
                '  <option class="option">Preparatoria</option>\n'
                '  <option class="option">Licenciatura</option>\n'
                '  <option class="option">Posgrado</option>\n'
                '</select>',
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Cuarta fila: Ocupación y Grupo
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Ocupación</label>', unsafe_allow_html=True)
            st.markdown(
                '<select class="custom-input" id="ocupacion">\n'
                '  <option selected>Selecciona una opción</option>\n'
                '  <option class="option">Estudiante</option>\n'
                '  <option class="option">Empleado</option>\n'
                '  <option class="option">Independiente</option>\n'
                '  <option class="option">Desempleado</option>\n'
                '  <option class="option">Jubilado</option>\n'
                '  <option class="option">Otro</option>\n'
                '</select>',
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Grupo al que pertenece</label>', unsafe_allow_html=True)
            st.markdown('<input type="text" class="custom-input" id="grupo"/>', unsafe_allow_html=True)
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
    if step == 1:
        registrar_component()
    elif step == 2:
        uploader_component()
    elif step == 3:
        st.write("Componente para el paso 3")
    elif step == 4:
        st.write("Componente para el paso 4")
    
        

    st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
    col_back, col_next = st.columns([1, 1])
    with col_back:
        back_disabled = step <= 1
        if st.button("Atrás", disabled=back_disabled, key="nav_back", type="secondary"):
            if not back_disabled:
                st.session_state["current_step"] = max(1, step - 1)
                st.rerun()
    with col_next:
        next_disabled = step >= 4
        next_label = "Siguiente" if step < 4 else "Finalizar"
        if st.button(next_label, disabled=next_disabled, key="nav_next", type="primary"):
            if not next_disabled:
                st.session_state["current_step"] = min(4, step + 1)
                st.rerun()
    

