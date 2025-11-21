import streamlit as st
import os
import hashlib
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timedelta
from services.db import fetch_df
from services.queries.q_usuarios import GET_USUARIO_BY_USERNAME, UPDATE_ULTIMO_ACCESO
import logging

logger = logging.getLogger(__name__)


def _auth_debug(msg: str):
    """Intento seguro de registrar mensajes de depuración para autenticación.
    - Añade la entrada a st.session_state['auth_debug_logs'] si está disponible.
    - También hace logging vía logger.debug y print como fallback.
    No debe incluir valores secretos (no imprime claves ni tokens completos).
    """
    try:
        # logger puede estar configurado por el entorno
        logger.debug(msg)
    except Exception:
        pass
    try:
        if hasattr(st, "session_state"):
            logs = st.session_state.get("auth_debug_logs") or []
            # asegurarse lista
            if not isinstance(logs, list):
                logs = [str(logs)]
            logs.append(f"{datetime.utcnow().isoformat()} - {msg}")
            st.session_state["auth_debug_logs"] = logs
    except Exception:
        try:
            # último recurso: imprimir
            print("AUTH DEBUG:", msg)
        except Exception:
            pass


def _get_secret_key():

    try:
        try:
            val = st.secrets["JWT_SECRET_KEY"]
        except Exception:
            val = st.secrets.get("JWT_SECRET_KEY") if hasattr(st, "secrets") else None
        if val:
            _auth_debug("_get_secret_key: usando JWT secret desde st.secrets (no mostrar valor)")
            return val
    except Exception:
        # st.secrets podría no estar disponible en ciertos entornos
        pass
    env_val = os.environ.get("JWT_SECRET_KEY")
    if env_val:
        _auth_debug("_get_secret_key: usando JWT secret desde variable de entorno (no mostrar valor)")
    else:
        _auth_debug("_get_secret_key: no se encontró JWT_SECRET_KEY en st.secrets ni en entorno")
    return env_val


def hash_password(password: str) -> str:
    """Hash simple usando sha256. Devuelve hex digest."""
    if password is None:
        return ""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_token(username: str, role: str, id_usuario: int | None = None) -> str:
    """Genera un JWT con expiración de 24 horas."""
    secret = _get_secret_key()
    if not secret:
        _auth_debug("create_token: JWT_SECRET_KEY no configurada, no se puede crear token")
        raise RuntimeError("JWT_SECRET_KEY no configurada en st.secrets ni en la variable de entorno JWT_SECRET_KEY")
    now = datetime.utcnow()
    
    iat = int(now.timestamp()) - 60
    exp = int((now + timedelta(hours=2)).timestamp()) #* duración del token 
    payload = {
        "sub": username,
        "role": role,
        "iat": iat,
        "exp": exp,
    }
    if id_usuario is not None:
        payload["id_usuario"] = int(id_usuario)
        _auth_debug(f"create_token: creando token para user={username} id_usuario={id_usuario}")
        print(f"Creating token with id_usuario: {id_usuario}")
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token


def verify_token(token: str):
    """Valida y decodifica el token. Devuelve payload o None si inválido/expirado."""
    secret = _get_secret_key()
    if not secret:
        return None
    try:
        # Permitir un leeway pequeño para tolerar diferencias de reloj entre firma y verificación
        # Desactivar la verificación de 'iat' (puede ser comprobada estrictamente en algunos entornos)
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            leeway=10,
            options={"verify_iat": False},
        )
        # limpiar error previo
        try:
            if "auth_error" in st.session_state:
                del st.session_state["auth_error"]
        except Exception:
            pass
        _auth_debug(f"verify_token: token verificado para sub={payload.get('sub')} exp={payload.get('exp')}")
        return payload
    except ExpiredSignatureError as e:
        try:
            st.session_state["auth_error"] = "Token expirado"
        except Exception:
            pass
        _auth_debug(f"verify_token: token expirado: {str(e)}")
        return None
    except InvalidTokenError as e:
        try:
            st.session_state["auth_error"] = f"Token inválido: {str(e)}"
        except Exception:
            pass
        _auth_debug(f"verify_token: token inválido: {str(e)}")
        return None
    except Exception as e:
        try:
            st.session_state["auth_error"] = f"Error verificando token: {str(e)}"
        except Exception:
            pass
        _auth_debug(f"verify_token: error no esperado verificando token: {str(e)}")
        return None


def logout():
    """Limpia la sesión y recarga la app."""
    try:
        current_keys = list(st.session_state.keys()) if hasattr(st, "session_state") else []
    except Exception:
        current_keys = []
    _auth_debug(f"logout: iniciando cierre de sesión, claves presentes: {current_keys}")
    keys = [k for k in current_keys if k.startswith("jwt_") or k in ("jwt_token", "user")]
    for k in keys:
        try:
            if k in st.session_state:
                del st.session_state[k]
        except Exception as exc:
            _auth_debug(f"logout: error borrando clave {k}: {str(exc)}")
    # Además limpiar caches relacionadas a vistas que dependen del usuario
    extra_caches = ["historial_df", "evaluados_df", "auth_debug_logs", "hist_delete_msg"]
    for k in extra_caches:
        try:
            if k in st.session_state:
                del st.session_state[k]
                _auth_debug(f"logout: eliminada cache {k}")
        except Exception as exc:
            _auth_debug(f"logout: fallo borrando cache {k}: {str(exc)}")
    # Además eliminar claves relacionadas con subidas / media que pueden referenciar ids en memoria
    media_like = [
        "uploaded_file",
        "file_uploader",
        "agregar_file_uploader",
        # posibles variantes internas
    ]
    try:
        for fk in media_like:
            if fk in st.session_state:
                try:
                    del st.session_state[fk]
                    _auth_debug(f"logout: eliminada clave de media conocida: {fk}")
                except Exception as exc:
                    _auth_debug(f"logout: fallo eliminando clave de media {fk}: {str(exc)}")
        # eliminar claves que contengan palabras relacionadas con archivos subidos (con cuidado)
        for k in list(st.session_state.keys()):
            low = k.lower()
            if "uploaded" in low or "file_uploader" in low or low.startswith("file_") or "_file" in low:
                try:
                    del st.session_state[k]
                    _auth_debug(f"logout: eliminada clave de media heurística: {k}")
                except Exception:
                    # ignorar fallos individuales
                    pass
    except Exception:
        pass
    # asegurar que user y jwt_token están eliminados
    for k in ("user", "jwt_token"):
        try:
            if k in st.session_state:
                del st.session_state[k]
        except Exception as exc:
            _auth_debug(f"logout: error borrando {k} en cleanup: {str(exc)}")
    _auth_debug(f"logout: borradas claves: {keys}")
    # intentar forzar recarga/rerun en entornos que lo soporten
    # Forzar recarga: probar st.rerun() (nueva), luego st.experimental_rerun(), luego st.stop()
    try:
        rerun_new = getattr(st, "rerun", None)
        if callable(rerun_new):
            _auth_debug("logout: ejecutando st.rerun()")
            rerun_new()
            return
    except Exception as exc:
        _auth_debug(f"logout: st.rerun fallo: {str(exc)}")
    try:
        rerun = getattr(st, "experimental_rerun", None)
        if callable(rerun):
            _auth_debug("logout: ejecutando st.experimental_rerun()")
            rerun()
            return
    except Exception as exc:
        _auth_debug(f"logout: experimental_rerun fallo: {str(exc)}")
    _auth_debug("logout: no se pudo llamar a rerun; llamando st.stop() como último recurso")
    try:
        st.stop()
    except Exception:
        pass
    
def _test_direct_connection():
    """Prueba simple de conexión a DB usando la capa `services.db`.
    Evita usar `pyodbc` directamente (que requiere controladores del sistema)
    y devuelve un mensaje legible para los logs.
    """
    try:
        # Intentar ejecutar una consulta simple vía fetch_df (SQLAlchemy)
        df = fetch_df("SELECT TOP 1 usuario FROM Usuario;")
        print(f"[auth] prueba conexión DB fetch_df result: {df}")
        if df is None:
            return "[ERROR] No se recibió resultado de la consulta de prueba"
        return "[OK] Consulta de prueba ejecutada (SQLAlchemy)"
    except Exception as e:
        # Devolver el error para que el log muestre por qué falló (p. ej. falta de driver)
        return f"[ERROR] fallo conexión DB vía SQLAlchemy: {e}"


def verify_user(username: str, password: str):
    """Verifica credenciales contra la tabla `usuarios`.
    Devuelve diccionario con datos de usuario si ok: {username, role, name, email}
    o None si falla.
    """
    if not username or not password:
        return None

    try:
        df = fetch_df(GET_USUARIO_BY_USERNAME, {"usuario": username})
        st.write("DEBUG DF:", df)
    except Exception as exc:
        _auth_debug(f"verify_user: error conectando a DB para usuario={username}: {str(exc)}")
        st.error("Error al conectarse a la base de datos al verificar usuario.")
        return None

    if df is None or df.empty:
        _auth_debug(f"verify_user: usuario no encontrado: {username}")
        return None

    row = df.iloc[0]
    stored_hash = None
    try:
        stored_hash = row.get("password_hash")
    except Exception:
        stored_hash = None
    if stored_hash is None:
        _auth_debug(f"verify_user: password_hash ausente para usuario={username}")
        return None
    if stored_hash == hash_password(password):
        # Mapear campos a nombres consistentes en session_state
        # Asegurar que id_usuario sea un int nativo si existe
        raw_id = None
        try:
            if "id_usuario" in row:
                raw_id = row.get("id_usuario")
            elif "id" in row:
                raw_id = row.get("id")
        except Exception:
            raw_id = None

        id_usuario_val = None
        try:
            if raw_id is not None:
                id_usuario_val = int(raw_id)
        except Exception:
            id_usuario_val = None

        mapped = {
            "username": row.get("usuario") or row.get("username"),
            "role": row.get("rol") or row.get("role"),
            "id_usuario": id_usuario_val,
            "name": row.get("nombre_completo") or row.get("name") or row.get("usuario"),
            "email": row.get("email"),
        }
        _auth_debug(f"verify_user: credenciales correctas para usuario={username} id_usuario={id_usuario_val}")
        # Actualizar último acceso en la base de datos. No bloquear el login si falla.
        try:
            if id_usuario_val is not None:
                print(f"[auth] intentando actualizar ultimo_acceso para id_usuario={id_usuario_val}")
                fetch_df(UPDATE_ULTIMO_ACCESO, {"id_usuario": id_usuario_val})
                print(f"[auth] UPDATE_ULTIMO_ACCESO ejecutado para id_usuario={id_usuario_val}")
                _auth_debug(f"verify_user: actualizado ultimo_acceso para id_usuario={id_usuario_val}")
        except Exception as e:
            print(f"[auth] error actualizando ultimo_acceso para id_usuario={id_usuario_val}: {e}")
            _auth_debug(f"verify_user: error actualizando ultimo_acceso para id_usuario={id_usuario_val}: {e}")

        return mapped
    _auth_debug(f"verify_user: password incorrecta para usuario={username}")
    return None


def is_logged_in() -> bool:
    st.write(_test_direct_connection())
    """Verifica si hay sesión activa y token válido. Si expiró, hace logout y devuelve False."""
    token = st.session_state.get("jwt_token")
    _auth_debug(f"is_logged_in: token presente? {'si' if token else 'no'}")
    if not token:
        return False
    payload = verify_token(token)
    if not payload:
        logout()
        return False
    if "user" not in st.session_state:
        st.session_state["user"] = {
            "username": payload.get("sub"),
            "role": payload.get("role"),
            "id_usuario": payload.get("id_usuario"),
        }
        _auth_debug(f"is_logged_in: reconstruido st.session_state['user'] desde payload para {payload.get('sub')}")
    return True


def is_admin() -> bool:
    """Devuelve True si el usuario autenticado tiene rol 'admin'."""
    user = st.session_state.get("user")
    if not user:
        return False
    return (user.get("role") or "").lower() == "administrador"

def is_especialista() -> bool:
    """Devuelve True si el usuario autenticado tiene rol 'especialista'."""
    user = st.session_state.get("user")
    if not user:
        return False
    return (user.get("role") or "").lower() == "especialista"

def is_operador() -> bool:
    """Devuelve True si el usuario autenticado tiene rol 'operador'."""
    user = st.session_state.get("user")
    if not user:
        return False
    return (user.get("role") or "").lower() == "operador"



