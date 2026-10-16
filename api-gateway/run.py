"""Arranca el API Gateway SOLO por HTTPS en 127.0.0.1:8000.

Caddy (en la misma VM) lo publica en https://tu-app.duckdns.org.
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
            sys.exit(f"Falta el certificado TLS '{ruta}'. Genéralo con: sudo bash infra/oracle/instalar_vm.sh (ver docs/manual_instalacion.md).")
    uvicorn.run(
        "app.main:app",
        host=s.host,
        port=s.port,
        ssl_certfile=s.ssl_certfile,
        ssl_keyfile=s.ssl_keyfile,
        proxy_headers=True,  # Respeta X-Forwarded-For/Proto de Caddy
        forwarded_allow_ips="127.0.0.1",  # Sólo confía en Caddy (loopback)
        server_header=False,  # No revela "uvicorn" en la cabecera Server
    )
