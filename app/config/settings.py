from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
UPLOADS_DIR = BASE_DIR.parent / "uploads"
TEMP_DIR = UPLOADS_DIR / "temp"
STD_DIR = UPLOADS_DIR / "standardized"

ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png"]
MAX_IMAGE_MB = 10
MAX_STD_SIZE = (512, 512)  
