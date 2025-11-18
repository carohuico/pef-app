#!/usr/bin/env python3
"""
Lee `metadata.json`, guarda los indicadores por `image_filename` y dibuja
las bounding boxes encontradas en `bbox_original` sobre la imagen.

Uso:
  python extract_and_draw.py [--metadata METADATA] [--outdir OUTDIR]

El script guarda por cada imagen dos salidas en `OUTDIR` (por defecto la
misma carpeta que `metadata.json`):
  - `<image_filename>_indicators.json` : lista de detecciones con `indicator_ids`
  - `<image_filename>_bboxes.png` : imagen con bounding boxes y etiquetas

Requiere: Pillow (PIL)
  pip install Pillow
"""
from __future__ import annotations

import argparse
import json
import os
from typing import List, Dict, Any

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except Exception:
    raise RuntimeError("Pillow no está instalado. Instálalo con: pip install Pillow")


def load_metadata(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def save_json(obj: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def draw_bboxes_on_image(image_path: str, detections: List[Dict[str, Any]], out_path: str, meta_w: int | None = None, meta_h: int | None = None) -> Dict[str, bool]:
    """Dibuja bounding boxes en la imagen.

    Si `meta_w` y `meta_h` se suministran y difieren del tamaño real de la
    imagen, las cajas se escalan automáticamente.

    Retorna dict: {"drawn": bool, "scaled": bool}
    """
    if not os.path.isfile(image_path):
        return {"drawn": False, "scaled": False}
    im = Image.open(image_path).convert("RGB")
    # aplicar rotación EXIF si existe
    im = ImageOps.exif_transpose(im)
    draw = ImageDraw.Draw(im)
    real_w, real_h = im.size
    scaled_any = False

    def convert_bbox_to_real(bbox, meta_w, meta_h, real_w, real_h):
        """Convierte bbox del espacio metadata/model a coordenadas en la imagen real.

        - Si meta coincide con real: devuelve bbox sin cambios.
        - Si meta es cuadrado (p. ej. modelo 640x640) y difiere del tamaño real,
          asumimos letterbox/padding y deshacemos padding+escala.
        - En el resto de casos hacemos un escalado simple por sx, sy.
        """
        x1, y1, x2, y2 = bbox[:4]
        if not meta_w or not meta_h:
            return [x1, y1, x2, y2]
        # caso exacto
        if meta_w == real_w and meta_h == real_h:
            return [int(x1), int(y1), int(x2), int(y2)]

        # detectar letterbox: meta es cuadrado (modelo) y difiere de real
        if meta_w == meta_h and (meta_w != real_w or meta_h != real_h):
            model_w = float(meta_w)
            model_h = float(meta_h)
            gain = min(model_w / real_w, model_h / real_h)
            pad_x = (model_w - real_w * gain) / 2.0
            pad_y = (model_h - real_h * gain) / 2.0
            # quitar padding y dividir por gain
            rx1 = (x1 - pad_x) / gain
            ry1 = (y1 - pad_y) / gain
            rx2 = (x2 - pad_x) / gain
            ry2 = (y2 - pad_y) / gain
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
            rx1 = int(round(x1 * sx))
            ry1 = int(round(y1 * sy))
            rx2 = int(round(x2 * sx))
            ry2 = int(round(y2 * sy))
            # clamp
            rx1 = max(0, min(real_w, rx1))
            ry1 = max(0, min(real_h, ry1))
            rx2 = max(0, min(real_w, rx2))
            ry2 = max(0, min(real_h, ry2))
            return [rx1, ry1, rx2, ry2]
        except Exception:
            return [int(x1), int(y1), int(x2), int(y2)]

    # Try to load a default truetype font, fallback to load_default
    try:
        font = ImageFont.truetype("arial.ttf", size=14)
    except Exception:
        font = ImageFont.load_default()

    for det in detections:
        bbox = det.get("bbox_original")
        if not bbox or len(bbox) < 4:
            continue
        x1, y1, x2, y2 = bbox[:4]
        # convertir bbox del espacio metadata/model al real
        if meta_w and meta_h:
            new_bbox = convert_bbox_to_real([x1, y1, x2, y2], meta_w, meta_h, real_w, real_h)
            # marcar si hubo escalado (o letterbox) comparando
            if new_bbox != [int(x1), int(y1), int(x2), int(y2)]:
                scaled_any = True
            x1, y1, x2, y2 = new_bbox
        # dibujar rectángulo
        draw.rectangle([x1, y1, x2, y2], outline=(255, 0, 0), width=3)
        # etiqueta: base_label_yolo + confidence
        label = det.get("base_label_yolo", "")
        conf = det.get("confidence_base")
        if conf is not None:
            label = f"{label} {conf:.2f}"
        # dibujar fondo para la etiqueta
        # textsize puede no existir en algunas versiones de Pillow; usar textbbox o font.getsize
        try:
            tb = draw.textbbox((0, 0), label, font=font)
            text_w = tb[2] - tb[0]
            text_h = tb[3] - tb[1]
        except Exception:
            try:
                text_w, text_h = font.getsize(label)
            except Exception:
                text_w = max(10, len(label) * 6)
                text_h = 12
        text_bg = [x1, max(0, y1 - text_h - 4), x1 + text_w + 4, y1]
        draw.rectangle(text_bg, fill=(255, 0, 0))
        draw.text((text_bg[0] + 2, text_bg[1] + 1), label, fill=(255, 255, 255), font=font)

    im.save(out_path)
    return {"drawn": True, "scaled": scaled_any}


def process(metadata_path: str, outdir: str) -> None:
    items = load_metadata(metadata_path)
    os.makedirs(outdir, exist_ok=True)

    summary = []
    for item in items:
        image_filename = item.get("image_filename") or os.path.basename(item.get("image_original_path", ""))
        detections = item.get("detections", [])

        # extraer indicadores: detecciones con indicator_ids no vacío
        indicators = []
        for det in detections:
            ids = det.get("indicator_ids", []) or []
            if ids:
                indicators.append({
                    "indicator_ids": ids,
                    "base_label_yolo": det.get("base_label_yolo"),
                    "confidence_base": det.get("confidence_base"),
                    "bbox_original": det.get("bbox_original"),
                    "crop_filename": det.get("crop_filename"),
                })

        # guardar archivo de indicadores por imagen
        if not image_filename:
            continue
        out_ind_path = os.path.join(outdir, f"{image_filename}_indicators.json")
        save_json(indicators, out_ind_path)

        # dibujar bounding boxes (todas las detecciones) sobre la imagen
        image_path = item.get("image_original_path")
        # si no existe, intentar buscar en la carpeta de metadata
        if not image_path or not os.path.isfile(image_path):
            # intentar ruta relativa
            meta_dir = os.path.dirname(metadata_path)
            candidate = os.path.join(meta_dir, image_filename)
            if os.path.isfile(candidate):
                image_path = candidate

        # guardar imágenes anotadas en subcarpeta 'bboxes' dentro de outdir
        imgs_outdir = os.path.join(outdir, "bboxes")
        os.makedirs(imgs_outdir, exist_ok=True)
        out_img_path = os.path.join(imgs_outdir, f"{image_filename}_bboxes.png")
        drew = False
        scaled = False
        if image_path and os.path.isfile(image_path):
            # Si la imagen encontrada tiene exactamente las dimensiones usadas por el
            # detector/modelo (p. ej. 640x640), probablemente se trate de la imagen
            # estandarizada. Intentar localizar una versión original (mayor) para
            # dibujar las cajas correctamente sobre la imagen real.
            meta_w = item.get("image_width")
            meta_h = item.get("image_height")
            try:
                with Image.open(image_path) as check_im:
                    real_w, real_h = check_im.size
            except Exception:
                real_w = None
                real_h = None

            # si la imagen actual tiene las mismas dimensiones que meta/model,
            # buscar una alternativa que tenga distinto tamaño (preferiblemente mayor)
            if meta_w and meta_h and real_w and real_h and int(real_w) == int(meta_w) and int(real_h) == int(meta_h):
                meta_dir = os.path.dirname(metadata_path)
                alt = _find_alternative_image(meta_dir, image_filename, image_path, meta_w, meta_h)
                if alt:
                    print(f"Encontrada imagen alternativa para '{image_filename}': {alt} (reemplazando {image_path})")
                    image_path = alt

            result = draw_bboxes_on_image(image_path, detections, out_img_path, meta_w=meta_w, meta_h=meta_h)
            drew = bool(result.get("drawn"))
            scaled = bool(result.get("scaled"))

        summary.append({
            "image_filename": image_filename,
            "indicators_saved": len(indicators),
            "indicators_path": out_ind_path,
            "bboxes_drawn": drew,
            "bboxes_path": out_img_path if drew else None,
            "bboxes_scaled": scaled,
        })

    # guardar resumen
    summary_path = os.path.join(outdir, "metadata_processing_summary.json")
    save_json(summary, summary_path)
    print(f"Procesamiento terminado. Resumen guardado en: {summary_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrae indicadores y dibuja bounding boxes desde metadata.json")
    parser.add_argument("--metadata", "-m", default="metadata1.json", help="Ruta a metadata.json")
    parser.add_argument("--outdir", "-o", default=None, help="Carpeta donde guardar salidas (por defecto la carpeta de metadata.json)")
    args = parser.parse_args()

    metadata_path = args.metadata
    if not os.path.isabs(metadata_path):
        metadata_path = os.path.abspath(metadata_path)
    if not os.path.isfile(metadata_path):
        print(f"No se encontró el archivo de metadata: {metadata_path}")
        return

    outdir = args.outdir or os.path.dirname(metadata_path)
    process(metadata_path, outdir)


if __name__ == "__main__":
    main()
