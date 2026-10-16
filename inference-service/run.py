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
            sys.exit(f"Falta el certificado TLS '{ruta}'. Genéralo con: sudo bash infra/oracle/instalar_vm.sh (ver docs/manual_instalacion.md).")
        # La llave privada debe ser legible por el usuario del contenedor (uid 10001, grupo 10001)
        if not os.access(ruta, os.R_OK):
            sys.exit(
                f"Sin permiso de lectura sobre '{ruta}'. Repite en la VM: "
                "sudo bash infra/oracle/instalar_vm.sh (ajusta grupo 10001 y permisos 640 de la llave)"
            )
    uvicorn.run("app.main:app", host=s.host, port=s.port, ssl_certfile=s.ssl_certfile, ssl_keyfile=s.ssl_keyfile)
