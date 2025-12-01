import streamlit as st
import logging
import mimetypes
import os
import base64
import json
from google.cloud import storage
from google.oauth2 import service_account
import re

# Inicializar cliente GCS con credenciales de Streamlit secrets
_gcs_client = None

def get_gcs_client():
    """Obtiene un cliente de GCS autenticado usando GCP_SA_KEY_JSON de secrets"""
    global _gcs_client
    
    if _gcs_client is not None:
        return _gcs_client
    
    try:
        # Primero intentar desde Streamlit secrets
        if hasattr(st, 'secrets') and 'GCP_SA_KEY_JSON' in st.secrets:
            sa_json = st.secrets['GCP_SA_KEY_JSON']
            # Try to load JSON normally, but accept malformed multiline private_key
            try:
                sa_info = json.loads(sa_json)
            except json.JSONDecodeError:
                try:
                    # Escape real newlines inside the private_key value so json.loads can parse it
                    def _escape_private_key(match):
                        prefix = match.group(1)
                        key_body = match.group(2)
                        suffix = match.group(3)
                        return prefix + key_body.replace('\n', '\\n') + suffix

                    fixed = re.sub(r'("private_key"\s*:\s*")([\s\S]*?)(")', _escape_private_key, sa_json, flags=re.MULTILINE)
                    sa_info = json.loads(fixed)
                except Exception:
                    raise
            credentials = service_account.Credentials.from_service_account_info(sa_info)
            _gcs_client = storage.Client(credentials=credentials)
            logging.info("GCS client initialized from st.secrets['GCP_SA_KEY_JSON']")
            return _gcs_client
    except Exception as e:
        logging.warning(f"Failed to get GCS credentials from st.secrets: {e}")
    
    try:
        # Fallback: intentar desde variable de entorno
        env_json = os.environ.get('GCP_SA_KEY_JSON')
        if env_json:
            try:
                sa_info = json.loads(env_json)
            except json.JSONDecodeError:
                try:
                    fixed = re.sub(r'("private_key"\s*:\s*")([\s\S]*?)(")', lambda m: m.group(1) + m.group(2).replace('\n', '\\n') + m.group(3), env_json, flags=re.MULTILINE)
                    sa_info = json.loads(fixed)
                except Exception:
                    raise
            credentials = service_account.Credentials.from_service_account_info(sa_info)
            _gcs_client = storage.Client(credentials=credentials)
            logging.info("GCS client initialized from GCP_SA_KEY_JSON environment variable")
            return _gcs_client
    except Exception as e:
        logging.warning(f"Failed to get GCS credentials from environment: {e}")
    
    # Si todo falla, retornar None
    logging.error("No GCP service account credentials found")
    return None


def download_gcs_uri_to_tmp(gcs_uri: str) -> str:
    """Descarga un archivo desde GCS a un archivo temporal y retorna la ruta local.
    
    Args:
        gcs_uri: URI en formato gs://bucket-name/path/to/file
        
    Returns:
        Ruta local del archivo descargado, o None si falla
    """
    if not isinstance(gcs_uri, str) or not gcs_uri.startswith('gs://'):
        logging.error(f"Invalid GCS URI: {gcs_uri}")
        return None
    
    client = get_gcs_client()
    if client is None:
        logging.error("GCS client not available")
        return None
    
    try:
        # Normalizar URI
        uri = str(gcs_uri).strip()
        if uri.startswith('gs:/') and not uri.startswith('gs://'):
            uri = 'gs://' + uri.split(':', 1)[1].lstrip('/')
        
        # Extraer bucket y blob path
        parts = uri.replace('gs://', '').split('/', 1)
        if len(parts) != 2:
            logging.error(f"Invalid GCS URI format: {uri}")
            return None
        
        bucket_name = parts[0]
        blob_path = parts[1]
        
        # Limpiar path
        while '//' in blob_path:
            blob_path = blob_path.replace('//', '/')
        
        # Obtener el blob
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        # Verificar existencia
        if not blob.exists():
            logging.error(f"Blob does not exist: {uri}")
            return None
        
        # Crear directorio temporal
        import tempfile
        import hashlib
        
        tmp_dir = os.path.join(tempfile.gettempdir(), 'gcs_cache')
        os.makedirs(tmp_dir, exist_ok=True)
        
        # Generar nombre único
        file_hash = hashlib.md5(uri.encode()).hexdigest()
        ext = os.path.splitext(blob_path)[1] or '.tmp'
        local_path = os.path.join(tmp_dir, f"{file_hash}{ext}")
        
        # Cache: si ya existe, retornarlo
        if os.path.exists(local_path):
            logging.debug(f"Using cached file: {local_path}")
            return local_path
        
        # Descargar
        blob.download_to_filename(local_path)
        logging.info(f"Downloaded {uri} to {local_path}")
        return local_path
        
    except Exception as e:
        logging.error(f"Failed to download {gcs_uri}: {e}")
        return None


def get_image_local_path(gcs_uri: str) -> str:
    """Download a gs:// URI to a temp file and return the local path.

    Returns None on failure.
    """
    if not isinstance(gcs_uri, str) or not gcs_uri.startswith('gs://'):
        return None

    try:
        # Normalizar URI
        g = str(gcs_uri)
        if g.startswith('gs:/') and not g.startswith('gs://'):
            g = 'gs://' + g.split(':', 1)[1].lstrip('/')
        if g.startswith('gs://'):
            rest = g[5:]
            while '//' in rest:
                rest = rest.replace('//', '/')
            g = 'gs://' + rest.lstrip('/')
        gcs_uri = g
    except Exception:
        pass

    try:
        local = download_gcs_uri_to_tmp(gcs_uri)
        return local
    except Exception as e:
        logging.error('Failed to download %s: %s', gcs_uri, str(e))
        return None


def get_image_data_uri(gcs_uri: str) -> str:
    """Return a data URI (data:<mime>;base64,...) for the image at `gcs_uri`.

    Downloads the blob to a temp file and converts it.
    Returns None on failure.
    """
    local = get_image_local_path(gcs_uri)
    if not local or not os.path.exists(local):
        return None
    try:
        mime = mimetypes.guess_type(local)[0] or 'image/jpeg'
        with open(local, 'rb') as f:
            data = f.read()
        b64 = base64.b64encode(data).decode('ascii')
        return f"data:{mime};base64,{b64}"
    except Exception:
        logging.exception('Failed to build data URI for %s', gcs_uri)
        return None


def clear_gcs_cache():
    """Limpia el cache de archivos descargados de GCS"""
    import tempfile
    import shutil
    
    tmp_dir = os.path.join(tempfile.gettempdir(), 'gcs_cache')
    if os.path.exists(tmp_dir):
        try:
            shutil.rmtree(tmp_dir)
            logging.info("GCS cache cleared")
        except Exception as e:
            logging.error(f"Failed to clear GCS cache: {e}")