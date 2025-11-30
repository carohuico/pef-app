from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

UPLOADS_DIR = BASE_DIR.parent / "uploads"
TEMP_DIR = UPLOADS_DIR / "temp"

ORIGINALS_DIR = UPLOADS_DIR / "originals"

ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png"]
MAX_IMAGE_MB = 10

GCS_BUCKET = "bucket-pbll"
GCS_PRUEBAS_PREFIX = "pruebas"
