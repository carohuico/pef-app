from PIL import Image
from pathlib import Path
from config.settings import MAX_STD_SIZE

def estandarizar_imagen(image: Image.Image, output_path) -> Path:
    """
    Redimensiona la imagen directamente a 512x512 píxeles.
    """
    salida = Path(output_path)
    salida.parent.mkdir(parents=True, exist_ok=True)

    img = image.resize((512, 512))

    img.save(salida)

    return salida
