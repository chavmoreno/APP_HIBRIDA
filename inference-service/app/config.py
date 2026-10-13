"""Configuración del microservicio de inferencia, leída de variables de entorno / archivo .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parámetros del servicio. Cada atributo se puede sobreescribir con una variable de entorno."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    host: str = "127.0.0.1"  # Sólo loopback: no se expone a la red
    port: int = 8001
    ssl_certfile: str = "../infra/certs/localhost.pem"  # Certificado TLS (HTTPS obligatorio)
    ssl_keyfile: str = "../infra/certs/localhost-key.pem"  # Llave privada del certificado

    model_path: str = "models/model_v1.joblib"  # Paquete exportado desde Colab
    internal_api_key: str = ""  # Secreto compartido con el API Gateway

    errores_db_url: str = ""  # URL SQLAlchemy de errores_db (vacío = sólo archivo de respaldo)
    log_fallback_path: str = "logs/errores_respaldo.log"  # Respaldo rotativo si MySQL falla


@lru_cache
def get_settings() -> Settings:
    """Devuelve una única instancia de configuración (se cachea)."""
    return Settings()
