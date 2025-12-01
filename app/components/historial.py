import streamlit as st
import pandas as pd
from typing import List, Dict
from pathlib import Path
from services.db import fetch_df
from services.queries.q_individual import GET_RESULTADOS_POR_PRUEBA
from services.exportar import render_export_popover
from services.queries.q_historial import LISTADO_HISTORIAL_SQL, LISTADO_HISTORIAL_POR_ESPECIALISTA
from components.loader import show_loader


# Cached loaders for historial
@st.cache_data(ttl=300, max_entries=64)
def load_historial_base():
    return fetch_df(LISTADO_HISTORIAL_SQL)


@st.cache_data(ttl=300, max_entries=256)
def load_historial_por_especialista(id_usuario: int):
    return fetch_df(LISTADO_HISTORIAL_POR_ESPECIALISTA, {"id_usuario": int(id_usuario)})


@st.cache_data(ttl=300, max_entries=512)
def load_resultados_por_prueba(id_prueba: int):
    return fetch_df(GET_RESULTADOS_POR_PRUEBA, {"id_prueba": int(id_prueba)})


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
        if st.button(":material/check: Sí, eliminar", use_container_width=True, type="primary", key="hist_confirmar_eliminar"):
            try:
                ids = []
                orig_df = st.session_state.get('historial_df', pd.DataFrame())
                try:
                    for _, row in selected_rows_df.iterrows():
                        id_val = row.get('id_prueba', None) if 'id_prueba' in selected_rows_df.columns else None
                        if id_val is None or (isinstance(id_val, float) and pd.isna(id_val)):
                            continue
                        try:
                            ids.append(int(id_val))
                        except Exception:
                            continue
                except Exception:
                    # Fallback: original logic (index-based) if iteration fails for some reason
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
                            continue

                if not ids:
                    st.warning('No se pudieron resolver los ids seleccionados.')
                else:
                    try:
                        placeholders = ','.join(['%s'] * len(ids))

                        sql_del_resultados = f"DELETE FROM dbo.Resultado WHERE id_prueba IN ({placeholders})"
                        fetch_df(sql_del_resultados, tuple(ids))

                        sql_del_pruebas = f"DELETE FROM dbo.Prueba OUTPUT DELETED.id_prueba AS id_prueba WHERE id_prueba IN ({placeholders})"
                        fetch_df(sql_del_pruebas, tuple(ids))

                        # Invalidate cached historial data so UI shows fresh results
                        try:
                            load_historial_base.clear()
                            load_historial_por_especialista.clear()
                            load_resultados_por_prueba.clear()
                        except Exception:
                            pass

                        # Also clear cached data used by the individual view so it refreshes
                        try:
                            from components import individual as _individual
                            try:
                                _individual.get_pruebas_data.clear()
                            except Exception:
                                pass
                            try:
                                _individual.get_info.clear()
                            except Exception:
                                pass
                        except Exception:
                            pass

                        if 'historial_df' in st.session_state:
                            try:
                                del st.session_state['historial_df']
                            except Exception:
                                pass
                        if 'historial_selected_indices' in st.session_state:
                            del st.session_state['historial_selected_indices']
                        if 'historial_page_selections' in st.session_state:
                            del st.session_state['historial_page_selections']
                    except Exception as e:
                        st.error(f"Error al eliminar evaluaciones: {e}")
            except Exception as e:
                st.error(f":material/error: Error al procesar eliminación: {e}")
            st.rerun()

    with col_no:
        if st.button(":material/cancel: Cancelar", use_container_width=True, key="hist_cancelar_eliminar"):
            st.rerun()


@st.dialog(":material/filter_list: Filtros")
def dialog_filtros():
    """Diálogo para filtrar datos por columnas."""
    original_data = get_historial_data()
    df_original = pd.DataFrame(original_data)
    
    if 'active_historial_filters' not in st.session_state:
        st.session_state['active_historial_filters'] = {}
    
    evaluado_options = ["Todos"] + sorted(df_original['Nombre del evaluado'].dropna().unique().tolist())
    evaluado_filter = st.selectbox(
        "Evaluado",
        evaluado_options,
        index=evaluado_options.index(st.session_state['active_historial_filters'].get('Evaluado', 'Todos')) if st.session_state['active_historial_filters'].get('Evaluado', 'Todos') in evaluado_options else 0,
        key="filter_evaluado"
    )
    
    sexo_options = ["Todos"] + sorted(df_original['Sexo'].dropna().unique().tolist())
    sexo_filter = st.selectbox(
        "Sexo",
        sexo_options,
        index=sexo_options.index(st.session_state['active_historial_filters'].get('Sexo', 'Todos')) if st.session_state['active_historial_filters'].get('Sexo', 'Todos') in sexo_options else 0,
        key="filter_sexo"
    )
    
    grupo_options = ["Todos"] + sorted(df_original['Grupo'].dropna().unique().tolist())
    grupo_filter = st.selectbox(
        "Grupo",
        grupo_options,
        index=grupo_options.index(st.session_state['active_historial_filters'].get('Grupo', 'Todos')) if st.session_state['active_historial_filters'].get('Grupo', 'Todos') in grupo_options else 0,
        key="filter_grupo"
    )
    
    edad_min = st.number_input(
        "Edad mínima",
        min_value=18,
        max_value=100,
        value=st.session_state['active_historial_filters'].get('edad_min', 18),
        key="filter_edad_min"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_desde = st.date_input(
            "Fecha desde",
            value=st.session_state['active_historial_filters'].get('fecha_desde', None),
            key="filter_fecha_desde"
        )
    with col2:
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

    col1, col3 = st.columns(2)
    with col1:
        st.markdown("<br><br/>", unsafe_allow_html=True)
        if st.button(":material/refresh: Limpiar", use_container_width=True, key="clear_filters"):
            st.session_state['active_historial_filters'] = {}
            st.session_state.historial_current_page = 1
            if 'historial_df' in st.session_state:
                del st.session_state['historial_df']
            if 'historial_selected_indices' in st.session_state:
                del st.session_state['historial_selected_indices']
            if 'historial_page_selections' in st.session_state:
                del st.session_state['historial_page_selections']
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

            try:
                if fecha_desde is not None and fecha_hasta is not None and fecha_hasta < fecha_desde:
                    st.session_state['historial_filters_invalid_date'] = True
                    st.stop()
                else:
                    if 'historial_filters_invalid_date' in st.session_state:
                        try:
                            del st.session_state['historial_filters_invalid_date']
                        except Exception:
                            pass
            except Exception:
                pass

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
                st.session_state.historial_current_page = 1
                if 'historial_selected_indices' in st.session_state:
                    del st.session_state['historial_selected_indices']
                if 'historial_page_selections' in st.session_state:
                    del st.session_state['historial_page_selections']
                if 'historial_filters_no_results' in st.session_state:
                    try:
                        del st.session_state['historial_filters_no_results']
                    except Exception:
                        pass
                st.rerun()


def get_historial_data() -> List[Dict]:
    """Obtiene el historial de pruebas/evaluaciones desde la BD."""
    try:
        is_especialista = False
        is_admin = False
        try:
            import services.auth as auth
            try:
                auth.is_logged_in()
            except Exception:
                pass
            try:
                is_admin = auth.is_admin()
            except Exception:
                is_admin = False
            try:
                is_especialista = auth.is_especialista()
            except Exception:
                is_especialista = False
        except Exception:
            is_admin = False
            is_especialista = False

        if is_admin:
            df = load_historial_base()
        elif is_especialista:
            user = st.session_state.get("user", {})
            id_usuario = user.get("id_usuario")
            if not id_usuario:
                return []
            try:
                id_usuario = int(id_usuario)
            except Exception:
                return []

            df = load_historial_por_especialista(id_usuario)
            try:
                ids_df = fetch_df("SELECT id_evaluado FROM Evaluado WHERE id_usuario = @id_usuario", {"id_usuario": int(id_usuario)})
                if ids_df is None or ids_df.empty:
                    return []
                assigned_ids = [int(x) for x in ids_df['id_evaluado'].tolist()]
                if 'id_evaluado' in df.columns:
                    df = df[df['id_evaluado'].astype('Int64').isin(assigned_ids)]
                else:
                    try:
                        df = df[df['id_evaluado'].astype('Int64').isin(assigned_ids)]
                    except Exception:
                        return []
            except Exception:
                return []
        else:
            df = load_historial_base()

        if df is None or df.empty:
            return []

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
    
    # Configuración
    st.set_page_config(page_title="Rainly - Historial", layout="wide", initial_sidebar_state="auto")
    
    # CSS
    _css_grupos = Path(__file__).parent.parent / 'assets' / 'grupos.css'
    _css_historial = Path(__file__).parent.parent / 'assets' / 'historial.css'
    
    try:
        with open(_css_grupos, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
        with open(_css_historial, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="page-header">Historial de evaluaciones</div>', unsafe_allow_html=True)
    
    if 'historial_df' not in st.session_state:
        st.session_state['historial_df'] = pd.DataFrame(get_historial_data())
    
    if st.session_state['historial_df'].empty:
        st.info(":material/info: No hay evaluaciones registradas.")
        return
    
    df = st.session_state['historial_df'].copy()
    
    if 'historial_selected_indices' not in st.session_state:
        st.session_state['historial_selected_indices'] = set()
    
    if 'historial_page_selections' not in st.session_state:
        st.session_state['historial_page_selections'] = {}
    
    columns_order = ['id_prueba', 'Nombre del evaluado', 'Edad', 'Sexo', 'Grupo', 'Fecha de evaluación']
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
        filtros_btn = st.button(":material/filter_list: Filtros", use_container_width=True, type="secondary", key="historial_btn_filtros_top")
    
    with col_exportar:
        exportar_btn = st.button(":material/file_download: Exportar", use_container_width=True, type="secondary", key="historial_btn_exportar_top")
    
    with col_eliminar:
        eliminar_btn = st.button(":material/delete: Eliminar", use_container_width=True, type="secondary", key="historial_btn_eliminar_top")

    with col_vermas:
        ver_mas_btn = st.button("Ver resultados", type="primary", use_container_width=True, key="historial_btn_vermas_top")
    
    st.markdown("<br/>", unsafe_allow_html=True)
    
    if buscar:
        mask = df_display[['Nombre del evaluado', 'Sexo', 'Grupo']].apply(
            lambda row: row.astype(str).str.contains(buscar, case=False).any(), axis=1
        )
        df_display = df_display[mask]
        df = df[mask]
    
    ROWS_PER_PAGE = 10

    if 'historial_current_page' not in st.session_state:
        st.session_state.historial_current_page = 1

    total_rows = len(df_display)
    total_pages = max(1, (total_rows + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)

    if st.session_state.historial_current_page > total_pages:
        st.session_state.historial_current_page = total_pages

    page = st.session_state.historial_current_page
    start_idx = (page - 1) * ROWS_PER_PAGE
    end_idx = start_idx + ROWS_PER_PAGE
    df_display_page = df_display.iloc[start_idx:end_idx].copy()
    
    global_to_local = {global_idx: local_idx for local_idx, global_idx in enumerate(df_display_page.index)}
    
    preselected_local = [
        global_to_local[idx] 
        for idx in st.session_state['historial_selected_indices'] 
        if idx in global_to_local
    ]
    
    table_key = f"historial_table_page_{page}"
    
    event = st.dataframe(
        df_display_page,
        use_container_width=True,
        hide_index=True,
        key=table_key,
        on_select="rerun",
        selection_mode="multi-row",
        column_config={
            "id_prueba": st.column_config.TextColumn("ID", width="small"),
            "Nombre del evaluado": st.column_config.TextColumn("Nombre del evaluado", width="medium"),
            "Edad": st.column_config.NumberColumn("Edad", width="small"),
            "Sexo": st.column_config.TextColumn("Sexo", width="small"),
            "Grupo": st.column_config.TextColumn("Grupo", width="small"),
            "Fecha de evaluación": st.column_config.TextColumn("Fecha de evaluación", width="small"),
        }
    )
    
    current_local_selections = set(event.selection.rows)
    previous_local_selections = set(st.session_state['historial_page_selections'].get(page, []))
    
    if current_local_selections != previous_local_selections:
        for local_idx in current_local_selections - previous_local_selections:
            if local_idx < len(df_display_page):
                global_idx = df_display_page.index[local_idx]
                st.session_state['historial_selected_indices'].add(global_idx)
        
        for local_idx in previous_local_selections - current_local_selections:
            if local_idx < len(df_display_page):
                global_idx = df_display_page.index[local_idx]
                st.session_state['historial_selected_indices'].discard(global_idx)
        
        st.session_state['historial_page_selections'][page] = list(current_local_selections)
    
    elif preselected_local and not current_local_selections:
        st.session_state['historial_page_selections'][page] = preselected_local
        st.rerun()
    
    all_selected_indices = list(st.session_state['historial_selected_indices'])
    seleccionados = df.loc[df.index.isin(all_selected_indices)] if all_selected_indices else pd.DataFrame()
    
    st.caption(f"**Total de evaluaciones:** {len(df)} - **Mostrando:** {start_idx + 1}-{min(end_idx, total_rows)} - **Seleccionadas:** {len(seleccionados)}")

    if total_pages > 1:
        col_prev, col_center, col_next = st.columns([1, 2, 1])

        with col_prev:
            if st.button(":material/arrow_back: Anterior", disabled=(st.session_state.historial_current_page == 1), key="btn_prev_page", type="tertiary", use_container_width=True):
                st.session_state.historial_current_page -= 1
                st.rerun()

        with col_center:
            st.markdown(
                f"<div style='text-align: center; padding-top: 6px;'><strong>Página {st.session_state.historial_current_page} de {total_pages}</strong></div>",
                unsafe_allow_html=True
            )

        with col_next:
            if st.button("Siguiente :material/arrow_forward:", disabled=(st.session_state.historial_current_page == total_pages), key="btn_next_page", type="tertiary", use_container_width=True):
                st.session_state.historial_current_page += 1
                st.rerun()

        st.markdown("<br/>", unsafe_allow_html=True)
    
    if filtros_btn:
        dialog_filtros()

    if exportar_btn:
        if len(seleccionados) == 0:
            st.markdown("""
            <div class="warning">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
            <span>Selecciona al menos una evaluación para exportar</span>
            </div>
            """, unsafe_allow_html=True)
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
                    # Construir lista de indicadores por fila consultando los resultados asociados a cada id_prueba
                    indicadores_por_fila = []
                    for idx in seleccionados.index.tolist():
                        try:
                            row = df.loc[idx]
                        except Exception:
                            indicadores_por_fila.append([])
                            continue

                        id_prueba = row.get('id_prueba', None)
                        if id_prueba is None or pd.isna(id_prueba):
                            indicadores_por_fila.append([])
                            continue

                        try:
                            try:
                                df_res = load_resultados_por_prueba(int(id_prueba))
                            except Exception:
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
                                        "id_categoria": r.get('id_categoria') if 'id_categoria' in r else None,
                                        "categoria_nombre": r.get('categoria_nombre') if 'categoria_nombre' in r else None,
                                        "categoria": r.get('categoria') if 'categoria' in r else None,
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
            st.markdown("""
            <div class="warning">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
            <span>Selecciona al menos una evaluación para eliminar</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            confirmar_eliminacion_pruebas(seleccionados)

    if ver_mas_btn:
        if len(seleccionados) != 1:
            st.markdown("""
            <div class="warning">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
            <span>Selecciona exactamente una evaluación para ver sus resultados.</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            try:
                idx = seleccionados.index[0]
                selected_data = df.loc[idx]
                st.session_state["open_prueba_id"] = selected_data['id_prueba']
                st.session_state["selected_evaluation_id"] = selected_data['id_evaluado']
                st.session_state['from_ajustes'] = False
                # Signal the individual view to show its loader (consistent with sidebar logic)
                try:
                    st.session_state['show_individual_loader'] = True
                except Exception:
                    pass
                st.session_state["active_view"] = "individual"
                st.rerun()
            except Exception as e:
                st.error(f":material/error: Error: {e}")
    
    show_loader('show_historial_loader', min_seconds=1.0)