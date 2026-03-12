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

    @model_validator(mode="after")
    def build_database_url(self) -> "Settings":
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