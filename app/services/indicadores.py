from services.queries.q_model import GET_INDICADORES, GET_INDICADORES_POR_IDS
from services.db import fetch_df
import json

def simular_resultado(image_name: str) -> list:
    """Lee el JSON de metadata con múltiples imágenes, busca la entrada cuya
    `image_filename` coincida con `image_name` (exacto, con normalización mínima)
    y extrae [id, confianza, bbox] para completar nombre/significado desde la BD.

    Retorna lista de dicts con keys:
      id_indicador, nombre, significado, confianza, x_min, x_max, y_min, y_max
    """
    baseJSON = r"C:/Users/Usuario/Desktop/9no/PEF/pef-app/app/components/uploads/udem/metadata.json"

    indicadores = []
    # parsear el json para obtener id, confianza y bbox de la entrada que coincida
    path = baseJSON
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

        target_entry = None
        try:
            from pathlib import Path as _P
            image_basename = _P(image_name).name
        except Exception:
            image_basename = image_name

        # try exact match against image_filename
        if isinstance(data, list):
            for entry in data:
                if not isinstance(entry, dict):
                    continue
                fname = entry.get('image_filename')
                if fname == image_basename or fname == image_name:
                    target_entry = entry
                    break
        elif isinstance(data, dict):
            target_entry = data

        if target_entry is None:
            candidates = [image_basename, image_basename + '.jpeg', image_basename + '.jpg']
            if '.' in image_basename:
                candidates = [image_basename]
            if isinstance(data, list):
                for entry in data:
                    fname = entry.get('image_filename')
                    if fname in candidates:
                        target_entry = entry
                        break

        if target_entry is None:
            print(f"No se encontró entrada en metadata.json para image_name='{image_name}'")
            return []

        detections = target_entry.get('detections', [])
        for det in detections:
            ids = det.get('indicator_ids', [])
            confianza = det.get('confidence_base', 0.0)
            bbox = det.get('bbox_original', [0, 0, 0, 0])  # [x_min, y_min, x_max, y_max]
            for id_indicador in ids:
                indicadores.append({
                    'id_indicador': int(id_indicador),
                    'confianza': float(confianza),
                    'x_min': int(bbox[0]),
                    'y_min': int(bbox[1]),
                    'x_max': int(bbox[2]),
                    'y_max': int(bbox[3])
                })
    if not indicadores:
        return []
    # consultar la BD por los ids y construir un mapa id -> (nombre, descripcion)
    ids = [item['id_indicador'] for item in indicadores]
    ids_csv = ','.join(str(i) for i in ids)
    df = fetch_df(GET_INDICADORES_POR_IDS, {"ids_csv": ids_csv})
    id_map = {}
    if df is not None and not df.empty:
        for _, row in df.iterrows():
            id_indicador = row.get('id_indicador')
            nombre = row.get('nombre')
            significado = row.get('significado')
            try:
                id_map[int(id_indicador)] = (nombre, significado)
            except Exception:
                continue
    resultados = []
    for p in indicadores:
        iid = p['id_indicador']
        meta = id_map.get(iid, ('', ''))
        resultados.append({
            'id_indicador': iid,
            'nombre': meta[0],
            'significado': meta[1],
            'confianza': p.get('confianza', 0.0),
            'x_min': p.get('x_min', 0),
            'x_max': p.get('x_max', 0),
            'y_min': p.get('y_min', 0),
            'y_max': p.get('y_max', 0)
        })   
    return resultados
