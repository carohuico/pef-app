import streamlit as st
import pandas as pd
import time
from pathlib import Path
from services.db import fetch_df
from services.queries.q_grupos import (
    GET_GRUPOS, CREATE_GRUPO, CREATE_SUBGRUPO, 
    UPDATE_GRUPO, DELETE_SUBGRUPOS, DELETE_GRUPO, UPDATE_EVALUADOS_A_INDIVIDUALES
)

def grupos():
    # Cargar CSS
    _css_grupos = Path(__file__).parent.parent / 'assets' / 'grupos.css'
    try:
        with open(_css_grupos, 'r', encoding='utf-8') as _f:
            st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
    except Exception as _e:
        st.error(f"Error loading CSS: {_e}")
    
    # Cargar datos
    if 'grupos_df' not in st.session_state:
        st.session_state.grupos_df = fetch_df(GET_GRUPOS)
    
    # Cargar municipios
    municipios_df = fetch_df('SELECT id_municipio, nombre FROM Municipio')
    municipios_dict = dict(zip(municipios_df['nombre'], municipios_df['id_municipio']))
    
    # Filtrar solo grupos principales
    grupos_principales = st.session_state.grupos_df[
        st.session_state.grupos_df['Grupo Padre'].isna()
    ].copy() if not st.session_state.grupos_df.empty else pd.DataFrame()
    
    if grupos_principales.empty:
        st.info("No hay grupos registrados.")
        button_label = ":material/add: Crear nuevo grupo"
        if st.button(button_label, type="primary", key="grupos_crear_empty"):
            mostrar_dialogo_crear_grupo(municipios_df['nombre'].tolist(), municipios_dict)
        return
    
    # Preparar DataFrame para visualización
    df_display = grupos_principales[['ID', 'Nombre', 'Municipio', 'Dirección']].copy()
    df_display.insert(0, 'Seleccionar', False)
    df_display = df_display.reset_index(drop=True)
    
    # Mostrar información ANTES de la barra de búsqueda
    # Necesitamos verificar si hay selección previa en session_state
    seleccion_previa = None
    if 'editor_grupos' in st.session_state:
        try:
            # Intentar obtener la selección previa del data_editor
            seleccion_previa = st.session_state.editor_grupos.get('edited_rows', {})
        except:
            pass
    
    # Contar cuántos grupos están seleccionados (estimado antes del data_editor)
    if seleccion_previa:
        num_seleccionados = sum(1 for row_changes in seleccion_previa.values() 
                                if row_changes.get('Seleccionar', False))
    else:
        num_seleccionados = 0
    
    # Mostrar mensajes informativos
    if num_seleccionados == 0:
        label = ":material/info: Selecciona un grupo para gestionar sus subgrupos"
        st.info(label)
        st.markdown("<br>", unsafe_allow_html=True)
    elif num_seleccionados > 1:
        label = ":material/info: Selecciona solo un grupo para gestionar sus subgrupos"
        st.info(label)

    # Barra de búsqueda y botones
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        buscar = st.text_input("Buscar grupo:", placeholder="Buscar...", label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)

    with col2:
        button_label = ":material/edit: Editar"
        editar_btn = st.button(button_label, type="secondary", use_container_width=True, key="grupos_btn_editar_top")
    with col3:
        button_label = ":material/delete: Eliminar"
        eliminar_btn = st.button(button_label, type="secondary", use_container_width=True, key="grupos_btn_eliminar_top")
    with col4:
        button_label = ":material/add: Crear"
        crear_btn = st.button(button_label, type="primary", use_container_width=True, key="grupos_btn_crear_top")
        st.markdown("<br>", unsafe_allow_html=True)

    # Aplicar búsqueda
    if buscar:
        mask = df_display[['Nombre', 'Municipio', 'Dirección']].apply(
            lambda row: row.astype(str).str.contains(buscar, case=False).any(), axis=1
        )
        df_display = df_display[mask]
        st.caption(f"💡 Resultados: {len(df_display)} grupo(s)")
    
    # Mostrar tabla (solo lectura con checkbox)
    edited_df = st.data_editor(
        df_display,
        use_container_width=True,
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn("", width="small"),
            "ID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "Nombre": st.column_config.TextColumn("Nombre", disabled=True, width="medium"),
            "Municipio": st.column_config.TextColumn("Municipio", disabled=True, width="medium"),
            "Dirección": st.column_config.TextColumn("Dirección", disabled=True, width="large"),
        },
        column_order=['Seleccionar', 'Nombre', 'Municipio', 'Dirección'],
        hide_index=True,
        disabled=['ID', 'Nombre', 'Municipio', 'Dirección'],
        key="editor_grupos",
        height=150
    )
    
    # Manejar acciones
    seleccionados = edited_df[edited_df['Seleccionar'] == True]
    
    if crear_btn:
        mostrar_dialogo_crear_grupo(municipios_df['nombre'].tolist(), municipios_dict)
    
    if editar_btn:
        if len(seleccionados) == 0:
            st.warning("Selecciona un grupo para editar")
        elif len(seleccionados) > 1:
            st.warning("Selecciona solo un grupo para editar")
        else:
            grupo = seleccionados.iloc[0]
            mostrar_dialogo_editar_grupo(grupo, municipios_df['nombre'].tolist(), municipios_dict)
    
    if eliminar_btn:
        if len(seleccionados) == 0:
            st.warning("Selecciona al menos un grupo para eliminar")
        else:
            eliminar_grupos_seleccionados(seleccionados)
    
    # Mostrar subgrupos si solo hay 1 grupo seleccionado
    if len(seleccionados) == 1:
        grupo = seleccionados.iloc[0]
        st.markdown("<br>", unsafe_allow_html=True)
        gestionar_subgrupos(int(grupo['ID']), grupo['Nombre'], municipios_dict, municipios_df['nombre'].tolist())
    


@st.dialog("Crear Nuevo Grupo")
def mostrar_dialogo_crear_grupo(municipios_list, municipios_dict):
    """Modal para crear un nuevo grupo"""
    with st.form("form_crear_grupo"):
        nombre = st.text_input("Nombre *", max_chars=100)
        municipio = st.selectbox("Municipio *", municipios_list)
        direccion = st.text_area("Dirección *", max_chars=200)
        
        submitted = st.form_submit_button("Crear Grupo", type="primary", use_container_width=True)
        
        if submitted:
            if not nombre or not direccion or not municipio:
                st.error("Todos los campos son obligatorios")
                return
            
            try:
                id_municipio = municipios_dict.get(municipio)
                fetch_df(CREATE_GRUPO, {
                    'id_municipio': id_municipio,
                    'nombre': nombre,
                    'direccion': direccion
                })
                label = f":material/check: Grupo '{nombre}'"
                st.success(f"{label} creado exitosamente")
                time.sleep(1)
                st.session_state.grupos_df = fetch_df(GET_GRUPOS)
                st.rerun()
            except Exception as e:
                st.error(f"Error al crear grupo: {str(e)}")


@st.dialog("Editar Grupo")
def mostrar_dialogo_editar_grupo(grupo, municipios_list, municipios_dict):
    """Modal para editar un grupo existente"""
    with st.form("form_editar_grupo"):
        nombre = st.text_input("Nombre *", value=grupo['Nombre'], max_chars=100)
        municipio = st.selectbox("Municipio *", municipios_list, index=municipios_list.index(grupo['Municipio']))
        direccion = st.text_area("Dirección *", value=grupo['Dirección'], max_chars=200)
        
        submitted = st.form_submit_button("Guardar Cambios", type="primary", use_container_width=True)
        
        if submitted:
            if not nombre or not direccion or not municipio:
                st.error("Todos los campos son obligatorios")
                return
            
            try:
                id_municipio = municipios_dict.get(municipio)
                fetch_df(UPDATE_GRUPO, {
                    'nombre': nombre,
                    'direccion': direccion,
                    'id_municipio': id_municipio,
                    'parent_id': None,
                    'id_grupo': int(grupo['ID'])
                })
                label = f":material/check: Grupo '{grupo['Nombre']}'"
                st.success(f"{label} actualizado exitosamente")
                time.sleep(1)
                st.session_state.grupos_df = fetch_df(GET_GRUPOS)
                st.rerun()
            except Exception as e:
                st.error(f"Error al actualizar grupo: {str(e)}")


def eliminar_grupos_seleccionados(grupos_seleccionados):
    """Elimina grupos con sus subgrupos en cascada"""
    try:
        eliminados = []
        
        for idx, grupo in grupos_seleccionados.iterrows():
            id_grupo = int(grupo['ID'])
            
            # Contar subgrupos
            subgrupos = st.session_state.grupos_df[
                st.session_state.grupos_df['Grupo Padre'] == id_grupo
            ]
            num_subgrupos = len(subgrupos)
            
            # Eliminar en cascada
            fetch_df(UPDATE_EVALUADOS_A_INDIVIDUALES, {'id_grupo': id_grupo})
            fetch_df(DELETE_SUBGRUPOS, {'id_grupo': id_grupo})
            fetch_df(DELETE_GRUPO, {'id_grupo': id_grupo})
            
            label = f":material/check: Grupo '{grupo['Nombre']}'"
            if num_subgrupos > 0:
                eliminados.append(
                    f"{label} eliminado con {num_subgrupos} subgrupo(s). Evaluados ahora son individuales."
                )
            else:
                eliminados.append(f"{label} eliminado")

        for msg in eliminados:
            st.success(msg)
        
        time.sleep(2)
        st.session_state.grupos_df = fetch_df(GET_GRUPOS)
        st.rerun()
            
    except Exception as e:
        st.error(f"Error al eliminar grupos: {str(e)}")


def gestionar_subgrupos(id_grupo_padre, nombre_grupo_padre, municipios_dict, municipios_list):
    """Gestiona los subgrupos de un grupo seleccionado"""
    # Título con botones
    col_titulo, col_editar, col_eliminar, col_crear = st.columns([3, 1, 1, 1])
    
    with col_titulo:
        st.markdown(f"##### Subgrupos de: {nombre_grupo_padre}")
    
    # Obtener subgrupos
    subgrupos_df = st.session_state.grupos_df[
        st.session_state.grupos_df['Grupo Padre'] == id_grupo_padre
    ].copy()
    
    if subgrupos_df.empty:
        with col_crear:
            button_label = ":material/add: Crear"
            if st.button(button_label, key=f"crear_sub_{id_grupo_padre}", type="primary", use_container_width=True):
                mostrar_dialogo_crear_subgrupo(id_grupo_padre, municipios_list, municipios_dict)
        
        st.info(f"No hay subgrupos registrados para '{nombre_grupo_padre}'.")
        return
    
    # Preparar DataFrame para visualización
    df_display = subgrupos_df[['ID', 'Nombre', 'Municipio', 'Dirección']].copy()
    df_display.insert(0, 'Seleccionar', False)
    df_display = df_display.reset_index(drop=True)
    
    # Botones de acción en la fila del título
    with col_editar:
        button_label = ":material/edit: Editar"
        editar_sub_btn = st.button(button_label, key=f"editar_btn_{id_grupo_padre}", type="secondary", use_container_width=True)
    with col_eliminar:
        button_label = ":material/delete: Eliminar"
        eliminar_sub_btn = st.button(button_label, key=f"eliminar_btn_{id_grupo_padre}", type="secondary", use_container_width=True)
    with col_crear:
            button_label = ":material/add: Crear"
            crear_sub_btn = st.button(button_label, key=f"crear_btn_{id_grupo_padre}", type="primary", use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)

    # Tabla de subgrupos
    edited_subgrupos = st.data_editor(
        df_display,
        use_container_width=True,
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn("", width="small"),
            "ID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "Nombre": st.column_config.TextColumn("Nombre", disabled=True, width="medium"),
            "Municipio": st.column_config.TextColumn("Municipio", disabled=True, width="medium"),
            "Dirección": st.column_config.TextColumn("Dirección", disabled=True, width="large"),
        },
        column_order=['Seleccionar', 'Nombre', 'Municipio', 'Dirección'],
        hide_index=True,
        disabled=['ID', 'Nombre', 'Municipio', 'Dirección'],
        key=f"editor_subgrupos_{id_grupo_padre}",
        height=150
    )
    
    # Manejar acciones
    seleccionados = edited_subgrupos[edited_subgrupos['Seleccionar'] == True]
    
    if crear_sub_btn:
        mostrar_dialogo_crear_subgrupo(id_grupo_padre, municipios_list, municipios_dict)
    
    if editar_sub_btn:
        if len(seleccionados) == 0:
            st.warning("Selecciona un subgrupo para editar")
        elif len(seleccionados) > 1:
            st.warning("Selecciona solo un subgrupo para editar")
        else:
            subgrupo = seleccionados.iloc[0]
            mostrar_dialogo_editar_subgrupo(subgrupo, id_grupo_padre, municipios_list, municipios_dict)
    
    if eliminar_sub_btn:
        if len(seleccionados) == 0:
            st.warning("Selecciona al menos un subgrupo para eliminar")
        else:
            eliminar_subgrupos_seleccionados(seleccionados)


@st.dialog("Crear Nuevo Subgrupo")
def mostrar_dialogo_crear_subgrupo(id_grupo_padre, municipios_list, municipios_dict):
    """Modal para crear un nuevo subgrupo"""
    with st.form("form_crear_subgrupo"):
        nombre = st.text_input("Nombre *", max_chars=100)
        municipio = st.selectbox("Municipio *", municipios_list)
        direccion = st.text_area("Dirección *", max_chars=200)
        
        submitted = st.form_submit_button("Crear Subgrupo", type="primary", use_container_width=True)
        
        if submitted:
            if not nombre or not direccion or not municipio:
                st.error("Todos los campos son obligatorios")
                return
            
            try:
                id_municipio = municipios_dict.get(municipio)
                fetch_df(CREATE_SUBGRUPO, {
                    'parent_id': id_grupo_padre,
                    'id_municipio': id_municipio,
                    'nombre': nombre,
                    'direccion': direccion
                })
                st.success(f"✅ Subgrupo '{nombre}' creado exitosamente")
                time.sleep(1)
                st.session_state.grupos_df = fetch_df(GET_GRUPOS)
                st.rerun()
            except Exception as e:
                st.error(f"Error al crear subgrupo: {str(e)}")


@st.dialog("Editar Subgrupo")
def mostrar_dialogo_editar_subgrupo(subgrupo, id_grupo_padre, municipios_list, municipios_dict):
    """Modal para editar un subgrupo existente"""
    with st.form("form_editar_subgrupo"):
        nombre = st.text_input("Nombre *", value=subgrupo['Nombre'], max_chars=100)
        municipio = st.selectbox("Municipio *", municipios_list, index=municipios_list.index(subgrupo['Municipio']))
        direccion = st.text_area("Dirección *", value=subgrupo['Dirección'], max_chars=200)
        
        submitted = st.form_submit_button("Guardar Cambios", type="primary", use_container_width=True)
        
        if submitted:
            if not nombre or not direccion or not municipio:
                st.error("Todos los campos son obligatorios")
                return
            
            try:
                id_municipio = municipios_dict.get(municipio)
                fetch_df(UPDATE_GRUPO, {
                    'nombre': nombre,
                    'direccion': direccion,
                    'id_municipio': id_municipio,
                    'parent_id': id_grupo_padre,
                    'id_grupo': int(subgrupo['ID'])
                })
                label = f":material/check: Subgrupo '{nombre}'"
                st.success(f"{label} actualizado exitosamente")
                time.sleep(1)
                st.session_state.grupos_df = fetch_df(GET_GRUPOS)
                st.rerun()
            except Exception as e:
                st.error(f"Error al actualizar subgrupo: {str(e)}")


def eliminar_subgrupos_seleccionados(subgrupos_seleccionados):
    """Elimina subgrupos y convierte sus evaluados en individuales"""
    try:
        eliminados = []
        
        for idx, subgrupo in subgrupos_seleccionados.iterrows():
            id_subgrupo = int(subgrupo['ID'])
            
            # Eliminar subgrupo
            fetch_df(UPDATE_EVALUADOS_A_INDIVIDUALES, {'id_grupo': id_subgrupo})
            fetch_df(DELETE_GRUPO, {'id_grupo': id_subgrupo})

            eliminados.append(f":material/check: Subgrupo '{subgrupo['Nombre']}' eliminado. Evaluados ahora son individuales.")

        for msg in eliminados:
            st.success(msg)
        
        time.sleep(2)
        st.session_state.grupos_df = fetch_df(GET_GRUPOS)
        st.rerun()
            
    except Exception as e:
        st.error(f"Error al eliminar subgrupos: {str(e)}")