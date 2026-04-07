import logging
import random
import json
import string
from datetime import datetime, timedelta
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import AsyncSessionLocal
from app.models.auth import User
from app.models.tenants import Tenant
from app.models.resources import ITwin, IModel, AlertRule
from app.models.events import Event, WebhookDelivery
from app.models.integrations import Integration
from app.models.ops import ControlPlaneModule, LaunchCheck
from app.core.security import hash_password
from app.core.config import settings
from app.api.routes.integrations import INTEGRATION_CATALOG

logger = logging.getLogger("itwin_ops.seed")

DEMO_ITWINS = [
    {"id": "itwin-highrise-tower", "name": "Highrise Tower A", "type": "Project"},
    {"id": "itwin-campus-dist", "name": "Campus District 4", "type": "Asset"},
    {"id": "itwin-bridge-retro", "name": "Bridge Retrofit", "type": "Project"},
    {"id": "itwin-urban-rail", "name": "Urban Rail Corridor", "type": "Asset"},
    {"id": "itwin-data-center", "name": "Data Center Build", "type": "Project"},
    {"id": "itwin-hudson-park", "name": "Hudson Logistics Park", "type": "Asset"},
]

DEMO_IMODELS = [
    {"id": "imodel-struct-01", "name": "Structural Model", "state": "available"},
    {"id": "imodel-arch-02", "name": "Architectural Model", "state": "available"},
    {"id": "imodel-mep-03", "name": "MEP Model", "state": "available"},
    {"id": "imodel-civil-04", "name": "Civil Model", "state": "available"},
    {"id": "imodel-elec-05", "name": "Electrical Model", "state": "available"},
]

DEMO_EVENT_TYPES = [
    ("iModels.iModelCreated.v1", "iModels", "info"),
    ("iModels.iModelUpdated.v1", "iModels", "info"),
    ("iModels.iModelDeleted.v1", "iModels", "warning"),
    ("iTwins.iTwinCreated.v1", "iTwins", "info"),
    ("iTwins.iTwinUpdated.v1", "iTwins", "info"),
    ("accessControl.memberAdded.v1", "Access Control", "info"),
    ("synchronization.runCompleted.v1", "Synchronization", "success"),
    ("synchronization.runFailed.v1", "Synchronization", "error"),
    ("issues.issueCreated.v1", "Issues", "warning"),
]

async def seed_initial_data():
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(Tenant).limit(1))
        if result.scalars().first():
            logger.info("Database already contains data, skipping seed.")
            return

        logger.info("Seeding initial data...")

        # 1. Tenant & Admin
        default_tenant = Tenant(name="Bentley Operations", slug="bentley", is_active=True)
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

        # 2. iTwins & iModels
        itwin_objs = []
        for it in DEMO_ITWINS:
            obj = ITwin(id=it["id"], display_name=it["name"], type=it["type"], tenant_id=default_tenant.id, status="Active")
            session.add(obj)
            itwin_objs.append(obj)

        imodel_objs = []
        for im in DEMO_IMODELS:
            # Assign to random itwin
            itwin = random.choice(itwin_objs)
            obj = IModel(id=im["id"], display_name=im["name"], name=im["name"], state=im["state"], itwin_id=itwin.id, tenant_id=default_tenant.id)
            session.add(obj)
            imodel_objs.append(obj)

        # 3. Integrations (Connected & Disconnected)
        for i, item in enumerate(INTEGRATION_CATALOG):
            status = "connected" if i < 3 else "disconnected"
            enabled = i < 3
            integration = Integration(
                slug=item["slug"],
                name=item["name"],
                category=item["category"],
                description=item["description"],
                icon_emoji=item.get("icon_emoji"),
                icon_color=item.get("icon_color"),
                status=status,
                is_enabled=enabled,
                webhook_url="https://hooks.example.com/fake" if enabled else None
            )
            session.add(integration)

        # 4. Control Plane Modules
        cp_modules = [
            ControlPlaneModule(name="Website Studio", status="Operational", summary="Bentley.com, Docs, and Partner Portal"),
            ControlPlaneModule(name="Infrastructure", status="Operational", summary="Azure, AWS, and GCP Hybrid Clusters"),
            ControlPlaneModule(name="Environment Manager", status="Operational", summary="Dev, Staging, and Production Configs"),
            ControlPlaneModule(name="Security Hub", status="Operational", summary="Audit logs and access control policies"),
        ]
        for m in cp_modules:
            session.add(m)

        # 5. Launch Checks
        from app.services.launch_readiness import get_launch_readiness
        readiness = get_launch_readiness()
        for check in readiness["checks"]:
            session.add(LaunchCheck(label=check["label"], status=check["status"], detail=check["detail"]))

        # 6. Events (History)
        logger.info("Generating event history...")
        for i in range(100):
            etype, cat, sev = random.choice(DEMO_EVENT_TYPES)
            itwin = random.choice(itwin_objs)
            imodel = random.choice([m for m in imodel_objs if m.itwin_id == itwin.id] + [None])

            # Scatter over last 7 days
            days_ago = random.uniform(0, 7)
            received = datetime.utcnow() - timedelta(days=days_ago)

            event = Event(
                message_id=f"msg-{i}-{random.randint(1000,9999)}",
                event_type=etype,
                event_category=cat,
                severity=sev,
                itwin_id=itwin.id,
                itwin_name=itwin.display_name,
                imodel_id=imodel.id if imodel else None,
                imodel_name=imodel.display_name if imodel else None,
                received_at=received,
                processing_status="processed",
                raw_payload=json.dumps({"eventType": etype, "timestamp": received.isoformat()})
            )
            session.add(event)

            # Update last_event_at
            if not itwin.last_event_at or received > itwin.last_event_at:
                itwin.last_event_at = received
            if imodel and (not imodel.last_event_at or received > imodel.last_event_at):
                imodel.last_event_at = received

        await session.commit()
        logger.info("Seed completed successfully.")
