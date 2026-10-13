"""Worker de alertas: revisa errores_db y envía los CRITICAL no notificados por Telegram y/o correo.

Uso (proceso aparte, junto al gateway):
    python -m app.alertas
"""

import logging
import smtplib
import time
from email.message import EmailMessage

import httpx
from sqlalchemy import text

from .config import get_settings
from .db import engine_errores_admin

log = logging.getLogger("alertas")
settings = get_settings()


def _formatear(fila: dict) -> str:
    """Texto breve de la alerta (sin stack trace ni datos personales)."""
    return (
        f"🚨 [{fila['severidad']}] {fila['origen']} · {fila['tipo'] or ''}\n"
        f"{(fila['mensaje'] or '')[:500]}\n"
        f"Ruta: {fila['metodo'] or ''} {fila['ruta'] or ''} · HTTP {fila['codigo_http'] or '-'}\n"
        f"Request-ID: {fila['request_id'] or '-'} · {fila['creado_en']}"
    )


def enviar_telegram(texto: str) -> bool:
    """Envía el mensaje al chat configurado. Devuelve False si no está configurado o falla."""
    if not (settings.telegram_bot_token and settings.telegram_chat_id):
        return False
    r = httpx.post(
        f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
        json={"chat_id": settings.telegram_chat_id, "text": texto},
        timeout=10,
    )
    return r.status_code == 200


def enviar_correo(texto: str) -> bool:
    """Envía el correo por SMTP con STARTTLS (cifrado obligatorio)."""
    if not (settings.smtp_host and settings.smtp_user and settings.alert_email_to):
        return False
    msg = EmailMessage()
    msg["Subject"] = "Alerta crítica - Stroke Risk App"
    msg["From"] = settings.smtp_user
    msg["To"] = settings.alert_email_to
    msg.set_content(texto)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        smtp.starttls()
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)
    return True


def revisar_una_vez() -> int:
    """Envía las alertas pendientes y las marca como notificadas. Devuelve cuántas envió."""
    with engine_errores_admin().begin() as conn:
        filas = conn.execute(
            text(
                "SELECT id, request_id, origen, severidad, codigo_http, tipo, mensaje, ruta, metodo, creado_en "
                "FROM errores WHERE severidad = 'CRITICAL' AND notificado = 0 ORDER BY id LIMIT 20"
            )
        ).fetchall()
        enviadas = 0
        for fila in filas:
            texto = _formatear(dict(fila._mapping))
            ok = False
            for canal in (enviar_telegram, enviar_correo):
                try:
                    ok = canal(texto) or ok
                except Exception as exc:  # Un canal caído no impide probar el otro
                    log.warning("Fallo enviando alerta por %s: %s", canal.__name__, exc)
            if ok:
                conn.execute(text("UPDATE errores SET notificado = 1 WHERE id = :id"), {"id": fila.id})
                enviadas += 1
    return enviadas


def main() -> None:
    """Bucle infinito con intervalo configurable (ALERTAS_INTERVALO_SEG)."""
    logging.basicConfig(level=logging.INFO)
    log.info("Worker de alertas iniciado (cada %s s)", settings.alertas_intervalo_seg)
    while True:
        try:
            n = revisar_una_vez()
            if n:
                log.info("%s alertas enviadas", n)
        except Exception as exc:  # MySQL caído: se reintenta en el siguiente ciclo
            log.error("No se pudo revisar errores_db: %s", exc)
        time.sleep(settings.alertas_intervalo_seg)


if __name__ == "__main__":
    main()
