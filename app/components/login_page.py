import streamlit as st
import services.auth as auth
from services.db import fetch_df
from services.queries.q_usuarios import UPDATE_ULTIMO_ACCESO, GET_USUARIO_BY_ID, GET_USUARIO_BY_USERNAME


def login_page():
    """Página de login con diseño split screen limpio"""
    
    st.html("""
    <style>
        /* Ocultar elementos de Streamlit */
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
        
        /* Forzar las columnas a ser 50/50 en altura completa */
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
        
        [data-testid="stColumn"]:last-child {
            background: white !important;
            color: black !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            align-content: center !important;    
            padding: 4rem !important;      
        }
        
        /* Logo centrado */
        [data-testid="stColumn"]:first-child img {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            align-content: center !important;          
            margin: 0 auto !important;
        }
        
        [data-testid="stColumn"]:last-child .stTextInput > div {
            margin-bottom: 1.5rem !important;
        }
        
        /* Título Welcome */
        .welcome-title {
            color: black;
            font-size: 3.5rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 3rem;
            margin-top: 3rem !important;
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
        
        /* Alertas en fondo negro */
        .stAlert {
            border-radius: 12px !important;
            background-color: rgba(255, 255, 255, 0.1) !important;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        
        
        /* Caption */
        .stCaption div {
            color: rgba(255, 255, 255, 0.6) !important;
            text-align: center !important;
            margin-top: 2.5rem !important;
            font-size: 0.95rem !important;
        }
        
        /* Responsive */
        @media (max-width: 968px) {
            [data-testid="column"] {
                min-height: 50vh !important;
            }
            
            .welcome-title {
                font-size: 2.5rem;
            }
        }
    </style>
    """)
    
    col_left, col_right = st.columns(2)
    
    # ===== COLUMNA IZQUIERDA - LOGO =====
    with col_left:
        st.image("assets/logo.png", use_container_width=True)
            
    # ===== COLUMNA DERECHA - FORMULARIO =====
    with col_right:
        # Título
        st.html('<h1 class="welcome-title">¡Hola!</h1>')
        
        # Formulario
        username = st.text_input(
            "Usuario",
            key="login_username",
            placeholder="Usuario",
            label_visibility="collapsed"
        )
        
        password = st.text_input(
            "Contraseña",
            type="password",
            key="login_password",
            placeholder="Contraseña",
            label_visibility="collapsed"
        )
        
        # Botón de login
        if st.button("Iniciar sesión", type="primary", use_container_width=True):
            if not username or not password:
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
        