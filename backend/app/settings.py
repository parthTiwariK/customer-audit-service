from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(Path(__file__).resolve().parents[2] / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = ""
    db_dialect: str = "mysql"
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = ""
    db_password: str = ""
    db_name: str = "case_audit"
    db_ssl_ca: str = ""
    app_env: str = "development"
    session_secret: str = "change-me"
    auth_mode: str = "dev"

    local_auth_username: str = "root"
    local_auth_password: str = ""

    dev_user_email: str = "dev@example.com"
    dev_user_name: str = "Dev User"
    dev_user_role: str = "admin"

    cors_origins: str = "http://localhost:5173,http://localhost:8002"

    @property
    def db_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.db_dialect == "sqlite":
            return "sqlite+pysqlite:///:memory:"
        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password)
        return (
            f"mysql+pymysql://{user}:{password}@{self.db_host}:{self.db_port}"
            f"/{self.db_name}?charset=utf8mb4"
        )

    @property
    def auth_enabled(self) -> bool:
        return self.auth_mode not in ("none", "")

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()