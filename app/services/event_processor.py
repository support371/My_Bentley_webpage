import json
import logging
from datetime import datetime
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, func

from app.models.events import Event
from app.models.resources import ITwin, IModel

logger = logging.getLogger("itwin_ops.processor")

EVENT_CATEGORY_MAP = {
    "iModels.": "iModels",
    "iTwins.": "iTwins",
    "accessControl.": "Access Control",
    "forms.": "Forms",
    "issues.": "Issues",
    "synchronization.": "Synchronization",
    "transformations.": "Transformations",
    "realityModeling.": "Reality",
    "realityAnalysis.": "Reality",
    "realityConversion.": "Reality",
    "changedElements.": "Changed Elements",
}

SEVERITY_MAP = {
    "Deleted": "warning",
    "Removed": "warning",
    "Failed": "error",
    "Error": "error",
    "Created": "info",
    "Updated": "info",
    "Completed": "success",
}


def categorize_event(event_type: str) -> str:
    for prefix, category in EVENT_CATEGORY_MAP.items():
        if event_type.startswith(prefix):
            return category
    return "Other"


def classify_severity(event_type: str) -> str:
    for keyword, severity in SEVERITY_MAP.items():
        if keyword in event_type:
            return severity
    return "info"


def extract_ids(data: dict) -> dict:
    content = data.get("content", {})
    itwin_id = (
        content.get("iTwinId") or content.get("itwinId") or
        data.get("iTwinId") or data.get("itwinId") or ""
    )
    imodel_id = (
        content.get("iModelId") or content.get("imodelId") or
        data.get("iModelId") or data.get("imodelId") or ""
    )
    itwin_name = content.get("iTwinName") or content.get("displayName") or ""
    imodel_name = content.get("iModelName") or content.get("name") or ""

    if itwin_id and not itwin_name:
        itwin_name = f"iTwin-{itwin_id[:8]}"
    if imodel_id and not imodel_name:
        imodel_name = f"iModel-{imodel_id[:8]}"

    return {
        "itwin_id": itwin_id,
        "imodel_id": imodel_id,
        "itwin_name": itwin_name,
        "imodel_name": imodel_name,
    }


async def process_webhook_event(
    raw_body: bytes,
    headers: dict,
    session: AsyncSession,
    tenant_id: Optional[str] = None,
) -> Event:
    try:
        data = json.loads(raw_body) if raw_body else {}
    except json.JSONDecodeError:
        data = {}

    event_type = data.get("eventType", "UnknownEvent")
    message_id = data.get("messageId") or headers.get("x-bentley-message-id")
    ids = extract_ids(data)
    category = categorize_event(event_type)
    severity = classify_severity(event_type)

    normalized = {
        "eventType": event_type,
        "category": category,
        "severity": severity,
        **ids,
    }

    event = Event(
        message_id=message_id,
        event_type=event_type,
        event_category=category,
        tenant_id=tenant_id,
        itwin_id=ids["itwin_id"] or None,
        itwin_name=ids["itwin_name"] or None,
        imodel_id=ids["imodel_id"] or None,
        imodel_name=ids["imodel_name"] or None,
        raw_payload=raw_body.decode("utf-8", errors="replace"),
        normalized_payload=json.dumps(normalized),
        severity=severity,
        processing_status="processed",
    )

    if data.get("timestamp"):
        try:
            event.event_timestamp = datetime.fromisoformat(
                data["timestamp"].replace("Z", "+00:00")
            )
        except Exception:
            pass

    session.add(event)

    if ids["itwin_id"]:
        await upsert_itwin(session, ids["itwin_id"], ids["itwin_name"], tenant_id)
    if ids["imodel_id"] and ids["itwin_id"]:
        await upsert_imodel(session, ids["imodel_id"], ids["itwin_id"], ids["imodel_name"], tenant_id)

    await session.commit()
    await session.refresh(event)
    logger.info(f"Processed event {event_type} -> {event.id}")
    return event


async def upsert_itwin(session: AsyncSession, itwin_id: str, name: str, tenant_id: Optional[str]):
    result = await session.execute(select(ITwin).where(ITwin.id == itwin_id))
    existing = result.scalars().first()
    if existing:
        existing.last_event_at = datetime.utcnow()
        if name and not existing.display_name:
            existing.display_name = name
    else:
        session.add(ITwin(id=itwin_id, display_name=name, tenant_id=tenant_id, last_event_at=datetime.utcnow()))


async def upsert_imodel(session: AsyncSession, imodel_id: str, itwin_id: str, name: str, tenant_id: Optional[str]):
    result = await session.execute(select(IModel).where(IModel.id == imodel_id))
    existing = result.scalars().first()
    if existing:
        existing.last_event_at = datetime.utcnow()
        if name and not existing.display_name:
            existing.display_name = name
    else:
        session.add(IModel(id=imodel_id, itwin_id=itwin_id, display_name=name, tenant_id=tenant_id, last_event_at=datetime.utcnow()))


async def get_dashboard_stats(session: AsyncSession, hours: int = 24) -> dict:
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    total = await session.scalar(
        select(func.count(Event.id)).where(Event.received_at >= cutoff)
    ) or 0

    unique_itwins = await session.scalar(
        select(func.count(func.distinct(Event.itwin_id))).where(
            Event.received_at >= cutoff, Event.itwin_id != None
        )
    ) or 0

    unique_imodels = await session.scalar(
        select(func.count(func.distinct(Event.imodel_id))).where(
            Event.received_at >= cutoff, Event.imodel_id != None
        )
    ) or 0

    recent_result = await session.execute(
        select(Event).where(Event.received_at >= cutoff)
        .order_by(Event.received_at.desc())
        .limit(20)
    )
    recent_events = recent_result.scalars().all()

    type_result = await session.execute(
        select(Event.event_type, func.count(Event.id).label("cnt"))
        .where(Event.received_at >= cutoff)
        .group_by(Event.event_type)
        .order_by(func.count(Event.id).desc())
    )
    type_counts = {row[0]: row[1] for row in type_result.all()}

    cat_result = await session.execute(
        select(Event.event_category, func.count(Event.id).label("cnt"))
        .where(Event.received_at >= cutoff)
        .group_by(Event.event_category)
    )
    cat_counts = {row[0]: row[1] for row in cat_result.all()}

    total_itwins = await session.scalar(select(func.count(ITwin.id))) or 0
    total_imodels = await session.scalar(select(func.count(IModel.id))) or 0

    return {
        "total_events": total,
        "unique_itwins": unique_itwins,
        "unique_imodels": unique_imodels,
        "total_itwins": total_itwins,
        "total_imodels": total_imodels,
        "recent_events": recent_events,
        "type_counts": type_counts,
        "cat_counts": cat_counts,
    }
