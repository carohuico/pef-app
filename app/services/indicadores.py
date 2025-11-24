from services.queries.q_model import GET_INDICADORES, GET_INDICADORES_POR_IDS
from services.db import fetch_df

import json
import os
import tempfile
import logging
from datetime import datetime
from typing import List, Dict, Optional

# external libs
try:
    from google.cloud import storage
except Exception:
    storage = None

try:
    import requests
except Exception:
    requests = None

import streamlit as st


# Cached loader for indicadores by ids_csv
@st.cache_data(ttl=300, max_entries=256)
def load_indicadores_por_ids(ids_csv: str):
    return fetch_df(GET_INDICADORES_POR_IDS, {"ids_csv": ids_csv})


def _get_storage_client_from_secrets() -> 'storage.Client':
    """Create a google.storage client from service-account JSON placed in:
    - env `GCP_SA_KEY_JSON` (string JSON), or
    - `st.secrets['GCP_SA_KEY_JSON']`, or
    - any secret dict that looks like a service account.

    Raises RuntimeError when no usable credentials found.
    """
    if storage is None:
        raise RuntimeError("google-cloud-storage package not available")

    sa_json = os.environ.get('GCP_SA_KEY_JSON')
    if not sa_json:
        try:
            if isinstance(st.secrets, dict) and 'GCP_SA_KEY_JSON' in st.secrets:
                sa_json = st.secrets.get('GCP_SA_KEY_JSON')
            else:
                for k, v in st.secrets.items():
                    if isinstance(v, dict) and (v.get('type') == 'service_account' or 'private_key' in v):
                        sa_json = json.dumps(v)
                        break
        except Exception:
            sa_json = None

    parsed = None
    if sa_json:
        try:
            if isinstance(sa_json, str):
                parsed = json.loads(sa_json)
            elif isinstance(sa_json, dict):
                parsed = sa_json
        except Exception:
            try:
                repaired = sa_json.replace('\\n', '\n')
                parsed = json.loads(repaired)
            except Exception:
                parsed = None

    if parsed is None:
        raise RuntimeError("No GCP service account JSON found in 'GCP_SA_KEY_JSON' (env) or Streamlit secrets")

    try:
        # Normalize private_key newlines if they were escaped (common when storing JSON in env/secrets)
        try:
            pk = parsed.get('private_key')
            if isinstance(pk, str) and "\\n" in pk:
                parsed = dict(parsed)
                parsed['private_key'] = pk.replace('\\n', '\n')
        except Exception:
            # if normalization fails, continue and let from_service_account_info raise
            pass

        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_info(parsed)

        # Quick proactive refresh test to surface signature/invalid-key errors early.
        try:
            from google.auth.transport.requests import Request
            try:
                creds.refresh(Request())
            except Exception as e:
                # Log a safe debug message with key id (do NOT log private_key)
                logging.exception(
                    "Service account credential refresh failed for private_key_id=%s: %s",
                    parsed.get('private_key_id'), str(e)
                )
                raise
        except Exception:
            # If the transport package isn't available or refresh fails, we still proceed
            # to create the storage client and let the caller observe runtime errors.
            pass

        client = storage.Client(credentials=creds, project=parsed.get('project_id'))
        return client
    except Exception:
        logging.exception("Failed to create storage.Client from provided service account")
        raise


def find_and_download_latest_for_id(id_evaluado: int, bucket_name: str = 'bucket-pbll') -> str:
    """List objects under `pruebas/{id_evaluado}/` and download the most recently-updated blob to /tmp.

    Returns the local file path. Raises FileNotFoundError if no blobs found.
    """
    if storage is None:
        raise RuntimeError("google-cloud-storage package not available")

    try:
        client = _get_storage_client_from_secrets()
    except Exception:
        client = storage.Client()

    prefix = f"pruebas/{id_evaluado}/"
    blobs = list(client.list_blobs(bucket_name, prefix=prefix))
    if not blobs:
        raise FileNotFoundError(f"No blobs found under gs://{bucket_name}/{prefix}")

    # choose the most recently-updated blob
    blobs_sorted = sorted(blobs, key=lambda b: b.updated or datetime.min, reverse=True)
    chosen = blobs_sorted[0]
    local_path = os.path.join(tempfile.gettempdir(), os.path.basename(chosen.name))
    chosen.download_to_filename(local_path)
    return local_path


def download_gcs_uri_to_tmp(gcs_uri: str) -> str:
    """Download a gs://bucket/path into /tmp and return local path."""
    if not gcs_uri.startswith('gs://'):
        raise ValueError("gcs_uri must start with 'gs://'")
    if storage is None:
        raise RuntimeError("google-cloud-storage package not available")

    parts = gcs_uri[5:].split('/', 1)
    bucket_name = parts[0]
    blob_path = parts[1] if len(parts) > 1 else ''

    try:
        client = _get_storage_client_from_secrets()
    except Exception:
        client = storage.Client()

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    local_path = os.path.join(tempfile.gettempdir(), os.path.basename(blob_path))
    blob.download_to_filename(local_path)
    return local_path


@st.cache_data(ttl=60)
def simular_resultado(image_name_or_id) -> List[Dict]:
    """Call /predict on the Cloud Run model using a chosen local image.

    Selection priority for the image sent to the model:
      1. `st.session_state['uploaded_file']` if present (uploaded in UI)
      2. newest blob under `pruebas/{id_evaluado}/` when `id_evaluado` is known
      3. `image_name_or_id` interpreted as a local file path

    After receiving the response, prefer `archivo.ruta_gcs` from the model metadata
    to download an annotated preview image (saved to `/tmp/pef_img.jpg`).
    Returns a list of indicadores enriched from the DB.
    """
    if requests is None:
        raise RuntimeError("The 'requests' package is required. Install with: pip install requests")
    if storage is None:
        raise RuntimeError("The 'google-cloud-storage' package is required. Install with: pip install google-cloud-storage")

    # determine id_evaluado
    id_evaluado: Optional[int] = None
    try:
        id_evaluado = int(image_name_or_id)
    except Exception:
        try:
            parts = str(image_name_or_id).split('_')
            id_evaluado = int(parts[0])
        except Exception:
            id_evaluado = None

    # If still unknown, try session state (UI may have set it)
    if id_evaluado is None:
        try:
            sid = st.session_state.get('id_evaluado')
            if sid is not None:
                id_evaluado = int(sid)
        except Exception:
            id_evaluado = None

    if id_evaluado is None:
        raise RuntimeError("El endpoint de inferencia requiere 'id_evaluado'. Establece 'st.session_state[\'id_evaluado\']' o pasa el id como argumento.")

    tmp_dir = tempfile.gettempdir()
    tmp_send = os.path.join(tmp_dir, "pef_img_send.jpg")
    tmp_preview = os.path.join(tmp_dir, "pef_img.jpg")

    # 1) uploaded file
    uploaded = None
    try:
        uploaded = st.session_state.get('uploaded_file')
    except Exception:
        uploaded = None

    used_uploaded = False
    if uploaded is not None:
        with open(tmp_send, 'wb') as f:
            f.write(uploaded.getbuffer())
        used_uploaded = True
    else:
        # 2) try download newest from GCS if id present
        if id_evaluado is not None:
            try:
                downloaded = find_and_download_latest_for_id(id_evaluado)
                # copy to tmp_send (or reuse path)
                try:
                    with open(downloaded, 'rb') as r, open(tmp_send, 'wb') as w:
                        w.write(r.read())
                except Exception:
                    tmp_send = downloaded
            except FileNotFoundError:
                # 3) fallback: local path
                if os.path.exists(str(image_name_or_id)):
                    tmp_send = str(image_name_or_id)
                else:
                    logging.warning(f"No source image found for id {id_evaluado}")
                    return []
        else:
            if os.path.exists(str(image_name_or_id)):
                tmp_send = str(image_name_or_id)
            else:
                logging.warning("No uploaded file, no id_evaluado and image_name_or_id is not a local path")
                return []

    # call inference
    endpoint = "https://pef-model-326047181104.us-central1.run.app/predict"
    params = {}
    if id_evaluado is not None:
        params['id_evaluado'] = int(id_evaluado)

    import mimetypes
    mime_type = mimetypes.guess_type(tmp_send)[0] or 'application/octet-stream'
    try:
        with open(tmp_send, 'rb') as f:
            files = {"file": (os.path.basename(tmp_send), f, mime_type)}
            resp = requests.post(endpoint, params=params, files=files, timeout=60)
    except Exception:
        logging.exception("Error sending request to inference endpoint")
        raise

    if not resp.ok:
        body = None
        try:
            body = resp.text
        except Exception:
            body = '<unable to read body>'
        err_msg = f"Inference endpoint returned {resp.status_code}: {body}"
        logging.error(err_msg)
        raise RuntimeError(err_msg)

    try:
        data = resp.json()
    except Exception:
        logging.exception("Failed to parse JSON from inference response")
        raise

    if not data:
        return []

    principal = None
    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict) and (entry.get('detections') is not None or entry.get('archivo') is not None):
                principal = entry
                break
        if principal is None:
            for entry in data:
                if isinstance(entry, dict):
                    principal = entry
                    break
    elif isinstance(data, dict):
        principal = data

    if principal is None:
        return []

    # prefer archivo.ruta_gcs for preview if present
    archivo = principal.get('archivo') or {}
    ruta_gcs = archivo.get('ruta_gcs') if isinstance(archivo, dict) else None
    if ruta_gcs:
        try:
            preview_local = download_gcs_uri_to_tmp(ruta_gcs)
            try:
                with open(preview_local, 'rb') as r, open(tmp_preview, 'wb') as w:
                    w.write(r.read())
            except Exception:
                try:
                    os.replace(preview_local, tmp_preview)
                except Exception:
                    pass
        except Exception:
            logging.exception("Failed to download preview from archivo.ruta_gcs")
        # expose the GCS path to the app UI so the caller can persist it if needed
        try:
            st.session_state['last_ruta_gcs'] = ruta_gcs
            st.session_state['last_preview_local'] = tmp_preview
        except Exception:
            pass
    else:
        # fallback: make preview from the image we sent
        try:
            if used_uploaded:
                with open(tmp_send, 'rb') as r, open(tmp_preview, 'wb') as w:
                    w.write(r.read())
            elif id_evaluado is not None:
                try:
                    preview_local = find_and_download_latest_for_id(id_evaluado)
                    with open(preview_local, 'rb') as r, open(tmp_preview, 'wb') as w:
                        w.write(r.read())
                except Exception:
                    pass
        except Exception:
            pass

    detections = principal.get('detections', []) or []
    indicadores: List[Dict] = []
    for det in detections:
        ids = det.get('indicator_ids') or det.get('indicator_id') or []
        confianza = det.get('confidence_base') or det.get('confidence') or 0.0
        bbox = det.get('bbox_original') or det.get('bbox') or det.get('bbox_xyxy') or [0, 0, 0, 0]
        if not isinstance(ids, list):
            try:
                ids = [int(ids)]
            except Exception:
                ids = []
        for id_ind in ids:
            try:
                indicadores.append({
                    'id_indicador': int(id_ind),
                    'confianza': float(confianza),
                    'x_min': int(bbox[0]) if len(bbox) > 0 else 0,
                    'y_min': int(bbox[1]) if len(bbox) > 1 else 0,
                    'x_max': int(bbox[2]) if len(bbox) > 2 else 0,
                    'y_max': int(bbox[3]) if len(bbox) > 3 else 0,
                })
            except Exception:
                continue

    if not indicadores:
        return []

    ids_list = [p['id_indicador'] for p in indicadores]
    ids_csv = ','.join(str(i) for i in ids_list)
    df = load_indicadores_por_ids(ids_csv)
    id_map = {}
    if df is not None and not df.empty:
        for _, row in df.iterrows():
            try:
                id_map[int(row.get('id_indicador'))] = (row.get('nombre', ''), row.get('significado', ''))
            except Exception:
                continue

    resultados: List[Dict] = []
    for p in indicadores:
        iid = p['id_indicador']
        nombre, significado = id_map.get(iid, ('', ''))
        resultados.append({
            'id_indicador': iid,
            'nombre': nombre,
            'significado': significado,
            'confianza': p.get('confianza', 0.0),
            'x_min': p.get('x_min', 0),
            'x_max': p.get('x_max', 0),
            'y_min': p.get('y_min', 0),
            'y_max': p.get('y_max', 0),
        })

    return resultados
