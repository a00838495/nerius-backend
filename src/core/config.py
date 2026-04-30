from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Nerius API"
    app_env: str = "development"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"
    database_url: str | None = None
    db_echo: bool = False
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_root_password: str | None = None
    mysql_database: str | None = None
    session_expire_days: int = 30  # Session expiration in days
    db_ssl_ca: str | None = None  # Path to CA certificate for MySQL SSL (e.g. /secrets/ca.pem)
    # Cloud SQL via Unix socket on Cloud Run: set INSTANCE_CONNECTION_NAME to
    # "PROJECT:REGION:INSTANCE" and Cloud Run will mount the proxy at
    # /cloudsql/<INSTANCE_CONNECTION_NAME>. cloud_sql_socket_dir defaults to
    # /cloudsql but can be overridden for local Cloud SQL Auth Proxy testing.
    instance_connection_name: str | None = None
    cloud_sql_socket_dir: str = "/cloudsql"
    # Comma-separated list of allowed CORS origins; override in production
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080"
    ai_api_key: str | None = None
    emailjs_service_id: str | None = None
    emailjs_template_id: str | None = None
    emailjs_public_key: str | None = None
    emailjs_private_key: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_cloud_sql_socket(self) -> bool:
        return bool(self.instance_connection_name)

    @property
    def cloud_sql_socket_path(self) -> str | None:
        if not self.instance_connection_name:
            return None
        return f"{self.cloud_sql_socket_dir.rstrip('/')}/{self.instance_connection_name}"

    @model_validator(mode="after")
    def build_database_url(self) -> "Settings":
        # Cloud SQL via Unix socket (Cloud Run): if INSTANCE_CONNECTION_NAME
        # is set, it ALWAYS wins, even over a manually provided DATABASE_URL.
        # This prevents stale TCP DSNs from leaking into prod and ensures the
        # /cloudsql/<INSTANCE> socket mounted by Cloud Run is what we use.
        if self.instance_connection_name and self.mysql_root_password and self.mysql_database:
            password = quote_plus(self.mysql_root_password)
            socket_path = quote_plus(self.cloud_sql_socket_path or "")
            self.database_url = (
                f"mysql+pymysql://{self.mysql_user}:{password}@/"
                f"{self.mysql_database}?unix_socket={socket_path}"
            )
            return self

        if self.database_url:
            return self

        if self.mysql_root_password and self.mysql_database:
            password = quote_plus(self.mysql_root_password)
            self.database_url = (
                f"mysql+pymysql://{self.mysql_user}:{password}"
                f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            )
            return self

        self.database_url = "sqlite:///./app.db"
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()