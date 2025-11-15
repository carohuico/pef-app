import streamlit as st
from pathlib import Path
from PIL import Image
import datetime
import os
import pandas as pd
from sqlalchemy import text

from config.settings import TEMP_DIR, STD_DIR
from services.image_preprocess import estandarizar_imagen
from services.indicadores import simular_resultado
from services.db import get_engine, fetch_df
from services.queries.q_registro import POST_PRUEBA, POST_RESULTADO
from components.bounding_boxes import imagen_bboxes
from services.exportar import render_export_popover
# specialist list not needed here; avoid changing assigned user during adding a drawing
try:
    import numpy as _np
except Exception:
    _np = None


def _normalize_param_value(v):
    """Convert numpy scalar types and Paths to native types acceptable by pyodbc."""
    from pathlib import Path as _Path
    try:
        if _np is not None and isinstance(v, _np.generic):
            return v.item()
    except Exception:
        pass
    item = getattr(v, "item", None)
    if callable(item):
        try:
            return item()
        except Exception:
            pass
    # Path -> str
    if isinstance(v, _Path):
        return str(v)
    return v


def _normalize_params(d):
    return {k: _normalize_param_value(v) for k, v in d.items()}

@st.dialog("Agregar nueva prueba", width="large")
def agregar_dibujo(info_obj):
    """
    Modal para agregar una nueva prueba a un evaluado existente.
    Pasos: 1. Subir imagen, 2. Ver resultados, 3. Guardar
    """
    
    # ---------- INICIALIZAR ESTADO ----------
    if "agregar_step" not in st.session_state:
        st.session_state["agregar_step"] = 1
    if "agregar_uploaded_file" not in st.session_state:
        st.session_state["agregar_uploaded_file"] = None
    if "agregar_indicadores" not in st.session_state:
        st.session_state["agregar_indicadores"] = None

    # ---------- STEPPER ----------
    step = st.session_state.get("agregar_step", 1)
    steps = [
        {"label": "Subir dibujo"},
        {"label": "Resultados"},
        {"label": "Guardar"},
    ]
    
    st.markdown("""
    <style>
    .agregar-stepper .step { text-align: center; }
    .agregar-stepper .step-number { font-size: 16px; font-weight: 700; color: #333; }
    .agregar-stepper .step-label { font-size: 13px; color: #444; margin-top: 4px; }
    .agregar-stepper .step-container { padding: 6px 4px; align-items: center; justify-content: center; display: flex; flex-direction: column; }
    </style>
    """, unsafe_allow_html=True)

    cols = st.columns(len(steps))
    for idx, (col, s) in enumerate(zip(cols, steps), start=1):
        with col:
            st.markdown(
                f"<div class='agregar-stepper'><div class='step-container'><div class='step'><div class='step-number'>{idx}.</div><div class='step-label'>{s['label']}</div></div></div></div>",
                unsafe_allow_html=True,
            )
    
    st.divider()

    # --- Selección/Asignación de especialista (consistente con cargarImagen / evaluados) ---
    try:
        import auth
        is_admin = auth.is_admin()
        is_esp = auth.is_especialista()
    except Exception:
        is_admin = False
        is_esp = False

    # No mostrar selección de especialista en este modal.
    # Mantener la asignación existente si la hay; si el que abre es especialista,
    # asignamos automáticamente la prueba al especialista actual (comportamiento previo).
    current_assigned = st.session_state.get('assigned_id_usuario', None)
    if is_esp:
        user = st.session_state.get('user', {})
        uid = user.get('id_usuario')
        try:
            st.session_state['assigned_id_usuario'] = int(uid)
        except Exception:
            st.session_state['assigned_id_usuario'] = uid


    # ---------- COMPONENTES POR PASO ----------
    
    if step == 1:
        # PASO 1: Subir imagen
        uploaded_file = st.file_uploader(
            "Arrastra o selecciona una imagen", 
            type=["png", "jpg", "jpeg", "heic"], 
            key="agregar_file_uploader",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            st.session_state["agregar_uploaded_file"] = uploaded_file
    
    elif step == 2:
        # PASO 2: Mostrar resultados
        if st.session_state.get("agregar_uploaded_file") is not None:
            filename = st.session_state["agregar_uploaded_file"].name
            
            # Obtener indicadores
            with st.spinner("Analizando imagen..."):
                indicadores = simular_resultado(filename)
                st.session_state["agregar_indicadores"] = indicadores

            col1, col2 = st.columns([1, 2])

            with col1:
                original = Image.open(st.session_state["agregar_uploaded_file"])
                
                # Dibujar bounding boxes
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
                st.markdown("### Indicadores detectados")
                if not indicadores:
                    st.info("No se encontraron indicadores en la imagen.")
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
                        rows.append({
                            "Indicador": nombre, 
                            "Descripción": significado, 
                            "Confianza": conf_val
                        })
                    
                    df = pd.DataFrame(rows)
                    if 'Confianza' in df.columns:
                        df['Confianza'] = df['Confianza'].round(2)

                    # Mostrar DataFrame en modo sólo lectura usando data_editor
                    # y configurar el ancho de columnas solicitadas a "small".
                    try:
                        st.data_editor(
                            df,
                            use_container_width=True,
                            hide_index=True,
                            key="agregar_indicadores_table",
                            height=200,
                            column_config={
                                "Indicador": st.column_config.TextColumn("Indicador", width="small"),
                                "Descripción": st.column_config.TextColumn("Descripción", width="small"),
                                "Confianza": st.column_config.NumberColumn("Confianza", width="small"),
                            },
                            disabled=["Indicador", "Descripción", "Confianza"],
                        )
                    except Exception:
                        # Fallback: si data_editor no está disponible, usar st.dataframe simple
                        st.dataframe(df, use_container_width=True, hide_index=True)

    elif step == 3:
        df = pd.DataFrame([{
            "Nombre": info_obj.get("Nombre", "Desconocido"),
            "Apellido": info_obj.get("Apellido", "Desconocido"),
            "Edad": info_obj.get("Edad", "N/A"),
            "Sexo": info_obj.get("Sexo", "N/A"),
            "Estado civil": info_obj.get("Estado civil", "N/A"),
            "Escolaridad": info_obj.get("Escolaridad", "N/A"),
            "Ocupación": info_obj.get("Ocupación", "N/A"),
            "Grupo": info_obj.get("Grupo", "N/A"),
            #!FALTAN COLUMNAS DE INDICADORES + FECHA DE LA PRUEBA
        }])
        col1, col2 = st.columns(2)
        with col1:
            # Preparar info del evaluado para el exportador (puede aceptar dict o lista de dicts)
            info_evaluado = {
                "Fecha de evaluación": info_obj.get("Fecha de evaluación", ""),
                "Fecha": info_obj.get("Fecha de evaluación", ""),
                "Nombre": info_obj.get("Nombre", info_obj.get("Nombre del evaluado", "Desconocido")),
                "Nombre del evaluado": info_obj.get("Nombre", info_obj.get("Nombre del evaluado", "Desconocido")),
                "Apellido": info_obj.get("Apellido", ""),
                "Edad": info_obj.get("Edad", "N/A"),
                "Sexo": info_obj.get("Sexo", "N/A"),
                "Estado civil": info_obj.get("Estado civil", "N/A"),
                "Escolaridad": info_obj.get("Escolaridad", "N/A"),
                "Ocupación": info_obj.get("Ocupación", "N/A"),
                "Grupo": info_obj.get("Grupo", "N/A"),
            }

            if st.button("Exportar datos", use_container_width=True, key="agregar_export", type="tertiary"):
                indicadores = st.session_state.get("agregar_indicadores", [])
                # Llamar al popover de exportación (se mostrará encima del diálogo actual)
                render_export_popover(info_evaluado, indicadores)
        with col2:
            st.download_button(
                label="Descargar datos como JSON",
                data=df.to_json(orient='records', force_ascii=False),
                file_name="prueba_evaluado.json",
                mime='application/json; charset=utf-8',
                use_container_width=True,
                type="tertiary",
            )

    # ---------- NAVEGACIÓN ----------
    st.divider()
    col_back, col_next = st.columns(2)
    
    with col_back:
        if step > 1:
            button_label = ":material/arrow_back: Atrás"
            if st.button(button_label, use_container_width=True, key="agregar_back"):
                # Sólo retroceder un paso (no cerrar el modal)
                st.session_state["agregar_step"] = max(1, step - 1)
                st.rerun()
        else:
            if st.button("Cancelar", use_container_width=True, key="agregar_cancel"):
                # Limpiar y cerrar
                st.session_state["agregar_step"] = 1
                st.session_state["agregar_uploaded_file"] = None
                st.session_state["agregar_indicadores"] = None
                st.session_state['add_drawing'] = False
                # Limpiar la solicitud de apertura del diálogo
                st.session_state['_agregar_dialog_open_requested'] = False
                st.rerun()
    
    with col_next:
        # PASO 1 -> PASO 2
        if step == 1:
            button_label = "Siguiente :material/arrow_forward:"
            if st.button(button_label, type="primary", use_container_width=True, disabled=(st.session_state["agregar_uploaded_file"] is None), key="agregar_next_step1"):
                if st.session_state["agregar_uploaded_file"] is None:
                    label = ":material/warning: Por favor, sube una imagen para continuar"
                    st.error(label)
                else:
                    # Procesar imagen
                    with st.spinner("Procesando imagen..."):
                        imagen = Image.open(st.session_state["agregar_uploaded_file"])
                        nombre = st.session_state["agregar_uploaded_file"].name
                        temp_path = Path(TEMP_DIR) / nombre
                        std_path = Path(STD_DIR) / nombre
                        
                        imagen.save(temp_path)
                        estandarizar_imagen(imagen, std_path)
                    
                    st.session_state["agregar_step"] = 2
                    st.rerun(scope="fragment")
        
        # PASO 2 -> PASO 3
        elif step == 2:
            button_label = "Siguiente :material/arrow_forward:"
            if st.button(button_label, type="primary", use_container_width=True, key="agregar_next_step2"):
                st.session_state["agregar_step"] = 3
                st.rerun(scope="fragment")
        
        # PASO 3: GUARDAR
        elif step == 3:
            if st.button("Guardar prueba", type="primary", use_container_width=True, key="agregar_save"):
                with st.spinner("Guardando..."):
                    try:
                        engine = get_engine()
                        
                        # Insertar prueba
                        nombre_archivo = st.session_state["agregar_uploaded_file"].name
                        ruta_imagen = str(Path(STD_DIR) / nombre_archivo)
                        formato = os.path.splitext(nombre_archivo)[1].lstrip('.').lower()
                        fecha_actual = datetime.datetime.now()

                        with engine.begin() as conn:
                            # Insertar la prueba
                            id = info_obj.get("id_evaluado")
                            print("ID Evaluado:", id)
                            params_prueba = {
                                "id_evaluado": id,
                                "nombre_archivo": nombre_archivo,
                                "ruta_imagen": ruta_imagen,
                                "formato": formato,
                                "fecha": fecha_actual
                            }
                            params_prueba = _normalize_params(params_prueba)
                            id_prueba = conn.execute(text(POST_PRUEBA), params_prueba).fetchone()["id_prueba"]
                            
                            # Insertar resultados
                            indicadores = st.session_state.get("agregar_indicadores", [])
                            
                            try:
                                img_for_norm = Image.open(ruta_imagen)
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

                                params_result = {
                                    "id_prueba": id_prueba,
                                    "id_indicador": iid,
                                    "x_min": x_min_norm,
                                    "y_min": y_min_norm,
                                    "x_max": w_norm,
                                    "y_max": h_norm,
                                    "confianza": confianza
                                }
                                params_result = _normalize_params(params_result)
                                conn.execute(text(POST_RESULTADO), params_result)
                        
                        # Limpiar y cerrar
                        st.session_state["agregar_step"] = 1
                        st.session_state["agregar_uploaded_file"] = None
                        st.session_state["agregar_indicadores"] = None
                        st.session_state['add_drawing'] = False
                        # Limpiar la solicitud de apertura del diálogo
                        st.session_state['_agregar_dialog_open_requested'] = False
                        
                        st.balloons()
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error: {e}")