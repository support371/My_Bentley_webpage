import json
import logging
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models.auth import User
from app.models.tenants import Tenant
from app.core.security import hash_password
from app.core.config import settings

logger = logging.getLogger("itwin_ops.seed")

_SEED_TASKS = [
    {"id": "T-001", "title": "Configure Bentley OAuth credentials", "desc": "Set BENTLEY_CLIENT_ID and BENTLEY_CLIENT_SECRET in environment secrets.", "stage": "complete", "priority": "Critical", "tags": ["auth", "bentley"], "assignee": "Gregor S."},
    {"id": "T-002", "title": "Register webhook endpoint with iTwin platform", "desc": "Create webhook subscription via /admin/webhooks/create pointing to the public /webhook route.", "stage": "deployment", "priority": "High", "tags": ["webhook", "integration"], "assignee": "Gregor S."},
    {"id": "T-003", "title": "Enable HMAC signature verification", "desc": "Set SKIP_SIGNATURE_VERIFY=False and ensure WEBHOOK_SECRET matches Bentley registration.", "stage": "testing", "priority": "High", "tags": ["security"], "assignee": ""},
    {"id": "T-004", "title": "Configure Slack alert channel", "desc": "Create an incoming webhook in Slack and add it as a destination in Admin → Alert Rules.", "stage": "development", "priority": "Medium", "tags": ["alerts", "slack"], "assignee": ""},
    {"id": "T-005", "title": "Set up PostgreSQL for production", "desc": "Provision a managed PostgreSQL instance and update DATABASE_URL. Run smoke-test.sh to verify.", "stage": "planning", "priority": "High", "tags": ["database", "infra"], "assignee": ""},
    {"id": "T-006", "title": "Map custom domain and enable HTTPS", "desc": "Point DNS to the deployed service. Set COOKIE_SECURE=True and PUBLIC_BASE_URL to the custom domain.", "stage": "planning", "priority": "Medium", "tags": ["domain", "tls"], "assignee": ""},
    {"id": "T-007", "title": "Wire Sentry DSN for error tracking", "desc": "Add SENTRY_DSN to environment and install sentry-sdk. Verify error capture in the Sentry dashboard.", "stage": "registration", "priority": "Low", "tags": ["observability", "sentry"], "assignee": ""},
    {"id": "T-008", "title": "Deploy Helm chart to AKS", "desc": "Build Docker image, push to ACR, and deploy via the provided Helm chart with values override.", "stage": "registration", "priority": "Medium", "tags": ["kubernetes", "helm", "azure"], "assignee": ""},
]


async def seed_tasks(session: AsyncSession) -> None:
    from app.models.tasks import Task
    result = await session.execute(select(Task).limit(1))
    if result.scalars().first():
        return
    for td in _SEED_TASKS:
        task = Task(
            id=td["id"],
            title=td["title"],
            desc=td.get("desc", ""),
            stage=td["stage"],
            priority=td["priority"],
            tags=json.dumps(td.get("tags", [])),
            assignee=td.get("assignee", ""),
            comments=json.dumps([]),
        )
        session.add(task)
    await session.commit()
    logger.info(f"Seeded {len(_SEED_TASKS)} demo tasks")


async def seed_initial_data():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Tenant).limit(1))
        if result.scalars().first():
            await seed_tasks(session)
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

        await seed_tasks(session)
        logger.info(f"Seeded default tenant and admin user: {settings.INITIAL_ADMIN_EMAIL}")
