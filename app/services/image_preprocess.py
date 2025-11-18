from PIL import Image
from pathlib import Path
from config.settings import ORIGINALS_DIR

def estandarizar_imagen(image: Image.Image, output_path) -> Path:
    """
    Guarda la imagen tal cual (sin forzar redimensionamiento a 512x512).
    Mantener la imagen original permite que las coordenadas de bounding
    boxes sigan siendo válidas.
    """
    salida = Path(output_path)
    salida.parent.mkdir(parents=True, exist_ok=True)

    # Guardar la imagen sin cambiar su tamaño ni su proporción
    try:
        image.save(salida)
    except Exception:
        # fallback: convertir a RGB y guardar
        try:
            image.convert('RGB').save(salida)
        except Exception:
            raise

    return salida
