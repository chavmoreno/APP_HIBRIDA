"""Rutas de consultas: crear una predicción y ver el histórico del usuario."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from .. import db, inferencia
from ..auth import Usuario, usuario_actual
from ..contexto import errores, request_id_var
from ..schemas import Consulta, DatosPaciente, PaginaConsultas, RespuestaError

router = APIRouter(prefix="/api/consultas", tags=["Consultas"])

RESPUESTAS_COMUNES = {
    401: {"model": RespuestaError, "description": "Sin token o token inválido"},
    403: {"model": RespuestaError, "description": "Correo no verificado"},
}


@router.post(
    "",
    response_model=Consulta,
    status_code=201,
    summary="Crear consulta y obtener la probabilidad de stroke",
    responses={**RESPUESTAS_COMUNES, 422: {"model": RespuestaError}, 503: {"model": RespuestaError}},
)
def crear_consulta(datos: DatosPaciente, request: Request, usuario: Usuario = Depends(usuario_actual)) -> Consulta:
    """Llama al microservicio de inferencia, guarda la consulta en consultas_db y devuelve el resultado."""
    rid = request_id_var.get()
    try:
        resultado = inferencia.predecir(datos)
    except inferencia.InferenciaNoDisponible as exc:
        # Sin inferencia la app no sirve: se registra como CRITICAL para disparar la alerta
        errores.registrar(
            severidad="CRITICAL",
            tipo="InferenciaNoDisponible",
            mensaje=str(exc),
            codigo_http=503,
            ruta=request.url.path,
            metodo="POST",
            request_id=rid,
            firebase_uid=usuario.uid,
        )
        request.state.error_registrado = True  # Evita que el manejador global lo registre otra vez
        raise HTTPException(status_code=503, detail="El servicio de predicción no está disponible, intenta más tarde") from None

    try:
        consulta_id, creado_en = db.guardar_consulta(usuario.uid, rid, datos, resultado)
        guardada = True
    except Exception as exc:
        # La predicción ya se hizo: se muestra al usuario aunque no se haya podido guardar
        errores.registrar(
            severidad="ERROR",
            tipo=type(exc).__name__,
            mensaje=f"No se pudo guardar la consulta: {exc}",
            ruta=request.url.path,
            metodo="POST",
            request_id=rid,
            firebase_uid=usuario.uid,
        )
        consulta_id, creado_en, guardada = None, datetime.now(timezone.utc), False

    return Consulta(id=consulta_id, request_id=rid, creado_en=creado_en, datos=datos, resultado=resultado, guardada=guardada)


@router.get("", response_model=PaginaConsultas, summary="Histórico de consultas del usuario", responses=RESPUESTAS_COMUNES)
def historico(
    limit: int = Query(20, ge=1, le=100, description="Elementos por página"),
    offset: int = Query(0, ge=0, description="Desplazamiento"),
    usuario: Usuario = Depends(usuario_actual),
) -> PaginaConsultas:
    """Devuelve sólo las consultas del usuario autenticado, de la más reciente a la más antigua."""
    total, items = db.listar_consultas(usuario.uid, limit, offset)
    return PaginaConsultas(total=total, limit=limit, offset=offset, items=items)


@router.get(
    "/{consulta_id}",
    response_model=Consulta,
    summary="Detalle de una consulta",
    responses={**RESPUESTAS_COMUNES, 404: {"model": RespuestaError}},
)
def detalle(consulta_id: int, usuario: Usuario = Depends(usuario_actual)) -> Consulta:
    """404 tanto si no existe como si es de otro usuario (no se revela su existencia)."""
    consulta = db.obtener_consulta(usuario.uid, consulta_id)
    if consulta is None:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    return consulta
