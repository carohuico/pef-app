from PIL import Image
from pathlib import Path
from config.settings import MAX_STD_SIZE

def estandarizar_imagen(image: Image.Image, output_path) -> Path:
    """
    Redimensiona la imagen manteniendo proporciones y la guarda en output_path.
    output_path puede ser str o Path.
    """
    salida = Path(output_path)
    salida.parent.mkdir(parents=True, exist_ok=True)

    img = image.copy()
    img.thumbnail(MAX_STD_SIZE)
    img.save(salida)

    return salida
