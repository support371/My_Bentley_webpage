import time
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import AsyncGenerator

from app.core.config import settings

_app_start_time: float = time.time()

_db_url = settings.ASYNC_DATABASE_URL

if "sqlite" in _db_url:
    _connect_args = {"check_same_thread": False}
elif settings.DB_IS_POSTGRES and not settings.DB_SSL:
    _connect_args = {"ssl": False}
else:
    _connect_args = {}

async_engine = create_async_engine(
    _db_url,
    echo=settings.DEBUG,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False, autocommit=False
)


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
