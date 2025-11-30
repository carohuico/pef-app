import re
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import hashlib
import time
from services.db import fetch_df
from services.queries.q_usuarios import *
from components.evaluados import evaluados


# Cached loader for all usuarios list
@st.cache_data(ttl=300, max_entries=16)
def load_all_usuarios():
    return fetch_df(GET_ALL_USUARIOS)

def hash_password(password):
    """Genera un hash de la contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_usuario_unico(usuario, email, usuario_id=None):
    """Verifica que el usuario y email sean únicos"""
    # Verificar usuario
    result_usuario = fetch_df(GET_USUARIO_BY_USERNAME, {"usuario": usuario})
    
    if not result_usuario.empty and (usuario_id is None or result_usuario.iloc[0]['id_usuario'] != usuario_id):
        return False, "El nombre de usuario ya está en uso"
    
    # Verificar email
    result_email = fetch_df(GET_USUARIO_BY_EMAIL, {"email": email})
    
    if not result_email.empty and (usuario_id is None or result_email.iloc[0]['id_usuario'] != usuario_id):
        return False, "El email ya está registrado"
    
    return True, ""

label = ":material/add: Agregar Usuario"
@st.dialog(label)
def agregar_usuario_dialog():
    """Modal para agregar un nuevo usuario"""
    with st.form("form_agregar_usuario", border=False):
        st.write("Completa la información del nuevo usuario:")
        
        
        usuario = st.text_input(
            "Usuario :red[*]",
            placeholder="Ej: jperez",
            help="Nombre de usuario único para login",
            
        )
        nombre_completo = st.text_input(
            "Nombre Completo :red[*]",
            placeholder="Ej: Juan Pérez López"
        )
        email = st.text_input(
            "Email :red[*]",
            placeholder="usuario@example.com"
        )
    
        telefono = st.text_input(
            "Teléfono",
            placeholder="8112345678",
            max_chars=10
        )
        rol = st.selectbox(
            "Rol :red[*]",
            options=["Administrador", "Operador", "Especialista"],
            index=None,
            placeholder="Selecciona un rol"
        )
        password = st.text_input(
            "Contraseña :red[*]",
            type="password",
            help="Requisitos:\n- Debe tener al menos 12 caracteres.\n- Puedes usar letras, números y símbolos."
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
            if not usuario:
                campos_vacios.append("Usuario")
            if not nombre_completo:
                campos_vacios.append("Nombre Completo")
            if not email:
                campos_vacios.append("Email")
            if not rol:
                campos_vacios.append("Rol")
            if not password:
                campos_vacios.append("Contraseña")
            
            if campos_vacios:
                st.error(f"Los siguientes campos son obligatorios: {', '.join(campos_vacios)}")
                st.stop()
            
            #!validaciones de contraseña
            if len(password) < 12:
                st.error("La contraseña debe tener al menos 12 caracteres")
                st.stop()
            #si la contraseña no tiene al menos una mayuscula, una minuscula, un numero y un caracter especial
            elif re.search(r'[A-Z]', password):
                st.error("La contraseña debe contener al menos una letra mayúscula")
                st.stop()

            elif not re.search(r'[0-9]', password):
                st.error("La contraseña debe contener al menos un número")
                st.stop()
            elif re.search(r'[\W_]', password):
                st.error("La contraseña debe contener al menos un carácter especial")
                st.stop()
            
            
            if telefono and len(telefono) != 10:
                st.error("El teléfono debe tener exactamente 10 dígitos")
                st.stop()

            # Validar formato de correo (ej: nombre@dominio.com)
            email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
            if not re.match(email_pattern, email.strip()):
                st.error("El correo debe tener el formato nombre@dominio.com")
                st.stop()

            es_unico, mensaje = verificar_usuario_unico(usuario, email)
            if not es_unico:
                label = ":material/warning:"
                st.error(f"{label} {mensaje}")
                st.stop()
            
            try:
                password_hash = hash_password(password)
                
                fetch_df(INSERT_USUARIO, {
                    "usuario": usuario.strip(),
                    "nombre_completo": nombre_completo.strip(),
                    "email": email.strip().lower(),
                    "telefono": telefono.strip() if telefono else None,
                    "rol": rol,
                    "password_hash": password_hash
                })
                
                label = f":material/check: Usuario '{usuario}'"
                st.success(f"{label} creado exitosamente")
                time.sleep(1)
                try:
                    load_all_usuarios.clear()
                except Exception:
                    pass
                if 'usuarios_df' in st.session_state:
                    try:
                        del st.session_state.usuarios_df
                    except Exception:
                        pass
                st.rerun()
                
            except Exception as e:
                label = ":material/error:"
                st.error(f"{label} al crear el usuario: {str(e)}")

label = ":material/edit: Editar Usuario"
@st.dialog(label)
def editar_usuario_dialog(usuario_data):
    """Modal para editar un usuario existente"""
    with st.form("form_editar_usuario", border=False):
        st.write(f"Editando usuario: **{usuario_data['usuario']}**")
        
        
        usuario = st.text_input(
            "Usuario :red[*]",
            value=usuario_data["usuario"],
            help="Nombre de usuario único para login"
        )
        nombre_completo = st.text_input(
            "Nombre Completo :red[*]",
            value=usuario_data["nombre_completo"]
        )
        email = st.text_input(
            "Email :red[*]",
            value=usuario_data["email"]
        )
    
        telefono = st.text_input(
            "Teléfono",
            value=usuario_data.get("telefono", "") or "",
            max_chars=10
        )
        rol = st.selectbox(
            "Rol :red[*]",
            options=["Administrador", "Operador", "Especialista"],
            index=["Administrador", "Operador", "Especialista"].index(usuario_data["rol"])
        )
        # Mostrar contraseña actual (enmascarada) y permitir cambiarla
        nueva_password = st.text_input(
            "Contraseña",
            type="password",
            placeholder="Dejar vacío para mantener la contraseña actual",
            help="Requisitos:\n- Debe tener al menos 12 caracteres.\n- Puedes usar letras, números y símbolos.\n- Deja vacío si no deseas cambiarla."
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
            if not usuario:
                campos_vacios.append("Usuario")
            if not nombre_completo:
                campos_vacios.append("Nombre Completo")
            if not email:
                campos_vacios.append("Email")
            if not rol:
                campos_vacios.append("Rol")
            
            if campos_vacios:
                label = ":material/warning: Campos obligatorios"
                st.error(f"{label}: {', '.join(campos_vacios)}")
                st.stop()
            
            # Validar nueva contraseña solo si se proporcionó
            if nueva_password and len(nueva_password) < 12:
                label = ":material/warning:"
                st.error(f"{label} La nueva contraseña debe tener al menos 12 caracteres")
                st.stop()
            
            if telefono and len(telefono) != 10:
                label = ":material/warning:"
                st.error(f"{label} El teléfono debe tener exactamente 10 dígitos")
                st.stop()

            # Validar formato de correo (ej: nombre@dominio.com)
            email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
            if not re.match(email_pattern, email.strip()):
                label = ":material/warning:"
                st.error(f"{label} El correo debe tener el formato nombre@dominio.com")
                st.stop()

            # Verificar unicidad (excluyendo el usuario actual)
            es_unico, mensaje = verificar_usuario_unico(
                usuario, email, usuario_data["id_usuario"]
            )
            if not es_unico:
                label = ":material/warning:"
                st.error(f"{label} {mensaje}")
                st.stop()
            
            try:
                # Preparar hash de contraseña (solo cambiar si se proporcionó nueva)
                if nueva_password:
                    password_hash = hash_password(nueva_password)
                else:
                    password_hash = usuario_data["password_hash"]
                
                # Actualizar usuario
                fetch_df(UPDATE_USUARIO, {
                    "id_usuario": usuario_data["id_usuario"],
                    "usuario": usuario.strip(),
                    "nombre_completo": nombre_completo.strip(),
                    "email": email.strip().lower(),
                    "telefono": telefono.strip() if telefono else None,
                    "rol": rol,
                    "password_hash": password_hash
                })
                
                label = f":material/check: Usuario '{usuario}'"
                st.success(f"{label} actualizado exitosamente")
                time.sleep(1)
                try:
                    load_all_usuarios.clear()
                except Exception:
                    pass
                if 'usuarios_df' in st.session_state:
                    try:
                        del st.session_state.usuarios_df
                    except Exception:
                        pass
                st.rerun()
                
            except Exception as e:
                label = ":material/error: Error"
                st.error(f"{label} al actualizar el usuario: {str(e)}")

def eliminar_usuarios_seleccionados(usuarios_seleccionados):
    """Elimina los usuarios seleccionados"""
    try:
        eliminados = []
        
        for idx, usuario in usuarios_seleccionados.iterrows():
            fetch_df(DELETE_USUARIO, {"id_usuario": usuario["id_usuario"]})
            eliminados.append(f":material/check: Usuario '{usuario['usuario']}' eliminado")
        
        for msg in eliminados:
            st.success(msg)
        
        time.sleep(1)
        try:
            load_all_usuarios.clear()
        except Exception:
            pass
        if 'usuarios_df' in st.session_state:
            try:
                del st.session_state.usuarios_df
            except Exception:
                pass
        st.rerun()
    except Exception as e:
        label = ":material/error: Error"
        st.error(f"{label} al eliminar usuarios: {str(e)}")

@st.dialog(":material/warning: Confirmar Eliminación")
def confirmar_eliminacion_dialog(usuarios_seleccionados):
    """Modal de confirmación para eliminar usuarios"""
    if len(usuarios_seleccionados) == 1:
        st.warning(f"¿Estás seguro de que deseas eliminar al usuario **{usuarios_seleccionados.iloc[0]['nombre_completo']}**?")
    else:
        st.warning(f"¿Estás seguro de que deseas eliminar **{len(usuarios_seleccionados)} usuarios**?")
    
    st.write("Esta acción no se puede deshacer.")
    
    col_conf1, col_conf2 = st.columns(2)
    with col_conf2:
        label = ":material/check: Sí, eliminar"
        if st.button(label, use_container_width=True, type="primary", key="usuarios_confirmar_eliminar_modal"):
            try:
                eliminar_usuarios_seleccionados(usuarios_seleccionados)
            except Exception as e:
                st.error(f":material/error: Error al eliminar usuarios: {e}")
            st.rerun()
    with col_conf1:
        label = ":material/cancel: Cancelar"
        if st.button(label, use_container_width=True, key="usuarios_cancelar_eliminar_modal"):
            st.rerun()

def usuarios():
    """Renderiza la vista de administración de usuarios"""
        
    # Cargar datos (cached)
    if 'usuarios_df' not in st.session_state:
        st.session_state.usuarios_df = load_all_usuarios()
    
    # Verificar si hay usuarios
    if st.session_state.usuarios_df.empty:
        # Botón para agregar usuario cuando no hay datos
        col1, col2, col3 = st.columns([1, 5, 1])
        with col1:
            button_label = ":material/add: Crear"
            if st.button(button_label, use_container_width=True, type="primary"):
                agregar_usuario_dialog()
        
        label = ":material/info: No hay usuarios registrados."
        st.info(label)
        return
    
    # Preparar DataFrame
    df = st.session_state.usuarios_df.copy()
    
    # Formatear fecha de último acceso
    df["ultimo_acceso"] = pd.to_datetime(df["ultimo_acceso"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # Crear columna de selección
    df.insert(0, 'Seleccionar', False)
    
    # Ocultar password_hash para display
    df_display = df.drop(columns=["password_hash"])
    
    # Reordenar columnas para display (sin id_usuario visible)
    columns_order = ['Seleccionar', 'nombre_completo', 'usuario', 'rol', 'email', 'telefono', 'ultimo_acceso']
    df_display = df_display[[col for col in columns_order if col in df_display.columns]]
    
    # Barra de búsqueda y botones (como en la imagen)
    col_buscar, col_editar, col_eliminar, col_crear = st.columns([3, 1, 1, 1])
    
    with col_buscar:
        buscar = st.text_input(
            "Buscar usuario",
            placeholder="Buscar...",
            label_visibility="collapsed",
            key="buscar_usuario"
        )
    
    with col_editar:
        button_label = ":material/edit: Editar"
        editar_btn = st.button(button_label, use_container_width=True, type="secondary", key="usuarios_btn_editar_top")
    
    with col_eliminar:
        button_label = ":material/delete: Eliminar"
        eliminar_btn = st.button(button_label, use_container_width=True, type="secondary", key="usuarios_btn_eliminar_top")
    
    with col_crear:
        button_label = ":material/add: Crear"
        crear_btn = st.button(button_label, use_container_width=True, type="primary", key="usuarios_btn_crear_top")
    st.markdown("<br/>", unsafe_allow_html=True)
    # Aplicar búsqueda si hay texto
    if buscar:
        mask = df_display[['nombre_completo', 'usuario', 'email', 'rol']].apply(
            lambda row: row.astype(str).str.contains(buscar, case=False).any(), axis=1
        )
        df_display = df_display[mask]
        df = df[mask]  
    
    # ========== PAGINACIÓN (usuarios) ==========
    ROWS_PER_PAGE = 9
    page_key = 'usuarios_current_page'
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
        key="usuarios_table_editor",
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn("", width="small"),
            "id_usuario": None,  # Ocultar id_usuario
            "nombre_completo": st.column_config.TextColumn(
                "Nombre Completo",
                width="medium",
            ),
            "usuario": st.column_config.TextColumn(
                "Usuario",
                width="small",
            ),
            "rol": st.column_config.TextColumn(
                "Rol",
                width="small",
            ),
            "email": st.column_config.TextColumn(
                "Email",
                width="medium",
            ),
            "telefono": st.column_config.TextColumn(
                "Teléfono",
                width="small",
            ),
            "ultimo_acceso": st.column_config.TextColumn(
                "Último Acceso",
                width="medium",
            ),
        },
        disabled=['nombre_completo', 'usuario', 'rol', 'email', 'telefono', 'ultimo_acceso', 'id_usuario']
    )

    
    st.caption(f"**Total de usuarios:** {len(df)} | **Mostrando:** {start_idx + 1}-{min(end_idx, total_rows)}")

    # Obtener usuarios seleccionados
    seleccionados = edited_df[edited_df['Seleccionar'] == True]

    # Paginación debajo de la tabla
    if total_pages > 1:
        col_prev, col_center, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button(":material/arrow_back: Anterior", disabled=(st.session_state[page_key] == 1), key="usuarios_btn_prev", type="tertiary", use_container_width=True):
                st.session_state[page_key] -= 1
                st.rerun()
        with col_center:
            st.markdown(f"<div style='text-align: center; padding-top: 6px;'><strong>Página {st.session_state[page_key]} de {total_pages}</strong></div>", unsafe_allow_html=True)
        with col_next:
            if st.button("Siguiente :material/arrow_forward:", disabled=(st.session_state[page_key] == total_pages), key="usuarios_btn_next", type="tertiary", use_container_width=True):
                st.session_state[page_key] += 1
                st.rerun()
        st.markdown("<br/>", unsafe_allow_html=True)
    
    # Manejar acciones de los botones
    if crear_btn:
        agregar_usuario_dialog()
    
    if editar_btn:
        if len(seleccionados) == 0:
            st.markdown("""
            <div class="warning">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
            <span>Selecciona al menos un usuario para editar</span>
            </div>
            """, unsafe_allow_html=True)
        elif len(seleccionados) > 1:
            st.markdown("""
            <div class="warning">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
            <span>Selecciona solo un usuario para editar</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Obtener el usuario completo del df original con id_usuario
            idx = seleccionados.index[0]
            usuario_completo = df.loc[idx].to_dict()
            editar_usuario_dialog(usuario_completo)
    
    if eliminar_btn:
        if len(seleccionados) == 0:
            st.markdown("""
            <div class="warning">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" style="flex:0 0 14px;">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
            <span>Selecciona al menos un usuario para eliminar</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Obtener usuarios completos del df original
            indices = seleccionados.index
            usuarios_completos = df.loc[indices]
            
            confirmar_eliminacion_dialog(usuarios_completos)
     