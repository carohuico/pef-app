import sys, os
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import bootstrap
from streamlit_js_eval import streamlit_js_eval

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
            nombre_value = st.text_input("Nombre del evaluado", key="nombre", placeholder="Escribe el nombre aquí", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Apellido(s) del evaluado</label>', unsafe_allow_html=True)
            apellido_value = st.text_input("Apellido del evaluado", key="apellido", placeholder="Escribe el apellido aquí", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)

        # Segunda fila: Edad y Sexo
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Edad <span class="required" style="color: #e74c3c;">*</span></label>', unsafe_allow_html=True)
            edad_value = st.number_input("Edad del evaluado", key="edad", min_value=18, max_value=100, step=1, label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Sexo <span class="required" style="color: #e74c3c;">*</span></label>', unsafe_allow_html=True)
            sexo_value = st.selectbox("Sexo del evaluado", ["Selecciona una opción", "Masculino", "Femenino", "Otro"], key="sexo", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)

        # Tercera fila: Estado civil y Escolaridad
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Estado civil</label>', unsafe_allow_html=True)
            estado_civil_value = st.selectbox("Estado civil del evaluado", ["Selecciona una opción", "Soltero(a)", "Casado(a)", "Divorciado(a)", "Viudo(a)", "Separado(a)"], key="estado_civil", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Escolaridad</label>', unsafe_allow_html=True)
            escolaridad_value = st.selectbox("Escolaridad del evaluado", ["Selecciona una opción", "Ninguno", "Primaria", "Secundaria", "Preparatoria o Bachillerato", "Técnico", "Licenciatura", "Maestría", "Doctorado", "Posgrado"], key="escolaridad", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)

        # Cuarta fila: Ocupación y Grupo
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Ocupación</label>', unsafe_allow_html=True)
            ocupacion_value = st.selectbox("Ocupación del evaluado", ["Selecciona una opción", "Empleado(a)", "Desempleado(a)", "Jubilado(a) / Pensionado(a)", "Trabajador(a) por cuenta propia", "Empresario(a) / Emprendedor(a)", "Dedicado(a) al hogar", "Estudiante", "Otro"], key="ocupacion", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="form-group">', unsafe_allow_html=True)
            st.markdown('<label>Grupo al que pertenece</label>', unsafe_allow_html=True)
            grupo_value = st.text_input("Grupo del evaluado", key="grupo", placeholder="Escribe para buscar...", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)

        st.session_state.update({
            "form_nombre": nombre_value.strip(),
            "form_apellido": apellido_value.strip(),
            "form_edad": edad_value,
            "form_sexo": sexo_value,
            "form_estado_civil": estado_civil_value,
            "form_escolaridad": escolaridad_value,
            "form_ocupacion": ocupacion_value,
            "form_grupo": grupo_value.strip()
        })

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
        back_label = "Atrás" if step > 1 else "Cancelar"
        if st.button(back_label, disabled=back_disabled, key="nav_back", type="secondary"):
            if not back_disabled:
                st.session_state["current_step"] = max(1, step - 1)
                st.rerun()
    with col_next:
        next_disabled = step > 4
        next_label = "Siguiente" if step < 4 else "Finalizar"
        if st.button(next_label, disabled=next_disabled, key="nav_next", type="primary"):
            if not next_disabled:
                if step == 1:
                    nombre_value = st.session_state.get("nombre", "").strip()
                    apellido_value = st.session_state.get("apellido", "").strip()
                    edad_value = st.session_state.get("edad", 0)
                    sexo_value = st.session_state.get("sexo", "Selecciona una opción")
                    estado_civil_value = st.session_state.get("estado_civil", "Selecciona una opción")
                    escolaridad_value = st.session_state.get("escolaridad", "Selecciona una opción")
                    ocupacion_value = st.session_state.get("ocupacion", "Selecciona una opción")
                    grupo_value = st.session_state.get("grupo", "").strip()

                    if not nombre_value:
                        st.markdown("""
                            <div class="warning" style="font-size:12px; line-height:1.1; padding:4px 6px; display:flex; align-items:center; gap:6px;">
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                            </svg>
                            <span>El nombre del evaluado es obligatorio</span>
                            </div>
                        """, unsafe_allow_html=True)
                    elif not all(c.isalpha() or c.isspace() for c in nombre_value):
                        st.markdown("""
                            <div class="warning" style="font-size:12px; line-height:1.1; padding:4px 6px; display:flex; align-items:center; gap:6px;">
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                            </svg>
                            <span>El nombre solo debe contener letras alfabéticas y espacios</span>
                            </div>
                        """, unsafe_allow_html=True)
                    elif not edad_value or edad_value < 18:
                        st.markdown("""
                            <div class="warning" style="font-size:12px; line-height:1.1; padding:4px 6px; display:flex; align-items:center; gap:6px;">
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                            </svg>
                            <span>La edad del evaluado es obligatoria y debe ser mayor o igual a 18 años</span>
                            </div>
                        """, unsafe_allow_html=True)
                    elif not sexo_value or sexo_value == "Selecciona una opción":
                        st.markdown("""
                            <div class="warning" style="font-size:12px; line-height:1.1; padding:4px 6px; display:flex; align-items:center; gap:6px;">
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                            </svg>
                            <span>El sexo del evaluado es obligatorio</span>
                            </div>
                        """, unsafe_allow_html=True)
                    elif not all(c.isalpha() or c.isspace() for c in nombre_value):
                        st.markdown('<div class="warning" style="font-size:12px; line-height:1.1; padding:4px 6px; display:flex; align-items:center; gap:6px;"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" /></svg> El nombre solo debe contener letras alfabéticas y espacios</div>', unsafe_allow_html=True)
                    elif not edad_value or edad_value < 18:
                        st.markdown('<div class="warning" style="font-size:12px; line-height:1.1; padding:4px 6px; display:flex; align-items:center; gap:6px;">⚠️ La edad del evaluado es obligatoria y debe ser mayor o igual a 18 años</div>', unsafe_allow_html=True)
                    elif not sexo_value or sexo_value == "Selecciona una opción":
                        st.markdown('<div class="warning" style="font-size:12px; line-height:1.1; padding:4px 6px; display:flex; align-items:center; gap:6px;">⚠️ El sexo del evaluado es obligatorio</div>', unsafe_allow_html=True)
                    else:
                        st.session_state["form_nombre"] = nombre_value
                        st.session_state["current_step"] = min(4, step + 1)
                        st.rerun()
                else:
                    st.session_state["current_step"] = min(4, step + 1)
                    st.rerun()



