"""Ruta para que el frontend reporte errores de JavaScript (POST /api/errores)."""

import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ..auth import Usuario, usuario_opcional
from ..config import get_settings
from ..contexto import errores, hash_ip, ip_cliente, request_id_var
from ..schemas import ErrorFrontend, RespuestaError

router = APIRouter(prefix="/api/errores", tags=["Errores"])
settings = get_settings()

# Límite simple en memoria: últimas marcas de tiempo por IP (suficiente para un único proceso local)
_historial: dict[str, deque] = defaultdict(deque)


def _limitar(ip: str) -> None:
    """Rechaza con 429 si una IP envía demasiados reportes en 60 segundos."""
    ahora = time.monotonic()
    marcas = _historial[ip]
    while marcas and ahora - marcas[0] > 60:
        marcas.popleft()
    if len(marcas) >= settings.errores_frontend_por_minuto:
        raise HTTPException(status_code=429, detail="Demasiados reportes de error")
    marcas.append(ahora)


@router.post(
    "",
    status_code=204,
    response_class=Response,
    summary="Reportar un error de JavaScript del frontend",
    responses={429: {"model": RespuestaError}},
)
def reportar_error(error: ErrorFrontend, request: Request, usuario: Usuario | None = Depends(usuario_opcional)) -> Response:
    """No exige sesión (un error puede ocurrir antes del login); si hay token válido se asocia el uid."""
    ip = ip_cliente(request)
    _limitar(hash_ip(ip))
    errores.registrar(
        origen="frontend",
        severidad=error.severidad,
        tipo=error.tipo or "ErrorJS",
        mensaje=error.mensaje,
        ruta=error.ruta,
        metodo=None,
        request_id=request_id_var.get(),
        firebase_uid=usuario.uid if usuario else None,
        user_agent=request.headers.get("User-Agent"),
        ip_hash=hash_ip(ip),
        stack_trace=error.stack,
        contexto=error.contexto,
    )
    return Response(status_code=204)
