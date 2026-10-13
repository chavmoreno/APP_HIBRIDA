"""Configuración de pruebas: variables de entorno seguras antes de importar la app."""

import os
import tempfile

os.environ.setdefault("ERRORES_DB_URL", "")  # Sin MySQL: los errores van al archivo de respaldo
os.environ.setdefault("LOG_FALLBACK_PATH", os.path.join(tempfile.mkdtemp(), "errores.log"))
os.environ.setdefault("ALLOWED_HOSTS", "localhost,testserver")
os.environ.setdefault("CORS_ORIGINS", "https://ejemplo.web.app")
