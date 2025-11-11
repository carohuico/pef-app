from services.queries.q_model import GET_INDICADORES, GET_INDICADORES_POR_IDS
from services.db import get_engine
from sqlalchemy import text
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
    print(f"Consultando indicadores para ids: {ids}")  
    ids_csv = ','.join(str(i) for i in ids)
    #fetch_df
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(GET_INDICADORES_POR_IDS), {"ids_csv": ids_csv})
        rows = result.fetchall()
        print(f"Filas obtenidas de BD: {len(rows)}")
        id_map = {}
        for row in rows:
            id_indicador = row['id_indicador']
            nombre = row['nombre']
            significado = row['significado']
            id_map[int(id_indicador)] = (nombre, significado)
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
    print(f"Resultados preparados: {resultados[0]}")
    return resultados

# def simular_resultado(txt: str) -> list:
#     """Lee el TXT de predicciones, extrae [id, confianza, bbox] y completa nombre/significado desde la BD.

#     Retorna lista de dicts con keys:
#       id_indicador, nombre, significado, confianza, x_min, x_max, y_min, y_max
#     """
#     base = "C:/Users/Usuario/Desktop/9no/PEF/pef-app/app/components/uploads/udem/"
#     path = base + txt

#     indicadores = []
#     # parsear el txt para obtener id, confianza y bbox
#     with open(path, 'r', encoding='utf-8') as f:
#         lines = f.readlines()
#         current = {}
#         for line in lines:
#             line = line.strip()
#             if line.startswith('['):
#                 if current:
#                     indicadores.append(current)
#                     current = {}
#             elif line.startswith('Etiqueta Base:'):
#                 parts = line.split(':', 1)[1].strip().rsplit('(', 1)
#                 # confianza puede venir entre paréntesis
#                 nombre = parts[0].strip()
#                 confianza = parts[1].replace(')', '').strip() if len(parts) > 1 else '0'
#                 # confianza la dejamos pero la usaremos desde la línea
#                 try:
#                     current['confianza'] = float(confianza)
#                 except Exception:
#                     current['confianza'] = 0.0
#             elif line.startswith('Id:'):
#                 id_indicador = line.split(':', 1)[1].strip()
#                 try:
#                     current['id_indicador'] = int(id_indicador)
#                 except Exception:
#                     current['id_indicador'] = None
#             elif line.startswith('BBox:'):
#                 bbox_part = line.split(':', 1)[1].strip().strip('[]')
#                 coords = [c.strip() for c in bbox_part.split(',') if ':' in c]
#                 for coord in coords:
#                     key, value = coord.split(':')
#                     k = key.strip().lower()
#                     v = value.strip()
#                     try:
#                         current[k] = int(v)
#                     except Exception:
#                         try:
#                             current[k] = int(float(v))
#                         except Exception:
#                             current[k] = 0
#         if current:
#             indicadores.append(current)

#     # Normalizar bbox keys y preparar lista de ids
#     parsed = []
#     ids = []
#     for item in indicadores:
#         id_val = item.get('id_indicador')
#         if id_val is None:
#             continue
#         ids.append(int(id_val))

#         # mapear posibles nombres de keys
#         if 'x1' in item or 'y1' in item or 'x2' in item or 'y2' in item:
#             x_min = item.get('x1', 0)
#             y_min = item.get('y1', 0)
#             x_max = item.get('x2', 0)
#             y_max = item.get('y2', 0)
#         else:
#             x_min = item.get('x_min', 0)
#             y_min = item.get('y_min', 0)
#             x_max = item.get('x_max', 0)
#             y_max = item.get('y_max', 0)

#         parsed.append({
#             'id_indicador': int(id_val),
#             'confianza': float(item.get('confianza', 0.0)),
#             'x_min': int(x_min),
#             'x_max': int(x_max),
#             'y_min': int(y_min),
#             'y_max': int(y_max)
#         })

#     if not ids:
#         return []

#     # consultar la BD por los ids y construir un mapa id -> (nombre, descripcion)
#     print(f"Consultando indicadores para ids: {ids}")
#     #[15, 3, 9, 32]
#     ids_csv = ','.join(str(i) for i in ids)
#     engine = get_engine()
#     with engine.connect() as conn:
#         result = conn.execute(text(GET_INDICADORES_POR_IDS), {"ids_csv": ids_csv})
#         rows = result.fetchall()
#         print(f"Filas obtenidas de BD: {len(rows)}")
#         id_map = {}
#         for row in rows:
#             id_indicador = row['id_indicador']
#             nombre = row['nombre']
#             significado = row['significado']
#             id_map[int(id_indicador)] = (nombre, significado)
#     resultados = []
#     for p in parsed:
#         iid = p['id_indicador']
#         meta = id_map.get(iid, ('', ''))
#         resultados.append({
#             'id_indicador': iid,
#             'nombre': meta[0],
#             'significado': meta[1],
#             'confianza': p.get('confianza', 0.0),
#             'x_min': p.get('x_min', 0),
#             'x_max': p.get('x_max', 0),
#             'y_min': p.get('y_min', 0),
#             'y_max': p.get('y_max', 0)
#         })
#     return resultados

