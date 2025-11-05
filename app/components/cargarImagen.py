import sys, os
import pandas as pd
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import bootstrap
from streamlit_js_eval import streamlit_js_eval

from config.settings import ALLOWED_EXTENSIONS, TEMP_DIR, STD_DIR
from services.image_preprocess import estandarizar_imagen
from services.indicadores import simular_resultado
from services.db import get_engine, fetch_df
from services.queries.q_registro import CREAR_EVALUADO, GET_GRUPOS, POST_PRUEBA, POST_RESULTADO 
from components.bounding_boxes import imagen_bboxes
from sqlalchemy import text
import streamlit as st
from PIL import Image
import datetime

def cargar_imagen_component():
    # ---------- CONFIGURACIÓN ----------
    st.set_page_config(page_title="Nueva evaluación", layout="wide", initial_sidebar_state="auto")
    # ---------- CSS (externo) ----------
    _css_general = Path(__file__).parent.parent / 'assets' / 'general.css'
    _css_registrar = Path(__file__).parent.parent / 'assets' / '1_registrar.css'
    _css_cargar = Path(__file__).parent.parent / 'assets' / '2_cargarimagen.css'
    _css_sidebar = Path(__file__).parent.parent / 'assets' / 'sidebar_component.css'

    try:
        with open(_css_general, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        with open(_css_registrar, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        with open(_css_cargar, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        with open(_css_sidebar, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
    except Exception as _e:
        st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
        """, unsafe_allow_html=True)

    # ---------- SESIÓN ----------
    if "already_registered" not in st.session_state:
        st.session_state["already_registered"] = False
    if "uploaded_file" not in st.session_state:
        st.session_state["uploaded_file"] = None
    if "current_step" not in st.session_state:
        st.session_state["current_step"] = 1
    if "form_nombre" not in st.session_state:
        st.session_state["form_nombre"] = "Caro"
    if "form_apellido" not in st.session_state:
        st.session_state["form_apellido"] = ""
    if "form_fecha_nacimiento" not in st.session_state:
        st.session_state["form_fecha_nacimiento"] = None
    if "form_sexo" not in st.session_state:
        st.session_state["form_sexo"] = "Mujer"
    if "form_estado_civil" not in st.session_state:
        st.session_state["form_estado_civil"] = ""
    if "form_escolaridad" not in st.session_state:
        st.session_state["form_escolaridad"] = ""
    if "form_ocupacion" not in st.session_state:
        st.session_state["form_ocupacion"] = ""
    if "form_grupo" not in st.session_state:
        st.session_state["form_grupo"] = ""



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

        def registrar_component():
            # Primera fila: Nombre y Apellido
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="form-group">', unsafe_allow_html=True)
                st.markdown('<label>Nombre(s) del evaluado <span class="required" style="color: #e74c3c;">*</span></label>', unsafe_allow_html=True)
                nombre_value = st.text_input("Nombre del evaluado", key="nombre", placeholder="Escribe el nombre aquí", label_visibility="collapsed", value=st.session_state.get("form_nombre", ""))
                st.session_state["form_nombre"] = nombre_value.strip()
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="form-group">', unsafe_allow_html=True)
                st.markdown('<label>Apellido(s) del evaluado</label>', unsafe_allow_html=True)
                apellido_value = st.text_input("Apellido del evaluado", key="apellido", placeholder="Escribe el apellido aquí", label_visibility="collapsed", value=st.session_state.get("form_apellido", ""))
                st.session_state["form_apellido"] = apellido_value.strip()
                st.markdown('</div>', unsafe_allow_html=True)

            # Segunda fila: Fecha de nacimiento y Sexo
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="form-group">', unsafe_allow_html=True)
                st.markdown('<label>Fecha de nacimiento <span class="required" style="color: #e74c3c;">*</span></label>', unsafe_allow_html=True)
                today = datetime.date.today()
                #november 01
                max_dob = today - datetime.timedelta(days=18 * 365)
                min_dob = today - datetime.timedelta(days=100 * 365)

                st.date_input(
                    "Fecha de nacimiento del evaluado",
                    key="fecha_nacimiento_widget",
                    label_visibility="collapsed",
                    min_value=min_dob,
                    max_value=max_dob,
                    value=st.session_state.get("form_fecha_nacimiento", None),
                    format="DD/MM/YYYY"
                )
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="form-group">', unsafe_allow_html=True)
                st.markdown('<label>Sexo <span class="required" style="color: #e74c3c;">*</span></label>', unsafe_allow_html=True)
                sexo_value = st.selectbox(
                    "Sexo del evaluado",
                    ["Selecciona una opción", "Mujer", "Hombre"],
                    key="sexo",
                    label_visibility="collapsed",
                    index=["Selecciona una opción", "Mujer", "Hombre"].index(st.session_state["form_sexo"])
                )
                st.session_state["form_sexo"] = sexo_value
                st.markdown('</div>', unsafe_allow_html=True)

            # Tercera fila: Estado civil y Escolaridad
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="form-group">', unsafe_allow_html=True)
                st.markdown('<label>Estado civil</label>', unsafe_allow_html=True)
                if "form_estado_civil" not in st.session_state or st.session_state["form_estado_civil"] not in ["Selecciona una opción", "Soltero(a)", "Casado(a)", "Divorciado(a)", "Viudo(a)", "Separado(a)", "Convivencia civil"]:
                    st.session_state["form_estado_civil"] = "Selecciona una opción"

                estado_civil_value = st.selectbox(
                    "Estado civil del evaluado",
                    ["Selecciona una opción", "Soltero(a)", "Casado(a)", "Divorciado(a)", "Viudo(a)", "Separado(a)", "Convivencia civil"],
                    key="estado_civil",
                    label_visibility="collapsed",
                    index=["Selecciona una opción", "Soltero(a)", "Casado(a)", "Divorciado(a)", "Viudo(a)", "Separado(a)", "Convivencia civil"].index(st.session_state["form_estado_civil"])
                )
                st.session_state["form_estado_civil"] = estado_civil_value
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="form-group">', unsafe_allow_html=True)
                st.markdown('<label>Último grado alcanzado</label>', unsafe_allow_html=True)
                if "form_escolaridad" not in st.session_state or st.session_state["form_escolaridad"] not in ["Selecciona una opción", "Ninguno", "Primaria", "Secundaria", "Preparatoria o Bachillerato", "Técnico", "Licenciatura", "Maestría", "Doctorado", "Posgrado"]:
                    st.session_state["form_escolaridad"] = "Selecciona una opción"

                escolaridad_value = st.selectbox(
                    "Último grado de estudios del evaluado",
                    ["Selecciona una opción", "Ninguno", "Primaria", "Secundaria", "Preparatoria o Bachillerato", "Técnico", "Licenciatura", "Maestría", "Doctorado", "Posgrado"],
                    key="escolaridad",
                    label_visibility="collapsed",
                    index=["Selecciona una opción", "Ninguno", "Primaria", "Secundaria", "Preparatoria o Bachillerato", "Técnico", "Licenciatura", "Maestría", "Doctorado", "Posgrado"].index(st.session_state["form_escolaridad"])
                )
                st.session_state["form_escolaridad"] = escolaridad_value
                st.markdown('</div>', unsafe_allow_html=True)

            # Cuarta fila: Ocupación y Grupo
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="form-group">', unsafe_allow_html=True)
                st.markdown('<label>Ocupación</label>', unsafe_allow_html=True)
                if "form_ocupacion" not in st.session_state or st.session_state["form_ocupacion"] not in ["Selecciona una opción", "Empleado(a)", "Desempleado(a)", "Jubilado(a) / Pensionado(a)", "Trabajador(a) por cuenta propia", "Empresario(a) / Emprendedor(a)", "Dedicado(a) al hogar", "Estudiante", "Otro"]:
                    st.session_state["form_ocupacion"] = "Selecciona una opción"

                ocupacion_value = st.selectbox(
                    "Ocupación del evaluado",
                    ["Selecciona una opción", "Empleado(a)", "Desempleado(a)", "Jubilado(a) / Pensionado(a)", "Trabajador(a) por cuenta propia", "Empresario(a) / Emprendedor(a)", "Dedicado(a) al hogar", "Estudiante", "Otro"],
                    key="ocupacion",
                    label_visibility="collapsed",
                    index=["Selecciona una opción", "Empleado(a)", "Desempleado(a)", "Jubilado(a) / Pensionado(a)", "Trabajador(a) por cuenta propia", "Empresario(a) / Emprendedor(a)", "Dedicado(a) al hogar", "Estudiante", "Otro"].index(st.session_state["form_ocupacion"])
                )
                st.session_state["form_ocupacion"] = ocupacion_value
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="form-group">', unsafe_allow_html=True)
                st.markdown('<label>Grupo al que pertenece</label>', unsafe_allow_html=True)
                try:
                    df_groups = fetch_df(GET_GRUPOS)
                    group_names = [str(x) for x in df_groups['nombre'].fillna('')]
                    if not group_names:
                        group_options = ["Sin grupo"]
                    else:
                        group_options = ["Selecciona un grupo"] + group_names
                except Exception:
                    group_options = ["Selecciona un grupo"]

                current = st.session_state.get("form_grupo", "")
                # Si el valor actual no está en opciones, usar el índice 0
                try:
                    index = group_options.index(current) if current in group_options else 0
                except Exception:
                    index = 0

                selected = st.selectbox(
                    "Grupo del evaluado",
                    group_options,
                    key="grupo_select",
                    label_visibility="collapsed",
                    index=index
                )
                if selected in ("Selecciona un grupo", "Sin grupo"):
                    st.session_state["form_grupo"] = ""
                else:
                    st.session_state["form_grupo"] = selected
                st.markdown('</div>', unsafe_allow_html=True)

        def uploader_component():
            st.markdown('<br></br>', unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Selecciona una imagen", type=["png", "jpg", "jpeg", "heic"], key="file_uploader", label_visibility="collapsed")
            if uploaded_file is not None:
                st.session_state["uploaded_file"] = uploaded_file
                    
        def resultados_component():
            #nombre archivo pero .txt
            if st.session_state.get("uploaded_file") is not None:
                filename = st.session_state["uploaded_file"].name
                txt_filename = os.path.splitext(filename)[0] + ".txt"
            indicadores = simular_resultado(txt_filename)
            st.session_state["indicadores"] = indicadores

            col1, col2 = st.columns([1,2], vertical_alignment="top")

            with col1:
                if st.session_state.get("uploaded_file") is not None:
                    original = Image.open(st.session_state["uploaded_file"])
                    # st.image(image, use_container_width=True)
                    #dibujar bounding boxes en la imagen 
                    boxes = []
                    for ind in indicadores:
                        box = {
                            'nombre': ind.get('nombre', ''),
                            'x_min': ind.get('x_min', 0),
                            'x_max': ind.get('x_max', 0),
                            'y_min': ind.get('y_min', 0),
                            'y_max': ind.get('y_max', 0),
                        }
                        boxes.append(box)
                        
                    preview = imagen_bboxes(original, boxes)
                    st.image(preview, use_container_width=True)

            with col2:
                with st.container(): 
                    if not indicadores:
                        st.markdown("No se encontraron indicadores.")
                    else:
                        rows = []
                        for ind in indicadores:
                            nombre = ind.get('nombre', '')
                            significado = ind.get('significado', '')
                            confianza = ind.get('confianza', None)
                            try:
                                conf_val = float(confianza)
                            except Exception:
                                conf_val = None
                            rows.append({"Indicador": nombre, "Descripción": significado, "Confianza": conf_val})
                        df = pd.DataFrame(rows)
                        if 'Confianza' in df.columns:
                            df['Confianza'] = df['Confianza'].round(2)
                        def style_dataframe(df):
                            return df.style.set_properties(**{'border-radius': '10px', 'border': '1px solid #ddd', 'margin-left': '20px',
                                          'text-align': 'center', 'background-color': "#ffffff", 'color': "#000000", 'height': '40px', 'font-family': 'Poppins'})
                        styled_df = style_dataframe(df)
                        st.dataframe(styled_df, use_container_width=True)
                        
        def exportar_component():
            st.markdown("""Vista de exportación de resultados en proceso...""")

        # ---------- LÓGICA DE PASOS ----------
        if step == 1 and st.session_state["already_registered"] == False:
            registrar_component()
        else:
            st.session_state["current_step"] = max(2, step)
        if step == 2:
            uploader_component()
        elif step == 3:
            resultados_component()
        elif step == 4:
            exportar_component()
        

        st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
        col_back, col_next = st.columns([1, 1])
        with col_back:
            back_label = "Atrás" if step > 1 else "Cancelar"

            if st.button(back_label, key="nav_back", type="secondary"):
                if step > 1:
                    st.session_state["current_step"] = max(1, step - 1)
                    st.rerun()
                else:
                    # Cancel -> return to the app's inicio/main view
                    st.session_state["active_view"] = "inicio"
                    st.session_state["current_step"] = 1
                    st.rerun()
        with col_next:
            next_disabled = step > 4
            next_label = "Siguiente" if step < 4 else "Finalizar"
            if st.button(next_label, disabled=next_disabled, key="nav_next", type="primary"):
                if not next_disabled:
                    if step == 1:
                        nombre_value = st.session_state.get("nombre", "").strip()
                        apellido_value = st.session_state.get("apellido", "").strip()
                        fecha_nacimiento = st.session_state.get("fecha_nacimiento_widget", st.session_state.get("form_fecha_nacimiento", ""))
                        sexo_value = st.session_state.get("sexo", "Selecciona una opción")
                        estado_civil_value = st.session_state.get("estado_civil", "Selecciona una opción")
                        escolaridad_value = st.session_state.get("escolaridad", "Selecciona una opción")
                        ocupacion_value = st.session_state.get("ocupacion", "Selecciona una opción")
                        grupo_value = st.session_state.get("form_grupo", "").strip()
                        if not nombre_value:
                            st.markdown("""
                                <div class="warning">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                                </svg>
                                <span>El nombre del evaluado es obligatorio</span>
                                </div>
                            """, unsafe_allow_html=True)
                        elif not all(c.isalpha() or c.isspace() for c in nombre_value):
                            st.markdown("""
                                <div class="warning">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                                </svg>
                                <span>El nombre solo debe contener letras alfabéticas y espacios</span>
                                </div>
                            """, unsafe_allow_html=True)
                        elif not fecha_nacimiento:
                            st.markdown("""
                                <div class="warning">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                                </svg>
                                <span>La fecha de nacimiento del evaluado es obligatoria</span>
                                </div>
                            """, unsafe_allow_html=True)
                        elif not sexo_value or sexo_value == "Selecciona una opción":
                            st.markdown("""
                                <div class="warning">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                                </svg>
                                <span>El sexo del evaluado es obligatorio</span>
                                </div>
                            """, unsafe_allow_html=True)
                        elif not all(c.isalpha() or c.isspace() for c in nombre_value):
                            st.markdown('<div class="warning"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" /></svg> El nombre solo debe contener letras alfabéticas y espacios</div>', unsafe_allow_html=True)
                        elif not sexo_value or sexo_value == "Selecciona una opción":
                            st.markdown('<div class="warning"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" /></svg> El sexo del evaluado es obligatorio</div>', unsafe_allow_html=True)
                        else:
                            # Guardar campos en sesión
                            st.session_state["form_nombre"] = nombre_value
                            st.session_state["form_apellido"] = apellido_value
                            st.session_state["form_fecha_nacimiento"] = fecha_nacimiento
                            st.session_state["form_sexo"] = sexo_value
                            st.session_state["form_estado_civil"] = estado_civil_value
                            st.session_state["form_escolaridad"] = escolaridad_value
                            st.session_state["form_ocupacion"] = ocupacion_value
                            st.session_state["form_grupo"] = grupo_value

                            st.session_state["current_step"] = min(4, step + 1)
                            st.rerun()
                    elif step == 2:
                        if st.session_state["uploaded_file"] is None:
                            st.markdown("""
                                <div class="warning">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                                </svg>
                                <span>Por favor, sube una imagen para continuar</span>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            imagen = Image.open(st.session_state["uploaded_file"])
                            nombre = st.session_state["uploaded_file"].name
                            temp_path = Path(TEMP_DIR) / nombre
                            std_path = Path(STD_DIR) / nombre
                            imagen.save(temp_path)
                            estandarizar_imagen(imagen, std_path)
                            st.session_state["current_step"] = min(4, step + 1)
                            st.rerun()
                    elif step == 3:
                        st.session_state["current_step"] = min(4, step + 1)
                        st.rerun()
                    elif step == 4:
                            nombre = st.session_state.get("form_nombre", "")
                            apellido = st.session_state.get("form_apellido", "")
                            fecha_nacimiento = st.session_state.get("fecha_nacimiento_widget", st.session_state.get("form_fecha_nacimiento", ""))
                            sexo = st.session_state.get("form_sexo", "")
                            estado_civil = st.session_state.get("form_estado_civil", "")
                            escolaridad = st.session_state.get("form_escolaridad", "")
                            ocupacion = st.session_state.get("form_ocupacion", "")
                            grupo = st.session_state.get("form_grupo", "")

                            params = {
                                "nombre": nombre,
                                "apellido": apellido,
                                "fecha_nacimiento": fecha_nacimiento,
                                "sexo": sexo,
                                "estado_civil": estado_civil,
                                "escolaridad": escolaridad,
                                "ocupacion": ocupacion,
                                "grupo": grupo if grupo else None,
                            }
                            try:
                                engine = get_engine()
                                st.session_state['created_ok'] = False
                                with engine.begin() as conn:
                                    # Resolver id_grupo si se proporcionó nombre de grupo
                                    id_grupo = None
                                    if grupo:
                                        try:
                                            res_g = conn.execute(text("SELECT TOP 1 id_grupo FROM Grupo WHERE nombre = :grupo"), {"grupo": grupo})
                                            row_g = res_g.fetchone()
                                            if row_g is not None:
                                                # row_g may be a RowMapping or tuple
                                                id_grupo = row_g[0] if len(row_g) > 0 else None
                                        except Exception:
                                            id_grupo = None

                                    # Añadir id_grupo a los parámetros y ejecutar la inserción
                                    params["id_grupo"] = id_grupo
                                    res = conn.execute(text(CREAR_EVALUADO), params)
                                    row = res.fetchone()
                                    if row is not None:
                                        # row could be a mapping
                                        try:
                                            st.session_state['id_evaluado'] = int(row['id_evaluado'])
                                        except Exception:
                                            # fallback if row is tuple
                                            st.session_state['id_evaluado'] = int(row[0])
                                st.session_state['created_ok'] = True
                            except Exception as e:
                                st.error(f"Error al crear evaluado en la base de datos: {e}")
                                # No avanzar de paso si falla la inserción
                                return
                            
                            """
                                subir resultados de la prueba
                                id_prueba
                                id_evaluado
                                nombre_archivo
                                ruta_imagen
                                formato
                                fecha
                            """
                            try:
                                id_evaluado = st.session_state.get('id_evaluado')
                                if id_evaluado is not None:
                                    nombre_archivo = st.session_state["uploaded_file"].name
                                    ruta_imagen = str(Path(STD_DIR) / nombre_archivo)
                                    formato = os.path.splitext(nombre_archivo)[1].lstrip('.').lower()
                                    fecha_actual = datetime.datetime.now()

                                    with engine.begin() as conn:
                                        id_prueba = conn.execute(
                                            text(POST_PRUEBA),
                                            {
                                                "id_evaluado": id_evaluado,
                                                "nombre_archivo": nombre_archivo,
                                                "ruta_imagen": ruta_imagen,
                                                "formato": formato,
                                                "fecha": fecha_actual
                                            }
                                        ).fetchone()["id_prueba"]
                            except Exception as e:
                                st.error(f"Error al registrar la prueba en la base de datos: {e}")
                                return
                            
                            """
                                subir a la bd los resultados de la prueba
                                INSERT INTO dbo.Resultado (id_prueba, id_indicador, x_min, y_min, x_max, y_max, confianza)
                            """
                            try:
                                with engine.begin() as conn:
                                    indicadores = st.session_state.get("indicadores", [])
                                    # Open the standardized image to compute normalized coordinates
                                    try:
                                        img_for_norm = Image.open(ruta_imagen)
                                        img_w, img_h = img_for_norm.size
                                    except Exception:
                                        img_w, img_h = None, None

                                    for ind in indicadores:
                                        # indicadores from simular_resultado use key 'id_indicador'
                                        iid = ind.get("id_indicador") or ind.get("id")
                                        x_min = float(ind.get("x_min", 0))
                                        x_max = float(ind.get("x_max", 0))
                                        y_min = float(ind.get("y_min", 0))
                                        y_max = float(ind.get("y_max", 0))
                                        confianza = float(ind.get("confianza", 0.0))

                                        # If we have image dimensions, convert to normalized coordinates (x_min, y_min, width, height)
                                        if img_w and img_h and img_w > 0 and img_h > 0:
                                            x_min_norm = x_min / img_w
                                            y_min_norm = y_min / img_h
                                            w_norm = (x_max - x_min) / img_w
                                            h_norm = (y_max - y_min) / img_h
                                        else:
                                            # fallback: send raw pixel values
                                            x_min_norm = x_min
                                            y_min_norm = y_min
                                            w_norm = (x_max - x_min)
                                            h_norm = (y_max - y_min)

                                        conn.execute(
                                            text(POST_RESULTADO),
                                            {
                                                "id_prueba": id_prueba,
                                                "id_indicador": iid,
                                                "x_min": x_min_norm,
                                                "y_min": y_min_norm,
                                                "x_max": w_norm,
                                                "y_max": h_norm,
                                                "confianza": confianza
                                            }
                                        )
                            except Exception as e:
                                st.error(f"Error al registrar los resultados en la base de datos: {e}")
                                return
                            st.session_state["active_view"] = "inicio"
                            st.session_state["current_step"] = 1
                            
                            #limpiar variables de sesión relacionadas con el formulario
                            st.session_state["form_nombre"] = ""
                            st.session_state["form_apellido"] = ""
                            st.session_state["form_fecha_nacimiento"] = None
                            st.session_state["form_sexo"] = ""
                            st.session_state["form_estado_civil"] = ""
                            st.session_state["form_escolaridad"] = ""
                            st.session_state["form_ocupacion"] = ""
                            st.session_state["form_grupo"] = ""
                            st.session_state["uploaded_file"] = None
                            st.session_state["indicadores"] = None
                            
                            st.rerun()
                        
                    else:
                        st.session_state["current_step"] = min(4, step + 1)
                        st.rerun()



