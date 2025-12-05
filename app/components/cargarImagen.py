import sys, os
import pandas as pd
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from services.exportar import render_export_popover
import bootstrap
from streamlit_js_eval import streamlit_js_eval

from config.settings import TEMP_DIR, ORIGINALS_DIR
from services.image_preprocess import estandarizar_imagen
from services.indicadores import simular_resultado
from services.db import fetch_df
from services.queries.q_registro import CREAR_EVALUADO, GET_GRUPOS, POST_PRUEBA, POST_RESULTADO 
from services.queries.q_usuarios import GET_ESPECIALISTAS
from components.bounding_boxes import imagen_bboxes
import streamlit as st
from PIL import Image
import datetime

def cargar_imagen_component():
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
        st.session_state["form_nombre"] = ""
    if "form_apellido" not in st.session_state:
        st.session_state["form_apellido"] = ""
    if "form_fecha_nacimiento" not in st.session_state:
        st.session_state["form_fecha_nacimiento"] = None
    if "form_sexo" not in st.session_state:
        st.session_state["form_sexo"] = ""
    if "form_estado_civil" not in st.session_state:
        st.session_state["form_estado_civil"] = ""
    if "form_escolaridad" not in st.session_state:
        st.session_state["form_escolaridad"] = ""
    if "form_ocupacion" not in st.session_state:
        st.session_state["form_ocupacion"] = ""
    if "form_grupo" not in st.session_state:
        st.session_state["form_grupo"] = ""

    if "_saving_in_progress" not in st.session_state:
        st.session_state["_saving_in_progress"] = False

    try:
        import services.auth as auth
        is_admin = auth.is_admin()
        is_esp = auth.is_especialista()
        is_op = auth.is_operador()
    except Exception:
        is_admin = False
        is_esp = False
        is_op = False
    
    with st.container():
        step = st.session_state.get("current_step", 1)
        st.markdown('<div class="page-header">Nueva evaluación</div>', unsafe_allow_html=True)
        
        steps = [
            {"label": "Registrar"},
            {"label": "Subir dibujo"},
            {"label": "Resultados"},
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
            # Obtener lista de especialistas para el selectbox
            try:
                df_esp = fetch_df(GET_ESPECIALISTAS)
                esp_options = df_esp['nombre_completo'].tolist() if not df_esp.empty else []
                esp_ids = df_esp['id_usuario'].tolist() if not df_esp.empty else []
            except Exception:
                esp_options = []
                esp_ids = []

            # Determinar valor por defecto (si existe assigned_id_usuario en sesión)
            current_assigned = st.session_state.get('assigned_id_usuario', None)

            if is_admin:
                if not esp_options:
                    st.info("No hay especialistas disponibles para asignar.")
                else:
                    # Calcular índice por id si existe
                    default_index = 0
                    if current_assigned is not None:
                        try:
                            default_index = esp_ids.index(int(current_assigned)) + 1
                        except Exception:
                            default_index = 0
                    # Mostrar label HTML con asterisco rojo de obligatorio
                    st.markdown('<label>Especialista responsable <span class="required" style="color: #e74c3c;">*</span></label>', unsafe_allow_html=True)
                    sel = st.selectbox("", ["Selecciona un especialista"] + esp_options, index=default_index, label_visibility='collapsed')
                    if sel != "Selecciona un especialista":
                        sel_idx = esp_options.index(sel)
                        try:
                            st.session_state['assigned_id_usuario'] = int(esp_ids[sel_idx])
                        except Exception:
                            st.session_state['assigned_id_usuario'] = esp_ids[sel_idx]
                    else:
                        if 'assigned_id_usuario' in st.session_state:
                            try:
                                del st.session_state['assigned_id_usuario']
                            except Exception:
                                st.session_state['assigned_id_usuario'] = None
            elif is_esp:
                user = st.session_state.get("user", {})
                uid = user.get("id_usuario")
                try:
                    st.session_state['assigned_id_usuario'] = int(uid)
                except Exception:
                    st.session_state['assigned_id_usuario'] = uid

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
                sexo_options = ["Selecciona una opción", "Mujer", "Hombre"]
                sexo_index = sexo_options.index(st.session_state.get("form_sexo")) if st.session_state.get("form_sexo") in sexo_options else 0
                sexo_value = st.selectbox(
                    "Sexo del evaluado",
                    sexo_options,
                    key="sexo",
                    label_visibility="collapsed",
                    index=sexo_index
                )
                st.session_state["form_sexo"] = sexo_value
                st.markdown('</div>', unsafe_allow_html=True)

            # Tercera fila: Estado civil y Escolaridad
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="form-group">', unsafe_allow_html=True)
                st.markdown('<label>Estado civil</label>', unsafe_allow_html=True)
                if "form_estado_civil" not in st.session_state or st.session_state["form_estado_civil"] not in ["Selecciona una opción", "Soltero(a)", "Casado(a)", "Divorciado(a)", "Viudo(a)", "Separado(a)", "Convivencia civil"]:
                    st.session_state["form_estado_civil"] = ""

                estado_options = ["Selecciona una opción", "Soltero(a)", "Casado(a)", "Divorciado(a)", "Viudo(a)", "Separado(a)", "Convivencia civil"]
                estado_index = estado_options.index(st.session_state.get("form_estado_civil")) if st.session_state.get("form_estado_civil") in estado_options else 0
                estado_civil_value = st.selectbox(
                    "Estado civil del evaluado",
                    estado_options,
                    key="estado_civil",
                    label_visibility="collapsed",
                    index=estado_index
                )
                # Guardar vacío si el usuario dejó la opción por defecto
                st.session_state["form_estado_civil"] = "" if estado_civil_value == "Selecciona una opción" else estado_civil_value
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="form-group">', unsafe_allow_html=True)
                st.markdown('<label>Último grado alcanzado</label>', unsafe_allow_html=True)
                if "form_escolaridad" not in st.session_state or st.session_state["form_escolaridad"] not in ["Selecciona una opción", "Ninguno", "Primaria", "Secundaria", "Preparatoria o Bachillerato", "Técnico", "Licenciatura", "Maestría", "Doctorado", "Posgrado"]:
                    st.session_state["form_escolaridad"] = ""

                escolaridad_options = ["Selecciona una opción", "Ninguno", "Primaria", "Secundaria", "Preparatoria o Bachillerato", "Técnico", "Licenciatura", "Maestría", "Doctorado", "Posgrado"]
                escolaridad_index = escolaridad_options.index(st.session_state.get("form_escolaridad")) if st.session_state.get("form_escolaridad") in escolaridad_options else 0
                escolaridad_value = st.selectbox(
                    "Último grado de estudios del evaluado",
                    escolaridad_options,
                    key="escolaridad",
                    label_visibility="collapsed",
                    index=escolaridad_index
                )
                # Guardar vacío si el usuario dejó la opción por defecto
                st.session_state["form_escolaridad"] = "" if escolaridad_value == "Selecciona una opción" else escolaridad_value
                st.markdown('</div>', unsafe_allow_html=True)

            # Cuarta fila: Ocupación y Grupo
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="form-group">', unsafe_allow_html=True)
                st.markdown('<label>Ocupación</label>', unsafe_allow_html=True)
                if "form_ocupacion" not in st.session_state or st.session_state["form_ocupacion"] not in ["Selecciona una opción", "Empleado(a)", "Desempleado(a)", "Jubilado(a) / Pensionado(a)", "Trabajador(a) por cuenta propia", "Empresario(a) / Emprendedor(a)", "Dedicado(a) al hogar", "Estudiante", "Otro"]:
                    st.session_state["form_ocupacion"] = ""

                ocupacion_options = ["Selecciona una opción", "Empleado(a)", "Desempleado(a)", "Jubilado(a) / Pensionado(a)", "Trabajador(a) por cuenta propia", "Empresario(a) / Emprendedor(a)", "Dedicado(a) al hogar", "Estudiante", "Otro"]
                ocupacion_index = ocupacion_options.index(st.session_state.get("form_ocupacion")) if st.session_state.get("form_ocupacion") in ocupacion_options else 0
                ocupacion_value = st.selectbox(
                    "Ocupación del evaluado",
                    ocupacion_options,
                    key="ocupacion",
                    label_visibility="collapsed",
                    index=ocupacion_index
                )
                # Guardar vacío si el usuario dejó la opción por defecto
                st.session_state["form_ocupacion"] = "" if ocupacion_value == "Selecciona una opción" else ocupacion_value
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
                # Ensure evaluado exists: if not, try to create from form data
                id_evaluado = st.session_state.get('id_evaluado')
                if id_evaluado is None:
                    # Attempt to create evaluado automatically using form fields (if present)
                    nombre_value = st.session_state.get("nombre", "").strip()
                    apellido_value = st.session_state.get("apellido", "").strip()
                    fecha_nacimiento = st.session_state.get("fecha_nacimiento_widget", st.session_state.get("form_fecha_nacimiento", ""))
                    sexo_value = st.session_state.get("sexo", "")

                    if nombre_value and fecha_nacimiento and sexo_value and sexo_value != "Selecciona una opción":
                        try:
                            grupo = st.session_state.get("form_grupo", "")
                            params = {
                                "nombre": nombre_value,
                                "apellido": apellido_value,
                                "fecha_nacimiento": fecha_nacimiento,
                                "sexo": sexo_value,
                                "estado_civil": st.session_state.get("form_estado_civil", None) if st.session_state.get("form_estado_civil", "") not in ("", "Selecciona una opción") else None,
                                "escolaridad": st.session_state.get("form_escolaridad", None) if st.session_state.get("form_escolaridad", "") not in ("", "Selecciona una opción") else None,
                                "ocupacion": st.session_state.get("form_ocupacion", None) if st.session_state.get("form_ocupacion", "") not in ("", "Selecciona una opción") else None,
                                "id_usuario": st.session_state.get('assigned_id_usuario', None),
                            }
                            id_grupo = None
                            if grupo:
                                try:
                                    df_g = fetch_df("SELECT TOP 1 id_grupo FROM Grupo WHERE nombre = @grupo", {"grupo": grupo})
                                    if not df_g.empty:
                                        id_grupo = int(df_g.at[0, 'id_grupo'])
                                except Exception:
                                    id_grupo = None
                            params["id_grupo"] = id_grupo
                            try:
                                if params.get("id_usuario") is not None:
                                    params["id_usuario"] = int(params["id_usuario"])
                            except Exception:
                                params["id_usuario"] = None

                            sql_crear = CREAR_EVALUADO
                            df_row = fetch_df(sql_crear, params)
                            if not df_row.empty:
                                try:
                                    st.session_state['id_evaluado'] = int(df_row.at[0, 'id_evaluado'])
                                except Exception:
                                    st.session_state['id_evaluado'] = int(df_row.iloc[0, 0])
                                st.session_state['already_registered'] = True
                                id_evaluado = st.session_state.get('id_evaluado')
                        except Exception as e:
                            st.error(f"No se pudo crear el evaluado automáticamente: {e}")

                raw_indicadores = []
                if id_evaluado is None:
                    st.error("No se encontró el ID del evaluado. Completa el registro antes de obtener resultados.")
                    raw_indicadores = []
                else:
                    if not st.session_state.get('_saving_in_progress', False):
                        should_run = st.session_state.get('_run_inference_on_results', False)
                        cached = st.session_state.get('raw_indicadores', None)
                        if should_run or cached is None:
                            raw_indicadores = simular_resultado(id_evaluado, show_overlay=True)
                            try:
                                st.session_state['_run_inference_on_results'] = False
                            except Exception:
                                pass
                            try:
                                st.session_state['raw_indicadores'] = raw_indicadores
                            except Exception:
                                pass
                        else:
                            raw_indicadores = cached or []
                    else:
                        raw_indicadores = st.session_state.get('raw_indicadores', []) or []
            else:
                raw_indicadores = []

            if is_op:
                indicadores = []
                for ind in (raw_indicadores or []):
                    try:
                        sig = ind.get('significado', None)
                    except Exception:
                        sig = None
                    if sig is None:
                        continue
                    if isinstance(sig, str) and sig.strip() == "":
                        continue
                    if isinstance(sig, str) and sig.strip() == "-":
                        continue
                    indicadores.append(ind)

                # store for later saving but do not render details
                try:
                    st.session_state['raw_indicadores'] = raw_indicadores
                except Exception:
                    pass
                try:
                    st.session_state['indicadores'] = indicadores
                except Exception:
                    pass

                st.success("Análisis generado correctamente")
                return

            indicadores = []
            for ind in (raw_indicadores or []):
                try:
                    sig = ind.get('significado', None)
                except Exception:
                    sig = None
                if sig is None:
                    continue
                if isinstance(sig, str) and sig.strip() == "":
                    continue
                if isinstance(sig, str) and sig.strip() == "-":
                    continue
                indicadores.append(ind)

            # Guardar indicadores filtrados en sesión para usos posteriores
            st.session_state["indicadores"] = indicadores

            col1, col2 = st.columns([1,2], vertical_alignment="top")

            with col1:
                if st.session_state.get("uploaded_file") is not None:
                    original = Image.open(st.session_state["uploaded_file"])
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
                        # Intentar mostrar con data_editor y configurar ancho de columnas.
                            try:
                                st.data_editor(
                                    df,
                                    use_container_width=True,
                                hide_index=True,
                                key="cargar_indicadores_table",
                                column_config={
                                    "Indicador": st.column_config.TextColumn("Indicador", width="small"),
                                    "Descripción": st.column_config.TextColumn("Descripción", width="medium"),
                                    "Confianza": st.column_config.NumberColumn("Confianza", width="small"),
                                },
                                disabled=["Indicador", "Descripción", "Confianza"],
                            )
                            except Exception:
                                # Fallback simple cuando data_editor no está disponible
                                def style_dataframe(df):
                                    return df.style.set_properties(**{'border-radius': '10px', 'border': '1px solid #ddd', 'margin-left': '20px',
                                                    'text-align': 'center', 'background-color': "#ffffff", 'color': "#000000", 'height': '40px', 'font-family': 'Poppins'})
                                styled_df = style_dataframe(df)
                                st.dataframe(styled_df, use_container_width=True)

        # ---------- LÓGICA DE PASOS ----------
        if step == 1 and st.session_state["already_registered"] == False:
            registrar_component()
        else:
            st.session_state["current_step"] = max(2, step)
        if step == 2:
            uploader_component()
        elif step == 3:
            resultados_component()

        

        st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
        col_back, col_exp, col_next = st.columns([1, 1, 1])
        with col_back:
            back_label = "Atrás" if step > 1 else "Cancelar"

            if st.button(back_label, key="nav_back", type="secondary"):
                if step > 1:
                    # Si estamos en paso 2 y el evaluado ya está registrado, volver al inicio
                    if step == 2 and st.session_state.get("already_registered", False):
                        st.session_state["active_view"] = "inicio"
                        st.session_state["current_step"] = 1
                        st.session_state["already_registered"] = False
                        # Limpiar variables de sesión
                        st.session_state["form_nombre"] = ""
                        st.session_state["form_apellido"] = ""
                        st.session_state["form_fecha_nacimiento"] = None
                        st.session_state["form_sexo"] = ""
                        st.session_state["form_estado_civil"] = ""
                        st.session_state["form_escolaridad"] = ""
                        st.session_state["form_ocupacion"] = ""
                        st.session_state["form_grupo"] = ""
                        st.session_state["uploaded_file"] = None
                        st.rerun()
                    else:
                        # Comportamiento normal: retroceder un paso
                        st.session_state["current_step"] = max(1, step - 1)
                        st.rerun()
                else:
                    # Cancel -> return to the app's inicio/main view
                    st.session_state["active_view"] = "inicio"
                    st.session_state["current_step"] = 1
                    st.session_state["already_registered"] = False
                    # Limpiar variables de sesión
                    st.session_state["form_nombre"] = ""
                    st.session_state["form_apellido"] = ""
                    st.session_state["form_fecha_nacimiento"] = None
                    st.session_state["form_sexo"] = ""
                    st.session_state["form_estado_civil"] = ""
                    st.session_state["form_escolaridad"] = ""
                    st.session_state["form_ocupacion"] = ""
                    st.session_state["form_grupo"] = ""
                    st.session_state["uploaded_file"] = None
                    st.rerun()
        if step == 3:
            with col_exp:
                info_evaluado = {}
                if not is_op:
                    button_label = ":material/download: Exportar resultados"
                    if st.button(button_label, key="export_results", type="tertiary"):
                        if not st.session_state.get("already_registered", False):
                            info_evaluado = {
                                "nombre": st.session_state.get("form_nombre", ""),
                                "apellido": st.session_state.get("form_apellido", ""),
                                "fecha_nacimiento": st.session_state.get("form_fecha_nacimiento_widget", ""),
                                "sexo": st.session_state.get("sexo", ""),
                                "estado_civil": st.session_state.get("estado_civil", ""),
                                "escolaridad": st.session_state.get("escolaridad", ""),
                                "ocupacion": st.session_state.get("ocupacion", ""),
                                "grupo": st.session_state.get("form_grupo", ""),
                            }
                            try:
                                ruta = st.session_state.get('last_saved_image_path', None)
                                if ruta:
                                    info_evaluado['ruta_imagen'] = ruta
                            except Exception:
                                pass
                            render_export_popover(info_evaluado, st.session_state.get("indicadores", []))
                        else:
                            id_evaluado = st.session_state.get("id_evaluado", None)
                            if id_evaluado is None:
                                st.error("No se encontró el ID del evaluado en la sesión.")
                                return
                            df_evaluado = fetch_df(
                                "SELECT nombre, apellido, fecha_nacimiento, sexo, estado_civil, escolaridad, ocupacion, id_grupo FROM Evaluado WHERE id_evaluado = @id",
                                {"id": id_evaluado},
                            )
                            info_evaluado = {
                                "nombre": df_evaluado.at[0, "nombre"] if not df_evaluado.empty else "",
                                "apellido": df_evaluado.at[0, "apellido"] if not df_evaluado.empty else "",
                                "fecha_nacimiento": df_evaluado.at[0, "fecha_nacimiento"] if not df_evaluado.empty else "",
                                "sexo": df_evaluado.at[0, "sexo"] if not df_evaluado.empty else "",
                                "estado_civil": df_evaluado.at[0, "estado_civil"] if not df_evaluado.empty else "",
                                "escolaridad": df_evaluado.at[0, "escolaridad"] if not df_evaluado.empty else "",
                                "ocupacion": df_evaluado.at[0, "ocupacion"] if not df_evaluado.empty else "",
                                "grupo": (
                                    (
                                            fetch_df(
                                            "SELECT nombre FROM Grupo WHERE id_grupo = @id",
                                            {"id": int(df_evaluado.at[0, "id_grupo"]) }
                                        ).at[0, "nombre"]
                                        if not pd.isna(df_evaluado.at[0, "id_grupo"]) else ""
                                    ) if not df_evaluado.empty else ""
                                ),
                            }
                            # Intentar resolver una ruta de imagen conocida (raw_indicadores o sesión)
                            try:
                                ruta = None
                                raw_ind = st.session_state.get('raw_indicadores', None)
                                if isinstance(raw_ind, dict):
                                    ruta = raw_ind.get('ruta_imagen') or raw_ind.get('ruta') or raw_ind.get('image') or raw_ind.get('imagen')
                                elif isinstance(raw_ind, list):
                                    for item in raw_ind:
                                        if isinstance(item, dict) and item.get('ruta_imagen'):
                                            ruta = item.get('ruta_imagen')
                                            break
                                # Fallback a la última imagen guardada en esta sesión
                                if not ruta:
                                    ruta = st.session_state.get('last_saved_image_path', None)
                                if ruta:
                                    info_evaluado['ruta_imagen'] = ruta
                            except Exception:
                                pass
                            render_export_popover(info_evaluado, st.session_state.get("indicadores", []))
                        
        with col_next:
            next_disabled = step > 3
            next_label = "Siguiente" if step < 3 else "Finalizar"
            if st.button(next_label, disabled=next_disabled, key="nav_next", type="primary"):
                if not next_disabled:
                    if step == 1:
                        nombre_value = st.session_state.get("nombre", "").strip()
                        apellido_value = st.session_state.get("apellido", "").strip()
                        fecha_nacimiento = st.session_state.get("fecha_nacimiento_widget", st.session_state.get("form_fecha_nacimiento", ""))
                        sexo_value = st.session_state.get("sexo", "")
                        estado_civil_value = st.session_state.get("estado_civil", "")
                        escolaridad_value = st.session_state.get("escolaridad", "")
                        ocupacion_value = st.session_state.get("ocupacion", "")
                        grupo_value = st.session_state.get("form_grupo", "").strip()
                        try:
                            import services.auth as auth
                            _is_admin_for_validation = auth.is_admin()
                        except Exception:
                            _is_admin_for_validation = False

                        if _is_admin_for_validation:
                            assigned = st.session_state.get('assigned_id_usuario', None)
                            if not assigned:
                                st.markdown("""
                                    <div class="warning">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                                    </svg>
                                    <span>Debes asignar un especialista antes de continuar</span>
                                    </div>
                                """, unsafe_allow_html=True)
                                return
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
                        elif not sexo_value or sexo_value == "Selecciona una opción" or sexo_value.strip() == "":
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
                        elif not sexo_value or sexo_value == "Selecciona una opción" or sexo_value.strip() == "":
                            st.markdown('<div class="warning"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" /></svg> El sexo del evaluado es obligatorio</div>', unsafe_allow_html=True)
                        else:
                            st.session_state["form_nombre"] = nombre_value
                            st.session_state["form_apellido"] = apellido_value
                            st.session_state["form_fecha_nacimiento"] = fecha_nacimiento
                            st.session_state["form_sexo"] = sexo_value
                            st.session_state["form_estado_civil"] = "" if estado_civil_value == "Selecciona una opción" else estado_civil_value
                            st.session_state["form_escolaridad"] = "" if escolaridad_value == "Selecciona una opción" else escolaridad_value
                            st.session_state["form_ocupacion"] = "" if ocupacion_value == "Selecciona una opción" else ocupacion_value
                            st.session_state["form_grupo"] = grupo_value

                            if not st.session_state.get('already_registered', False):
                                try:
                                    grupo = st.session_state.get("form_grupo", "")
                                    params = {
                                        "nombre": nombre_value,
                                        "apellido": apellido_value,
                                        "fecha_nacimiento": fecha_nacimiento,
                                        "sexo": sexo_value,
                                        "estado_civil": st.session_state.get("form_estado_civil", None) if st.session_state.get("form_estado_civil", "") not in ("", "Selecciona una opción") else None,
                                        "escolaridad": st.session_state.get("form_escolaridad", None) if st.session_state.get("form_escolaridad", "") not in ("", "Selecciona una opción") else None,
                                        "ocupacion": st.session_state.get("form_ocupacion", None) if st.session_state.get("form_ocupacion", "") not in ("", "Selecciona una opción") else None,
                                        "id_usuario": st.session_state.get('assigned_id_usuario', None),
                                    }
                                    id_grupo = None
                                    if grupo:
                                        try:
                                            df_g = fetch_df("SELECT TOP 1 id_grupo FROM Grupo WHERE nombre = @grupo", {"grupo": grupo})
                                            if not df_g.empty:
                                                id_grupo = int(df_g.at[0, 'id_grupo'])
                                        except Exception:
                                            id_grupo = None
                                    params["id_grupo"] = id_grupo
                                    try:
                                        if params.get("id_usuario") is not None:
                                            params["id_usuario"] = int(params["id_usuario"])
                                    except Exception:
                                        params["id_usuario"] = None

                                    sql_crear = CREAR_EVALUADO
                                    df_row = fetch_df(sql_crear, params)
                                    if not df_row.empty:
                                        try:
                                            st.session_state['id_evaluado'] = int(df_row.at[0, 'id_evaluado'])
                                        except Exception:
                                            st.session_state['id_evaluado'] = int(df_row.iloc[0, 0])
                                    st.session_state['already_registered'] = True
                                except Exception as e:
                                    st.error(f"Error al crear evaluado al avanzar al paso 2: {e}")
                                    return

                            # mark that we should run inference when showing results
                            st.session_state['_run_inference_on_results'] = True
                            st.session_state["current_step"] = min(3, step + 1)
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
                            # Validate extension before any processing
                            try:
                                allowed_exts = {"png", "jpg", "jpeg", "heic"}
                                uploaded_name = getattr(st.session_state.get("uploaded_file"), "name", "") or ""
                                uploaded_ext = os.path.splitext(uploaded_name)[1].lstrip('.').lower()
                            except Exception:
                                uploaded_ext = ""

                            if uploaded_ext not in allowed_exts:
                                st.markdown(f"""
                                    <div class="warning">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                                    </svg>
                                    <span>Extensión no permitida: {uploaded_ext}. Extensiones válidas: {', '.join(sorted(allowed_exts))}.</span>
                                    </div>
                                """, unsafe_allow_html=True)
                                return

                            imagen = Image.open(st.session_state["uploaded_file"])
                            nombre = st.session_state["uploaded_file"].name
                            temp_path = Path(TEMP_DIR) / nombre
                            orig_path = Path(ORIGINALS_DIR) / nombre
                            # Ensure parent directories exist before saving
                            try:
                                temp_path.parent.mkdir(parents=True, exist_ok=True)
                            except Exception:
                                pass
                            try:
                                orig_path.parent.mkdir(parents=True, exist_ok=True)
                            except Exception:
                                pass
                            try:
                                estandarizar_imagen(imagen, orig_path)
                            except Exception as e:
                                st.error(f"Error saving original image: {e}")
                            try:
                                imagen.save(temp_path)
                            except Exception as e:
                                st.warning(f"No se pudo guardar copia temporal de la imagen: {e}")
                            # Guardar ruta en la sesión para permitir la exportación con imagen
                            try:
                                # Preferir la imagen estandarizada (orig_path) si existe
                                if orig_path.exists():
                                    st.session_state['last_saved_image_path'] = str(orig_path)
                                else:
                                    st.session_state['last_saved_image_path'] = str(temp_path)
                            except Exception:
                                try:
                                    st.session_state['last_saved_image_path'] = str(orig_path)
                                except Exception:
                                    pass

                            # Si el evaluado NO está registrado aún, intentar crear uno ahora
                            if not st.session_state.get("already_registered", False):
                                nombre_value = st.session_state.get("nombre", "").strip()
                                apellido_value = st.session_state.get("apellido", "").strip()
                                fecha_nacimiento = st.session_state.get("fecha_nacimiento_widget", st.session_state.get("form_fecha_nacimiento", ""))
                                sexo_value = st.session_state.get("sexo", "")

                                # Validaciones mínimas requeridas para crear evaluado
                                if not nombre_value or not fecha_nacimiento or not sexo_value or sexo_value == "Selecciona una opción":
                                    st.markdown("""
                                        <div class="warning">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                                        </svg>
                                        <span>Completa los datos obligatorios del evaluado (nombre, fecha de nacimiento y sexo) antes de continuar.</span>
                                        </div>
                                    """, unsafe_allow_html=True)
                                    return

                                # Preparar parámetros y crear evaluado en BD
                                try:
                                    grupo = st.session_state.get("form_grupo", "")
                                    params = {
                                        "nombre": nombre_value,
                                        "apellido": apellido_value,
                                        "fecha_nacimiento": fecha_nacimiento,
                                        "sexo": sexo_value,
                                        "estado_civil": st.session_state.get("form_estado_civil", None) if st.session_state.get("form_estado_civil", "") not in ("", "Selecciona una opción") else None,
                                        "escolaridad": st.session_state.get("form_escolaridad", None) if st.session_state.get("form_escolaridad", "") not in ("", "Selecciona una opción") else None,
                                        "ocupacion": st.session_state.get("form_ocupacion", None) if st.session_state.get("form_ocupacion", "") not in ("", "Selecciona una opción") else None,
                                        "id_usuario": st.session_state.get('assigned_id_usuario', None),
                                    }
                                    id_grupo = None
                                    if grupo:
                                        try:
                                            df_g = fetch_df("SELECT TOP 1 id_grupo FROM Grupo WHERE nombre = @grupo", {"grupo": grupo})
                                            if not df_g.empty:
                                                id_grupo = int(df_g.at[0, 'id_grupo'])
                                        except Exception:
                                            id_grupo = None
                                    params["id_grupo"] = id_grupo
                                    try:
                                        if params.get("id_usuario") is not None:
                                            params["id_usuario"] = int(params["id_usuario"])
                                    except Exception:
                                        params["id_usuario"] = None

                                    sql_crear = CREAR_EVALUADO
                                    df_row = fetch_df(sql_crear, params)
                                    if not df_row.empty:
                                        try:
                                            st.session_state['id_evaluado'] = int(df_row.at[0, 'id_evaluado'])
                                        except Exception:
                                            st.session_state['id_evaluado'] = int(df_row.iloc[0, 0])
                                    st.session_state['already_registered'] = True
                                except Exception as e:
                                    st.error(f"No se pudo crear el evaluado antes de avanzar: {e}")
                                    return

                            st.session_state["current_step"] = min(3, step + 1)
                            st.rerun()
                    elif step == 3:
                        # Finalizar: registrar evaluado (si aplica), crear prueba y subir resultados
                        if not st.session_state.get("already_registered", False):
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
                                "estado_civil": estado_civil if estado_civil and str(estado_civil).strip() != "" else None,
                                "escolaridad": escolaridad if escolaridad and str(escolaridad).strip() != "" else None,
                                "ocupacion": ocupacion if ocupacion and str(ocupacion).strip() != "" else None,
                                "grupo": grupo if grupo and str(grupo).strip() != "" else None,
                                "id_usuario": st.session_state.get('assigned_id_usuario', None),
                            }
                            try:
                                st.session_state['created_ok'] = False
                                # Resolver id_grupo si se proporcionó nombre de grupo
                                id_grupo = None
                                if grupo:
                                    try:
                                        df_g = fetch_df("SELECT TOP 1 id_grupo FROM Grupo WHERE nombre = @grupo", {"grupo": grupo})
                                        if not df_g.empty:
                                            id_grupo = int(df_g.at[0, 'id_grupo'])
                                    except Exception:
                                        id_grupo = None

                                params["id_grupo"] = id_grupo
                                try:
                                    if params.get("id_usuario") is not None:
                                        params["id_usuario"] = int(params["id_usuario"])
                                except Exception:
                                    params["id_usuario"] = None

                                sql_crear = CREAR_EVALUADO
                                df_row = fetch_df(sql_crear, params)
                                if not df_row.empty:
                                    try:
                                        st.session_state['id_evaluado'] = int(df_row.at[0, 'id_evaluado'])
                                    except Exception:
                                        st.session_state['id_evaluado'] = int(df_row.iloc[0, 0])

                                st.session_state['created_ok'] = True
                            except Exception as e:
                                st.error(f"Error al crear evaluado en la base de datos: {e}")
                                return
                        else:
                            if 'id_evaluado' not in st.session_state or st.session_state['id_evaluado'] is None:
                                st.error("Error: No se encontró el ID del evaluado seleccionado")
                                return

                        try:
                            id_evaluado = st.session_state.get('id_evaluado')
                            if id_evaluado is not None:
                                nombre_archivo = st.session_state["uploaded_file"].name
                                raw_ind = st.session_state.get('raw_indicadores', None)
                                ruta_imagen = None
                                if isinstance(raw_ind, dict):
                                    ruta_imagen = raw_ind.get('ruta_imagen', None)
                                elif isinstance(raw_ind, list):
                                    for item in raw_ind:
                                        if isinstance(item, dict) and 'ruta_imagen' in item and item.get('ruta_imagen'):
                                            ruta_imagen = item.get('ruta_imagen')
                                            break
                                    
                                formato = os.path.splitext(nombre_archivo)[1].lstrip('.').lower()
                                fecha_actual = datetime.datetime.now()

                                params_prueba = {
                                    "id_evaluado": id_evaluado,
                                    "nombre_archivo": nombre_archivo,
                                    "ruta_imagen": ruta_imagen,
                                    "formato": formato,
                                    "fecha": fecha_actual,
                                }

                                sql_prueba = POST_PRUEBA
                                df_prueba = fetch_df(sql_prueba, params_prueba)
                                if not df_prueba.empty:
                                    try:
                                        id_prueba = int(df_prueba.at[0, "id_prueba"])
                                    except Exception:
                                        id_prueba = int(df_prueba.iloc[0, 0])
                                else:
                                    raise Exception("No se obtuvo id_prueba al insertar la prueba")
                        except Exception as e:
                            st.error(f"Error al registrar la prueba en la base de datos: {e}")
                            return

                        # SUBIR RESULTADOS
                        try:
                            indicadores = st.session_state.get("indicadores", [])
                            try:
                                img_for_norm = Image.open(st.session_state["uploaded_file"])
                                img_w, img_h = img_for_norm.size
                            except Exception:
                                img_w, img_h = None, None

                            for ind in indicadores:
                                iid = ind.get("id_indicador") or ind.get("id")
                                x_min = float(ind.get("x_min", 0))
                                x_max = float(ind.get("x_max", 0))
                                y_min = float(ind.get("y_min", 0))
                                y_max = float(ind.get("y_max", 0))
                                confianza = float(ind.get("confianza", 0.0))

                                if img_w and img_h and img_w > 0 and img_h > 0:
                                    x_min_norm = x_min / img_w
                                    y_min_norm = y_min / img_h
                                    w_norm = (x_max - x_min) / img_w
                                    h_norm = (y_max - y_min) / img_h
                                else:
                                    x_min_norm = x_min
                                    y_min_norm = y_min
                                    w_norm = (x_max - x_min)
                                    h_norm = (y_max - y_min)

                                params_res = {
                                    "id_prueba": id_prueba,
                                    "id_indicador": iid,
                                    "x_min": x_min_norm,
                                    "y_min": y_min_norm,
                                    "x_max": w_norm,
                                    "y_max": h_norm,
                                    "confianza": confianza,
                                }

                                sql_res = POST_RESULTADO
                                # Ejecutar INSERT de resultado (fetch_df manejará commit)
                                fetch_df(sql_res, params_res)
                        except Exception as e:
                            st.error(f"Error al registrar los resultados en la base de datos: {e}")
                            return

                        # LIMPIAR Y VOLVER A INICIO
                        st.session_state['created_ok'] = True
                        st.session_state["active_view"] = "inicio"
                        st.session_state["current_step"] = 1
                        st.session_state["already_registered"] = False

                        # Limpiar variables de sesión relacionadas con el formulario
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
                        # Clear cached raw indicators used to avoid re-running inference
                        if 'raw_indicadores' in st.session_state:
                            try:
                                del st.session_state['raw_indicadores']
                            except Exception:
                                st.session_state['raw_indicadores'] = None
                        # Limpiar asignación temporal de especialista si existe
                        if 'assigned_id_usuario' in st.session_state:
                            try:
                                del st.session_state['assigned_id_usuario']
                            except Exception:
                                st.session_state['assigned_id_usuario'] = None
                        # Invalidar cache de historial para que muestre las filas nuevas
                        if 'historial_df' in st.session_state:
                            try:
                                del st.session_state['historial_df']
                            except Exception:
                                st.session_state['historial_df'] = None
                        st.rerun()



