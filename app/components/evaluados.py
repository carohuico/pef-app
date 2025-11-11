import streamlit as st
import pandas as pd
from typing import List, Dict
from pathlib import Path
from services.exportar import render_export_popover
from services.db import fetch_df, get_engine
from services.queries.q_evaluados import LISTADO_EVALUADOS_SQL, ELIMINAR_EVALUADOS
from services.queries.q_registro import GET_GRUPOS, CREAR_EVALUADO
from sqlalchemy import text
import datetime


@st.dialog(":material/warning: Confirmar Eliminación")
def confirmar_eliminacion_historial(selected_rows_df):
    """Dialogo para confirmar eliminación de registros en historial."""
    try:
        n = len(selected_rows_df)
    except Exception:
        n = 0

    if n == 1:
        try:
            nombre = selected_rows_df.iloc[0].get('Nombre', '')
            apellido = selected_rows_df.iloc[0].get('Apellido', '')
            st.warning(f"¿Estás seguro de que deseas eliminar al evaluado **{nombre} {apellido}**?")
        except Exception:
            st.warning("¿Estás seguro de que deseas eliminar este evaluado?")
    else:
        st.warning(f"¿Estás seguro de que deseas eliminar **{n} evaluado(s)**?")

    st.write("Esta acción no se puede deshacer.")

    col_yes, col_no = st.columns(2)
    with col_yes:
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
                    st.warning('No se pudieron resolver los ids seleccionados.')
                else:
                    ids_csv = ','.join(str(x) for x in ids)
                    try:
                        with get_engine().begin() as conn:
                            res = conn.execute(text(ELIMINAR_EVALUADOS), {"ids_csv": ids_csv})
                            try:
                                deleted_rows = res.fetchall()
                                rows_deleted = len(deleted_rows)
                            except Exception:
                                rows_deleted = res.rowcount if hasattr(res, 'rowcount') and res.rowcount is not None else 0
                        st.success(f"Se eliminaron {rows_deleted} evaluado(s).")
                        st.session_state['evaluados_df'] = pd.DataFrame(get_historial_data())
                        st.session_state['historial_selection'] = {'rows': []}
                    except Exception as e:
                        st.error(f"Error al eliminar evaluados: {e}")
            except Exception as e:
                st.error(f":material/error: Error al procesar eliminación: {e}")
            st.rerun()

    with col_no:
        label = ":material/cancel: Cancelar"
        if st.button(label, use_container_width=True, key="hist_cancelar_eliminar"):
            st.rerun()


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
                df_groups = fetch_df(GET_GRUPOS)
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
            cancelar = st.form_submit_button(":material/cancel: Cancelar", use_container_width=True)
        
        with col2:
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
            
            # Crear evaluado en la base de datos
            try:
                engine = get_engine()
                
                # Resolver id_grupo
                id_grupo = None
                if grupo not in ("Selecciona un grupo", "Sin grupo", ""):
                    try:
                        with engine.begin() as conn:
                            res_g = conn.execute(text("SELECT TOP 1 id_grupo FROM Grupo WHERE nombre = :grupo"), {"grupo": grupo})
                            row_g = res_g.fetchone()
                            if row_g is not None:
                                id_grupo = row_g[0]
                    except Exception:
                        pass
                
                # Preparar valores
                estado_civil_val = None if estado_civil == "Selecciona una opción" else estado_civil
                escolaridad_val = None if escolaridad == "Selecciona una opción" else escolaridad
                ocupacion_val = None if ocupacion == "Selecciona una opción" else ocupacion
                
                params = {
                    "nombre": nombre.strip(),
                    "apellido": apellido.strip() if apellido else "",
                    "fecha_nacimiento": fecha_nacimiento,
                    "sexo": sexo,
                    "estado_civil": estado_civil_val,
                    "escolaridad": escolaridad_val,
                    "ocupacion": ocupacion_val,
                    "id_grupo": id_grupo
                }
                
                with engine.begin() as conn:
                    res = conn.execute(text(CREAR_EVALUADO), params)
                    row = res.fetchone()
                    if row is not None:
                        try:
                            id_evaluado = int(row['id_evaluado'])
                        except Exception:
                            id_evaluado = int(row[0])
                
                st.success(f":material/check: Evaluado '{nombre}' creado exitosamente")
                del st.session_state['evaluados_df']
                import time
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f":material/error: Error al crear evaluado: {e}")


@st.dialog(":material/edit: Editar Evaluado")
def dialog_editar_evaluado(evaluado_data):
    """Diálogo para editar información de un evaluado existente."""
    # Hacer el diálogo más ancho para edición (mantener diseño de 2 columnas)
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
                df_groups = fetch_df(GET_GRUPOS)
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
        
        # Botones de acción
        col1, col2 = st.columns(2)
        with col1:
            cancelar = st.form_submit_button(":material/cancel: Cancelar", use_container_width=True)
        
        with col2:
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
            
            # Actualizar en la base de datos
            try:
                engine = get_engine()
                id_evaluado = evaluado_data.get('id_evaluado')
                
                # Resolver id_grupo
                id_grupo = None
                if grupo not in ("Selecciona un grupo", "Sin grupo", ""):
                    try:
                        with engine.begin() as conn:
                            res_g = conn.execute(text("SELECT TOP 1 id_grupo FROM Grupo WHERE nombre = :grupo"), {"grupo": grupo})
                            row_g = res_g.fetchone()
                            if row_g is not None:
                                id_grupo = row_g[0]
                    except Exception:
                        pass
                
                # Preparar valores para actualización
                estado_civil_val = None if estado_civil == "Selecciona una opción" else estado_civil
                escolaridad_val = None if escolaridad == "Selecciona una opción" else escolaridad
                ocupacion_val = None if ocupacion == "Selecciona una opción" else ocupacion
                
                update_query = """
                UPDATE dbo.Evaluado
                SET nombre = :nombre,
                    apellido = :apellido,
                    fecha_nacimiento = :fecha_nacimiento,
                    sexo = :sexo,
                    estado_civil = :estado_civil,
                    escolaridad = :escolaridad,
                    ocupacion = :ocupacion,
                    id_grupo = :id_grupo
                WHERE id_evaluado = :id_evaluado
                """
                
                with engine.begin() as conn:
                    conn.execute(
                        text(update_query),
                        {
                            "id_evaluado": id_evaluado,
                            "nombre": nombre.strip(),
                            "apellido": apellido.strip(),
                            "fecha_nacimiento": fecha_nacimiento,
                            "sexo": sexo,
                            "estado_civil": estado_civil_val,
                            "escolaridad": escolaridad_val,
                            "ocupacion": ocupacion_val,
                            "id_grupo": id_grupo
                        }
                    )
                
                st.success(f":material/check: Evaluado '{nombre}' actualizado correctamente")
                del st.session_state['evaluados_df']
                import time
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f":material/error: Error al actualizar evaluado: {e}")


@st.dialog(":material/filter_list: Filtros")
def dialog_filtros():
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
        key="filter_sexo"
    )
    
    # Filtro por Estado civil
    estado_options = ["Todos"] + sorted(df_original['Estado civil'].dropna().unique().tolist())
    estado_filter = st.selectbox(
        "Estado civil",
        estado_options,
        index=estado_options.index(st.session_state['active_filters'].get('Estado civil', 'Todos')) if st.session_state['active_filters'].get('Estado civil', 'Todos') in estado_options else 0,
        key="filter_estado"
    )
    
    # Filtro por Escolaridad
    escolaridad_options = ["Todos"] + sorted(df_original['Escolaridad'].dropna().unique().tolist())
    escolaridad_filter = st.selectbox(
        "Escolaridad",
        escolaridad_options,
        index=escolaridad_options.index(st.session_state['active_filters'].get('Escolaridad', 'Todos')) if st.session_state['active_filters'].get('Escolaridad', 'Todos') in escolaridad_options else 0,
        key="filter_escolaridad"
    )
    
    # Filtro por Ocupación
    ocupacion_options = ["Todos"] + sorted(df_original['Ocupación'].dropna().unique().tolist())
    ocupacion_filter = st.selectbox(
        "Ocupación",
        ocupacion_options,
        index=ocupacion_options.index(st.session_state['active_filters'].get('Ocupación', 'Todos')) if st.session_state['active_filters'].get('Ocupación', 'Todos') in ocupacion_options else 0,
        key="filter_ocupacion"
    )
    
    # Filtro por Grupo
    grupo_options = ["Todos"] + sorted(df_original['Grupo'].dropna().unique().tolist())
    grupo_filter = st.selectbox(
        "Grupo",
        grupo_options,
        index=grupo_options.index(st.session_state['active_filters'].get('Grupo', 'Todos')) if st.session_state['active_filters'].get('Grupo', 'Todos') in grupo_options else 0,
        key="filter_grupo"
    )
    
    # Filtro por edad mínima
    edad_min = st.number_input(
        "Edad mínima",
        min_value=18,
        max_value=100,
        value=st.session_state['active_filters'].get('edad_min', 18),
        key="filter_edad_min"
    )
    
    # Botones de acción
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(":material/refresh: Limpiar", use_container_width=True, key="clear_filters"):
            st.session_state['active_filters'] = {}
            del st.session_state['evaluados_df']
            st.rerun()
    
    with col2:
        if st.button(":material/cancel: Cancelar", use_container_width=True, key="cancel_filters"):
            st.rerun()
    
    with col3:
        if st.button(":material/check: Aplicar", use_container_width=True, type="primary", key="apply_filters"):
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


def get_historial_data() -> List[Dict]:
    """Attempt to fetch historial data from the DB using the LISTADO_EVALUADOS_SQL."""
    try:
        df = fetch_df(LISTADO_EVALUADOS_SQL)
        if df is None or df.empty:
            raise ValueError("No rows returned from DB")

        if 'Ocupacion' in df.columns:
            df = df.rename(columns={'Ocupacion': 'Ocupación'})

        expected_cols = [
            'id_evaluado', 'Nombre', 'Apellido', 'Edad', 'Sexo', 'Estado civil',
            'Escolaridad', 'Ocupación', 'Grupo'
        ]
        for c in expected_cols:
            if c not in df.columns:
                df[c] = ''

        records = df[expected_cols].fillna('').to_dict(orient='records')
        return records
    except Exception as e:
        st.error(f"Error fetching data from database: {e}")
        return []


def evaluados():
    """Renderiza la vista de administración de evaluados"""
    # Cargar datos
    if 'evaluados_df' not in st.session_state:
        st.session_state['evaluados_df'] = pd.DataFrame(get_historial_data())
    
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
    
    # Reordenar columnas para display (sin id_evaluado visible)
    columns_order = ['Seleccionar', 'Nombre', 'Apellido', 'Edad', 'Sexo', 'Estado civil', 'Escolaridad', 'Ocupación', 'Grupo']
    df_display = df[[col for col in columns_order if col in df.columns]]
    
    # Barra de búsqueda y botones
    col_buscar, col_filtros, col_editar, col_eliminar, col_crear = st.columns([3, 1, 1, 1, 1])
    
    with col_buscar:
        buscar = st.text_input(
            "Buscar evaluado",
            placeholder="Buscar...",
            label_visibility="collapsed",
            key="buscar_evaluado"
        )
    
    with col_filtros:
        button_label = ":material/filter_list: Filtros"
        filtros_btn = st.button(button_label, use_container_width=True, type="secondary", key="evaluados_btn_filtros_top")
    
    with col_editar:
        button_label = ":material/edit: Editar"
        editar_btn = st.button(button_label, use_container_width=True, type="secondary", key="evaluados_btn_editar_top")
    
    with col_eliminar:
        button_label = ":material/delete: Eliminar"
        eliminar_btn = st.button(button_label, use_container_width=True, type="secondary", key="evaluados_btn_eliminar_top")
    
    with col_crear:
        button_label = ":material/add: Crear"
        crear_btn = st.button(button_label, use_container_width=True, type="primary", key="evaluados_btn_crear_top")
    
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Aplicar búsqueda si hay texto
    if buscar:
        mask = df_display[['Nombre', 'Apellido', 'Sexo', 'Estado civil', 'Escolaridad', 'Ocupación', 'Grupo']].apply(
            lambda row: row.astype(str).str.contains(buscar, case=False).any(), axis=1
        )
        df_display = df_display[mask]
        df = df[mask]
    
    # Mostrar tabla con checkboxes
    edited_df = st.data_editor(
        df_display,
        use_container_width=True,
        hide_index=True,
        key="evaluados_table_editor",
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
        },
        disabled=['Nombre', 'Apellido', 'Edad', 'Sexo', 'Estado civil', 'Escolaridad', 'Ocupación', 'Grupo']
    )
    
    # Total de evaluados debajo de la tabla
    st.caption(f"**Total de evaluados:** {len(df)}")
    
    # Obtener evaluados seleccionados
    seleccionados = edited_df[edited_df['Seleccionar'] == True]
    
    # Manejar acciones de los botones
    if crear_btn:
        dialog_crear_evaluado()
    
    if filtros_btn:
        dialog_filtros()
    
    if editar_btn:
        if len(seleccionados) == 0:
            st.warning(":material/warning: Selecciona un evaluado para editar")
        elif len(seleccionados) > 1:
            st.warning(":material/warning: Selecciona solo un evaluado para editar")
        else:
            idx = seleccionados.index[0]
            evaluado_completo = df.loc[idx].to_dict()
            dialog_editar_evaluado(evaluado_completo)
    
    if eliminar_btn:
        if len(seleccionados) == 0:
            st.warning(":material/warning: Selecciona al menos un evaluado para eliminar")
        else:
            indices = seleccionados.index
            evaluados_completos = df.loc[indices]
            confirmar_eliminacion_historial(evaluados_completos)
    
    # BOTÓN VER EXPEDIENTE (restaurado)
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        ver_expediente_btn = st.button("Ver expediente", type="primary", use_container_width=True, key="ver_expediente_btn")
        
        if ver_expediente_btn:
            if len(seleccionados) != 1:
                st.warning(":material/warning: Selecciona un solo evaluado para ver el expediente")
            else:
                try:
                    idx = seleccionados.index[0]
                    selected_data = df.loc[idx]
                    st.session_state["selected_evaluation_id"] = selected_data['id_evaluado']
                    st.session_state["active_view"] = "individual"
                    st.rerun()
                except Exception as e:
                    st.error(f":material/error: Error: {e}")