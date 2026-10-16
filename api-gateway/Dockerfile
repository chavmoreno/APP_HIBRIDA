# =====================================================================
# Imagen del API Gateway (y del worker de alertas, que usa el mismo código).
# - Mismo patrón que la inferencia: Python fijado, usuario sin privilegios y sólo HTTPS.
# - Los secretos (.env, cuenta de servicio de Firebase) y los certificados se MONTAN, nunca se copian.
# =====================================================================
FROM python:3.12.10-slim-bookworm

# Sin .pyc (sistema de archivos de sólo lectura), logs sin búfer y pip sin caché
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Usuario sin privilegios (mismo uid que la inferencia: los certificados se comparten)
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

# Dependencias primero: esta capa se reutiliza mientras requirements.txt no cambie
COPY requirements.txt .
RUN pip install -r requirements.txt

# Código de la aplicación
COPY app/ app/
COPY run.py ./

# Puntos de montaje: secrets (cuenta de servicio, sólo lectura) y logs (respaldo rotativo, escribible por "app")
RUN mkdir -p /app/secrets /app/logs /certs && chown app:app /app/logs

USER app

EXPOSE 8000

CMD ["python", "run.py"]
