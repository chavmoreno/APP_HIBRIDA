"""Arranca el microservicio de inferencia SOLO por HTTPS en 127.0.0.1:8001.

Uso:  python run.py
"""

import os
import sys

import uvicorn

from app.config import get_settings

if __name__ == "__main__":
    s = get_settings()
    # HTTPS obligatorio: sin certificado no se arranca (nunca se sirve HTTP plano)
    for ruta in (s.ssl_certfile, s.ssl_keyfile):
        if not os.path.isfile(ruta):
            sys.exit(f"Falta el certificado TLS '{ruta}'. Genera uno con mkcert (ver docs/manual_instalacion.md).")
    uvicorn.run("app.main:app", host=s.host, port=s.port, ssl_certfile=s.ssl_certfile, ssl_keyfile=s.ssl_keyfile)
