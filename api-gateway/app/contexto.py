"""Objetos compartidos por todo el gateway: request-id por petición y logger de errores."""

import hashlib
from contextvars import ContextVar

from fastapi import Request

from .config import get_settings
from .error_logger import ErrorLogger

# Identificador de la petición en curso (lo fija el middleware X-Request-ID)
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

_settings = get_settings()
errores = ErrorLogger(_settings.errores_db_url, _settings.log_fallback_path, origen="gateway")


def ip_cliente(request: Request) -> str:
    """IP real del cliente: Cloudflare la envía en CF-Connecting-IP (el túnel conecta desde localhost)."""
    return request.headers.get("CF-Connecting-IP") or (request.client.host if request.client else "")


def hash_ip(ip: str) -> str:
    """Anonimiza la IP con SHA-256 + sal: permite correlacionar eventos sin guardar la IP real."""
    return hashlib.sha256(f"{_settings.ip_hash_salt}:{ip}".encode()).hexdigest()[:64] if ip else ""
