import streamlit as st
import pandas as pd
from pathlib import Path
from services.db import fetch_df
from services.queries.q_grupos import GET_GRUPOS

# Nueva query para obtener subgrupos
GET_SUBGRUPOS = (
    "SELECT g.id_grupo AS ID, g.nombre AS Subgrupo, "
    "g.direccion AS Dirección, "
    "pg.nombre AS 'Grupo Padre', "
    "m.nombre AS Municipio "
    "FROM Grupo g "
    "INNER JOIN Grupo pg ON g.parent_id = pg.id_grupo "
    "LEFT JOIN Municipio m ON g.id_municipio = m.id_municipio "
    "WHERE g.parent_id IS NOT NULL"
)

def grupos():
    """Vista CRUD para la gestión de Grupos"""
        
    grupos_df = fetch_df(GET_GRUPOS)
    if 'grupos_df' not in st.session_state:
        st.session_state.grupos_df = grupos_df
        print("Grupos DataFrame cargado en el estado de la sesión.", st.session_state.grupos_df)
    
    # Selector de operación CRUD
    col1, col2 = st.columns([3, 1])
    with col1:
        operacion = st.radio(
            "Selecciona una operación:",
            ["Ver Grupos", "Crear Grupo", "Editar Grupo", "Eliminar Grupo"],
            horizontal=True, label_visibility="collapsed"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    # VER GRUPOS
    if operacion == "Ver Grupos":
        mostrar_grupos()
    
    # CREAR GRUPO
    elif operacion == "Crear Grupo":
        crear_grupo()
    
    # EDITAR GRUPO
    elif operacion == "Editar Grupo":
        editar_grupo()
    
    # ELIMINAR GRUPO
    elif operacion == "Eliminar Grupo":
        eliminar_grupo()


def mostrar_grupos():
    """Mostrar todos los grupos en una tabla"""
    
    if st.session_state.grupos_df.empty:
        st.info("No hay grupos registrados.")
        return
    
    # Filtrar solo grupos principales (sin parent_id)
    grupos_principales = st.session_state.grupos_df[
        st.session_state.grupos_df['Grupo Padre'].isna()
    ].copy()
    
    buscar_grupos = st.text_input("Buscar grupo:", placeholder="Buscar...", key="buscar_grupos", label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)
    
    df_grupos_filtrado = grupos_principales.copy()
    
    if buscar_grupos:
        df_grupos_filtrado = df_grupos_filtrado[
            df_grupos_filtrado.apply(lambda row: row.astype(str).str.contains(buscar_grupos, case=False).any(), axis=1)
        ]
    
    st.dataframe(
        df_grupos_filtrado,
        use_container_width=True,
        height=100,
        hide_index=True
    )
    
    st.caption(f"Total de grupos principales: {len(df_grupos_filtrado)}")
    
    # TABLA DE SUBGRUPOS
    st.markdown("---")
    
    try:
        subgrupos_df = fetch_df(GET_SUBGRUPOS)
        
        if subgrupos_df.empty:
            st.info("No hay subgrupos registrados.")
        else:
            buscar_subgrupos = st.text_input("Buscar subgrupo:", placeholder="Buscar...", key="buscar_subgrupos", label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)
            
            df_subgrupos_filtrado = subgrupos_df.copy()
            
            if buscar_subgrupos:
                df_subgrupos_filtrado = df_subgrupos_filtrado[
                    df_subgrupos_filtrado.apply(lambda row: row.astype(str).str.contains(buscar_subgrupos, case=False).any(), axis=1)
                ]
            
            st.dataframe(
                df_subgrupos_filtrado,
                use_container_width=True,
                height=100,
                hide_index=True
            )
            
            st.caption(f"Total de subgrupos: {len(df_subgrupos_filtrado)}")
    except Exception as e:
        st.error(f"Error al cargar subgrupos: {str(e)}")


def crear_grupo():
    """Formulario para crear un nuevo grupo"""
    
    with st.form("form_crear_grupo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre del Grupo*", placeholder="Ej: UDEM")
            municipios = fetch_df('SELECT id_municipio, nombre FROM Municipio')
            municipio_seleccionado = st.selectbox(
                "Selecciona el Municipio*",
                municipios['nombre'].tolist(),
                key="municipio_crear"
            )
            
            # Obtener el id_municipio del municipio seleccionado
            id_municipio = municipios[municipios['nombre'] == municipio_seleccionado]['id_municipio'].iloc[0]
            
            # Opción para crear subgrupo
            es_subgrupo = st.checkbox("Este es un subgrupo")
            parent_id = None
            
            if es_subgrupo:
                # Filtrar solo grupos principales
                grupos_principales = st.session_state.grupos_df[
                    st.session_state.grupos_df['Grupo Padre'].isna()
                ].copy()
                
                if not grupos_principales.empty:
                    grupo_padre_seleccionado = st.selectbox(
                        "Selecciona el Grupo Padre*",
                        grupos_principales.apply(lambda x: f"{x['ID']} - {x['Nombre']}", axis=1).tolist(),
                        key="grupo_padre_crear"
                    )
                    parent_id = int(grupo_padre_seleccionado.split(' - ')[0])
                else:
                    st.warning("No hay grupos principales disponibles. Debes crear primero un grupo principal.")
        
        with col2:
            direccion = st.text_area("Dirección*", placeholder="Ej: Av. Ignacio Morones Prieto", height=100)
        
        submitted = st.form_submit_button("✅ Crear Grupo", use_container_width=True)
        
        if submitted:
            if not nombre or not direccion:
                st.error("⚠️ Los campos Nombre y Dirección son obligatorios.")
            elif es_subgrupo and parent_id is None:
                st.error("⚠️ Debes seleccionar un grupo padre para crear un subgrupo.")
            else:
                # Generar nuevo ID
                nuevo_id = st.session_state.grupos_df['ID'].max() + 1 if not st.session_state.grupos_df.empty else 1
                
                # Crear nuevo registro
                nuevo_grupo = pd.DataFrame({
                    'Nombre': [nombre],
                    'ID': [nuevo_id],
                    'Dirección': [direccion],
                    'Grupo Padre': [parent_id],
                    'Municipio': [municipio_seleccionado]
                })
                
                # Agregar al DataFrame
                st.session_state.grupos_df = pd.concat(
                    [st.session_state.grupos_df, nuevo_grupo],
                    ignore_index=True
                )
                
                tipo = "Subgrupo" if es_subgrupo else "Grupo"
                st.success(f"✅ {tipo} '{nombre}' creado exitosamente con ID: {nuevo_id}")
                st.balloons()
                st.rerun()


def editar_grupo():
    """Formulario para editar un grupo existente"""
    
    if st.session_state.grupos_df.empty:
        st.warning("No hay grupos para editar.")
        return
    
    # Selector de grupo
    grupos_lista = st.session_state.grupos_df.apply(
        lambda x: f"{x['ID']} - {x['Nombre']}", axis=1
    ).tolist()
    
    grupo_seleccionado = st.selectbox("Selecciona el grupo a editar:", grupos_lista)
    
    if grupo_seleccionado:
        id_seleccionado = int(grupo_seleccionado.split(' - ')[0])
        grupo_actual = st.session_state.grupos_df[
            st.session_state.grupos_df['ID'] == id_seleccionado
        ].iloc[0]
        
        with st.form("form_editar_grupo"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre = st.text_input("Nombre del Grupo*", value=grupo_actual['Nombre'])
                
                municipios = fetch_df('SELECT id_municipio, nombre FROM Municipio')
                municipio_actual = grupo_actual['Municipio']
                indice_municipio = municipios['nombre'].tolist().index(municipio_actual) if municipio_actual in municipios['nombre'].tolist() else 0
                
                municipio_seleccionado = st.selectbox(
                    "Selecciona el Municipio*",
                    municipios['nombre'].tolist(),
                    index=indice_municipio,
                    key="municipio_editar"
                )
                
                # Opción para convertir en subgrupo
                es_subgrupo = st.checkbox("Este es un subgrupo", value=pd.notna(grupo_actual['Grupo Padre']))
                parent_id = None
                
                if es_subgrupo:
                    grupos_principales = st.session_state.grupos_df[
                        (st.session_state.grupos_df['Grupo Padre'].isna()) & 
                        (st.session_state.grupos_df['ID'] != id_seleccionado)
                    ].copy()
                    
                    if not grupos_principales.empty:
                        grupos_padre_lista = grupos_principales.apply(
                            lambda x: f"{x['ID']} - {x['Nombre']}", axis=1
                        ).tolist()
                        
                        indice_padre = 0
                        if pd.notna(grupo_actual['Grupo Padre']):
                            try:
                                indice_padre = [int(g.split(' - ')[0]) for g in grupos_padre_lista].index(int(grupo_actual['Grupo Padre']))
                            except (ValueError, KeyError):
                                indice_padre = 0
                        
                        grupo_padre_seleccionado = st.selectbox(
                            "Selecciona el Grupo Padre*",
                            grupos_padre_lista,
                            index=indice_padre,
                            key="grupo_padre_editar"
                        )
                        parent_id = int(grupo_padre_seleccionado.split(' - ')[0])
            
            with col2:
                direccion = st.text_area("Dirección*", value=grupo_actual['Dirección'], height=100)
            
            submitted = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
            
            if submitted:
                if not nombre or not direccion:
                    st.error("⚠️ Los campos Nombre y Dirección son obligatorios.")
                else:
                    # Actualizar registro
                    idx = st.session_state.grupos_df[
                        st.session_state.grupos_df['ID'] == id_seleccionado
                    ].index[0]
                    
                    st.session_state.grupos_df.at[idx, 'Nombre'] = nombre
                    st.session_state.grupos_df.at[idx, 'Municipio'] = municipio_seleccionado
                    st.session_state.grupos_df.at[idx, 'Grupo Padre'] = parent_id if es_subgrupo else None
                    st.session_state.grupos_df.at[idx, 'Dirección'] = direccion
                    
                    st.success(f"✅ Grupo '{nombre}' actualizado exitosamente.")
                    st.rerun()


def eliminar_grupo():
    """Formulario para eliminar un grupo"""
    
    if st.session_state.grupos_df.empty:
        st.warning("No hay grupos para eliminar.")
        return
    
    # Selector de grupo
    grupos_lista = st.session_state.grupos_df.apply(
        lambda x: f"{x['ID']} - {x['Nombre']}", axis=1
    ).tolist()
    
    grupo_seleccionado = st.selectbox("Selecciona el grupo a eliminar:", grupos_lista)
    
    if grupo_seleccionado:
        id_seleccionado = int(grupo_seleccionado.split(' - ')[0])
        grupo_actual = st.session_state.grupos_df[
            st.session_state.grupos_df['ID'] == id_seleccionado
        ].iloc[0]
        
        # Verificar si tiene subgrupos
        tiene_subgrupos = not st.session_state.grupos_df[
            st.session_state.grupos_df['Grupo Padre'] == id_seleccionado
        ].empty
        
        if tiene_subgrupos:
            st.error("⚠️ No puedes eliminar este grupo porque tiene subgrupos asociados. Elimina primero los subgrupos.")
            return
        
        # Mostrar información del grupo
        st.warning(f"⚠️ Estás a punto de eliminar el grupo:")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**ID:** {grupo_actual['ID']}")
            st.info(f"**Nombre:** {grupo_actual['Nombre']}")
        with col2:
            st.info(f"**Municipio:** {grupo_actual['Municipio']}")
            st.info(f"**Dirección:** {grupo_actual['Dirección']}")
        
        st.markdown("---")
        
        # Confirmación de eliminación
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            if st.button("🗑️ Confirmar Eliminación", type="primary", use_container_width=True):
                # Eliminar registro
                st.session_state.grupos_df = st.session_state.grupos_df[
                    st.session_state.grupos_df['ID'] != id_seleccionado
                ].reset_index(drop=True)
                
                st.success(f"✅ Grupo '{grupo_actual['Nombre']}' eliminado exitosamente.")
                st.rerun()