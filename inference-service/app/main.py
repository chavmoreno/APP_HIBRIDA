"""Microservicio de inferencia (:8001).

Carga los pesos del modelo desde el model registry local y expone /predict.
Sólo escucha en 127.0.0.1 por HTTPS y sólo acepta llamadas del API Gateway (cabecera X-Internal-API-Key).
"""

import logging
import secrets
import traceback
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from .config import get_settings
from .error_logger import ErrorLogger
from .model_loader import ModeloStroke
from .schemas import DatosPaciente, InfoModelo, ResultadoPrediccion

logging.basicConfig(level=logging.INFO)
settings = get_settings()
errores = ErrorLogger(settings.errores_db_url, settings.log_fallback_path, origen="inferencia")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carga el modelo una sola vez al arrancar; si falla, el servicio responde 503 y registra CRITICAL."""
    try:
        app.state.modelo = ModeloStroke(settings.model_path)
    except Exception as exc:
        app.state.modelo = None
        errores.registrar(
            severidad="CRITICAL",
            tipo=type(exc).__name__,
            mensaje=f"No se pudo cargar el modelo desde {settings.model_path}: {exc}",
            stack_trace=traceback.format_exc(),
        )
    yield


app = FastAPI(
    title="Stroke - Microservicio de inferencia",
    version="1.0.0",
    description="Servicio interno que calcula la probabilidad de derrame cerebral. Sólo accesible desde el API Gateway.",
    lifespan=lifespan,
)


def verificar_llave_interna(x_internal_api_key: str = Header(default="", description="Secreto compartido")) -> None:
    """Rechaza cualquier llamada que no venga del API Gateway (comparación en tiempo constante)."""
    if not settings.internal_api_key or not secrets.compare_digest(x_internal_api_key, settings.internal_api_key):
        raise HTTPException(status_code=401, detail="Llave interna inválida")


def obtener_modelo(request: Request) -> ModeloStroke:
    """Devuelve el modelo cargado o 503 si no está disponible."""
    modelo = getattr(request.app.state, "modelo", None)
    if modelo is None:
        raise HTTPException(status_code=503, detail="Modelo no disponible")
    return modelo


@app.middleware("http")
async def cabeceras_seguridad(request: Request, call_next):
    """Propaga X-Request-ID y añade HSTS (el servicio sólo se sirve por HTTPS)."""
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", "")
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.exception_handler(Exception)
async def error_no_controlado(request: Request, exc: Exception) -> JSONResponse:
    """Errores de inferencia: se registran en errores_db y se responde sin filtrar detalles internos."""
    request_id = request.headers.get("X-Request-ID")
    errores.registrar(
        severidad="ERROR",
        tipo=type(exc).__name__,
        mensaje=str(exc),
        codigo_http=500,
        ruta=request.url.path,
        metodo=request.method,
        request_id=request_id,
        stack_trace=traceback.format_exc(),
    )
    return JSONResponse(status_code=500, content={"detail": "Error interno de inferencia", "request_id": request_id})


@app.get("/health", tags=["Salud"], summary="Estado del servicio")
def health(request: Request) -> dict:
    """Indica si el servicio está vivo y si el modelo está cargado."""
    modelo = getattr(request.app.state, "modelo", None)
    return {"estado": "ok" if modelo else "degradado", "modelo_cargado": modelo is not None}


@app.get(
    "/model/info",
    response_model=InfoModelo,
    tags=["Modelo"],
    summary="Metadatos del modelo",
    dependencies=[Depends(verificar_llave_interna)],
)
def info_modelo(modelo: ModeloStroke = Depends(obtener_modelo)) -> InfoModelo:
    """Versión, algoritmo, umbral, bandas de riesgo y métricas de evaluación del modelo cargado."""
    p = modelo.paquete
    return InfoModelo(
        version=p["version"],
        algoritmo=p["algoritmo"],
        umbral=p["umbral"],
        bandas_riesgo=p["bandas_riesgo"],
        metricas=p["metricas"],
        sklearn_version=p["sklearn_version"],
        entrenado_en=p["entrenado_en"],
    )


@app.post(
    "/predict",
    response_model=ResultadoPrediccion,
    tags=["Modelo"],
    summary="Calcula la probabilidad de stroke",
    dependencies=[Depends(verificar_llave_interna)],
)
def predecir(datos: DatosPaciente, modelo: ModeloStroke = Depends(obtener_modelo)) -> ResultadoPrediccion:
    """Recibe las variables clínicas y devuelve probabilidad, clase y nivel de riesgo."""
    return modelo.predecir(datos)
