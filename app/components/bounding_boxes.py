from PIL import Image, ImageDraw, ImageFont


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
    all_vals = [v for v in (x_min, x_max, y_min, y_max) if v is not None]
    if not all_vals:
        return 0, 0, 0, 0

    max_val = max(all_vals)

    # normalized floats 0..1
    if isinstance(max_val, float) and max_val <= 1.0:
        x_min_px = int(x_min * width)
        x_max_px = int(x_max * width)
        y_min_px = int(y_min * height)
        y_max_px = int(y_max * height)
        return x_min_px, y_min_px, x_max_px, y_max_px

    # percentages 0..100
    if max_val <= 100:
        x_min_px = int(float(x_min) * width / 100.0)
        x_max_px = int(float(x_max) * width / 100.0)
        y_min_px = int(float(y_min) * height / 100.0)
        y_max_px = int(float(y_max) * height / 100.0)
        return x_min_px, y_min_px, x_max_px, y_max_px

    # otherwise assume pixel coordinates already
    try:
        return int(x_min), int(y_min), int(x_max), int(y_max)
    except Exception:
        return 0, 0, 0, 0


def imagen_bboxes(image: Image, boxes: list[dict]) -> Image:
    """Dibuja bounding boxes en una imagen.

    The function is tolerant to several coordinate formats (normalized, percent, pixels).
    """
    # Work on a copy to avoid mutating the original image object unexpectedly
    img = image.convert('RGBA').copy()
    draw = ImageDraw.Draw(img)
    colors = ["#FF0000", "#0000FF", "#3AAC3A", "#D6D604", "#A111A1", "#FFA500"]
    width, height = img.size
    for i, box in enumerate(boxes):
        x_min, y_min, x_max, y_max = _to_pixel_coords(box, width, height)
        # clamp to image bounds
        x_min = max(0, min(width - 1, x_min))
        x_max = max(0, min(width - 1, x_max))
        y_min = max(0, min(height - 1, y_min))
        y_max = max(0, min(height - 1, y_max))

        if x_max <= x_min or y_max <= y_min:
            # skip invalid boxes
            continue

        # Draw rectangle
        draw.rectangle([x_min, y_min, x_max, y_max], outline=colors[i % len(colors)], width=2)

        # Draw label inside the bounding box (top-left) with the same color as the box
        label = box.get('nombre') or box.get('label') or box.get('nombre_indicador')
        if label:
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None

            # measure text size
            try:
                if font is not None:
                    text_w, text_h = draw.textsize(str(label), font=font)
                else:
                    text_w, text_h = draw.textsize(str(label))
            except Exception:
                text_w, text_h = (len(str(label)) * 6, 10)

            padding_x = 4
            padding_y = 2

            # Background rectangle coordinates (inside the bounding box, top-left)
            label_x0 = x_min
            label_y0 = y_min
            label_x1 = x_min + text_w + padding_x * 2
            label_y1 = y_min + text_h + padding_y * 2

            # If the label background would overflow the box to the right, clamp it to the box's x_max
            if label_x1 > x_max - 1:
                label_x1 = x_max - 1
            # If label height would overflow the box bottom, clamp to y_max
            if label_y1 > y_max - 1:
                label_y1 = min(y_max - 1, label_y1)

            # ensure minimum size
            if label_x1 <= label_x0 + 4:
                label_x1 = label_x0 + 8
            if label_y1 <= label_y0 + 4:
                label_y1 = label_y0 + 8

            # determine fill color from rectangle color
            box_color = colors[i % len(colors)]

            # Draw filled rectangle with the same color as the box (label background)
            try:
                draw.rectangle([label_x0, label_y0, label_x1, label_y1], fill=box_color)
            except Exception:
                # fallback to RGB tuple if color name isn't supported for some reason
                draw.rectangle([label_x0, label_y0, label_x1, label_y1], fill=(0, 0, 0))

            # Draw text in white for contrast
            text_x = label_x0 + padding_x
            text_y = label_y0 + padding_y
            try:
                if font is not None:
                    draw.text((text_x, text_y), str(label), fill="white", font=font)
                else:
                    draw.text((text_x, text_y), str(label), fill="white")
            except Exception:
                pass

    return img