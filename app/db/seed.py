import logging
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models.auth import User
from app.models.tenants import Tenant
from app.core.security import hash_password
from app.core.config import settings

logger = logging.getLogger("itwin_ops.seed")


async def seed_initial_data():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Tenant).limit(1))
        if result.scalars().first():
            return

        default_tenant = Tenant(
            name="Default Organization",
            slug="default",
            is_active=True,
        )
        session.add(default_tenant)
        await session.commit()
        await session.refresh(default_tenant)

        admin_user = User(
            email=settings.INITIAL_ADMIN_EMAIL,
            hashed_password=hash_password(settings.INITIAL_ADMIN_PASSWORD),
            full_name="Platform Admin",
            role="admin",
            tenant_id=default_tenant.id,
        )
        session.add(admin_user)
        await session.commit()

        logger.info(f"Seeded default tenant and admin user: {settings.INITIAL_ADMIN_EMAIL}")
