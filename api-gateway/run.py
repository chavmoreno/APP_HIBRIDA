"""Arranca el API Gateway SOLO por HTTPS en 127.0.0.1:8000.

Cloudflare Tunnel publica este puerto en https://api.tudominio.com.
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
    uvicorn.run(
        "app.main:app",
        host=s.host,
        port=s.port,
        ssl_certfile=s.ssl_certfile,
        ssl_keyfile=s.ssl_keyfile,
        proxy_headers=True,  # Respeta X-Forwarded-Proto de cloudflared
        forwarded_allow_ips="127.0.0.1",  # Sólo confía en el túnel local
        server_header=False,  # No revela "uvicorn" en la cabecera Server
    )
