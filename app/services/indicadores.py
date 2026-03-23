from services.queries.q_model import GET_INDICADORES, GET_INDICADORES_POR_IDS
from services.db import fetch_df

import json
import os
import tempfile
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse

# external libs
try:
    import requests
except Exception:
    requests = None

import streamlit as st
import threading
import time


# Cached loader for indicadores by ids_csv
@st.cache_data(ttl=300, max_entries=256)
def load_indicadores_por_ids(ids_csv: str):
    return fetch_df(GET_INDICADORES_POR_IDS, {"ids_csv": ids_csv})


def download_image_source_to_tmp(image_source: str) -> str:
    """Resolve a preview source into a local temp file path.

    Supports:
    - Hostinger/public URLs (http/https)
    - Hostinger relative paths like /static/pruebas/... (using HOSTINGER_BASE_URL)
    - Local filesystem paths
    """
    if not image_source:
        raise ValueError("Empty image source")

    src = str(image_source).strip().strip("\"'")
    if not src:
        raise ValueError("Empty image source")

    # Relative hostinger path (e.g. /static/pruebas/...) -> absolute URL
    if src.startswith('/') and not src.startswith('//'):
        hostinger_base = os.environ.get("HOSTINGER_BASE_URL", "http://187.124.151.106:8080")
        src = f"{hostinger_base.rstrip('/')}{src}"

    # HTTP(S): download to temp
    if src.startswith("http://") or src.startswith("https://"):
        if requests is None:
            raise RuntimeError("The 'requests' package is required to download http(s) images")

        parsed = urlparse(src)
        ext = os.path.splitext(parsed.path)[1] or '.jpg'
        fd, local_path = tempfile.mkstemp(prefix='pef_preview_', suffix=ext)
        os.close(fd)

        try:
            resp = requests.get(src, timeout=60)
            resp.raise_for_status()
            with open(local_path, 'wb') as f:
                f.write(resp.content)
            return local_path
        except Exception:
            try:
                os.remove(local_path)
            except Exception:
                pass
            raise

    # Local file path
    if os.path.exists(src):
        return src

    raise FileNotFoundError(f"Unsupported or missing image source: {src}")


def simular_resultado(image_name_or_id, show_overlay: bool = False) -> List[Dict]:
    """Call /predict on the Cloud Run model using a chosen local image.

    Selection priority for the image sent to the model:
      1. `st.session_state['uploaded_file']` if present (uploaded in UI)
            2. `image_name_or_id` interpreted as URL o local file path

        After receiving the response, prefer `archivo.ruta_imagen` from the model metadata
    to download an annotated preview image (saved to `/tmp/pef_img.jpg`).
    Returns a list of indicadores enriched from the DB.
    """
    if requests is None:
        raise RuntimeError("The 'requests' package is required. Install with: pip install requests")

    id_evaluado: Optional[int] = None
    try:
        id_evaluado = int(image_name_or_id)
    except Exception:
        try:
            parts = str(image_name_or_id).split('_')
            id_evaluado = int(parts[0])
        except Exception:
            id_evaluado = None

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
        resolved_source = None
        source_candidate = str(image_name_or_id)
        try:
            resolved_source = download_image_source_to_tmp(source_candidate)
        except Exception:
            if os.path.exists(source_candidate):
                resolved_source = source_candidate

        if resolved_source is None:
            logging.warning("No source image found for id=%s source=%s", str(id_evaluado), str(image_name_or_id))
            return []

        try:
            with open(resolved_source, 'rb') as r, open(tmp_send, 'wb') as w:
                w.write(r.read())
        except Exception:
            tmp_send = resolved_source


    loading_messages = [
        "Cargando imagen...",
        "Analizando trazos del dibujo...",
        "Detectando indicadores...",
        "Interpretando elementos...",
        "Generando análisis completo...",
    ]

    result_holder = {"done": False, "result": None, "error": None}

    def worker():
        try:
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
                    resp = requests.post(endpoint, params=params, files=files, timeout=120)
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
                result_holder['result'] = []
                return

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
                result_holder['result'] = []
                return

            # Prefer model-provided image path/url for preview if present.
            archivo = principal.get('archivo') or {}
            ruta_imagen = None
            if isinstance(archivo, dict):
                ruta_imagen = archivo.get('ruta_imagen')
            if ruta_imagen:
                try:
                    preview_local = download_image_source_to_tmp(ruta_imagen)
                    try:
                        with open(preview_local, 'rb') as r, open(tmp_preview, 'wb') as w:
                            w.write(r.read())
                    except Exception:
                        try:
                            os.replace(preview_local, tmp_preview)
                        except Exception:
                            pass
                except Exception as e:
                    logging.warning("Failed to download preview from archivo.ruta_imagen: %s", str(e))
                try:
                    st.session_state['last_ruta_imagen'] = ruta_imagen
                    st.session_state['last_preview_local'] = tmp_preview
                except Exception:
                    pass
            else:
                try:
                    if used_uploaded:
                        with open(tmp_send, 'rb') as r, open(tmp_preview, 'wb') as w:
                            w.write(r.read())
                except Exception:
                    pass

            detections = principal.get('detections', []) or []
            indicadores_local: List[Dict] = []
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
                        indicadores_local.append({
                            'id_indicador': int(id_ind),
                            'confianza': float(confianza),
                            'x_min': int(bbox[0]) if len(bbox) > 0 else 0,
                            'y_min': int(bbox[1]) if len(bbox) > 1 else 0,
                            'x_max': int(bbox[2]) if len(bbox) > 2 else 0,
                            'y_max': int(bbox[3]) if len(bbox) > 3 else 0,
                            'ruta_imagen': ruta_imagen,
                        })
                    except Exception:
                        continue

            if not indicadores_local:
                result_holder['result'] = []
                return

            ids_list = [p['id_indicador'] for p in indicadores_local]
            ids_csv = ','.join(str(i) for i in ids_list)
            df = load_indicadores_por_ids(ids_csv)
            id_map = {}
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    try:
                        iid = int(row.get('id_indicador'))
                    except Exception:
                        continue
                    try:
                        id_map[iid] = {
                            'nombre': row.get('nombre', '') if 'nombre' in row.index else row.get('nombre', ''),
                            'significado': row.get('significado', '') if 'significado' in row.index else row.get('significado', ''),
                            'id_categoria': row.get('id_categoria') if 'id_categoria' in row.index else None,
                            'categoria_nombre': row.get('categoria_nombre') if 'categoria_nombre' in row.index else None,
                        }
                    except Exception:
                        id_map[iid] = {
                            'nombre': row.get('nombre', ''),
                            'significado': row.get('significado', ''),
                            'id_categoria': None,
                            'categoria_nombre': None,
                        }

            resultados_local: List[Dict] = []
            for p in indicadores_local:
                iid = p['id_indicador']
                meta = id_map.get(iid, {}) if isinstance(id_map, dict) else {}
                nombre = meta.get('nombre') if isinstance(meta, dict) else ''
                significado = meta.get('significado') if isinstance(meta, dict) else ''
                id_categoria = meta.get('id_categoria') if isinstance(meta, dict) else None
                categoria_nombre = meta.get('categoria_nombre') if isinstance(meta, dict) else None
                resultados_local.append({
                    'id_indicador': iid,
                    'nombre': nombre,
                    'significado': significado,
                    'confianza': p.get('confianza', 0.0),
                    'x_min': p.get('x_min', 0),
                    'x_max': p.get('x_max', 0),
                    'y_min': p.get('y_min', 0),
                    'y_max': p.get('y_max', 0),
                    'ruta_imagen': p.get('ruta_imagen', None),
                    'id_categoria': id_categoria,
                    'categoria_nombre': categoria_nombre,
                })

            # Business rule: if indicator 16 is present AND any of indicators {8,9,10,11,12,13} present,
            # then add indicator 61 to the results (with its name, significado and id_categoria)
            try:
                present_ids = {r.get('id_indicador') for r in resultados_local}
                trigger_set = {8, 9, 10, 11, 12, 13}
                if 16 in present_ids and (present_ids & trigger_set):
                    # Fetch indicator 61 details
                    try:
                        df61 = load_indicadores_por_ids('61')
                        if df61 is not None and not df61.empty:
                            row = df61.iloc[0]
                            try:
                                nombre61 = row.get('nombre', '')
                            except Exception:
                                nombre61 = ''
                            try:
                                significado61 = row.get('significado', '')
                            except Exception:
                                significado61 = ''
                            try:
                                id_categoria61 = row.get('id_categoria') if 'id_categoria' in row.index else None
                            except Exception:
                                id_categoria61 = None
                            # Append if not already present
                            if 61 not in present_ids:
                                resultados_local.append({
                                    'id_indicador': 61,
                                    'nombre': nombre61,
                                    'significado': significado61,
                                    'confianza': 0.0,
                                    'x_min': 0,
                                    'x_max': 0,
                                    'y_min': 0,
                                    'y_max': 0,
                                    'ruta_imagen': None,
                                    'id_categoria': id_categoria61,
                                })
                    except Exception:
                        # Ignore failures to fetch the extra indicator
                        pass
            except Exception:
                pass

            result_holder['result'] = resultados_local
        except Exception as e:
            # Report the error concisely to avoid noisy stack traces in normal runs
            logging.error("Error in simular_resultado worker: %s", str(e))
            result_holder['error'] = e
        finally:
            result_holder['done'] = True

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    overlay_ph = st.empty()

    # rotate messages once while the worker is running; if worker finishes earlier, stop
    for msg in loading_messages:
        if result_holder.get('done'):
            break
        try:
            if show_overlay:
                overlay_html = f"""
                <div style="width:100%;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,0.96);padding:1rem;border-radius:8px;">
                    <div style="max-width:900px;width:100%;text-align:center;">
                        <div style="font-family: Poppins, sans-serif; font-weight:600; font-size:1.05rem; color:#222;margin-bottom:12px;">{msg}</div>
                        <style>
                            @keyframes inlineLoaderJump {{ 0%,60%,100% {{ transform: translateY(0); }} 30% {{ transform: translateY(-8px); }} }}
                            .inline-loader-dots {{ display:flex; gap:10px; justify-content:center; align-items:center; margin-top:6px; }}
                            .inline-loader-dots span {{ width:12px; height:12px; background:#FFC107; border-radius:50%; display:inline-block; animation:inlineLoaderJump 0.8s infinite ease-in-out; }}
                            .inline-loader-dots span:nth-child(2) {{ animation-delay: 0.15s; }}
                            .inline-loader-dots span:nth-child(3) {{ animation-delay: 0.3s; }}
                        </style>
                        <div class="inline-loader-dots">
                            <span></span><span></span><span></span>
                        </div>
                    </div>
                </div>
                """
                overlay_ph.markdown(overlay_html, unsafe_allow_html=True)
            else:
                overlay_ph.info(msg)
        except Exception:
            try:
                overlay_ph.markdown(f"**{msg}**")
            except Exception:
                pass
        # wait up to 10 seconds but exit early if worker finishes
        waited = 0.0
        while waited < 10.0 and not result_holder.get('done'):
            time.sleep(0.25)
            waited += 0.25

    if not result_holder.get('done'):
        try:
            if show_overlay:
                overlay_html = f"""
                <div style="width:100%;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,0.96);padding:1rem;border-radius:8px;">
                    <div style="max-width:900px;width:100%;text-align:center;">
                        <div style="font-family: Poppins, sans-serif; font-weight:600; font-size:1.05rem; color:#222;margin-bottom:12px;">{loading_messages[-1]}</div>
                        <style>
                            @keyframes inlineLoaderJump {{ 0%,60%,100% {{ transform: translateY(0); }} 30% {{ transform: translateY(-8px); }} }}
                            .inline-loader-dots {{ display:flex; gap:10px; justify-content:center; align-items:center; margin-top:6px; }}
                            .inline-loader-dots span {{ width:12px; height:12px; background:#FFC107; border-radius:50%; display:inline-block; animation:inlineLoaderJump 0.8s infinite ease-in-out; }}
                            .inline-loader-dots span:nth-child(2) {{ animation-delay: 0.15s; }}
                            .inline-loader-dots span:nth-child(3) {{ animation-delay: 0.3s; }}
                        </style>
                        <div class="inline-loader-dots">
                            <span></span><span></span><span></span>
                        </div>
                    </div>
                </div>
                """
                overlay_ph.markdown(overlay_html, unsafe_allow_html=True)
            else:
                overlay_ph.info(loading_messages[-1] + " (finalizando...)")
        except Exception:
            try:
                overlay_ph.markdown(f"**{loading_messages[-1]} (finalizando...)**")
            except Exception:
                pass

    # poll until done (avoid busy loop)
    while not result_holder.get('done'):
        time.sleep(0.25)

    # clean placeholder
    try:
        overlay_ph.empty()
    except Exception:
        pass

    if result_holder.get('error') is not None:
        raise result_holder.get('error')

    return result_holder.get('result') or []
