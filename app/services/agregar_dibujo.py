import streamlit as st
from pathlib import Path
from PIL import Image
import datetime
import os
import pandas as pd

from config.settings import TEMP_DIR, ORIGINALS_DIR
from services.image_preprocess import estandarizar_imagen
from services.indicadores import simular_resultado
from services.db import fetch_df
from services.queries.q_registro import POST_PRUEBA, POST_RESULTADO
from components.bounding_boxes import imagen_bboxes
from services.exportar import render_export_popover
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
        import services.auth as auth
        is_admin = auth.is_admin()
        is_esp = auth.is_especialista()
    except Exception:
        is_admin = False
        is_esp = False

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
            
            prev_uploaded = st.session_state.get('uploaded_file', None)
            try:
                st.session_state['uploaded_file'] = st.session_state.get('agregar_uploaded_file')
            except Exception:
                pass

            id_evaluado = info_obj.get('id_evaluado')
            if st.session_state.get("agregar_indicadores") is None:
                try:
                    raw_indicadores = simular_resultado(id_evaluado, show_overlay=True)
                    # Store raw result (same idea as cargarImagen)
                    try:
                        st.session_state['agregar_raw_indicadores'] = raw_indicadores
                    except Exception:
                        pass

                    # Filter indicators to only those with a usable 'significado' (same as cargarImagen)
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

                    st.session_state["agregar_indicadores"] = indicadores
                    try:
                        st.session_state['indicadores'] = indicadores
                    except Exception:
                        pass

                    # Try to capture ruta_gcs/ruta_imagen reported by the model (prefer raw entries)
                    try:
                        for ind in (raw_indicadores or []):
                            ruta = None
                            if isinstance(ind, dict):
                                ruta = ind.get('ruta_imagen') or ind.get('ruta_gcs')
                            if ruta:
                                st.session_state['last_ruta_gcs'] = ruta
                                break
                    except Exception:
                        pass
                except RuntimeError as e:
                    st.error(f"Error al consultar el servicio de inferencia: {e}")
                    st.session_state["agregar_indicadores"] = []
                except Exception as e:
                    st.error(f"Error inesperado al procesar la imagen: {e}")
                    st.session_state["agregar_indicadores"] = []
            else:
                indicadores = st.session_state.get("agregar_indicadores", [])

            # restore previous uploaded_file (if any)
            try:
                if prev_uploaded is not None:
                    st.session_state['uploaded_file'] = prev_uploaded
                else:
                    try:
                        del st.session_state['uploaded_file']
                    except Exception:
                        pass
            except Exception:
                pass

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
                    st.markdown(
                        """
                        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:12px;background:transparent;">
                            <div style="font-family: Poppins, sans-serif; font-weight:600; font-size:1rem; color:#333;margin-bottom:8px;">No se encontraron indicadores en la imagen.</div>
                            <style>
                                @keyframes smallLoaderJump { 0%,60%,100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }
                                .small-loader-dots { display:flex; gap:8px; justify-content:center; align-items:center; }
                                .small-loader-dots span { width:10px; height:10px; background:#CCCCCC; border-radius:50%; display:inline-block; animation:smallLoaderJump 0.8s infinite ease-in-out; }
                                .small-loader-dots span:nth-child(2) { animation-delay: 0.12s; }
                                .small-loader-dots span:nth-child(3) { animation-delay: 0.24s; }
                            </style>
                            <div class="small-loader-dots"><span></span><span></span><span></span></div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    rows = []
                    for ind in indicadores:
                        nombre = ind.get('nombre', '')
                        significado = ind.get('significado', '') or ''
                        try:
                            sig_str = significado.strip() if isinstance(significado, str) else str(significado).strip()
                        except Exception:
                            sig_str = ''
                        if sig_str == '' or sig_str == '-':
                            continue
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
                    
                    # If filtering removed all rows, show informational message (custom markup)
                    if not rows:
                        st.markdown(
                            """
                            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:12px;background:transparent;">
                                <div style="font-family: Poppins, sans-serif; font-weight:600; font-size:1rem; color:#333;margin-bottom:8px;">No se encontraron indicadores con descripción disponible.</div>
                                <style>
                                    @keyframes smallLoaderJump { 0%,60%,100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }
                                    .small-loader-dots { display:flex; gap:8px; justify-content:center; align-items:center; }
                                    .small-loader-dots span { width:10px; height:10px; background:#CCCCCC; border-radius:50%; display:inline-block; animation:smallLoaderJump 0.8s infinite ease-in-out; }
                                    .small-loader-dots span:nth-child(2) { animation-delay: 0.12s; }
                                    .small-loader-dots span:nth-child(3) { animation-delay: 0.24s; }
                                </style>
                                <div class="small-loader-dots"><span></span><span></span><span></span></div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        df = pd.DataFrame(rows)
                        if 'Confianza' in df.columns:
                            df['Confianza'] = df['Confianza'].round(2)

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
        }])
        col1 = st.columns(1)[0]
        with col1:
            ruta_imagen = None
            indicadores = st.session_state.get("agregar_indicadores", [])
            for ind in indicadores:
                if 'ruta_imagen' in ind and ind.get('ruta_imagen'):
                    ruta_imagen = ind.get('ruta_imagen')
                    break
            
            
            info_evaluado = {
                "Fecha de evaluación": datetime.datetime.now().strftime("%d/%m/%Y"),
                "Nombre": info_obj.get("Nombre", info_obj.get("Nombre del evaluado", "Desconocido")),
                "Apellido": info_obj.get("Apellido", ""),
                "Edad": info_obj.get("Edad", "N/A"),
                "Sexo": info_obj.get("Sexo", "N/A"),
                "Estado civil": info_obj.get("Estado civil", "N/A"),
                "Escolaridad": info_obj.get("Escolaridad", "N/A"),
                "Ocupación": info_obj.get("Ocupación", "N/A"),
                "Grupo": info_obj.get("Grupo", "N/A"),
                "ruta_imagen": ruta_imagen
            }
            st.markdown("<style>[data-testid=\"stBaseButton-tertiary\"]:not([data-testid=\"stSidebar\"] *) { background: #FFFFFF; border:none; color: #000000; margin-top: 1rem; padding: 16px 24px; display: inline-block; text-decoration: underline;  cursor: pointer; }</style>", unsafe_allow_html=True)
            if st.button("Exportar prueba", use_container_width=True, key="agregar_export", type="tertiary"):
                """"
                lista_inds.append({
                    "nombre": r.get('nombre_indicador') if 'nombre_indicador' in r else r.get('nombre') if 'nombre' in r else None,
                    "significado": r.get('significado') if 'significado' in r else None,
                    "confianza": r.get('confianza') if 'confianza' in r else None,
                    "id_indicador": r.get('id_indicador') if 'id_indicador' in r else None,
                    "id_categoria": r.get('id_categoria') if 'id_categoria' in r else None,
                    "categoria_nombre": r.get('categoria_nombre') if 'categoria_nombre' in r else None,
                    "categoria": r.get('categoria') if 'categoria' in r else None,
                })
                """
                indicadores = []
                raw_inds = st.session_state.get('agregar_raw_indicadores', [])
                for r in raw_inds:
                    lista_inds = []
                    try:
                        nombre = r.get('nombre_indicador') if 'nombre_indicador' in r else r.get('nombre') if 'nombre' in r else None
                    except Exception:
                        nombre = None
                    try:
                        significado = r.get('significado') if 'significado' in r else None
                    except Exception:
                        significado = None
                    try:
                        confianza = r.get('confianza') if 'confianza' in r else None
                    except Exception:
                        confianza = None
                    try:
                        id_indicador = r.get('id_indicador') if 'id_indicador' in r else None
                    except Exception:
                        id_indicador = None
                    try:
                        id_categoria = r.get('id_categoria') if 'id_categoria' in r else None
                    except Exception:
                        id_categoria = None
                    try:
                        categoria_nombre = r.get('categoria_nombre') if 'categoria_nombre' in r else None
                    except Exception:
                        categoria_nombre = None
                    try:
                        categoria = r.get('categoria') if 'categoria' in r else None
                    except Exception:
                        categoria = None

                    indicadores.append({
                        "nombre": nombre,
                        "significado": significado, 
                        "confianza": confianza,
                        "id_indicador": id_indicador,
                        "id_categoria": id_categoria,
                        "categoria_nombre": categoria_nombre,
                        "categoria": categoria,
                    })                
                render_export_popover(info_evaluado, indicadores)

    # ---------- NAVEGACIÓN ----------
    st.divider()
    col_back, col_next = st.columns(2)
    
    with col_back:
        if step > 1:
            button_label = "Atrás"
            if st.button(button_label, use_container_width=True, key="agregar_back"):
                st.session_state["agregar_step"] = max(1, step - 1)
                st.rerun()
        else:
            if st.button("Cancelar", use_container_width=True, key="agregar_cancel"):
                st.session_state["agregar_step"] = 1
                st.session_state["agregar_uploaded_file"] = None
                st.session_state["agregar_indicadores"] = None
                st.session_state['add_drawing'] = False
                st.session_state['_agregar_dialog_open_requested'] = False
                st.rerun()
    
    with col_next:
        # PASO 1 -> PASO 2
        if step == 1:
            button_label = "Siguiente"
            if st.button(button_label, type="primary", use_container_width=True, disabled=(st.session_state["agregar_uploaded_file"] is None), key="agregar_next_step1"):
                if st.session_state["agregar_uploaded_file"] is None:
                    label = ":material/warning: Por favor, sube una imagen para continuar"
                    st.error(label)
                else:
                    with st.spinner("Procesando imagen..."):
                        imagen = Image.open(st.session_state["agregar_uploaded_file"])
                        nombre = st.session_state["agregar_uploaded_file"].name
                        temp_path = Path(TEMP_DIR) / nombre
                        orig_path = Path(ORIGINALS_DIR) / nombre

                        try:
                            temp_path.parent.mkdir(parents=True, exist_ok=True)
                        except Exception:
                            pass
                        try:
                            orig_path.parent.mkdir(parents=True, exist_ok=True)
                        except Exception:
                            pass

                        # Try to save standardized original first, then a temp copy
                        try:
                            estandarizar_imagen(imagen, orig_path)
                        except Exception as e:
                            st.error(f"Error saving original image: {e}")
                        try:
                            imagen.save(temp_path)
                        except Exception as e:
                            st.warning(f"No se pudo guardar copia temporal de la imagen: {e}")
                    
                    st.session_state["agregar_step"] = 2
                    st.rerun(scope="fragment")
        
        # PASO 2 -> PASO 3
        elif step == 2:
            button_label = "Siguiente"
            if st.button(button_label, type="primary", use_container_width=True, key="agregar_next_step2"):
                st.session_state["agregar_step"] = 3
                st.rerun(scope="fragment")
        
        # PASO 3: GUARDAR
        elif step == 3:
            if st.button("Guardar prueba", type="primary", use_container_width=True, key="agregar_save"):
                    try:
                        nombre_archivo = st.session_state["agregar_uploaded_file"].name

                        ruta_imagen = None
                        raw_ind = st.session_state.get('agregar_raw_indicadores', None)
                        try:
                            if isinstance(raw_ind, dict):
                                ruta_imagen = raw_ind.get('ruta_imagen') or raw_ind.get('ruta_gcs')
                            elif isinstance(raw_ind, list):
                                for item in raw_ind:
                                    if isinstance(item, dict) and item.get('ruta_imagen'):
                                        ruta_imagen = item.get('ruta_imagen')
                                        break
                        except Exception:
                            ruta_imagen = None

                        last_preview = st.session_state.get('last_preview_local', None)
                        last_gcs = st.session_state.get('last_ruta_gcs', None)

                        if not ruta_imagen:
                            if last_gcs:
                                ruta_imagen = last_gcs
                            else:
                                # Prefer storing a relative uploads path rather than an absolute filesystem path
                                ruta_imagen = str(Path("uploads") / "originals" / nombre_archivo)
                        formato = os.path.splitext(nombre_archivo)[1].lstrip('.').lower()
                        fecha_actual = datetime.datetime.now()

                        id_evaluado = info_obj.get("id_evaluado")
                        params_prueba = {
                            "id_evaluado": id_evaluado,
                            "nombre_archivo": nombre_archivo,
                            "ruta_imagen": ruta_imagen,
                            "formato": formato,
                            "fecha": fecha_actual
                        }
                        params_prueba = _normalize_params(params_prueba)
                        sql_prueba = POST_PRUEBA
                        df_prueba = fetch_df(sql_prueba, params_prueba)
                        if df_prueba is None or df_prueba.empty:
                            raise Exception("No se obtuvo id_prueba al insertar la prueba")
                        try:
                            id_prueba = int(df_prueba.iloc[0]["id_prueba"])
                        except Exception:
                            id_prueba = df_prueba.iloc[0].get("id_prueba")

                        # Insertar resultados
                        indicadores = st.session_state.get("agregar_indicadores", [])
                        try:
                            img_for_norm = Image.open(st.session_state["agregar_uploaded_file"])  # Usar el archivo subido
                            img_w, img_h = img_for_norm.size
                        except Exception:
                            img_w, img_h = None, None

                        sql_resultado = POST_RESULTADO
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
                            fetch_df(sql_resultado, params_result)

                        try:
                            import importlib
                            module_names = [
                                'app.components.individual',
                                'components.individual',
                            ]
                            for mod_name in module_names:
                                try:
                                    mod = importlib.import_module(mod_name)
                                except Exception:
                                    mod = None
                                if mod is not None:
                                    try:
                                        mod.get_pruebas_data.clear()
                                    except Exception:
                                        pass
                                    try:
                                        mod.get_info.clear()
                                    except Exception:
                                        pass
                        except Exception:
                            pass

                        # Store the newly created prueba id so the individual view can open it
                        try:
                            st.session_state['open_prueba_id'] = id_prueba
                        except Exception:
                            pass

                        # Limpiar y cerrar
                        st.session_state["agregar_step"] = 1
                        st.session_state["agregar_uploaded_file"] = None
                        st.session_state["agregar_indicadores"] = None
                        # Clear raw indicators and mirrored indicadores (same as cargarImagen cleanup)
                        if 'agregar_raw_indicadores' in st.session_state:
                            try:
                                del st.session_state['agregar_raw_indicadores']
                            except Exception:
                                st.session_state['agregar_raw_indicadores'] = None
                        if 'indicadores' in st.session_state:
                            try:
                                del st.session_state['indicadores']
                            except Exception:
                                st.session_state['indicadores'] = None
                        st.session_state['add_drawing'] = False
                        # Limpiar la solicitud de apertura del diálogo
                        st.session_state['_agregar_dialog_open_requested'] = False

                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")