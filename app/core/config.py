import os
import logging
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

logger = logging.getLogger("itwin_ops.config")


class Settings(BaseSettings):
    APP_NAME: str = "Bentley iTwin Operations Center"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")

    HOST: str = "0.0.0.0"
    PORT: int = Field(default=5000, env="PORT")

    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./itwin_ops.db", env="DATABASE_URL")

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        from urllib.parse import urlparse, urlunparse, urlencode, parse_qs
        url = self.DATABASE_URL
        if url.startswith("postgresql://") or url.startswith("postgres://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            query_params.pop("sslmode", None)
            new_query = urlencode({k: v[0] for k, v in query_params.items()})
            url = urlunparse(parsed._replace(query=new_query))
        return url

    @property
    def DB_IS_POSTGRES(self) -> bool:
        url = self.DATABASE_URL
        return url.startswith("postgresql://") or url.startswith("postgres://")

    @property
    def DB_SSL(self) -> bool:
        if "sslmode=disable" in self.DATABASE_URL:
            return False
        return self.DB_IS_POSTGRES

    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production-min-32-chars", env="SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 8

    COOKIE_SECURE: bool = Field(default=False, env="COOKIE_SECURE")

    WEBHOOK_SECRET: str = Field(default="", env="WEBHOOK_SECRET")
    SKIP_SIGNATURE_VERIFY: bool = Field(default=True, env="SKIP_SIGNATURE_VERIFY")

    BENTLEY_CLIENT_ID: Optional[str] = Field(default=None, env="BENTLEY_CLIENT_ID")
    BENTLEY_CLIENT_SECRET: Optional[str] = Field(default=None, env="BENTLEY_CLIENT_SECRET")
    BENTLEY_AUTHORITY: str = Field(default="https://ims.bentley.com", env="BENTLEY_AUTHORITY")
    BENTLEY_API_BASE: str = Field(default="https://api.bentley.com", env="BENTLEY_API_BASE")
    BENTLEY_SCOPE: str = Field(
        default="itwins:read imodels:read webhooks:read webhooks:modify",
        env="BENTLEY_SCOPE",
    )

    PUBLIC_BASE_URL: Optional[str] = Field(default=None, env="PUBLIC_BASE_URL")

    INITIAL_ADMIN_EMAIL: str = Field(default="admin@example.com", env="INITIAL_ADMIN_EMAIL")
    INITIAL_ADMIN_PASSWORD: str = Field(default="admin123", env="INITIAL_ADMIN_PASSWORD")

    ALERT_EMAIL_SMTP: Optional[str] = Field(default=None, env="ALERT_EMAIL_SMTP")
    ALERT_EMAIL_PORT: int = Field(default=587, env="ALERT_EMAIL_PORT")
    ALERT_EMAIL_USER: Optional[str] = Field(default=None, env="ALERT_EMAIL_USER")
    ALERT_EMAIL_PASS: Optional[str] = Field(default=None, env="ALERT_EMAIL_PASS")
    ALERT_EMAIL_FROM: Optional[str] = Field(default=None, env="ALERT_EMAIL_FROM")
    ALERT_SLACK_WEBHOOK: Optional[str] = Field(default=None, env="ALERT_SLACK_WEBHOOK")
    ALERT_DISCORD_WEBHOOK: Optional[str] = Field(default=None, env="ALERT_DISCORD_WEBHOOK")

    MAX_EVENTS_IN_MEMORY: int = 1000
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def _emit_production_warnings() -> None:
    if settings.ENVIRONMENT != "production":
        return
    if settings.SKIP_SIGNATURE_VERIFY:
        logger.warning(
            "PRODUCTION WARNING: SKIP_SIGNATURE_VERIFY=True — webhook signatures are not checked. "
            "Set SKIP_SIGNATURE_VERIFY=False and configure WEBHOOK_SECRET immediately."
        )
    if not settings.WEBHOOK_SECRET:
        logger.warning(
            "PRODUCTION WARNING: WEBHOOK_SECRET is not set — any caller can POST to /webhook."
        )
    if not settings.COOKIE_SECURE:
        logger.warning(
            "PRODUCTION WARNING: COOKIE_SECURE=False — session cookies are not marked Secure. "
            "Set COOKIE_SECURE=True for HTTPS deployments."
        )


_emit_production_warnings()


def is_production() -> bool:
    return settings.ENVIRONMENT == "production"


def get_db_url() -> str:
    return settings.DATABASE_URL
