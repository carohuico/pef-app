from PIL import Image, ImageDraw, ImageFont, ImageOps
import os

# Enable debug prints when BBOX_DEBUG=1 in environment
BBOX_DEBUG = os.environ.get('BBOX_DEBUG', '0') in ('1', 'true', 'True')


def _to_pixel_coords(box: dict, width: int, height: int) -> tuple:
    """Convert a box dict to pixel coords (x_min, y_min, x_max, y_max).

    Accepts coordinates in three common formats:
    - normalized floats in [0,1]
    - percentages in [0,100]
    - absolute pixel coordinates (large ints)
    The function heuristically detects the format based on values.
    """
    x_min = box.get('x_min', 0)
    x_max = box.get('x_max', 0)
    y_min = box.get('y_min', 0)
    y_max = box.get('y_max', 0)

    # Helper to detect format
    def is_number(v):
        try:
            return float(v)
        except Exception:
            return None

    vals = [is_number(v) for v in (x_min, x_max, y_min, y_max)]
    vals = [v for v in vals if v is not None]
    if not vals:
        return 0, 0, 0, 0

    max_val = max(vals)
    min_val = min(vals)

    # If values are a mix (some <=1 and some >1), treat per-value:
    # - values <= 1 -> normalized (fraction of width/height)
    # - values > 1 and <=100 -> percentage
    # - values > 100 -> pixels
    if any(v <= 1.0 for v in vals) and any(v > 1.0 for v in vals):
        def to_px(val, is_x=True):
            if val is None:
                return 0
            try:
                fv = float(val)
            except Exception:
                return 0
            if fv <= 1.0:
                return int(fv * (width if is_x else height))
            if fv <= 100.0:
                return int(fv * (width if is_x else height) / 100.0)
            return int(fv)

        x_min_px = to_px(x_min, is_x=True)
        x_max_px = to_px(x_max, is_x=True)
        y_min_px = to_px(y_min, is_x=False)
        y_max_px = to_px(y_max, is_x=False)
        return x_min_px, y_min_px, x_max_px, y_max_px

    # normalized floats 0..1 (all values small)
    if max_val <= 1.0:
        x_min_px = int(float(x_min) * width)
        x_max_px = int(float(x_max) * width)
        y_min_px = int(float(y_min) * height)
        y_max_px = int(float(y_max) * height)
        return x_min_px, y_min_px, x_max_px, y_max_px

    # percentages 0..100
    if max_val <= 100.0:
        x_min_px = int(float(x_min) * width / 100.0)
        x_max_px = int(float(x_max) * width / 100.0)
        y_min_px = int(float(y_min) * height / 100.0)
        y_max_px = int(float(y_max) * height / 100.0)
        return x_min_px, y_min_px, x_max_px, y_max_px

    # otherwise assume pixel coordinates already
    try:
        return int(float(x_min)), int(float(y_min)), int(float(x_max)), int(float(y_max))
    except Exception:
        return 0, 0, 0, 0


def _convert_bbox_from_meta(bbox, meta_w, meta_h, real_w, real_h):
    """
    Convierte una bbox definida en las dimensiones del modelo/meta
    (por ejemplo 640x640 con letterbox) a coordenadas en la imagen real.

    bbox: [x1,y1,x2,y2]
    meta_w, meta_h: dimensiones del espacio meta (modelo)
    real_w, real_h: dimensiones de la imagen real
    """
    if not meta_w or not meta_h:
        return [int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])]

    x1, y1, x2, y2 = bbox[:4]
    try:
        meta_w = float(meta_w)
        meta_h = float(meta_h)
        real_w = float(real_w)
        real_h = float(real_h)
    except Exception:
        return [int(x1), int(y1), int(x2), int(y2)]

    # caso exacto
    if int(meta_w) == int(real_w) and int(meta_h) == int(real_h):
        return [int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))]

    # detectar letterbox: meta es cuadrado (modelo) y difiere del tamaño real
    if int(meta_w) == int(meta_h) and (int(meta_w) != int(real_w) or int(meta_h) != int(real_h)):
        model_w = meta_w
        model_h = meta_h
        gain = min(model_w / real_w, model_h / real_h)
        pad_x = (model_w - real_w * gain) / 2.0
        pad_y = (model_h - real_h * gain) / 2.0
        # quitar padding y dividir por gain
        rx1 = (float(x1) - pad_x) / gain
        ry1 = (float(y1) - pad_y) / gain
        rx2 = (float(x2) - pad_x) / gain
        ry2 = (float(y2) - pad_y) / gain
        # clamp
        rx1 = max(0, min(real_w, rx1))
        ry1 = max(0, min(real_h, ry1))
        rx2 = max(0, min(real_w, rx2))
        ry2 = max(0, min(real_h, ry2))
        return [int(round(rx1)), int(round(ry1)), int(round(rx2)), int(round(ry2))]

    # fallback: escalado simple (si meta no es cuadrado)
    try:
        sx = real_w / float(meta_w)
        sy = real_h / float(meta_h)
        rx1 = int(round(float(x1) * sx))
        ry1 = int(round(float(y1) * sy))
        rx2 = int(round(float(x2) * sx))
        ry2 = int(round(float(y2) * sy))
        # clamp
        rx1 = max(0, min(int(real_w), rx1))
        ry1 = max(0, min(int(real_h), ry1))
        rx2 = max(0, min(int(real_w), rx2))
        ry2 = max(0, min(int(real_h), ry2))
        return [rx1, ry1, rx2, ry2]
    except Exception:
        return [int(x1), int(y1), int(x2), int(y2)]


def imagen_bboxes(image: Image, boxes: list[dict]) -> Image:
    """Dibuja bounding boxes en una imagen.

    The function is tolerant to several coordinate formats (normalized, percent, pixels).
    """
    # Work on a copy to avoid mutating the original image object unexpectedly
    img = image.convert('RGB').copy()
    # apply EXIF orientation if present
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    draw = ImageDraw.Draw(img)
    # A palette of distinct colors
    colors = ["#FF0000", "#0000FF", "#3AAC3A", "#D6D604", "#A111A1", "#FFA500", "#8B4513", "#1E90FF", "#228B22"]
    width, height = img.size

    def convert_bbox_to_real(bbox, meta_w, meta_h, real_w, real_h):
        # reuse the already implemented helper logic where appropriate
        try:
            return _convert_bbox_from_meta(bbox, meta_w, meta_h, real_w, real_h)
        except Exception:
            return [int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])]

    # Try to load a truetype font, fall back to default
    try:
        font = ImageFont.truetype("arial.ttf", size=14)
    except Exception:
        font = ImageFont.load_default()

    for i, det in enumerate(boxes):
        if BBOX_DEBUG:
            try:
                print(f"[BBOX_DEBUG] image_size={width}x{height} idx={i} det_keys={list(det.keys()) if isinstance(det, dict) else type(det)}")
            except Exception:
                print(f"[BBOX_DEBUG] image_size={width}x{height} idx={i} det={det}")
        # Robust parsing of bbox from detection-like dicts
        def parse_bbox(det):
            # Prefer explicit bbox_original or bbox
            raw = None
            if det is None:
                return None
            if 'bbox_original' in det and det.get('bbox_original'):
                raw = det.get('bbox_original')
            elif 'bbox' in det and det.get('bbox'):
                raw = det.get('bbox')

            meta_w = det.get('meta_w') or det.get('image_width') or det.get('meta_width')
            meta_h = det.get('meta_h') or det.get('image_height') or det.get('meta_height')

            if raw and isinstance(raw, (list, tuple)) and len(raw) >= 4:
                try:
                    vals = [float(v) for v in raw[:4]]
                except Exception:
                    return None

                # If meta dims present, use letterbox-aware conversion
                if meta_w and meta_h:
                    try:
                        return [int(v) for v in _convert_bbox_from_meta(vals, meta_w, meta_h, width, height)]
                    except Exception:
                        pass

                # If values look normalized (<=1), detect whether format is [x1,y1,x2,y2] or [x,y,w,h]
                if all(v <= 1.0 for v in vals):
                    x0, y0, v2, v3 = vals
                    # If meta dims are present, the normalization is likely relative to meta
                    try:
                        mw = float(meta_w) if meta_w is not None else None
                        mh = float(meta_h) if meta_h is not None else None
                    except Exception:
                        mw = mh = None

                    # if v2 < x0 or v3 < y0 assume width/height
                    if v2 < x0 or v3 < y0:
                        if mw and mh:
                            x = int(round(x0 * mw))
                            y = int(round(y0 * mh))
                            w = int(round(v2 * mw))
                            h = int(round(v3 * mh))
                            # convert from model space to real image
                            try:
                                conv = _convert_bbox_from_meta([x, y, x + w, y + h], mw, mh, width, height)
                                return [int(round(c)) for c in conv]
                            except Exception:
                                return [x, y, x + w, y + h]
                        else:
                            x = int(round(x0 * width))
                            y = int(round(y0 * height))
                            w = int(round(v2 * width))
                            h = int(round(v3 * height))
                            return [x, y, x + w, y + h]
                    else:
                        # treat as [x1,y1,x2,y2] normalized
                        if mw and mh:
                            # values are relative to meta dims
                            x1m = vals[0] * mw
                            y1m = vals[1] * mh
                            x2m = vals[2] * mw
                            y2m = vals[3] * mh
                            try:
                                conv = _convert_bbox_from_meta([x1m, y1m, x2m, y2m], mw, mh, width, height)
                                return [int(round(c)) for c in conv]
                            except Exception:
                                return [int(round(x1m)), int(round(y1m)), int(round(x2m)), int(round(y2m))]
                        else:
                            return [int(round(vals[0] * width)), int(round(vals[1] * height)), int(round(vals[2] * width)), int(round(vals[3] * height))]

                # otherwise assume already pixel coords
                try:
                    return [int(round(vals[0])), int(round(vals[1])), int(round(vals[2])), int(round(vals[3]))]
                except Exception:
                    return None

            # fallback: maybe keys x_min/x_max etc are present
            try:
                return _to_pixel_coords(det, width, height)
            except Exception:
                return None

        parsed = parse_bbox(det)
        if BBOX_DEBUG:
            try:
                print(f"[BBOX_DEBUG] raw_bbox_candidate={det.get('bbox_original') or det.get('bbox')} meta_w/meta_h={det.get('meta_w') or det.get('image_width')}/{det.get('meta_h') or det.get('image_height')} parsed={parsed}")
            except Exception:
                print(f"[BBOX_DEBUG] parsed={parsed}")
        if not parsed:
            continue
        x1, y1, x2, y2 = parsed

        # clamp and int cast
        try:
            x1 = max(0, min(width - 1, int(round(x1))))
            y1 = max(0, min(height - 1, int(round(y1))))
            x2 = max(0, min(width - 1, int(round(x2))))
            y2 = max(0, min(height - 1, int(round(y2))))
        except Exception:
            continue

        if x2 <= x1 or y2 <= y1:
            continue

        color = colors[i % len(colors)]

        # draw rectangle (thicker stroke to match extract_and_draw)
        try:
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
        except Exception:
            draw.rectangle([x1, y1, x2, y2], outline=color)

        # draw label similar to extract_and_draw
        label = det.get('base_label_yolo') or det.get('nombre') or det.get('label') or det.get('nombre_indicador')
        conf = det.get('confidence_base') or det.get('confianza') or det.get('confidence')
        if label is None:
            label = ''
        if conf is not None:
            try:
                # if confidence is 0..1, show percent with 1 decimal
                fconf = float(conf)
                if 0.0 <= fconf <= 1.0:
                    label = f"{label} {fconf*100:.1f}%"
                else:
                    label = f"{label} {fconf:.2f}"
            except Exception:
                label = f"{label} {conf}"

        try:
            tb = draw.textbbox((0, 0), str(label), font=font)
            text_w = tb[2] - tb[0]
            text_h = tb[3] - tb[1]
        except Exception:
            try:
                text_w, text_h = font.getsize(str(label))
            except Exception:
                text_w = max(10, len(str(label)) * 6)
                text_h = 12

        text_bg = [x1, max(0, y1 - text_h - 4), x1 + text_w + 4, y1]
        try:
            draw.rectangle(text_bg, fill=color)
        except Exception:
            draw.rectangle(text_bg, fill=(0, 0, 0))

        try:
            draw.text((text_bg[0] + 2, text_bg[1] + 1), str(label), fill=(255, 255, 255), font=font)
        except Exception:
            try:
                draw.text((text_bg[0] + 2, text_bg[1] + 1), str(label), fill="white")
            except Exception:
                pass

    return img