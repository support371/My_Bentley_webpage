import os
import logging
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional

logger = logging.getLogger("itwin_ops.config")


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    APP_NAME: str = "Bentley iTwin Operations Center"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 5000

    DATABASE_URL: str = "sqlite+aiosqlite:///./itwin_ops.db"

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

    SECRET_KEY: str = "dev-secret-key-change-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 8

    COOKIE_SECURE: bool = False

    WEBHOOK_SECRET: str = ""
    SKIP_SIGNATURE_VERIFY: bool = True

    BENTLEY_CLIENT_ID: Optional[str] = None
    BENTLEY_CLIENT_SECRET: Optional[str] = None
    BENTLEY_AUTHORITY: str = "https://ims.bentley.com"
    BENTLEY_API_BASE: str = "https://api.bentley.com"
    BENTLEY_SCOPE: str = "itwins:read imodels:read webhooks:read webhooks:modify"

    PUBLIC_BASE_URL: Optional[str] = None

    INITIAL_ADMIN_EMAIL: str = "admin@example.com"
    INITIAL_ADMIN_PASSWORD: str = "admin123"

    ALERT_EMAIL_SMTP: Optional[str] = None
    ALERT_SLACK_WEBHOOK: Optional[str] = None

    MAX_EVENTS_IN_MEMORY: int = 1000
    RATE_LIMIT_PER_MINUTE: int = 60


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
