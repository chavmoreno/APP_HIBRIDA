"""Exporta la especificación OpenAPI (Swagger) de ambos servicios a docs/api/.

Uso (con un entorno que tenga las dependencias de ambos servicios + PyYAML):
    python scripts/exportar_openapi.py

Cada servicio se importa en un subproceso porque los dos paquetes se llaman `app`.
"""

import json
import pathlib
import subprocess
import sys

import yaml

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "docs" / "api"
SERVICIOS = {
    "openapi-gateway": RAIZ / "api-gateway",
    "openapi-inferencia": RAIZ / "inference-service",
}
# URL del servidor que aparecerá en el Swagger de cada servicio
SERVIDORES = {
    "openapi-gateway": [{"url": "https://api.tudominio.com", "description": "Producción (Cloudflare Tunnel)"},
                        {"url": "https://localhost:8000", "description": "Local"}],
    "openapi-inferencia": [{"url": "https://127.0.0.1:8001", "description": "Sólo loopback (uso interno)"}],
}
CODIGO = "import json; from app.main import app; print(json.dumps(app.openapi(), ensure_ascii=False))"


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    for nombre, carpeta in SERVICIOS.items():
        # ERRORES_DB_URL vacío: no intenta conectar a MySQL al importar
        entorno = {"ERRORES_DB_URL": "", "LOG_FALLBACK_PATH": str(SALIDA / ".tmp.log")}
        salida = subprocess.run(
            [sys.executable, "-c", CODIGO], cwd=carpeta, capture_output=True, text=True, check=True,
            env={**__import__("os").environ, **entorno},
        ).stdout
        spec = json.loads(salida)
        spec["servers"] = SERVIDORES[nombre]
        if nombre == "openapi-gateway":
            # Documenta el esquema de seguridad Bearer (ID token de Firebase) para el botón "Authorize"
            spec.setdefault("components", {})["securitySchemes"] = {
                "FirebaseIdToken": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT",
                                    "description": "ID token de Firebase Authentication"}
            }
            spec["security"] = [{"FirebaseIdToken": []}]
            # Rutas públicas: sin token obligatorio
            spec["paths"]["/api/health"]["get"]["security"] = []
            spec["paths"]["/api/errores"]["post"]["security"] = [{}, {"FirebaseIdToken": []}]  # Token opcional
        else:
            spec.setdefault("components", {})["securitySchemes"] = {
                "LlaveInterna": {"type": "apiKey", "in": "header", "name": "X-Internal-API-Key"}
            }
            for ruta in ("/predict", "/model/info"):
                for operacion in spec["paths"][ruta].values():
                    operacion["security"] = [{"LlaveInterna": []}]
        (SALIDA / f"{nombre}.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (SALIDA / f"{nombre}.yaml").write_text(yaml.safe_dump(spec, allow_unicode=True, sort_keys=False), encoding="utf-8")
        print(f"✔ {nombre}: {len(spec['paths'])} rutas")
    (SALIDA / ".tmp.log").unlink(missing_ok=True)


if __name__ == "__main__":
    main()
