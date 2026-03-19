import json
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_session
from app.models.events import Event
from app.schemas.events import EventOut, EventsResponse

router = APIRouter()


@router.get("/events", response_model=EventsResponse, tags=["Events"])
async def list_events(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    event_type: Optional[str] = None,
    category: Optional[str] = None,
    itwin_id: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    offset = (page - 1) * page_size

    query = select(Event).order_by(Event.received_at.desc())
    count_query = select(func.count(Event.id))

    if event_type:
        query = query.where(Event.event_type == event_type)
        count_query = count_query.where(Event.event_type == event_type)
    if category:
        query = query.where(Event.event_category == category)
        count_query = count_query.where(Event.event_category == category)
    if itwin_id:
        query = query.where(Event.itwin_id == itwin_id)
        count_query = count_query.where(Event.itwin_id == itwin_id)

    total = await session.scalar(count_query) or 0

    result = await session.execute(query.offset(offset).limit(page_size))
    events = result.scalars().all()

    return EventsResponse(
        events=[EventOut.from_orm(e) for e in events],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/events/{event_id}", tags=["Events"])
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
        **EventOut.from_orm(event).dict(),
        "raw_payload": raw,
    }
