"""Middleware X-Request-ID + cabeceras de seguridad, y manejadores globales de excepciones.

Todo error 4xx/5xx se registra (sanitizado) en errores_db; si MySQL falla, en el archivo .log rotativo.
"""

import re
import traceback
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .contexto import errores, hash_ip, ip_cliente, request_id_var

# Un X-Request-ID recibido sólo se acepta si es corto y seguro; si no, se genera uno nuevo
PATRON_REQUEST_ID = re.compile(r"^[A-Za-z0-9\-_]{8,64}$")

CABECERAS_SEGURIDAD = {
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",  # Fuerza HTTPS en el navegador
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",  # Datos de salud: no se cachean
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}


def _rid(request: Request) -> str:
    """Request-ID de la petición (request.state sobrevive aunque la excepción salga del middleware)."""
    return getattr(request.state, "request_id", "") or request_id_var.get()


def _respuesta_error(request: Request, codigo: int, mensaje: str, detalles: list | None = None) -> JSONResponse:
    """Construye la respuesta de error uniforme e incluye el request-id para soporte."""
    rid = _rid(request)
    cuerpo = {"error": {"codigo": codigo, "mensaje": mensaje, "request_id": rid}}
    if detalles:
        cuerpo["error"]["detalles"] = detalles
    return JSONResponse(status_code=codigo, content=cuerpo, headers={"X-Request-ID": rid, **CABECERAS_SEGURIDAD})


def _registrar(request: Request, *, codigo: int, severidad: str, tipo: str, mensaje: str, **extra) -> None:
    """Guarda el error con el contexto de la petición (sin cuerpo ni cabeceras sensibles)."""
    usuario = getattr(request.state, "usuario", None)
    errores.registrar(
        severidad=severidad,
        tipo=tipo,
        mensaje=mensaje,
        codigo_http=codigo,
        ruta=request.url.path,
        metodo=request.method,
        request_id=_rid(request),
        firebase_uid=usuario.uid if usuario else None,
        user_agent=request.headers.get("User-Agent"),
        ip_hash=hash_ip(ip_cliente(request)),
        **extra,
    )


def configurar(app: FastAPI) -> None:
    """Registra el middleware y los manejadores de excepciones en la app."""

    @app.middleware("http")
    async def request_id_y_seguridad(request: Request, call_next):
        # 1) Request-ID: se reutiliza el del frontend si es válido; si no, se genera uno
        recibido = request.headers.get("X-Request-ID", "")
        rid = recibido if PATRON_REQUEST_ID.match(recibido) else uuid.uuid4().hex
        request.state.request_id = rid
        request_id_var.set(rid)  # Cada petición corre en su propio contexto: no hace falta resetear
        response = await call_next(request)
        # 2) Cabeceras de seguridad en todas las respuestas
        response.headers["X-Request-ID"] = rid
        for clave, valor in CABECERAS_SEGURIDAD.items():
            response.headers.setdefault(clave, valor)
        return response

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        """4xx/5xx lanzados a propósito (401, 403, 404, 503...)."""
        if getattr(request.state, "error_registrado", False):  # Ya se registró con más detalle
            return _respuesta_error(request, exc.status_code, str(exc.detail))
        severidad = "ERROR" if exc.status_code >= 500 else "WARNING"
        _registrar(request, codigo=exc.status_code, severidad=severidad, tipo="HTTPException", mensaje=str(exc.detail))
        return _respuesta_error(request, exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validacion(request: Request, exc: RequestValidationError):
        """422: se registran sólo campo y tipo de error, NUNCA los valores (son datos de salud)."""
        detalles = [{"campo": ".".join(str(p) for p in e["loc"]), "error": e["msg"]} for e in exc.errors()]
        _registrar(
            request,
            codigo=422,
            severidad="WARNING",
            tipo="RequestValidationError",
            mensaje="Datos de entrada inválidos",
            contexto={"campos": [d["campo"] for d in detalles]},
        )
        return _respuesta_error(request, 422, "Datos de entrada inválidos", detalles)

    @app.exception_handler(Exception)
    async def no_controlado(request: Request, exc: Exception):
        """500: cualquier excepción inesperada. Se guarda el stack trace, al cliente sólo el request-id."""
        _registrar(
            request,
            codigo=500,
            severidad="ERROR",
            tipo=type(exc).__name__,
            mensaje=str(exc) or type(exc).__name__,
            stack_trace=traceback.format_exc(),
        )
        return _respuesta_error(request, 500, "Error interno del servidor")

