"""Autenticación: valida el ID token de Firebase enviado como 'Authorization: Bearer <token>'."""

from dataclasses import dataclass

import firebase_admin
from fastapi import Depends, HTTPException, Request
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

from .config import get_settings

settings = get_settings()


@dataclass(frozen=True)
class Usuario:
    """Datos mínimos del usuario autenticado que necesita el backend."""

    uid: str
    email: str | None
    proveedor: str  # 'password' (correo) o 'google.com' (Gmail)
    es_admin: bool = False


def _inicializar_firebase() -> None:
    """Inicializa el SDK Admin de Firebase una sola vez con la cuenta de servicio."""
    if not firebase_admin._apps:  # noqa: SLF001 - forma documentada de comprobar la inicialización
        cred = credentials.Certificate(settings.firebase_credentials)
        firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id or None})


def verificar_token(token: str) -> dict:
    """Verifica firma, expiración, audiencia y revocación del ID token. Lanza excepción si no es válido."""
    _inicializar_firebase()
    return firebase_auth.verify_id_token(token, check_revoked=True)


def _extraer_token(request: Request) -> str | None:
    """Obtiene el token de la cabecera Authorization (formato 'Bearer <token>')."""
    cabecera = request.headers.get("Authorization", "")
    tipo, _, token = cabecera.partition(" ")
    return token.strip() if tipo.lower() == "bearer" and token.strip() else None


def _a_usuario(claims: dict) -> Usuario:
    """Convierte los claims del token en un Usuario y aplica la política de correo verificado."""
    proveedor = claims.get("firebase", {}).get("sign_in_provider", "")
    email = (claims.get("email") or "").lower() or None
    if settings.require_email_verified and proveedor == "password" and not claims.get("email_verified"):
        raise HTTPException(status_code=403, detail="Debes verificar tu correo antes de usar la aplicación")
    return Usuario(
        uid=claims["uid"],
        email=email,
        proveedor=proveedor,
        es_admin=bool(email and email in settings.admin_emails_list and claims.get("email_verified")),
    )


def usuario_actual(request: Request) -> Usuario:
    """Dependencia: exige un usuario autenticado (401 si no hay token o es inválido)."""
    token = _extraer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Falta el token de autenticación")
    try:
        claims = verificar_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido, expirado o revocado") from None
    usuario = _a_usuario(claims)
    request.state.usuario = usuario  # Para que los manejadores de error sepan quién era
    return usuario


def usuario_opcional(request: Request) -> Usuario | None:
    """Dependencia: devuelve el usuario si el token es válido, o None (no falla)."""
    token = _extraer_token(request)
    if not token:
        return None
    try:
        usuario = _a_usuario(verificar_token(token))
        request.state.usuario = usuario
        return usuario
    except Exception:
        return None


def usuario_admin(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
    """Dependencia: exige que el usuario esté en ADMIN_EMAILS (403 si no)."""
    if not usuario.es_admin:
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores")
    return usuario
