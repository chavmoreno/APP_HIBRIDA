"""API Gateway (:8000): único punto de entrada público (vía Caddy en la VM de Oracle).

Responsabilidades:
- Validar el ID token de Firebase de cada petición.
- Orquestar la llamada al microservicio de inferencia y guardar la consulta en consultas_db.
- Registrar todos los errores en errores_db (con respaldo en archivo).
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from . import middleware
from .config import get_settings
from .routers import admin, consultas, errores

logging.basicConfig(level=logging.INFO)
settings = get_settings()

app = FastAPI(
    title="Stroke Risk - API Gateway",
    version="1.0.0",
    description=(
        "API pública de la aplicación de predicción de riesgo de derrame cerebral.\n\n"
        "**Autenticación:** todas las rutas (salvo `/api/health` y `POST /api/errores`) requieren "
        "`Authorization: Bearer <ID token de Firebase>`.\n\n"
        "**Trazabilidad:** cada respuesta incluye `X-Request-ID`; puedes enviar el tuyo en la petición.\n\n"
        "> Resultado orientativo: no sustituye una valoración médica."
    ),
    openapi_tags=[
        {"name": "Consultas", "description": "Crear consultas y ver el histórico del usuario"},
        {"name": "Errores", "description": "Reporte de errores del frontend"},
        {"name": "Administración", "description": "Panel de errores (sólo administradores)"},
        {"name": "Salud", "description": "Estado del servicio"},
    ],
    # Swagger UI en vivo sólo si EXPONER_DOCS=true (en producción la spec estática está en docs/api/)
    docs_url="/docs" if settings.exponer_docs else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.exponer_docs else None,
)

# Middleware propio (X-Request-ID, cabeceras de seguridad) y manejadores de excepciones
middleware.configurar(app)

# CORS: sólo los orígenes https:// del frontend en Firebase Hosting
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,  # Se usa Bearer token, no cookies
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
    max_age=600,
)

# Rechaza peticiones con cabecera Host inesperada (DNS rebinding, accesos directos no previstos)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)

app.include_router(consultas.router)
app.include_router(errores.router)
app.include_router(admin.router)


@app.get("/api/health", tags=["Salud"], summary="Estado del gateway")
def health() -> dict:
    """Comprobación de vida para monitoreo."""
    return {"estado": "ok"}
