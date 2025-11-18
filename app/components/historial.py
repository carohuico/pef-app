import streamlit as st
import pandas as pd
from typing import List, Dict
from pathlib import Path
from services.db import fetch_df, get_engine
from services.queries.q_individual import GET_RESULTADOS_POR_PRUEBA
from services.exportar import render_export_popover
from services.queries.q_historial import LISTADO_HISTORIAL_SQL, ELIMINAR_PRUEBAS
from services.queries.q_registro import GET_GRUPOS
from sqlalchemy import text
import datetime


@st.dialog(":material/warning: Confirmar Eliminación")
def confirmar_eliminacion_pruebas(selected_rows_df):
    """Dialogo para confirmar eliminación de pruebas/evaluaciones."""
    try:
        n = len(selected_rows_df)
    except Exception:
        n = 0

    if n == 1:
        try:
            nombre = selected_rows_df.iloc[0].get('Nombre del evaluado', '')
            fecha = selected_rows_df.iloc[0].get('Fecha de evaluación', '')
            st.warning(f"¿Estás seguro de que deseas eliminar la evaluación de **{nombre}** del **{fecha}**?")
        except Exception:
            st.warning("¿Estás seguro de que deseas eliminar esta evaluación?")
    else:
        st.warning(f"¿Estás seguro de que deseas eliminar **{n} evaluación(es)**?")

    st.write("Esta acción no se puede deshacer.")

    col_yes, col_no = st.columns(2)
    with col_yes:
        label = ":material/check: Sí, eliminar"
        if st.button(label, use_container_width=True, type="primary", key="hist_confirmar_eliminar"):
            try:
                ids = []
                orig_df = st.session_state.get('historial_df', pd.DataFrame())
                for idx in selected_rows_df.index.tolist():
                    id_val = None
                    if 'id_prueba' in selected_rows_df.columns:
                        try:
                            id_val = selected_rows_df.loc[idx].get('id_prueba', None)
                        except Exception:
                            id_val = None

                    if (id_val is None or (isinstance(id_val, float) and pd.isna(id_val))) and not orig_df.empty:
                        try:
                            row = orig_df.loc[idx]
                            id_val = row.get('id_prueba', None)
                        except Exception:
                            id_val = None

                    try:
                        if id_val is not None and not (isinstance(id_val, float) and pd.isna(id_val)):
                            ids.append(int(id_val))
                    except Exception:
                        # ignore non-int ids
                        continue

                if not ids:
                    st.warning('No se pudieron resolver los ids seleccionados.')
                else:
                    ids_csv = ','.join(str(x) for x in ids)
                    try:
                        with get_engine().begin() as conn:
                            res = conn.execute(text(ELIMINAR_PRUEBAS), {"ids_csv": ids_csv})
                            try:
                                deleted_rows = res.fetchall()
                                rows_deleted = len(deleted_rows)
                            except Exception:
                                rows_deleted = res.rowcount if hasattr(res, 'rowcount') and res.rowcount is not None else 0
                        # Eliminar solo si existe para evitar KeyError transitorio
                        if 'historial_df' in st.session_state:
                            try:
                                del st.session_state['historial_df']
                            except Exception:
                                # Protección extra: si falla la eliminación, simplemente continuar
                                pass
                    except Exception as e:
                        st.error(f"Error al eliminar evaluaciones: {e}")
            except Exception as e:
                st.error(f":material/error: Error al procesar eliminación: {e}")
            st.rerun()

    with col_no:
        label = ":material/cancel: Cancelar"
        if st.button(label, use_container_width=True, key="hist_cancelar_eliminar"):
            st.rerun()


@st.dialog(":material/filter_list: Filtros")
def dialog_filtros():
    """Diálogo para filtrar datos por columnas."""
        
    # Obtener datos originales
    original_data = get_historial_data()
    df_original = pd.DataFrame(original_data)
    
    # Inicializar filtros en session_state si no existen
    if 'active_historial_filters' not in st.session_state:
        st.session_state['active_historial_filters'] = {}
    
    # Filtro por Evaluado (nombre completo)
    evaluado_options = ["Todos"] + sorted(df_original['Nombre del evaluado'].dropna().unique().tolist())
    evaluado_filter = st.selectbox(
        "Evaluado",
        evaluado_options,
        index=evaluado_options.index(st.session_state['active_historial_filters'].get('Evaluado', 'Todos')) if st.session_state['active_historial_filters'].get('Evaluado', 'Todos') in evaluado_options else 0,
        key="filter_evaluado"
    )
    
    # Filtro por Sexo
    sexo_options = ["Todos"] + sorted(df_original['Sexo'].dropna().unique().tolist())
    sexo_filter = st.selectbox(
        "Sexo",
        sexo_options,
        index=sexo_options.index(st.session_state['active_historial_filters'].get('Sexo', 'Todos')) if st.session_state['active_historial_filters'].get('Sexo', 'Todos') in sexo_options else 0,
        key="filter_sexo"
    )
    
    # Filtro por Grupo
    grupo_options = ["Todos"] + sorted(df_original['Grupo'].dropna().unique().tolist())
    grupo_filter = st.selectbox(
        "Grupo",
        grupo_options,
        index=grupo_options.index(st.session_state['active_historial_filters'].get('Grupo', 'Todos')) if st.session_state['active_historial_filters'].get('Grupo', 'Todos') in grupo_options else 0,
        key="filter_grupo"
    )
    
    # Filtro por edad mínima
    edad_min = st.number_input(
        "Edad mínima",
        min_value=18,
        max_value=100,
        value=st.session_state['active_historial_filters'].get('edad_min', 18),
        key="filter_edad_min"
    )
    
    # Filtro por rango de fechas
    col1, col2 = st.columns(2)
    with col1:
        fecha_desde = st.date_input(
            "Fecha desde",
            value=st.session_state['active_historial_filters'].get('fecha_desde', None),
            key="filter_fecha_desde"
        )
    with col2:
        # si el usuario ya seleccionó fecha_desde, evitar que fecha_hasta pueda ser anterior
        min_hasta = None
        try:
            if fecha_desde is not None:
                min_hasta = fecha_desde
        except Exception:
            min_hasta = None

        fecha_hasta = st.date_input(
            "Fecha hasta",
            value=st.session_state['active_historial_filters'].get('fecha_hasta', None),
            key="filter_fecha_hasta",
            min_value=min_hasta
        )
    
    if st.session_state.get('historial_filters_invalid_date'):
        st.markdown("<br/>", unsafe_allow_html=True)
        st.error(":material/warning: La 'Fecha hasta' no puede ser anterior a la 'Fecha desde'.")
    elif st.session_state.get('historial_filters_no_results'):
        st.markdown("<br/>", unsafe_allow_html=True)
        st.warning(":material/info: No hay evaluaciones registradas que cumplan estos criterios")

    # Botones de acción
    col1, col3 = st.columns(2)
    with col1:
        st.markdown("<br><br/>", unsafe_allow_html=True)
        if st.button(":material/refresh: Limpiar", use_container_width=True, key="clear_filters"):
            st.session_state['active_historial_filters'] = {}
            if 'historial_df' in st.session_state:
                del st.session_state['historial_df']
            for k in ('historial_filters_no_results', 'historial_filters_invalid_date'):
                if k in st.session_state:
                    try:
                        del st.session_state[k]
                    except Exception:
                        pass
            st.rerun()
    
    with col3:
        st.markdown("<br><br/>", unsafe_allow_html=True)  
        if st.button(":material/check: Aplicar", use_container_width=True, type="primary", key="apply_filters"):
            filters = {}
            if evaluado_filter != "Todos":
                filters['Evaluado'] = evaluado_filter
            if sexo_filter != "Todos":
                filters['Sexo'] = sexo_filter
            if grupo_filter != "Todos":
                filters['Grupo'] = grupo_filter
            filters['edad_min'] = edad_min
            if fecha_desde:
                filters['fecha_desde'] = fecha_desde
            if fecha_hasta:
                filters['fecha_hasta'] = fecha_hasta

            st.session_state['active_historial_filters'] = filters

            # Validación: 'fecha_hasta' no puede ser anterior a 'fecha_desde'
            try:
                if fecha_desde is not None and fecha_hasta is not None and fecha_hasta < fecha_desde:
                    st.session_state['historial_filters_invalid_date'] = True
                    # detener ejecución para mantener el diálogo abierto y mostrar el error
                    st.stop()
                else:
                    if 'historial_filters_invalid_date' in st.session_state:
                        try:
                            del st.session_state['historial_filters_invalid_date']
                        except Exception:
                            pass
            except Exception:
                pass

            # Aplicar filtros
            df_filtered = df_original.copy()

            if evaluado_filter != "Todos":
                df_filtered = df_filtered[df_filtered['Nombre del evaluado'] == evaluado_filter]

            if sexo_filter != "Todos":
                df_filtered = df_filtered[df_filtered['Sexo'] == sexo_filter]

            if grupo_filter != "Todos":
                df_filtered = df_filtered[df_filtered['Grupo'] == grupo_filter]

            df_filtered = df_filtered[df_filtered['Edad'] >= edad_min]

            if fecha_desde:
                df_filtered = df_filtered[pd.to_datetime(df_filtered['Fecha de evaluación']) >= pd.to_datetime(fecha_desde)]

            if fecha_hasta:
                df_filtered = df_filtered[pd.to_datetime(df_filtered['Fecha de evaluación']) <= pd.to_datetime(fecha_hasta)]

            if df_filtered is None or df_filtered.empty:
                st.session_state['historial_filters_no_results'] = True
            else:
                st.session_state['historial_df'] = df_filtered
                if 'historial_filters_no_results' in st.session_state:
                    try:
                        del st.session_state['historial_filters_no_results']
                    except Exception:
                        pass
                st.rerun()


def get_historial_data() -> List[Dict]:
    """Obtiene el historial de pruebas/evaluaciones desde la BD."""
    try:
        try:
            import services.auth as auth
            if auth.is_especialista():
                user = st.session_state.get("user", {})
                id_usuario = user.get("id_usuario")
                base_sql = LISTADO_HISTORIAL_SQL
                if not id_usuario:
                    return []
                try:
                    id_usuario = int(id_usuario)
                except Exception:
                    return []
                if "ORDER BY" in base_sql.upper():
                    idx = base_sql.upper().rfind("ORDER BY")
                    filtered_sql = base_sql[:idx] + "\nWHERE e.id_usuario = :id_usuario\n" + base_sql[idx:]
                else:
                    filtered_sql = base_sql + "\nWHERE e.id_usuario = :id_usuario"
                df = fetch_df(filtered_sql, {"id_usuario": id_usuario})
            else:
                df = fetch_df(LISTADO_HISTORIAL_SQL)
        except Exception:
            print("Error checking user role, loading full historial as fallback.")
        if df is None or df.empty:
            raise ValueError("No rows returned from DB")

        expected_cols = [
            'id_prueba', 'id_evaluado', 'ruta_imagen', 'Nombre del evaluado', 
            'Edad', 'Sexo', 'Grupo', 'Fecha de evaluación'
        ]
        for c in expected_cols:
            if c not in df.columns:
                df[c] = ''

        records = df[expected_cols].fillna('').to_dict(orient='records')
        return records
    except Exception as e:
        st.error(f"Error fetching data from database: {e}")
        return []


def historial():
    """Renderiza la vista de historial de evaluaciones/pruebas"""
    # ---------- CONFIGURACIÓN ----------
    st.set_page_config(page_title="Rainly - Historial", layout="wide", initial_sidebar_state="auto")
    
    # ---------- CSS (externo) ----------
    _css_grupos = Path(__file__).parent.parent / 'assets' / 'grupos.css'  
    _css_historial = Path(__file__).parent.parent / 'assets' / 'historial.css'      
    
    try:
        with open(_css_grupos, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        with open(_css_historial, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        
    except Exception as _e:
        st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="page-header">Historial de evaluaciones</div>', unsafe_allow_html=True)
    
    # Cargar datos
    if 'historial_df' not in st.session_state:
        st.session_state['historial_df'] = pd.DataFrame(get_historial_data())
    
    # Verificar si hay evaluaciones
    if st.session_state['historial_df'].empty:
        st.info(":material/info: No hay evaluaciones registradas.")
        return
    
    # Preparar DataFrame
    df = st.session_state['historial_df'].copy()
    
    # Crear columna de selección
    df.insert(0, 'Seleccionar', False)
    
    columns_order = ['Seleccionar','id_prueba', 'Nombre del evaluado', 'Edad', 'Sexo', 'Grupo', 'Fecha de evaluación']
    df_display = df[[col for col in columns_order if col in df.columns]]
    
    col_buscar, col_filtros, col_exportar, col_eliminar, col_vermas = st.columns([3, 1, 1, 1, 1])
    
    with col_buscar:
        buscar = st.text_input(
            "Buscar evaluación",
            placeholder="Buscar...",
            label_visibility="collapsed",
            key="buscar_historial"
        )
    
    with col_filtros:
        button_label = ":material/filter_list: Filtros"
        filtros_btn = st.button(button_label, use_container_width=True, type="secondary", key="historial_btn_filtros_top")
    
    with col_exportar:
        button_label = ":material/file_download: Exportar"
        exportar_btn = st.button(button_label, use_container_width=True, type="secondary", key="historial_btn_exportar_top")
        pass
    
    with col_eliminar:
        button_label = ":material/delete: Eliminar"
        eliminar_btn = st.button(button_label, use_container_width=True, type="secondary", key="historial_btn_eliminar_top")

    with col_vermas:
        # Botón "Ver más" junto a Exportar
        ver_mas_btn = st.button("Ver resultados", type="primary", use_container_width=True, key="historial_btn_vermas_top")
    
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Aplicar búsqueda si hay texto
    if buscar:
        mask = df_display[['Nombre del evaluado', 'Sexo', 'Grupo']].apply(
            lambda row: row.astype(str).str.contains(buscar, case=False).any(), axis=1
        )
        df_display = df_display[mask]
        df = df[mask]
    
    # Mostrar tabla con checkboxes
    edited_df = st.data_editor(
        df_display,
        use_container_width=True,
        hide_index=True,
        key="historial_table_editor",
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn("", width="small"),
            "Nombre del evaluado": st.column_config.TextColumn("Nombre del evaluado", width="medium"),
            "Edad": st.column_config.NumberColumn("Edad", width="small"),
            "Sexo": st.column_config.TextColumn("Sexo", width="small"),
            "Grupo": st.column_config.TextColumn("Grupo", width="small"),
            "Fecha de evaluación": st.column_config.TextColumn("Fecha de evaluación", width="small"),
            "id_prueba": st.column_config.TextColumn("id_prueba", width="small"),
        },
        disabled=['Nombre del evaluado', 'Edad', 'Sexo', 'Grupo', 'Fecha de evaluación', 'id_prueba']
    )
    
    # Total de evaluaciones debajo de la tabla
    st.caption(f"**Total de evaluaciones:** {len(df)}")
    
    # Obtener evaluaciones seleccionadas
    seleccionados = edited_df[edited_df['Seleccionar'] == True]
    
    # Manejar acciones de los botones
    if filtros_btn:
        dialog_filtros()

    if exportar_btn:
        if len(seleccionados) == 0:
            st.warning(":material/warning: Selecciona al menos una evaluación para exportar")
        else:
            try:
                # Construir lista de diccionarios con la info básica de cada evaluado seleccionado
                info_list = []
                for idx in seleccionados.index.tolist():
                    try:
                        row = df.loc[idx]
                    except Exception:
                        continue

                    info = {
                        "Fecha de evaluación": row.get('Fecha de evaluación', ''),
                        "Fecha": row.get('Fecha de evaluación', ''),
                        "Nombre": row.get('Nombre del evaluado', ''),
                        "Nombre del evaluado": row.get('Nombre del evaluado', ''),
                        "Edad": row.get('Edad', ''),
                        "Sexo": row.get('Sexo', ''),
                        "Grupo": row.get('Grupo', ''),
                        "ruta_imagen": row.get('ruta_imagen', ''),  
                    }
                    info_list.append(info)

                if not info_list:
                    st.warning(":material/warning: No se pudo resolver la información de las evaluaciones seleccionadas.")
                else:
                    # Construir lista de indicadores por fila consultando los resultados asociados a cada id_prueba (si está disponible)
                    indicadores_por_fila = []
                    for idx in seleccionados.index.tolist():
                        try:
                            row = df.loc[idx]
                        except Exception:
                            indicadores_por_fila.append([])
                            continue

                        id_prueba = row.get('id_prueba', None)
                        if id_prueba is None or pd.isna(id_prueba):
                            # No hay prueba asociada -> no indicadores
                            indicadores_por_fila.append([])
                            continue

                        try:
                            df_res = fetch_df(GET_RESULTADOS_POR_PRUEBA, {"id_prueba": int(id_prueba)})
                            if df_res is None or df_res.empty:
                                indicadores_por_fila.append([])
                            else:
                                lista_inds = []
                                for _i, r in df_res.iterrows():
                                    lista_inds.append({
                                        "nombre": r.get('nombre_indicador') if 'nombre_indicador' in r else r.get('nombre') if 'nombre' in r else None,
                                        "significado": r.get('significado') if 'significado' in r else None,
                                        "confianza": r.get('confianza') if 'confianza' in r else None,
                                        "id_indicador": r.get('id_indicador') if 'id_indicador' in r else None,
                                    })
                                indicadores_por_fila.append(lista_inds)
                        except Exception:
                            indicadores_por_fila.append([])

                    # Si no se encontraron indicadores por fila, como fallback usar indicadores en sesión o lista vacía
                    use_indicadores = indicadores_por_fila if any(len(x) for x in indicadores_por_fila) else st.session_state.get("indicadores", [])
                    render_export_popover(info_list, use_indicadores)
            except Exception as e:
                st.error(f":material/error: Error al preparar exportación: {e}")

    if eliminar_btn:
        if len(seleccionados) == 0:
            st.warning(":material/warning: Selecciona al menos una evaluación para eliminar")
        else:
            confirmar_eliminacion_pruebas(seleccionados)            

    if ver_mas_btn:
        if len(seleccionados) != 1:
            st.warning(":material/warning: Selecciona una sola evaluación para ver los resultados")
        else:
            try:
                idx = seleccionados.index[0]
                selected_data = df.loc[idx]
                st.session_state["open_prueba_id"] = selected_data['id_prueba']
                st.session_state["selected_evaluation_id"] = selected_data['id_evaluado']
                # Indicar que venimos desde historial (no desde ajustes)
                st.session_state['from_ajustes'] = False
                st.session_state["active_view"] = "individual"
                st.rerun()
            except Exception as e:
                st.error(f":material/error: Error: {e}")
    
