"""Panel de administración: consulta del log de errores (sólo correos en ADMIN_EMAILS)."""

from typing import Literal

from fastapi import APIRouter, Depends, Query

from .. import db
from ..auth import usuario_admin
from ..schemas import PaginaErrores, RespuestaError

router = APIRouter(
    prefix="/api/admin",
    tags=["Administración"],
    dependencies=[Depends(usuario_admin)],
    responses={401: {"model": RespuestaError}, 403: {"model": RespuestaError}},
)


@router.get("/errores", response_model=PaginaErrores, summary="Listar errores registrados")
def listar_errores(
    severidad: Literal["INFO", "WARNING", "ERROR", "CRITICAL"] | None = None,
    origen: Literal["gateway", "inferencia", "frontend"] | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PaginaErrores:
    """Errores más recientes primero, con filtros opcionales por severidad y origen."""
    total, items = db.listar_errores(severidad, origen, limit, offset)
    return PaginaErrores(total=total, items=items)


@router.get("/errores/resumen", summary="Conteo de errores por origen y severidad")
def resumen(horas: int = Query(24, ge=1, le=720)) -> list[dict]:
    """Agregado de las últimas N horas (por defecto 24)."""
    return db.resumen_errores(horas)
