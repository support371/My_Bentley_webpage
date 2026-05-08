import csv
import io
import json
import random
import string
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, func, delete

from app.db.database import get_session
from app.models.events import Event
from app.schemas.events import EventOut, EventsResponse
from app.core.security import require_auth

router = APIRouter()

DEMO_EVENTS = [
    {"type": "iModels.iModelCreated.v1", "cat": "iModels", "sev": "info",
     "itwins": ["Highrise Tower A", "Campus District 4", "Bridge Retrofit Project"],
     "imodels": ["Structural Model", "Architectural Model", "MEP Model"]},
    {"type": "iModels.iModelUpdated.v1", "cat": "iModels", "sev": "info",
     "itwins": ["Urban Rail Corridor", "Data Center Build"], "imodels": ["Civil Model", "Electrical Model"]},
    {"type": "iModels.iModelDeleted.v1", "cat": "iModels", "sev": "warning",
     "itwins": ["Legacy Project"], "imodels": ["Old Model v1"]},
    {"type": "iTwins.iTwinCreated.v1", "cat": "iTwins", "sev": "info",
     "itwins": ["New Airport Terminal", "Waterfront Plaza"], "imodels": []},
    {"type": "iTwins.iTwinUpdated.v1", "cat": "iTwins", "sev": "info",
     "itwins": ["Airport Terminal", "Waterfront Plaza"], "imodels": []},
    {"type": "accessControl.memberAdded.v1", "cat": "Access Control", "sev": "info",
     "itwins": ["Secure Zone B", "Finance Tower"], "imodels": []},
    {"type": "accessControl.memberRemoved.v1", "cat": "Access Control", "sev": "warning",
     "itwins": ["Secure Zone B"], "imodels": []},
    {"type": "synchronization.runCompleted.v1", "cat": "Synchronization", "sev": "success",
     "itwins": ["Design Hub Alpha"], "imodels": ["Site Survey Model"]},
    {"type": "synchronization.runFailed.v1", "cat": "Synchronization", "sev": "error",
     "itwins": ["Design Hub Alpha"], "imodels": ["Site Survey Model"]},
    {"type": "issues.issueCreated.v1", "cat": "Issues", "sev": "warning",
     "itwins": ["QA Platform"], "imodels": ["Review Model"]},
]


@router.get("/api/events", response_model=EventsResponse, tags=["Events"])
async def list_events(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    event_type: Optional[str] = None,
    category: Optional[str] = None,
    itwin_id: Optional[str] = None,
    severity: Optional[str] = None,
    search: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    offset = (page - 1) * page_size

    query = select(Event).order_by(Event.received_at.desc())
    count_query = select(func.count(Event.id))

    if event_type:
        query = query.where(Event.event_type.ilike(f"%{event_type}%"))
        count_query = count_query.where(Event.event_type.ilike(f"%{event_type}%"))
    if category:
        query = query.where(Event.event_category == category)
        count_query = count_query.where(Event.event_category == category)
    if itwin_id:
        query = query.where(Event.itwin_id == itwin_id)
        count_query = count_query.where(Event.itwin_id == itwin_id)
    if severity:
        query = query.where(Event.severity == severity)
        count_query = count_query.where(Event.severity == severity)
    if search:
        like = f"%{search}%"
        query = query.where(
            Event.event_type.ilike(like) |
            Event.itwin_name.ilike(like) |
            Event.imodel_name.ilike(like) |
            Event.event_category.ilike(like)
        )
        count_query = count_query.where(
            Event.event_type.ilike(like) |
            Event.itwin_name.ilike(like) |
            Event.imodel_name.ilike(like) |
            Event.event_category.ilike(like)
        )

    total = await session.scalar(count_query) or 0
    result = await session.execute(query.offset(offset).limit(page_size))
    events = result.scalars().all()

    return EventsResponse(
        events=[EventOut.model_validate(e) for e in events],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/api/events/export", tags=["Events"])
async def export_events_csv(
    event_type: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(default=1000, le=10000),
    session: AsyncSession = Depends(get_session),
):
    query = select(Event).order_by(Event.received_at.desc()).limit(limit)
    if event_type:
        query = query.where(Event.event_type.ilike(f"%{event_type}%"))
    if category:
        query = query.where(Event.event_category == category)
    if severity:
        query = query.where(Event.severity == severity)

    result = await session.execute(query)
    events = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "event_type", "event_category", "itwin_id", "itwin_name",
                     "imodel_id", "imodel_name", "severity", "processing_status", "received_at"])
    for e in events:
        writer.writerow([
            e.id, e.event_type, e.event_category, e.itwin_id or "", e.itwin_name or "",
            e.imodel_id or "", e.imodel_name or "", e.severity or "", e.processing_status or "",
            e.received_at.isoformat() if e.received_at else "",
        ])

    output.seek(0)
    filename = f"itwin_events_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/api/events/demo", tags=["Events"])
async def seed_demo_events(
    request: Request,
    user: dict = Depends(require_auth),
    count: int = Query(default=5, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
):
    from app.services.event_processor import process_webhook_event
    from app.models.events import WebhookDelivery
    ids = []
    for _ in range(count):
        template = random.choice(DEMO_EVENTS)
        itwin_name = random.choice(template["itwins"])
        imodel_name = random.choice(template["imodels"]) if template["imodels"] else None
        itwin_id = "itwin-" + itwin_name.lower().replace(" ", "-")[:16]
        imodel_id = ("imodel-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))) if imodel_name else None
        payload = {
            "eventType": template["type"],
            "content": {
                "iTwinId": itwin_id,
                "iTwinName": itwin_name,
                **({"iModelId": imodel_id, "iModelName": imodel_name} if imodel_id else {}),
            }
        }
        delivery = WebhookDelivery(
            remote_ip="127.0.0.1", http_method="POST",
            headers="{}", raw_body=json.dumps(payload),
            signature_valid=True, processing_status="received",
        )
        session.add(delivery)
        await session.flush()
        event = await process_webhook_event(
            json.dumps(payload).encode(), {}, session
        )
        if event and event.id:
            ids.append(str(event.id))
    return {"seeded": len(ids), "event_ids": ids[:10]}


@router.delete("/api/events/old", tags=["Events"])
async def delete_old_events(
    request: Request,
    user: dict = Depends(require_auth),
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
):
    cutoff = datetime.utcnow() - timedelta(days=days)
    result = await session.execute(
        select(func.count(Event.id)).where(Event.received_at < cutoff)
    )
    count = result.scalar() or 0
    await session.execute(
        delete(Event).where(Event.received_at < cutoff)
    )
    await session.commit()
    return {"deleted": count, "cutoff": cutoff.isoformat(), "days": days}


@router.get("/api/events/{event_id}", tags=["Events"])
async def get_event(event_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Event).where(Event.id == event_id))
    event = result.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    raw = {}
    if event.raw_payload:
        try:
            raw = json.loads(event.raw_payload)
        except Exception:
            pass
    return {
        **EventOut.model_validate(event).model_dump(),
        "raw_payload": raw,
    }
