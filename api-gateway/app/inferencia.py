"""Cliente HTTPS hacia el microservicio de inferencia (127.0.0.1:8001)."""

import os
from functools import lru_cache

import httpx
from fastapi import HTTPException

from .config import get_settings
from .contexto import request_id_var
from .schemas import DatosPaciente, Resultado

settings = get_settings()


@lru_cache
def _cliente() -> httpx.Client:
    """Cliente reutilizable. Verifica el certificado TLS de la inferencia con la CA interna (nunca verify=False)."""
    verificar: str | bool = settings.inference_ca_bundle if os.path.isfile(settings.inference_ca_bundle) else True
    return httpx.Client(base_url=settings.inference_url, verify=verificar, timeout=settings.inference_timeout)


class InferenciaNoDisponible(Exception):
    """El microservicio no respondió (caído, timeout o error TLS)."""


def predecir(datos: DatosPaciente) -> Resultado:
    """Envía los datos al microservicio y devuelve el resultado validado."""
    if not settings.inference_url.startswith("https://"):
        raise RuntimeError("INFERENCE_URL debe usar https://")
    try:
        r = _cliente().post(
            "/predict",
            json=datos.model_dump(),
            headers={"X-Internal-API-Key": settings.internal_api_key, "X-Request-ID": request_id_var.get()},
        )
    except httpx.HTTPError as exc:
        raise InferenciaNoDisponible(str(exc)) from exc
    if r.status_code == 503:
        raise InferenciaNoDisponible("El microservicio no tiene modelo cargado")
    if r.status_code == 422:
        raise HTTPException(status_code=422, detail="Datos rechazados por el modelo")
    if r.status_code != 200:
        raise RuntimeError(f"Inferencia respondió {r.status_code}")
    return Resultado(**r.json())
