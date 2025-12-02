import streamlit as st
import pandas as pd
from typing import List, Dict
from pathlib import Path
from services.exportar import render_export_popover
from services.db import fetch_df
from services.queries.q_evaluados import LISTADO_EVALUADOS_SQL, ELIMINAR_EVALUADOS
from services.queries.q_registro import GET_GRUPOS, CREAR_EVALUADO
from services.queries.q_usuarios import GET_ESPECIALISTAS
# sqlalchemy removed; use fetch_df
import datetime

# Cached loaders for heavy read queries
@st.cache_data(ttl=300, max_entries=128)
def load_especialistas():
    return fetch_df(GET_ESPECIALISTAS)


@st.cache_data(ttl=300, max_entries=128)
def load_grupos_cache():
    return fetch_df(GET_GRUPOS)


@st.cache_data(ttl=300, max_entries=64)
def load_listado_evaluados_base():
    return fetch_df(LISTADO_EVALUADOS_SQL)


@st.dialog(":material/warning: Confirmar Eliminación")
def confirmar_eliminacion_historial(selected_rows_df):
    """Dialogo para confirmar eliminación de registros en historial."""
    try:
        n = len(selected_rows_df)
    except Exception:
        n = 0

    # Key para mensaje de confirmación mostrado debajo de los botones
    msg_key = 'hist_delete_msg'

    if n == 1:
        try:
            nombre = selected_rows_df.iloc[0].get('Nombre', '')
            apellido = selected_rows_df.iloc[0].get('Apellido', '')
            st.warning(f"¿Estás seguro de que deseas eliminar al evaluado **{nombre} {apellido}**?")
        except Exception:
            st.warning("¿Estás seguro de que deseas eliminar este evaluado?")
    else:
        st.warning(f"¿Estás seguro de que deseas eliminar **{n} evaluado(s)**?")

    st.markdown("<span style='color: #e60000;'>Esta acción no se puede deshacer.</span>", unsafe_allow_html=True)

    col_yes, col_no = st.columns(2)
    with col_yes:
        st.markdown("<br><br/>", unsafe_allow_html=True)
        label = ":material/check: Sí, eliminar"
        if st.button(label, use_container_width=True, type="primary", key="hist_confirmar_eliminar"):
            try:
                ids = []
                for v in selected_rows_df['id_evaluado'].tolist():
                    try:
                        ids.append(int(v))
                    except Exception:
                        continue

                if not ids:
                    st.markdown("""
                    <div class="warning">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                    </svg>
                    <span>No se pudieron resolver los ids seleccionados.</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    ids_csv = ','.join(str(x) for x in ids)
                    try:

                        placeholders = ','.join(['%s'] * len(ids))
                        sql_del = f"DELETE FROM Evaluado OUTPUT DELETED.id_evaluado AS deleted_id WHERE id_evaluado IN ({placeholders})"
                        df_deleted = fetch_df(sql_del, tuple(ids))
                        try:
                            rows_deleted = len(df_deleted) if df_deleted is not None else 0
                        except Exception:
                            rows_deleted = 0

                        # Guardar el mensaje en session_state para mostrarlo fuera de la columna
                        st.session_state[msg_key] = f"Se eliminaron {rows_deleted} evaluado(s)."
                        # Invalidate cached read results so next view shows fresh data
                        try:
                            load_listado_evaluados_base.clear()
                            load_grupos_cache.clear()
                            load_especialistas.clear()
                        except Exception:
                            pass
                        # Actualizar datos en session_state
                        st.session_state['evaluados_df'] = pd.DataFrame(get_historial_data())
                        st.session_state['historial_selection'] = {'rows': []}
                    except Exception as e:
                        st.error(f"Error al eliminar evaluados: {e}")
            except Exception as e:
                st.error(f":material/error: Error al procesar eliminación: {e}")
            st.rerun()

    with col_no:
        st.markdown("<br><br/>", unsafe_allow_html=True)
        label = ":material/cancel: Cancelar"
        if st.button(label, use_container_width=True, key="hist_cancelar_eliminar"):
            # Si hay un mensaje previo de eliminación, eliminarlo al cancelar
            if msg_key in st.session_state:
                try:
                    del st.session_state[msg_key]
                except Exception:
                    pass
            st.rerun()

    # Mostrar mensaje de confirmación debajo de ambos botones si existe
    if msg_key in st.session_state and st.session_state.get(msg_key):
        st.markdown("<br/>", unsafe_allow_html=True)
        st.success(st.session_state.get(msg_key))


@st.dialog(":material/add: Crear Evaluado")
def dialog_crear_evaluado():
    """Diálogo para crear un nuevo evaluado."""
    # Hacer el diálogo más ancho para facilitar el formulario (solo mientras este diálogo esté abierto)
    st.markdown(
        """
        <style>
        div[role="dialog"] {
            width: 900px !important;
            max-width: 95vw !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.form("form_crear_evaluado", border=False):
        st.write("Completa la información del nuevo evaluado:")

        # --- Selección/Asignación de especialista (mismo comportamiento que en cargarImagen) ---
        try:
            import services.auth as auth
            is_admin = auth.is_admin()
            is_esp = auth.is_especialista()
        except Exception:
            is_admin = False
            is_esp = False

        # Obtener lista de especialistas (cached)
        try:
            df_esp = load_especialistas()
            esp_options = df_esp['nombre_completo'].tolist() if not df_esp.empty else []
            esp_ids = df_esp['id_usuario'].tolist() if not df_esp.empty else []
        except Exception:
            esp_options = []
            esp_ids = []

        # Valor por defecto si viene en sesión
        current_assigned = st.session_state.get('assigned_id_usuario', None)

        if is_admin:
            if not esp_options:
                st.info("No hay especialistas disponibles para asignar.")
                assigned_sel = None
            else:
                default_index = 0
                if current_assigned is not None:
                    try:
                        default_index = esp_ids.index(int(current_assigned)) + 1
                    except Exception:
                        default_index = 0
                sel = st.selectbox("Especialista responsable", ["Selecciona un especialista"] + esp_options, index=default_index, key="create_select_esp")
                if sel != "Selecciona un especialista":
                    sel_idx = esp_options.index(sel)
                    try:
                        assigned_sel = int(esp_ids[sel_idx])
                    except Exception:
                        assigned_sel = esp_ids[sel_idx]
                    st.session_state['assigned_id_usuario'] = assigned_sel
                else:
                    assigned_sel = None
                    if 'assigned_id_usuario' in st.session_state:
                        try:
                            del st.session_state['assigned_id_usuario']
                        except Exception:
                            st.session_state['assigned_id_usuario'] = None
        elif is_esp:
            # asignar automáticamente al especialista que está creando
            user = st.session_state.get('user', {})
            uid = user.get('id_usuario')
            try:
                st.session_state['assigned_id_usuario'] = int(uid)
            except Exception:
                st.session_state['assigned_id_usuario'] = uid
            assigned_sel = st.session_state['assigned_id_usuario']
        else:
            assigned_sel = None
        
        # Primera fila: Nombre y Apellido
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input(
                "Nombre(s) :red[*]",
                placeholder="Nombre del evaluado",
                key="create_nombre"
            )
        with col2:
            apellido = st.text_input(
                "Apellido(s)",
                placeholder="Apellido del evaluado",
                key="create_apellido"
            )
        
        # Segunda fila: Fecha de nacimiento y Sexo
        col1, col2 = st.columns(2)
        with col1:
            today = datetime.date.today()
            max_dob = today - datetime.timedelta(days=18 * 365)
            min_dob = today - datetime.timedelta(days=100 * 365)
            
            fecha_nacimiento = st.date_input(
                "Fecha de nacimiento :red[*]",
                min_value=min_dob,
                max_value=max_dob,
                format="DD/MM/YYYY",
                key="create_fecha_nacimiento",
                value=None
            )
        
        with col2:
            sexo_options = ["Selecciona una opción", "Mujer", "Hombre"]
            sexo = st.selectbox(
                "Sexo :red[*]",
                sexo_options,
                key="create_sexo"
            )
        
        # Tercera fila: Estado civil y Escolaridad
        col1, col2 = st.columns(2)
        with col1:
            estado_options = ["Selecciona una opción", "Soltero(a)", "Casado(a)", "Divorciado(a)", "Viudo(a)", "Separado(a)", "Convivencia civil"]
            estado_civil = st.selectbox(
                "Estado civil",
                estado_options,
                key="create_estado_civil"
            )
        
        with col2:
            escolaridad_options = ["Selecciona una opción", "Ninguno", "Primaria", "Secundaria", "Preparatoria o Bachillerato", "Técnico", "Licenciatura", "Maestría", "Doctorado", "Posgrado"]
            escolaridad = st.selectbox(
                "Último grado alcanzado",
                escolaridad_options,
                key="create_escolaridad"
            )
        
        # Cuarta fila: Ocupación y Grupo
        col1, col2 = st.columns(2)
        with col1:
            ocupacion_options = ["Selecciona una opción", "Empleado(a)", "Desempleado(a)", "Jubilado(a) / Pensionado(a)", "Trabajador(a) por cuenta propia", "Empresario(a) / Emprendedor(a)", "Dedicado(a) al hogar", "Estudiante", "Otro"]
            ocupacion = st.selectbox(
                "Ocupación",
                ocupacion_options,
                key="create_ocupacion"
            )
        
        with col2:
            try:
                df_groups = load_grupos_cache()
                group_names = [str(x) for x in df_groups['nombre'].fillna('')]
                if not group_names:
                    group_options = ["Sin grupo"]
                else:
                    group_options = ["Selecciona un grupo"] + group_names
            except Exception:
                group_options = ["Selecciona un grupo"]
            
            grupo = st.selectbox(
                "Grupo al que pertenece",
                group_options,
                key="create_grupo"
            )
        
        # Botones de acción
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<br><br/>", unsafe_allow_html=True)
            cancelar = st.form_submit_button(":material/cancel: Cancelar", use_container_width=True)
        
        with col2:
            st.markdown("<br><br/>", unsafe_allow_html=True)
            submitted = st.form_submit_button(":material/check: Guardar", use_container_width=True, type="primary")
        
        if cancelar:
            st.rerun()
        
        if submitted:
            # Validaciones
            campos_vacios = []
            if not nombre or not nombre.strip():
                campos_vacios.append("Nombre")
            if not fecha_nacimiento:
                campos_vacios.append("Fecha de nacimiento")
            if sexo == "Selecciona una opción":
                campos_vacios.append("Sexo")
            
            if campos_vacios:
                st.error(f":material/warning: Los siguientes campos son obligatorios: {', '.join(campos_vacios)}")
                st.stop()
            
            if not all(c.isalpha() or c.isspace() for c in nombre.strip()):
                st.error(":material/warning: El nombre solo debe contener letras alfabéticas y espacios")
                st.stop()
            
            # Crear evaluado en la base de datos (usar fetch_df)
            try:
                # Resolver id_grupo
                id_grupo = None
                if grupo not in ("Selecciona un grupo", "Sin grupo", ""):
                    try:
                        res_g_df = fetch_df("SELECT TOP 1 id_grupo FROM Grupo WHERE nombre = @grupo", {"grupo": grupo})
                        if res_g_df is not None and not res_g_df.empty:
                            row_g = res_g_df.iloc[0]
                            id_grupo = int(row_g[0]) if len(row_g) > 0 else None
                    except Exception:
                        pass

                # Preparar valores
                estado_civil_val = None if estado_civil == "Selecciona una opción" else estado_civil
                escolaridad_val = None if escolaridad == "Selecciona una opción" else escolaridad
                ocupacion_val = None if ocupacion == "Selecciona una opción" else ocupacion

                try:
                    import services.auth as auth
                    is_esp = auth.is_especialista()
                except Exception:
                    is_esp = False

                current_user_id = None
                try:
                    current_user_id = st.session_state.get('user', {}).get('id_usuario')
                except Exception:
                    current_user_id = None

                # Si el creador es admin, asegurar que seleccionó un especialista
                if is_admin:
                    assigned = st.session_state.get('assigned_id_usuario', None)
                    if assigned is None:
                        st.error(":material/warning: Debes seleccionar un especialista asignado al crear un evaluado.")
                        st.stop()
                    params_id_usuario = int(assigned)
                elif is_esp:
                    params_id_usuario = int(current_user_id) if current_user_id is not None else None
                else:
                    # para otros roles, no asignar por defecto
                    params_id_usuario = None

                params = {
                    "nombre": nombre.strip(),
                    "apellido": apellido.strip() if apellido else "",
                    "fecha_nacimiento": fecha_nacimiento,
                    "sexo": sexo,
                    "estado_civil": estado_civil_val,
                    "escolaridad": escolaridad_val,
                    "ocupacion": ocupacion_val,
                    "id_grupo": id_grupo,
                    "id_usuario": params_id_usuario
                }

                # Ejecutar insert y obtener id_evaluado
                sql_crear = CREAR_EVALUADO
                df_new = fetch_df(sql_crear, params)
                id_evaluado = None
                if df_new is not None and not df_new.empty:
                    try:
                        id_evaluado = int(df_new.iloc[0].get('id_evaluado') or df_new.iloc[0].iloc[0])
                    except Exception:
                        try:
                            id_evaluado = int(df_new.iloc[0].iloc[0])
                        except Exception:
                            id_evaluado = None

                st.success(f":material/check: Evaluado '{nombre}' creado exitosamente")
                if 'evaluados_df' in st.session_state:
                    del st.session_state['evaluados_df']
                # Invalidate cached read results so next view shows fresh data
                try:
                    load_listado_evaluados_base.clear()
                    load_grupos_cache.clear()
                    load_especialistas.clear()
                except Exception:
                    pass
                import time
                time.sleep(1)
                st.rerun()

            except Exception as e:
                st.error(f":material/error: Error al crear evaluado: {e}")


@st.dialog(":material/edit: Editar Evaluado")
def dialog_editar_evaluado(evaluado_data):
    """Diálogo para editar información de un evaluado existente."""

    with st.form("form_editar_evaluado", border=False):
        
        # Primera fila: Nombre y Apellido
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input(
                "Nombre(s) :red[*]",
                value=evaluado_data.get('Nombre', ''),
                key="edit_nombre",
                placeholder="Nombre del evaluado"
            )
        with col2:
            apellido = st.text_input(
                "Apellido(s)",
                value=evaluado_data.get('Apellido', ''),
                key="edit_apellido",
                placeholder="Apellido del evaluado"
            )
        
        # Segunda fila: Fecha de nacimiento y Sexo
        col1, col2 = st.columns(2)
        with col1:
            edad = evaluado_data.get('Edad', 18)
            try:
                edad_int = int(edad)
            except:
                edad_int = 18
            fecha_nacimiento_estimada = datetime.date.today() - datetime.timedelta(days=edad_int * 365)
            
            today = datetime.date.today()
            max_dob = today - datetime.timedelta(days=18 * 365)
            min_dob = today - datetime.timedelta(days=100 * 365)
            
            fecha_nacimiento = st.date_input(
                "Fecha de nacimiento :red[*]",
                value=fecha_nacimiento_estimada,
                min_value=min_dob,
                max_value=max_dob,
                format="DD/MM/YYYY",
                key="edit_fecha_nacimiento"
            )
        
        with col2:
            sexo_options = ["Selecciona una opción", "Mujer", "Hombre"]
            sexo_actual = evaluado_data.get('Sexo', 'Selecciona una opción')
            sexo_index = sexo_options.index(sexo_actual) if sexo_actual in sexo_options else 0
            sexo = st.selectbox(
                "Sexo :red[*]",
                sexo_options,
                index=sexo_index,
                key="edit_sexo"
            )
        
        # Tercera fila: Estado civil y Escolaridad
        col1, col2 = st.columns(2)
        with col1:
            estado_options = ["Selecciona una opción", "Soltero(a)", "Casado(a)", "Divorciado(a)", "Viudo(a)", "Separado(a)", "Convivencia civil"]
            estado_actual = evaluado_data.get('Estado civil', 'Selecciona una opción')
            estado_index = estado_options.index(estado_actual) if estado_actual in estado_options else 0
            estado_civil = st.selectbox(
                "Estado civil",
                estado_options,
                index=estado_index,
                key="edit_estado_civil"
            )
        
        with col2:
            escolaridad_options = ["Selecciona una opción", "Ninguno", "Primaria", "Secundaria", "Preparatoria o Bachillerato", "Técnico", "Licenciatura", "Maestría", "Doctorado", "Posgrado"]
            escolaridad_actual = evaluado_data.get('Escolaridad', 'Selecciona una opción')
            escolaridad_index = escolaridad_options.index(escolaridad_actual) if escolaridad_actual in escolaridad_options else 0
            escolaridad = st.selectbox(
                "Último grado alcanzado",
                escolaridad_options,
                index=escolaridad_index,
                key="edit_escolaridad"
            )
        
        # Cuarta fila: Ocupación y Grupo
        col1, col2 = st.columns(2)
        with col1:
            ocupacion_options = ["Selecciona una opción", "Empleado(a)", "Desempleado(a)", "Jubilado(a) / Pensionado(a)", "Trabajador(a) por cuenta propia", "Empresario(a) / Emprendedor(a)", "Dedicado(a) al hogar", "Estudiante", "Otro"]
            ocupacion_actual = evaluado_data.get('Ocupación', 'Selecciona una opción')
            ocupacion_index = ocupacion_options.index(ocupacion_actual) if ocupacion_actual in ocupacion_options else 0
            ocupacion = st.selectbox(
                "Ocupación",
                ocupacion_options,
                index=ocupacion_index,
                key="edit_ocupacion"
            )
        
        with col2:
            try:
                df_groups = load_grupos_cache()
                group_names = [str(x) for x in df_groups['nombre'].fillna('')]
                if not group_names:
                    group_options = ["Sin grupo"]
                else:
                    group_options = ["Selecciona un grupo"] + group_names
            except Exception:
                group_options = ["Selecciona un grupo"]
            
            grupo_actual = evaluado_data.get('Grupo', 'Selecciona un grupo')
            grupo_index = group_options.index(grupo_actual) if grupo_actual in group_options else 0
            grupo = st.selectbox(
                "Grupo al que pertenece",
                group_options,
                index=grupo_index,
                key="edit_grupo"
            )

        # Selector de especialista (permitir reasignar al editar)
        try:
            df_esp = load_especialistas()
            if df_esp is None or df_esp.empty:
                esp_map = {}
                esp_ids = [None]
            else:
                esp_map = dict(zip(df_esp['id_usuario'], df_esp['nombre_completo']))
                esp_ids = [None] + [int(x) for x in df_esp['id_usuario'].tolist()]
        except Exception:
            esp_map = {}
            esp_ids = [None]

        # Valor actual del especialista asignado al evaluado
        raw_current_esp = evaluado_data.get('id_usuario', None)
        try:
            current_esp = int(raw_current_esp) if raw_current_esp not in (None, '', float('nan')) else None
        except Exception:
            current_esp = None

        try:
            default_idx = esp_ids.index(current_esp) if current_esp in esp_ids else 0
        except Exception:
            default_idx = 0

        id_usuario_selected = st.selectbox(
            "Especialista asignado",
            options=esp_ids,
            index=default_idx,
            format_func=lambda x: "Sin especialista" if x is None else esp_map.get(int(x), str(x)),
            key="edit_id_usuario"
        )
        
        # Botones de acción
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<br><br/>", unsafe_allow_html=True)
            cancelar = st.form_submit_button(":material/cancel: Cancelar", use_container_width=True)
        
        with col2:
            st.markdown("<br><br/>", unsafe_allow_html=True)
            submitted = st.form_submit_button(":material/check: Guardar Cambios", use_container_width=True, type="primary")
        
        if cancelar:
            st.rerun()
        
        if submitted:
            # Validaciones
            if not nombre.strip():
                st.error(":material/warning: El nombre del evaluado es obligatorio")
                st.stop()
            
            if not all(c.isalpha() or c.isspace() for c in nombre.strip()):
                st.error(":material/warning: El nombre solo debe contener letras alfabéticas y espacios")
                st.stop()
            
            if not fecha_nacimiento:
                st.error(":material/warning: La fecha de nacimiento del evaluado es obligatoria")
                st.stop()
            
            if sexo == "Selecciona una opción":
                st.error(":material/warning: El sexo del evaluado es obligatorio")
                st.stop()
            
            try:
                id_evaluado = evaluado_data.get('id_evaluado')

                # Resolver id_grupo
                id_grupo = None
                if grupo not in ("Selecciona un grupo", "Sin grupo", ""):
                    try:
                        res_g_df = fetch_df("SELECT TOP 1 id_grupo FROM Grupo WHERE nombre = @grupo", {"grupo": grupo})
                        if res_g_df is not None and not res_g_df.empty:
                            row_g = res_g_df.iloc[0]
                            id_grupo = int(row_g[0]) if len(row_g) > 0 else None
                    except Exception:
                        pass

                # Preparar valores para actualización
                estado_civil_val = None if estado_civil == "Selecciona una opción" else estado_civil
                escolaridad_val = None if escolaridad == "Selecciona una opción" else escolaridad
                ocupacion_val = None if ocupacion == "Selecciona una opción" else ocupacion

                update_query = """
                UPDATE dbo.Evaluado
                SET nombre = @nombre,
                    apellido = @apellido,
                    fecha_nacimiento = @fecha_nacimiento,
                    sexo = @sexo,
                    estado_civil = @estado_civil,
                    escolaridad = @escolaridad,
                    ocupacion = @ocupacion,
                    id_grupo = @id_grupo,
                    id_usuario = @id_usuario
                WHERE id_evaluado = @id_evaluado
                """

                params_update = {
                    "id_evaluado": id_evaluado,
                    "nombre": nombre.strip(),
                    "apellido": apellido.strip(),
                    "fecha_nacimiento": fecha_nacimiento,
                    "sexo": sexo,
                    "estado_civil": estado_civil_val,
                    "escolaridad": escolaridad_val,
                    "ocupacion": ocupacion_val,
                    "id_grupo": id_grupo,
                    "id_usuario": int(id_usuario_selected) if id_usuario_selected is not None else None
                }

                fetch_df(update_query, params_update)

                st.success(f":material/check: Evaluado '{nombre}' actualizado correctamente")
                if 'evaluados_df' in st.session_state:
                    del st.session_state['evaluados_df']
                # Invalidate cached read results so next view shows fresh data
                try:
                    load_listado_evaluados_base.clear()
                    load_grupos_cache.clear()
                    load_especialistas.clear()
                except Exception:
                    pass
                import time
                time.sleep(1)
                st.rerun()

            except Exception as e:
                st.error(f":material/error: Error al actualizar evaluado: {e}")


@st.dialog(":material/filter_list: Filtros")
def dialog_filtros(key_prefix: str = None):
    """Diálogo para filtrar datos por columnas."""
    
    st.write("Selecciona los filtros que deseas aplicar:")
    
    # Obtener datos originales
    original_data = get_historial_data()
    df_original = pd.DataFrame(original_data)
    
    # Inicializar filtros en session_state si no existen
    if 'active_filters' not in st.session_state:
        st.session_state['active_filters'] = {}
    
    # Filtro por Sexo
    sexo_options = ["Todos"] + sorted(df_original['Sexo'].dropna().unique().tolist())
    sexo_filter = st.selectbox(
        "Sexo",
        sexo_options,
        index=sexo_options.index(st.session_state['active_filters'].get('Sexo', 'Todos')) if st.session_state['active_filters'].get('Sexo', 'Todos') in sexo_options else 0,
        key=(f"{key_prefix}__filter_sexo" if key_prefix else "filter_sexo")
    )
    
    # Filtro por Estado civil
    estado_options = ["Todos"] + sorted(df_original['Estado civil'].dropna().unique().tolist())
    estado_filter = st.selectbox(
        "Estado civil",
        estado_options,
        index=estado_options.index(st.session_state['active_filters'].get('Estado civil', 'Todos')) if st.session_state['active_filters'].get('Estado civil', 'Todos') in estado_options else 0,
        key=(f"{key_prefix}__filter_estado" if key_prefix else "filter_estado")
    )
    
    # Filtro por Escolaridad
    escolaridad_options = ["Todos"] + sorted(df_original['Escolaridad'].dropna().unique().tolist())
    escolaridad_filter = st.selectbox(
        "Escolaridad",
        escolaridad_options,
        index=escolaridad_options.index(st.session_state['active_filters'].get('Escolaridad', 'Todos')) if st.session_state['active_filters'].get('Escolaridad', 'Todos') in escolaridad_options else 0,
        key=(f"{key_prefix}__filter_escolaridad" if key_prefix else "filter_escolaridad")
    )
    
    # Filtro por Ocupación
    ocupacion_options = ["Todos"] + sorted(df_original['Ocupación'].dropna().unique().tolist())
    ocupacion_filter = st.selectbox(
        "Ocupación",
        ocupacion_options,
        index=ocupacion_options.index(st.session_state['active_filters'].get('Ocupación', 'Todos')) if st.session_state['active_filters'].get('Ocupación', 'Todos') in ocupacion_options else 0,
        key=(f"{key_prefix}__filter_ocupacion" if key_prefix else "filter_ocupacion")
    )
    
    # Filtro por Grupo
    grupo_options = ["Todos"] + sorted(df_original['Grupo'].dropna().unique().tolist())
    grupo_filter = st.selectbox(
        "Grupo",
        grupo_options,
        index=grupo_options.index(st.session_state['active_filters'].get('Grupo', 'Todos')) if st.session_state['active_filters'].get('Grupo', 'Todos') in grupo_options else 0,
        key=(f"{key_prefix}__filter_grupo" if key_prefix else "filter_grupo")
    )
    
    # Filtro por edad mínima
    edad_min = st.number_input(
        "Edad mínima",
        min_value=18,
        max_value=100,
        value=st.session_state['active_filters'].get('edad_min', 18),
        key=(f"{key_prefix}__filter_edad_min" if key_prefix else "filter_edad_min")
    )
    
    col1, col3 = st.columns(2)
    if key_prefix:
        def _k(s):
            return f"{key_prefix}__{s}"
    else:
        def _k(s):
            return s

    with col1:
        st.markdown("<br><br/>", unsafe_allow_html=True)
        if st.button(":material/refresh: Limpiar", use_container_width=True, key=_k("clear_filters")):
            st.session_state['active_filters'] = {}
            if 'evaluados_df' in st.session_state:
                del st.session_state['evaluados_df']
            st.rerun()

    
    with col3:
        st.markdown("<br><br/>", unsafe_allow_html=True)
        if st.button(":material/check: Aplicar", use_container_width=True, type="primary", key=_k("apply_filters")):
            # Guardar filtros activos
            filters = {}
            if sexo_filter != "Todos":
                filters['Sexo'] = sexo_filter
            if estado_filter != "Todos":
                filters['Estado civil'] = estado_filter
            if escolaridad_filter != "Todos":
                filters['Escolaridad'] = escolaridad_filter
            if ocupacion_filter != "Todos":
                filters['Ocupación'] = ocupacion_filter
            if grupo_filter != "Todos":
                filters['Grupo'] = grupo_filter

            # edad mínima siempre se guarda
            filters['edad_min'] = edad_min
            
            st.session_state['active_filters'] = filters
            
            # Aplicar filtros
            df_filtered = df_original.copy()
            
            if sexo_filter != "Todos":
                df_filtered = df_filtered[df_filtered['Sexo'] == sexo_filter]
            
            if estado_filter != "Todos":
                df_filtered = df_filtered[df_filtered['Estado civil'] == estado_filter]
            
            if escolaridad_filter != "Todos":
                df_filtered = df_filtered[df_filtered['Escolaridad'] == escolaridad_filter]
            
            if ocupacion_filter != "Todos":
                df_filtered = df_filtered[df_filtered['Ocupación'] == ocupacion_filter]
            
            if grupo_filter != "Todos":
                df_filtered = df_filtered[df_filtered['Grupo'] == grupo_filter]

            # Filtrar por edad mínima
            df_filtered = df_filtered[df_filtered['Edad'] >= edad_min]
            
            st.session_state['evaluados_df'] = df_filtered
            st.rerun()


def get_historial_data(user_id: int = None) -> List[Dict]:
    """Attempt to fetch historial data from the DB using the LISTADO_EVALUADOS_SQL.
    If user_id is provided, tries to filter the query by e.id_usuario = @id_usuario.
    Falls back to client-side filtering if the query-based filtering fails.
    """
    try:
        if user_id is None:
            # prefer cached base listado when available
            df = load_listado_evaluados_base()
        else:
            # Try server-side filtering first by appending WHERE on the base SQL
            try:
                    base_sql = LISTADO_EVALUADOS_SQL.strip().rstrip(';')
                    # If query already contains a WHERE, append with AND
                    if ' where ' in base_sql.lower():
                        qry = base_sql + " AND e.id_usuario = @id_usuario"
                    else:
                        # If the base SQL contains an ORDER BY clause, insert the WHERE before ORDER BY
                        lower_base = base_sql.lower()
                        order_idx = lower_base.rfind('order by')
                        if order_idx != -1:
                            before_order = base_sql[:order_idx]
                            order_clause = base_sql[order_idx:]
                            qry = before_order + " WHERE e.id_usuario = @id_usuario " + order_clause
                        else:
                            qry = base_sql + " WHERE e.id_usuario = @id_usuario"
                    df = fetch_df(qry, {"id_usuario": int(user_id)})
            except Exception:
                df = fetch_df(LISTADO_EVALUADOS_SQL)
        if df is None:
            raise ValueError("No rows returned from DB")

        if user_id is not None:
            try:
                if 'id_usuario' in df.columns:
                    df = df[df['id_usuario'].astype('Int64') == int(user_id)]
                else:
                    try:
                        ids_df = fetch_df("SELECT id_evaluado FROM Evaluado WHERE id_usuario = @id_usuario", {"id_usuario": int(user_id)})
                        if ids_df is None or ids_df.empty:
                            df = df.iloc[0:0]
                        else:
                            ids = [int(x) for x in ids_df['id_evaluado'].tolist()]
                            if ids:
                                df = df[df['id_evaluado'].astype('Int64').isin(ids)]
                            else:
                                df = df.iloc[0:0]
                    except Exception:
                        # En caso de fallo, devolver vacío para no exponer todos los registros
                        df = df.iloc[0:0]
            except Exception:
                # En caso de cualquier error de filtrado, devolver vacío para seguridad
                df = df.iloc[0:0]

        if df is None or df.empty:
            raise ValueError("No rows returned from DB")

        if 'Ocupacion' in df.columns:
            df = df.rename(columns={'Ocupacion': 'Ocupación'})

        expected_cols = [
            'id_evaluado', 'Nombre', 'Apellido', 'Edad', 'Sexo', 'Estado civil',
            'Escolaridad', 'Ocupación', 'Grupo', 'id_usuario', 'Especialista'
        ]
        for c in expected_cols:
            if c not in df.columns:
                df[c] = ''

        records = df[expected_cols].fillna('').to_dict(orient='records')
        return records
    except Exception as e:
        st.error(f"Error fetching data from database: {e}")
        return []


def evaluados(can_delete: bool = True, user_id: int = None, owner_name: str = None):
    """Renderiza la vista de administración de evaluados.

    Parameters:
    - can_delete: si False, ocultará la opción de eliminar (útil para especialistas).
    - user_id: si provisto, mostrará sólo evaluados asignados a ese usuario.
    """
    
    # --- Reset filters/session state ---
    # Ensure filters and any evaluados-related session keys are cleared so the view
    # always starts fresh and shows all evaluados (avoid stale cache/state interference).
    try:
        if 'active_filters' in st.session_state:
            try:
                del st.session_state['active_filters']
            except Exception:
                pass
    except Exception:
        pass

    try:
        # Remove any keys created by previous evaluados instances (prefixed with 'evaluados_')
        for k in list(st.session_state.keys()):
            try:
                if isinstance(k, str) and k.startswith('evaluados_'):
                    try:
                        del st.session_state[k]
                    except Exception:
                        pass
            except Exception:
                continue
    except Exception:
        pass

    # Remove cached in-memory dataframe so we always reload current DB state
    try:
        if 'evaluados_df' in st.session_state:
            try:
                del st.session_state['evaluados_df']
            except Exception:
                pass
    except Exception:
        pass

    _css_evaluados = Path(__file__).parent.parent / 'assets' / 'evaluados.css'
    
    try:
        with open(_css_evaluados, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        
    except Exception as _e:
        st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
        """, unsafe_allow_html=True)
    # Preparar prefijo único para keys (evita colisiones cuando la vista se instancia varias veces)
    # Inicializar un contador en session_state solo la primera vez para que el prefijo sea estable
    counter_key = '_evaluados_instance_counter'
    if counter_key not in st.session_state:
        try:
            st.session_state[counter_key] = 1
        except Exception:
            # fallback silencioso
            pass

    instance_idx = st.session_state.get(counter_key, 1)
    key_prefix = f"evaluados_{str(user_id) if user_id is not None else 'global'}_{instance_idx}"

    # Cargar datos
    # Evitar recargar en cada rerun: solo hacerlo si no existe el cache o si cambió el user_id
    last_user_key = '_evaluados_last_user_id'
    need_refresh = False
    if 'evaluados_df' not in st.session_state:
        need_refresh = True
    else:
        if st.session_state.get(last_user_key) != user_id:
            need_refresh = True

    if need_refresh:
        st.session_state['evaluados_df'] = pd.DataFrame(get_historial_data(user_id=user_id))
        try:
            st.session_state[last_user_key] = user_id
        except Exception:
            pass
    
    # Verificar si hay evaluados
    if st.session_state['evaluados_df'].empty:
        col1, col2, col3 = st.columns([1, 5, 1])
        with col1:
            button_label = ":material/add: Crear"
            if st.button(button_label, use_container_width=True, type="primary"):
                dialog_crear_evaluado()
        
        st.info(":material/info: No hay evaluados registrados.")
        return
    
    # Preparar DataFrame
    df = st.session_state['evaluados_df'].copy()

    # Crear columna de selección
    df.insert(0, 'Seleccionar', False)

    # Reordenar columnas para display (sin id_evaluado visible) e incluir Especialista
    columns_order = ['Seleccionar', 'Nombre', 'Apellido', 'Edad', 'Sexo', 'Estado civil', 'Escolaridad', 'Ocupación', 'Grupo', 'Especialista']
    # Asegurar columna Especialista (proviene de la query que une con Usuario)
    if 'Especialista' not in df.columns and 'id_usuario' in df.columns:
        try:
            df_esp = load_especialistas()
            esp_map = dict(zip(df_esp['id_usuario'], df_esp['nombre_completo'])) if not df_esp.empty else {}
            df['Especialista'] = df['id_usuario'].apply(lambda x: esp_map.get(int(x), '') if pd.notna(x) and x != '' else '')
        except Exception:
            df['Especialista'] = ''

    df_display = df[[col for col in columns_order if col in df.columns]]
    
    # Barra de búsqueda y botones (prefijados para evitar colisiones de key)
    if can_delete:
        # Barra de búsqueda y botones (prefijados para evitar colisiones de key)
        col_buscar, col_filtros, col_editar, col_eliminar, col_crear = st.columns([3, 1, 1, 1, 1])

        buscar_key = f"{key_prefix}__buscar_evaluado_can_delete"
        filtros_key = f"{key_prefix}__evaluados_btn_filtros_top"
        editar_key = f"{key_prefix}__evaluados_btn_editar_top"
        eliminar_key = f"{key_prefix}__evaluados_btn_eliminar_top"
        crear_key = f"{key_prefix}__evaluados_btn_crear_top"

        with col_buscar:
            buscar = st.text_input(
                "Buscar evaluado",
                placeholder="Buscar...",
                label_visibility="collapsed",
                key=buscar_key
            )

        with col_filtros:
            button_label = ":material/filter_list: Filtros"
            filtros_btn = st.button(button_label, use_container_width=True, type="secondary", key=filtros_key)

        with col_editar:
            button_label = ":material/edit: Editar"
            editar_btn = st.button(button_label, use_container_width=True, type="secondary", key=editar_key)
        with col_eliminar:
            button_label = ":material/delete: Eliminar"
            eliminar_btn = st.button(button_label, use_container_width=True, type="secondary", key=eliminar_key)

        with col_crear:
            button_label = ":material/add: Crear"
            crear_btn = st.button(button_label, use_container_width=True, type="primary", key=crear_key)

        st.markdown("<br/>", unsafe_allow_html=True)
        # Aplicar búsqueda si hay texto
        if buscar:
            mask = df_display[['Nombre', 'Apellido', 'Sexo', 'Estado civil', 'Escolaridad', 'Ocupación', 'Grupo']].apply(
                lambda row: row.astype(str).str.contains(buscar, case=False).any(), axis=1
            )
            df_display = df_display[mask]
            df = df[mask]
    else:
        # Barra de búsqueda y botones (prefijados para evitar colisiones de key)
        col_buscar, col_filtros, col_editar, col_crear = st.columns([4, 1, 1, 1])

        buscar_key = f"{key_prefix}__buscar_evaluado"
        filtros_key = f"{key_prefix}__evaluados_btn_filtros_top_can_delete_false"
        editar_key = f"{key_prefix}__evaluados_btn_editar_top_can_delete_false"
        crear_key = f"{key_prefix}__evaluados_btn_crear_top_can_delete_false"

        with col_buscar:
            buscar = st.text_input(
                "Buscar evaluado",
                placeholder="Buscar...",
                label_visibility="collapsed",
                key=buscar_key
            )

        with col_filtros:
            button_label = ":material/filter_list: Filtros"
            filtros_btn = st.button(button_label, use_container_width=True, type="secondary", key=filtros_key)
        with col_editar:
            button_label = ":material/edit: Editar"
            editar_btn = st.button(button_label, use_container_width=True, type="secondary", key=editar_key)

        with col_crear:
            button_label = ":material/add: Crear"
            crear_btn = st.button(button_label, use_container_width=True, type="primary", key=crear_key)

        st.markdown("<br/>", unsafe_allow_html=True)
        # Aplicar búsqueda si hay texto
        if buscar:
            mask = df_display[['Nombre', 'Apellido', 'Sexo', 'Estado civil', 'Escolaridad', 'Ocupación', 'Grupo']].apply(
                lambda row: row.astype(str).str.contains(buscar, case=False).any(), axis=1
            )
            df_display = df_display[mask]
            df = df[mask]
    

    # ========== PAGINACIÓN ==========
    ROWS_PER_PAGE = 9
    page_key = f"{key_prefix}__page"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    total_rows = len(df_display)
    total_pages = max(1, (total_rows + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
    if st.session_state[page_key] > total_pages:
        st.session_state[page_key] = total_pages

    page = st.session_state[page_key]
    start_idx = (page - 1) * ROWS_PER_PAGE
    end_idx = start_idx + ROWS_PER_PAGE

    # Filtrar el DataFrame para la página actual (conservar índices originales)
    df_display_page = df_display.iloc[start_idx:end_idx].copy()

    # Mostrar tabla con checkboxes
    edited_df = st.data_editor(
        df_display_page,
        use_container_width=True,
        hide_index=True,
        key=f"{key_prefix}__evaluados_table_editor",
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn("", width="small"),
            "Nombre": st.column_config.TextColumn("Nombre", width="small"),
            "Apellido": st.column_config.TextColumn("Apellido", width="small"),
            "Edad": st.column_config.NumberColumn("Edad", width="small"),
            "Sexo": st.column_config.TextColumn("Sexo", width="small"),
            "Estado civil": st.column_config.TextColumn("Estado civil", width="small"),
            "Escolaridad": st.column_config.TextColumn("Escolaridad", width="small"),
            "Ocupación": st.column_config.TextColumn("Ocupación", width="small"),
            "Grupo": st.column_config.TextColumn("Grupo", width="small"),
            "Especialista": st.column_config.TextColumn("Especialista", width="small"),
        },
            height=250,
        disabled=['Nombre', 'Apellido', 'Edad', 'Sexo', 'Estado civil', 'Escolaridad', 'Ocupación', 'Grupo', 'Especialista']
    )
    
    st.caption(f"**Total de evaluados:** {len(df)} | **Mostrando:** {start_idx + 1}-{min(end_idx, total_rows)}")

    # --- PAGINACIÓN (debajo de la tabla) ---
    if total_pages > 1:
        col_prev, col_center, col_next = st.columns([1, 2, 1])

        with col_prev:
            if st.button(":material/arrow_back: Anterior", disabled=(st.session_state[page_key] == 1), key=f"{key_prefix}__btn_prev_page", type="tertiary", use_container_width=True):
                st.session_state[page_key] -= 1
                st.rerun()

        with col_center:
            st.markdown(
                f"<div style='text-align: center; padding-top: 6px;'><strong>Página {st.session_state[page_key]} de {total_pages}</strong></div>",
                unsafe_allow_html=True
            )

        with col_next:
            if st.button("Siguiente :material/arrow_forward:", disabled=(st.session_state[page_key] == total_pages), key=f"{key_prefix}__btn_next_page", type="tertiary", use_container_width=True):
                st.session_state[page_key] += 1
                st.rerun()

        st.markdown("<br/>", unsafe_allow_html=True)
    
    # Obtener evaluados seleccionados
    seleccionados = edited_df[edited_df['Seleccionar'] == True]
    
    # Manejar acciones de los botones
    if crear_btn:
        dialog_crear_evaluado()
    
    if filtros_btn:
        dialog_filtros(key_prefix)
    
    if editar_btn:
        if len(seleccionados) == 0:
            st.markdown("""
                <div class="warning">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                </svg>
                <span>:material/warning: Selecciona un evaluado para editar</span>
                </div>
            """, unsafe_allow_html=True)
        elif len(seleccionados) > 1:
            st.markdown("""
                <div class="warning">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                </svg>
                <span>:material/warning: Selecciona solo un evaluado para editar</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            idx = seleccionados.index[0]
            evaluado_completo = df.loc[idx].to_dict()
            dialog_editar_evaluado(evaluado_completo)
    
    if can_delete and eliminar_btn:
        if len(seleccionados) == 0:
            st.markdown("""
                <div class="warning">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12
                        9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                </svg>
                <span>:material/warning: Selecciona al menos un evaluado para eliminar</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            indices = seleccionados.index
            evaluados_completos = df.loc[indices]
            confirmar_eliminacion_historial(evaluados_completos)
    
    # BOTÓN VER EXPEDIENTE (restaurado)
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        ver_key = f"{key_prefix}__ver_expediente_btn"
        ver_expediente_btn = st.button("Ver expediente", type="primary", use_container_width=True, key=ver_key)

        if ver_expediente_btn:
            if len(seleccionados) != 1:
                st.markdown("""
                <div class="warning">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                </svg>
                <span>Selecciona un solo evaluado para ver el expediente</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                try:
                    idx = seleccionados.index[0]
                    selected_data = df.loc[idx]
                    st.session_state["selected_evaluation_id"] = selected_data['id_evaluado']
                    # marcar si venimos desde la vista 'ajustes' para que el botón de regresar funcione correctamente
                    st.session_state['from_ajustes'] = True if st.session_state.get('active_view') == 'ajustes' else False
                    st.session_state["active_view"] = "individual"
                    st.rerun()
                except Exception as e:
                    st.error(f":material/error: Error: {e}")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)