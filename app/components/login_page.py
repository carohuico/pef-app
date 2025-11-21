import streamlit as st
import services.auth as auth
from services.db import fetch_df, get_db_info
from services.queries.q_usuarios import UPDATE_ULTIMO_ACCESO, GET_USUARIO_BY_ID, GET_USUARIO_BY_USERNAME
from pathlib import Path
import base64


def login_page():
    """Página de login con diseño split screen limpio y responsive"""
    
    st.html("""
    <style>
        /* ===== ESTILOS GENERALES ===== */
        [data-testid="stMainBlockContainer"] div { padding: 0 !important; margin: 0 !important; }
        [data-testid="stSidebar"] { display: none; }
        [data-testid="stToolbar"] { display: none; }
        .stApp > header { background-color: transparent; }
        
        /* Fondo gris */
        [data-testid="stAppViewContainer"] {
            background: #f5f5f5 !important;
        }
        
        /* Sin padding en el container */
        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
        
        /* ===== DISEÑO DESKTOP (Split Screen) ===== */
        [data-testid="stElement"] {
            padding: 0 !important;
            min-height: 100vh !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }
        
        [data-testid="stColumn"]:first-child div {
            background: #000000 !important;
            min-height: 95vh !important;
            height: 100%;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            align-content: center !important;          
        }
        
        /* COLUMNA DERECHA: Centrado vertical y horizontal */
        [data-testid="stColumn"]:last-child {
            background: white !important;
            color: black !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            padding-top: 4rem !important;
            padding-bottom: 8rem !important;
            min-height: 95vh !important;
        }
        
        /* Contenedor interno del formulario centrado */
        [data-testid="stColumn"]:last-child > div {
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
            width: 100% !important;
            max-width: 500px !important;
        }
        
        /* Todos los elementos del formulario centrados */
        [data-testid="stColumn"]:last-child [data-testid="stVerticalBlock"] {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
        }
        
        /* Logo centrado en columna izquierda */
        [data-testid="stColumn"]:first-child img {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            align-content: center !important;          
            margin: 0 auto !important;
        }
        
        /* OCULTAR logo negro en DESKTOP */
        .logo-black {
            display: none !important;
        }
        
        /* Título Welcome */
        .welcome-title {
            color: black;
            font-size: 3.5rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 3rem;
            margin-top: 0 !important;
        }
        
        /* Inputs centrados con ancho fijo */
        [data-testid="stColumn"]:last-child [data-testid="stTextInput"] {
            width: 100% !important;
            max-width: 500px !important;
        }
        
        /* Botón centrado con ancho fijo */
        [data-testid="stColumn"]:last-child .stButton {
            width: 100% !important;
            max-width: 500px !important;
        }
        
        /* Botón amarillo */
        .stButton > button[kind="primary"] {
            background: #FFE451;
            color: #000000;
            border:none;
            box-shadow: 0 3px 6px rgba(0,0,0,0.06);
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            width: 100% !important;
        }
        
        .stButton > button[kind="primary"]:hover {
            transform: scale(0.98);
            background: #FFD626;
        }
        
        .stButton > button[kind="primary"]:active {
            transform: translateY(0) !important;
        }
        
        /* Alertas centradas */
        [data-testid="stColumn"]:last-child .stAlert {
            width: 100% !important;
            max-width: 500px !important;
        }
        
        .stAlert {
            border-radius: 12px !important;
            background-color: rgba(0, 0, 0, 0.05) !important;
            color: black !important;
            border: 1px solid rgba(0, 0, 0, 0.1) !important;
        }
        
        /* Caption */
        .stCaption div {
            color: rgba(0, 0, 0, 0.6) !important;
            text-align: center !important;
            margin-top: 2.5rem !important;
            font-size: 0.95rem !important;
        }
        
        /* ===== RESPONSIVE MÓVIL ===== */
        @media (max-width: 768px) {
            /* Ocultar columna izquierda en móvil */
            [data-testid="stColumn"]:first-child {
                display: none !important;
            }
            
            /* Columna derecha ocupa toda la pantalla con fondo blanco */
            [data-testid="stColumn"]:last-child {
                background: white !important;
                min-height: 90vh !important;
                display: flex !important;
                flex-direction: column !important;
                justify-content: center !important;
                align-items: center !important;
            }
            
            /* MOSTRAR logo negro SOLO en móvil */
            .logo-black {
                display: block !important;
                margin: 0 auto 0rem auto !important;
                max-width: 200px !important;
                width: 60% !important;
            }
            
            /* Título más pequeño en móvil */
            .welcome-title {
                visibility: hidden !important;
            }
            
            /* Inputs en móvil */
            [data-testid="stTextInput"] input {
                font-size: 16px !important;
                padding: 0.75rem !important;
            }
            
            /* Botón en móvil */
            .stButton > button[kind="primary"] {
                font-size: 1rem !important;
                padding: 0.875rem !important;
                margin-top: 1.5rem !important;
            }
        }
        
        @media (max-width: 480px) {
            [data-testid="stColumn"]:last-child {
                padding: 1.5rem 1rem !important;
            }
            
            .logo-black {
                max-width: 160px !important;
            }
            
            .welcome-title {
                font-size: 1.75rem !important;
            }
        }
    </style>
    """)
    
    col_left, col_right = st.columns(2)

    # ===== COLUMNA IZQUIERDA - LOGO BLANCO (Solo Desktop) =====
    with col_left:
        try:
            left_logo_path = Path(__file__).parent.parent / 'assets' / 'logo.png'
            if left_logo_path.is_file():
                st.image(str(left_logo_path), use_container_width=True)
            else:
                # Fallback: try logo_black (may be used for mobile styles)
                fallback = Path(__file__).parent.parent / 'assets' / 'logo_black.png'
                if fallback.is_file():
                    with open(fallback, 'rb') as _f:
                        b64 = base64.b64encode(_f.read()).decode('ascii')
                    img_src = f"data:image/png;base64,{b64}"
                    st.markdown(f'<img src="{img_src}" style="max-width:100%;" alt="Rainly Logo">', unsafe_allow_html=True)
                else:
                    st.markdown("<div style='height:4rem;'></div>", unsafe_allow_html=True)
        except Exception:
            st.markdown("<div style='height:4rem;'></div>", unsafe_allow_html=True)

    # ===== COLUMNA DERECHA - FORMULARIO =====
    with col_right:
        # Logo negro usando HTML puro (controlado por CSS para móvil)
        try:
            logo_path = Path(__file__).parent.parent / 'assets' / 'logo_black.png'
            if logo_path.is_file():
                with open(logo_path, 'rb') as _f:
                    b64 = base64.b64encode(_f.read()).decode('ascii')
                img_src = f"data:image/png;base64,{b64}"
            else:
                img_src = "assets/logo_black.png"
        except Exception:
            img_src = "assets/logo_black.png"

        # Usar st.markdown en lugar de st.html para evitar problemas
        st.markdown(
            f'<img src="{img_src}" class="logo-black" alt="Rainly Logo">',
            unsafe_allow_html=True
        )

        # Título
        st.markdown('<h1 class="welcome-title">¡Hola!</h1>', unsafe_allow_html=True)

        # Formulario
        username = st.text_input(
            "Usuario",
            key="login_username",
            placeholder="Usuario",
            label_visibility="collapsed",
        )
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        password = st.text_input(
            "Contraseña",
            type="password",
            key="login_password",
            placeholder="Contraseña",
            label_visibility="collapsed",
        )

        # Botón de login
        if st.button("Iniciar sesión", type="primary", use_container_width=True):
            if not username or not password:
                st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
                label = ":material/warning: Por favor completa todos los campos"
                st.error(label)
            else:
                with st.spinner("Verificando credenciales..."):
                    user = auth.verify_user(username.strip(), password)
                    
                    if user:
                        try:
                            token = auth.create_token(
                                user["username"], 
                                user["role"], 
                                user.get("id_usuario")
                            )
                        except Exception as e:
                            label = ":material/error: Error al generar token"
                            st.error(f"{label} {e}")
                            return
                        
                        try:
                            uid = user.get("id_usuario")
                            uname = user.get("username")
                            if uid is not None:
                                fetch_df(UPDATE_ULTIMO_ACCESO, {"id_usuario": uid})
                                try:
                                    df_user = fetch_df(GET_USUARIO_BY_ID, {"id_usuario": uid})
                                    if df_user is not None and not df_user.empty:
                                        ua = df_user.iloc[0].get("ultimo_acceso")
                                        try:
                                            st.success("Inicio de sesión exitoso")
                                        except Exception:
                                            pass
                                except Exception as e:
                                    print(e)
                            else:
                                if uname:
                                    try:
                                        df_user = fetch_df(GET_USUARIO_BY_USERNAME, {"usuario": uname})
                                        if df_user is not None and not df_user.empty:
                                            row = df_user.iloc[0]
                                            uid2 = row.get("id_usuario")
                                            if uid2 is not None:
                                                fetch_df(UPDATE_ULTIMO_ACCESO, {"id_usuario": uid2})
                                    except Exception as e:
                                        print(e)
                        except Exception as e:
                            print(e)
                        try:
                            if "usuarios_df" in st.session_state:
                                del st.session_state["usuarios_df"]
                                print("[login_page] eliminada cache 'usuarios_df' en session_state")
                        except Exception as e:
                            print(e)

                        # Guardar en session state
                        st.session_state["jwt_token"] = token
                        st.session_state["user"] = user

                        for _k in ("historial_df", "evaluados_df", "auth_debug_logs", "hist_delete_msg"):
                            if _k in st.session_state:
                                try:
                                    del st.session_state[_k]
                                except Exception:
                                    pass
                        
                        try:
                            st.session_state["active_view"] = "inicio"
                        except Exception:
                            pass
                        
                        label = ":material/check_circle: Inicio de sesión exitoso"
                        st.success(label)
                        
                        try:
                            st.rerun()
                        except Exception:
                            try:
                                getattr(st, "experimental_rerun", lambda: None)()
                            finally:
                                st.stop()
                    else:
                        st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
                        label = ":material/error: Credenciales inválidas. Revisa usuario y contraseña."
                        st.error(label)
        
        # Mostrar errores de auth
        auth_err = None
        try:
            auth_err = st.session_state.get("auth_error")
        except Exception:
            pass
        
        if auth_err:
            label = ":material/warning: Aviso de autenticación"
            st.warning(f"{label} {auth_err}")

        # ===== PANEL DE DIAGNÓSTICO (temporal) =====
        with st.expander("Diagnóstico DB (solo debugging)"):
            if st.button("Ejecutar diagnóstico DB"):
                try:
                    info = get_db_info()
                    if isinstance(info, dict) and info.get("error"):
                        st.error(f"Error diagnóstico: {info.get('error')}")
                    else:
                        st.write("**Base de datos actual:**", info.get("current_db"))
                        st.write("**Usuario de conexión:**", info.get("current_user"))
                        st.write("**Tablas visibles (primeras 200):**")
                        tables = info.get("tables")
                        try:
                            st.dataframe(tables.head(200) if hasattr(tables, 'head') else tables)
                        except Exception:
                            st.write(tables)

                    # Ejecutar también la consulta de usuarios de prueba
                    try:
                        df_test = fetch_df("SELECT TOP 1 usuario FROM usuarios;")
                        st.write("**Resultado de SELECT TOP 1 usuario FROM usuarios;**")
                        st.write(df_test)
                    except Exception as e:
                        st.error(f"Consulta de prueba falló: {e}")

                except Exception as e:
                    st.error(f"Error ejecutando diagnóstico: {e}")