# bootstrap.py
import sys, os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(PROJECT_ROOT, "app")

# Asegurar que tanto la raíz como app/ estén en el path
for p in (PROJECT_ROOT, APP_DIR):
    if p not in sys.path:
        sys.path.append(p)

# Verificación
try:
    from config import settings
    print("✅ Paquete 'app' inicializado correctamente.")
except Exception as e:
    print("⚠️ Error al inicializar paquete:", e)
