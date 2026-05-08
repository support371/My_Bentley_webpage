from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import all models so Alembic can detect schema changes
from app.models.events import Event, WebhookDelivery, AuditLog          # noqa: F401
from app.models.resources import ITwin, IModel, AlertRule, Alert        # noqa: F401
from app.models.auth import User                                        # noqa: F401
from app.models.tenants import Tenant                                   # noqa: F401
from app.models.integrations import Integration                         # noqa: F401
from sqlmodel import SQLModel

from app.core.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _sync_url(url: str) -> str:
    """Strip async driver prefixes so Alembic can use a sync connection."""
    return (
        url.replace("sqlite+aiosqlite://", "sqlite://")
           .replace("postgresql+asyncpg://", "postgresql://")
    )


config.set_main_option("sqlalchemy.url", _sync_url(settings.DATABASE_URL))

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
