"""Configuración del API Gateway, leída de variables de entorno / archivo .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parámetros del gateway. Cada atributo se puede sobreescribir con una variable de entorno."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Servidor (sólo HTTPS; Caddy publica este puerto en tu-app.duckdns.org)
    host: str = "127.0.0.1"
    port: int = 8000
    ssl_certfile: str = "../infra/certs/localhost.pem"
    ssl_keyfile: str = "../infra/certs/localhost-key.pem"

    # Seguridad HTTP
    exponer_docs: bool = False  # /docs y /openapi.json públicos sólo si se activa (la spec está en docs/api/)
    cors_origins: str = ""  # Orígenes del frontend separados por coma
    allowed_hosts: str = "localhost,127.0.0.1"  # Valores aceptados en la cabecera Host

    # Firebase Authentication
    firebase_credentials: str = "secrets/firebase-service-account.json"
    firebase_project_id: str = ""
    require_email_verified: bool = True  # Cuentas correo/contraseña deben verificar su correo
    admin_emails: str = ""  # Correos con acceso al panel de errores

    # Microservicio de inferencia
    inference_url: str = "https://127.0.0.1:8001"
    inference_ca_bundle: str = "../infra/certs/rootCA.pem"  # CA interna para validar el TLS de la inferencia
    inference_timeout: float = 5.0
    internal_api_key: str = ""

    # Bases de datos XAMPP
    consultas_db_url: str = ""
    errores_db_url: str = ""  # Usuario con permiso de INSERT (log)
    errores_admin_db_url: str = ""  # Usuario con SELECT/UPDATE (panel admin y alertas)
    log_fallback_path: str = "logs/errores_respaldo.log"
    ip_hash_salt: str = "cambia-esta-sal"

    # Límite de reportes de error del frontend por IP y minuto (evita inundar el log)
    errores_frontend_por_minuto: int = 30

    # Alertas
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    alert_email_to: str = ""
    alertas_intervalo_seg: int = 60

    @staticmethod
    def _lista(valor: str) -> list[str]:
        """Convierte 'a, b ,c' en ['a', 'b', 'c']."""
        return [v.strip() for v in valor.split(",") if v.strip()]

    @property
    def cors_origins_list(self) -> list[str]:
        # Sólo se aceptan orígenes https:// (política HTTPS exclusiva)
        return [o for o in self._lista(self.cors_origins) if o.startswith("https://")]

    @property
    def allowed_hosts_list(self) -> list[str]:
        return self._lista(self.allowed_hosts)

    @property
    def admin_emails_list(self) -> list[str]:
        return [e.lower() for e in self._lista(self.admin_emails)]


@lru_cache
def get_settings() -> Settings:
    """Devuelve una única instancia de configuración (se cachea)."""
    return Settings()
