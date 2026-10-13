"""Registro de errores en errores_db (MySQL/XAMPP) con respaldo en archivo .log rotativo.

Si MySQL no responde, el error NO se pierde: se escribe en un archivo rotativo local.
Todo texto se sanitiza (se truncan cadenas y se ocultan claves sensibles) antes de guardarse.
"""

import json
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Claves que nunca deben guardarse en claro dentro del contexto del error
CLAVES_SENSIBLES = {"authorization", "password", "token", "id_token", "x-internal-api-key", "api_key", "cookie"}
MAX_TEXTO = 4000  # Límite de caracteres por campo de texto


def sanitizar(valor: Any, profundidad: int = 0) -> Any:
    """Oculta claves sensibles y trunca textos largos de forma recursiva."""
    if profundidad > 5:  # Evita recursión infinita en estructuras raras
        return "[...]"
    if isinstance(valor, dict):
        return {
            k: "[OCULTO]" if str(k).lower() in CLAVES_SENSIBLES else sanitizar(v, profundidad + 1)
            for k, v in list(valor.items())[:50]
        }
    if isinstance(valor, (list, tuple)):
        return [sanitizar(v, profundidad + 1) for v in list(valor)[:50]]
    if isinstance(valor, str):
        return valor[:MAX_TEXTO]
    return valor


class ErrorLogger:
    """Escribe errores en la tabla errores_db.errores y, si falla, en un archivo rotativo."""

    def __init__(self, db_url: str, fallback_path: str, origen: str) -> None:
        self.origen = origen  # 'gateway', 'inferencia' o 'frontend'
        # Pool pequeño y con pre_ping para detectar conexiones caídas de XAMPP
        self.engine: Engine | None = (
            create_engine(db_url, pool_pre_ping=True, pool_size=2, max_overflow=2, pool_recycle=1800)
            if db_url
            else None
        )
        # Logger de respaldo: 5 archivos de 5 MB máximo
        os.makedirs(os.path.dirname(fallback_path) or ".", exist_ok=True)
        self.respaldo = logging.getLogger(f"respaldo_errores_{origen}")
        if not self.respaldo.handlers:
            manejador = RotatingFileHandler(fallback_path, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
            manejador.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            self.respaldo.addHandler(manejador)
            self.respaldo.setLevel(logging.INFO)

    def registrar(
        self,
        *,
        severidad: str,
        mensaje: str,
        tipo: str | None = None,
        codigo_http: int | None = None,
        ruta: str | None = None,
        metodo: str | None = None,
        request_id: str | None = None,
        firebase_uid: str | None = None,
        stack_trace: str | None = None,
        contexto: dict | None = None,
        user_agent: str | None = None,
        ip_hash: str | None = None,
        origen: str | None = None,
    ) -> None:
        """Guarda un error. Nunca lanza excepciones (un fallo de logging no debe tumbar la API)."""
        fila = {
            "request_id": (request_id or "")[:64] or None,
            "origen": origen or self.origen,
            "severidad": severidad,
            "codigo_http": codigo_http,
            "tipo": (tipo or "")[:120] or None,
            "mensaje": sanitizar(mensaje or "")[:MAX_TEXTO],
            "ruta": (ruta or "")[:255] or None,
            "metodo": (metodo or "")[:10] or None,
            "firebase_uid": (firebase_uid or "")[:128] or None,
            "user_agent": (user_agent or "")[:255] or None,
            "ip_hash": ip_hash,
            "stack_trace": sanitizar(stack_trace)[:MAX_TEXTO * 4] if stack_trace else None,
            "contexto": json.dumps(sanitizar(contexto), ensure_ascii=False, default=str) if contexto else None,
        }
        try:
            if self.engine is None:
                raise RuntimeError("ERRORES_DB_URL no configurada")
            with self.engine.begin() as conn:  # Transacción corta con commit automático
                conn.execute(
                    text(
                        "INSERT INTO errores (request_id, origen, severidad, codigo_http, tipo, mensaje, ruta, metodo, "
                        "firebase_uid, user_agent, ip_hash, stack_trace, contexto) VALUES (:request_id, :origen, "
                        ":severidad, :codigo_http, :tipo, :mensaje, :ruta, :metodo, :firebase_uid, :user_agent, "
                        ":ip_hash, :stack_trace, :contexto)"
                    ),
                    fila,
                )
        except Exception as exc:  # MySQL caído, credenciales malas, etc. → respaldo en archivo
            fila["fallo_db"] = str(exc)[:300]
            self.respaldo.error(json.dumps(fila, ensure_ascii=False, default=str))
