import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import time
from services.db import fetch_df
from services.queries.q_indicadores import *

def verificar_indicador_unico(nombre, id_indicador=None):
    """Verifica que el nombre del indicador sea único"""
    result = fetch_df(GET_INDICADOR_BY_NOMBRE, {"nombre": nombre})
    
    if not result.empty and (id_indicador is None or result.iloc[0]['id_indicador'] != id_indicador):
        return False, "El nombre del indicador ya está en uso"
    
    return True, ""

label = ":material/add: Agregar Indicador"
@st.dialog(label)
def agregar_indicador_dialog():
    """Modal para agregar un nuevo indicador"""
    indicadores_existentes = fetch_df(GET_ALL_INDICADORES)
    opciones_indicadores = [""] + list(indicadores_existentes["nombre"].values) if not indicadores_existentes.empty else [""]
    
    with st.form("form_agregar_indicador", border=False):
        st.write("Completa la información del nuevo indicador:")
        
        nombre = st.text_input(
            "Nombre del Indicador :red[*]",
            help="Nombre único para el indicador"
        )
        
        st.write("##### Selecciona los indicadores a combinar:")
        indicador_1 = st.selectbox(
            "Primer Indicador :red[*]",
            options=opciones_indicadores,
            index=0,
            placeholder="Selecciona un indicador"
        )
        
        indicador_2 = st.selectbox(
            "Segundo Indicador :red[*]",
            options=opciones_indicadores,
            index=0,
            placeholder="Selecciona un indicador"
        )
        
        significado = st.text_area(
            "Significado :red[*]",
            placeholder="Describe el significado de combinar estos dos indicadores...",
            help="Explica qué representa la combinación de estos indicadores",
            height=150
        )
        
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn2:
            label = ":material/check: Guardar"
            submitted = st.form_submit_button(label, use_container_width=True, type="primary")
        with col_btn1:
            label = ":material/cancel: Cancelar"
            cancelar = st.form_submit_button(label, use_container_width=True)
        
        if cancelar:
            st.rerun()
        
        if submitted:
            # Validaciones
            campos_vacios = []
            if not nombre:
                campos_vacios.append("Nombre del Indicador")
            if not indicador_1:
                campos_vacios.append("Primer Indicador")
            if not indicador_2:
                campos_vacios.append("Segundo Indicador")
            if not significado:
                campos_vacios.append("Significado")
            
            if campos_vacios:
                st.error(f"⚠️ Los siguientes campos son obligatorios: {', '.join(campos_vacios)}")
                st.stop()
            
            # Verificar unicidad
            es_unico, mensaje = verificar_indicador_unico(nombre)
            if not es_unico:
                label = ":material/warning:"
                st.error(f"{label} {mensaje}")
                st.stop()
            
            try:
                # Insertar indicador
                fetch_df(INSERT_INDICADOR, {
                    "nombre": nombre.strip(),
                    "indicador_1": indicador_1.strip(),
                    "indicador_2": indicador_2.strip(),
                    "significado": significado.strip()
                })
                
                label = f":material/check: Indicador '{nombre}'"
                st.success(f"{label} creado exitosamente")
                time.sleep(1)
                del st.session_state.indicadores_df
                st.rerun()
                
            except Exception as e:
                label = ":material/error:"
                st.error(f"{label} al crear el indicador: {str(e)}")

label = ":material/edit: Editar Indicador"
@st.dialog(label)
def editar_indicador_dialog(indicador_data):
    """Modal para editar un indicador existente"""
    # Cargar lista de indicadores existentes para los selectores
    indicadores_existentes = fetch_df(GET_ALL_INDICADORES)
    opciones_indicadores = [""] + list(indicadores_existentes["nombre"].values) if not indicadores_existentes.empty else [""]
    
    with st.form("form_editar_indicador", border=False):
        st.write(f"Editando indicador: **{indicador_data['nombre']}**")
        
        nombre = st.text_input(
            "Nombre del Indicador :red[*]",
            value=indicador_data["nombre"],
            help="Nombre único para el indicador"
        )
        
        st.write("##### Selecciona los indicadores a combinar:")
        
        # Obtener índices para los selectores
        try:
            idx_1 = opciones_indicadores.index(indicador_data.get("indicador_1", ""))
        except ValueError:
            idx_1 = 0
            
        try:
            idx_2 = opciones_indicadores.index(indicador_data.get("indicador_2", ""))
        except ValueError:
            idx_2 = 0
        
        indicador_1 = st.selectbox(
            "Primer Indicador :red[*]",
            options=opciones_indicadores,
            index=idx_1
        )
        
        indicador_2 = st.selectbox(
            "Segundo Indicador :red[*]",
            options=opciones_indicadores,
            index=idx_2
        )
        
        significado = st.text_area(
            "Significado :red[*]",
            value=indicador_data["significado"],
            help="Explica qué representa la combinación de estos indicadores",
            height=150
        )
        
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn2:
            button_label = ":material/check: Guardar Cambios"
            submitted = st.form_submit_button(button_label, use_container_width=True, type="primary")
        with col_btn1:
            button_label = ":material/cancel: Cancelar"
            cancelar = st.form_submit_button(button_label, use_container_width=True)
        
        if cancelar:
            st.rerun()
        
        if submitted:
            # Validaciones
            campos_vacios = []
            if not nombre:
                campos_vacios.append("Nombre del Indicador")
            if not indicador_1:
                campos_vacios.append("Primer Indicador")
            if not indicador_2:
                campos_vacios.append("Segundo Indicador")
            if not significado:
                campos_vacios.append("Significado")
            
            if campos_vacios:
                label = ":material/warning: Campos obligatorios"
                st.error(f"{label}: {', '.join(campos_vacios)}")
                st.stop()
            
            # Verificar unicidad (excluyendo el indicador actual)
            es_unico, mensaje = verificar_indicador_unico(nombre, indicador_data["id_indicador"])
            if not es_unico:
                label = ":material/warning:"
                st.error(f"{label} {mensaje}")
                st.stop()
            
            try:
                # Actualizar indicador
                fetch_df(UPDATE_INDICADOR, {
                    "id_indicador": indicador_data["id_indicador"],
                    "nombre": nombre.strip(),
                    "indicador_1": indicador_1.strip(),
                    "indicador_2": indicador_2.strip(),
                    "significado": significado.strip()
                })
                
                label = f":material/check: Indicador '{nombre}'"
                st.success(f"{label} actualizado exitosamente")
                time.sleep(1)
                del st.session_state.indicadores_df
                st.rerun()
                
            except Exception as e:
                label = ":material/error: Error"
                st.error(f"{label} al actualizar el indicador: {str(e)}")

def eliminar_indicadores_seleccionados(indicadores_seleccionados):
    """Elimina los indicadores seleccionados"""
    try:
        eliminados = []
        
        for idx, indicador in indicadores_seleccionados.iterrows():
            fetch_df(DELETE_INDICADOR, {"id_indicador": indicador["id_indicador"]})
            eliminados.append(f":material/check: Indicador '{indicador['nombre']}' eliminado")
        
        for msg in eliminados:
            st.success(msg)
        
        time.sleep(1)
        del st.session_state.indicadores_df
        st.rerun()
    except Exception as e:
        label = ":material/error: Error"
        st.error(f"{label} al eliminar indicadores: {str(e)}")

@st.dialog(":material/warning: Confirmar Eliminación")
def confirmar_eliminacion_dialog(indicadores_seleccionados):
    """Modal de confirmación para eliminar indicadores"""
    if len(indicadores_seleccionados) == 1:
        st.warning(f"¿Estás seguro de que deseas eliminar el indicador **{indicadores_seleccionados.iloc[0]['nombre']}**?")
    else:
        st.warning(f"¿Estás seguro de que deseas eliminar **{len(indicadores_seleccionados)} indicadores**?")
    
    st.write("Esta acción no se puede deshacer.")
    
    col_conf1, col_conf2 = st.columns(2)
    with col_conf1:
        label = ":material/check: Sí, eliminar"
        if st.button(label, use_container_width=True, type="primary", key="indicadores_confirmar_eliminar_modal"):
            # Guardar los IDs para eliminar en session_state
            try:
                st.session_state['indicadores_a_eliminar'] = list(indicadores_seleccionados['id_indicador'].astype(int))
            except Exception:
                ids = []
                for i in range(len(indicadores_seleccionados)):
                    try:
                        ids.append(int(indicadores_seleccionados.iloc[i]['id_indicador']))
                    except Exception:
                        continue
                st.session_state['indicadores_a_eliminar'] = ids
            st.rerun()
    with col_conf2:
        label = ":material/cancel: Cancelar"
        if st.button(label, use_container_width=True, key="indicadores_cancelar_eliminar_modal"):
            st.rerun()

def indicadores():
    """Renderiza la vista de administración de indicadores"""
    # Cargar datos
    if 'indicadores_df' not in st.session_state:
        st.session_state.indicadores_df = fetch_df(GET_ALL_INDICADORES)
    
    # Verificar si hay indicadores
    if st.session_state.indicadores_df.empty:
        col1, col2, col3 = st.columns([1, 5, 1])
        with col1:
            button_label = ":material/add: Crear"
            if st.button(button_label, use_container_width=True, type="primary"):
                agregar_indicador_dialog()
        
        label = ":material/info: No hay indicadores registrados."
        st.info(label)
        return
    
    # Preparar DataFrame
    df = st.session_state.indicadores_df.copy()
    
    # Crear columna de selección
    df.insert(0, 'Seleccionar', False)
    
    # Reordenar columnas para display (sin id_indicador visible)
    columns_order = ['Seleccionar', 'nombre', 'significado']
    df_display = df[[col for col in columns_order if col in df.columns]]
    
    # Barra de búsqueda y botones
    col_buscar, col_editar, col_eliminar, col_crear = st.columns([3, 1, 1, 1])
    
    with col_buscar:
        buscar = st.text_input(
            "Buscar indicador",
            placeholder="Buscar...",
            label_visibility="collapsed",
            key="buscar_indicador"
        )
    
    with col_editar:
        button_label = ":material/edit: Editar"
        editar_btn = st.button(button_label, use_container_width=True, type="secondary", key="indicadores_btn_editar_top")
    
    with col_eliminar:
        button_label = ":material/delete: Eliminar"
        eliminar_btn = st.button(button_label, use_container_width=True, type="secondary", key="indicadores_btn_eliminar_top")
    
    with col_crear:
        button_label = ":material/add: Crear"
        crear_btn = st.button(button_label, use_container_width=True, type="primary", key="indicadores_btn_crear_top")
    
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Aplicar búsqueda si hay texto
    if buscar:
        mask = df_display[['nombre', 'significado']].apply(
            lambda row: row.astype(str).str.contains(buscar, case=False).any(), axis=1
        )
        df_display = df_display[mask]
        df = df[mask]
    
    # ========== PAGINACIÓN (indicadores) ==========
    ROWS_PER_PAGE = 9
    page_key = 'indicadores_current_page'
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    total_rows = len(df_display)
    total_pages = max(1, (total_rows + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
    if st.session_state[page_key] > total_pages:
        st.session_state[page_key] = total_pages

    page = st.session_state[page_key]
    start_idx = (page - 1) * ROWS_PER_PAGE
    end_idx = start_idx + ROWS_PER_PAGE
    df_display_page = df_display.iloc[start_idx:end_idx].copy()

    # Mostrar tabla con checkboxes
    edited_df = st.data_editor(
        df_display_page,
        use_container_width=True,
        hide_index=True,
        key="indicadores_table_editor",
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn("", width="small"),
            "id_indicador": None,
            "nombre": st.column_config.TextColumn(
                "Nombre del Indicador",
                width="medium",
            ),
            "significado": st.column_config.TextColumn(
                "Significado",
                width="large",
            ),
        },
        disabled=['nombre', 'significado', 'id_indicador']
    )
    
    # Total de indicadores debajo de la tabla
    st.caption(f"**Total de indicadores:** {len(df)} | **Mostrando:** {start_idx + 1}-{min(end_idx, total_rows)}")

    # Paginación debajo de la tabla
    if total_pages > 1:
        col_prev, col_center, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button(":material/arrow_back: Anterior", disabled=(st.session_state[page_key] == 1), key="indicadores_btn_prev", type="tertiary", use_container_width=True):
                st.session_state[page_key] -= 1
                st.rerun()
        with col_center:
            st.markdown(f"<div style='text-align: center; padding-top: 6px;'><strong>Página {st.session_state[page_key]} de {total_pages}</strong></div>", unsafe_allow_html=True)
        with col_next:
            if st.button("Siguiente :material/arrow_forward:", disabled=(st.session_state[page_key] == total_pages), key="indicadores_btn_next", type="tertiary", use_container_width=True):
                st.session_state[page_key] += 1
                st.rerun()
        st.markdown("<br/>", unsafe_allow_html=True)
    
    # Obtener indicadores seleccionados
    seleccionados = edited_df[edited_df['Seleccionar'] == True]
    
    # Manejar acciones de los botones
    if crear_btn:
        agregar_indicador_dialog()
    
    if editar_btn:
        if len(seleccionados) == 0:
            st.markdown("""
            <div class="warning">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
            <span>Selecciona al menos un indicador para editar</span>
            </div>
            """, unsafe_allow_html=True)
        elif len(seleccionados) > 1:
            st.markdown("""
            <div class="warning">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
            <span>Selecciona solo un indicador para editar</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            idx = seleccionados.index[0]
            indicador_completo = df.loc[idx].to_dict()
            editar_indicador_dialog(indicador_completo)
    
    if eliminar_btn:
        if len(seleccionados) == 0:
            st.markdown("""
            <div class="warning">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
            <span>Selecciona al menos un indicador para eliminar</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            indices = seleccionados.index
            indicadores_completos = df.loc[indices]
            confirmar_eliminacion_dialog(indicadores_completos)
    
    # Procesar eliminación después de confirmación en el modal
    ids_to_delete = st.session_state.pop('indicadores_a_eliminar', None)
    if ids_to_delete:
        try:
            indicadores_para_eliminar = st.session_state.indicadores_df[
                st.session_state.indicadores_df['id_indicador'].isin(ids_to_delete)
            ]
            eliminar_indicadores_seleccionados(indicadores_para_eliminar)
        except Exception as e:
            st.error(f":material/error: Error al procesar eliminación: {e}")