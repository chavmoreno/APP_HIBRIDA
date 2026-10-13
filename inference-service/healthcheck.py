"""Healthcheck del contenedor: consulta https://localhost:8001/health verificando el certificado.

Sale con código 0 si el servicio responde y el modelo está cargado; 1 en cualquier otro caso.
"""

import json
import os
import ssl
import sys
import urllib.request

# Se valida el certificado con la CA de mkcert (nunca se desactiva la verificación TLS)
contexto = ssl.create_default_context(cafile=os.environ.get("HEALTHCHECK_CA", "/certs/rootCA.pem"))
url = f"https://localhost:{os.environ.get('PORT', '8001')}/health"

try:
    with urllib.request.urlopen(url, context=contexto, timeout=4) as respuesta:
        estado = json.load(respuesta)
    sys.exit(0 if estado.get("modelo_cargado") else 1)  # Sin modelo cargado = no saludable
except Exception as exc:
    print(f"healthcheck falló: {exc}")
    sys.exit(1)
