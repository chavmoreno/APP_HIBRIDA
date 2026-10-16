# =====================================================================
# Imagen del microservicio de inferencia (stroke).
# - Python y scikit-learn fijados: el .joblib de Colab siempre carga con la versión correcta.
# - Los pesos del modelo NO se copian a la imagen: se montan desde inference-service/models (model registry local).
# - Corre como usuario sin privilegios y sólo sirve HTTPS.
# =====================================================================
FROM python:3.12.10-slim-bookworm

# Sin .pyc (el sistema de archivos del contenedor es de sólo lectura), logs sin búfer y pip sin caché
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Usuario sin privilegios (uid fijo para que los permisos sean predecibles)
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

# Dependencias primero: esta capa se reutiliza mientras requirements.txt no cambie
COPY requirements.txt .
RUN pip install -r requirements.txt

# Código de la aplicación
COPY app/ app/
COPY run.py healthcheck.py ./

# Puntos de montaje: models (pesos, sólo lectura) y logs (respaldo rotativo, escribible por "app")
RUN mkdir -p /app/models /app/logs /certs && chown app:app /app/logs

USER app

# Valores propios del contenedor (docker-compose.yml los vuelve a fijar para que el .env no los pise).
# Con network_mode "host" el contenedor comparte la red de la VM: sólo loopback.
ENV HOST=127.0.0.1 \
    PORT=8001 \
    SSL_CERTFILE=/certs/localhost.pem \
    SSL_KEYFILE=/certs/localhost-key.pem \
    HEALTHCHECK_CA=/certs/rootCA.pem

EXPOSE 8001

# Docker marca el contenedor como "unhealthy" si /health no responde por HTTPS
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD ["python", "healthcheck.py"]

CMD ["python", "run.py"]
