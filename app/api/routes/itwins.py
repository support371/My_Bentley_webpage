from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_session
from app.models.events import Event
from app.models.resources import ITwin, IModel

router = APIRouter()


@router.get("/api/itwins", tags=["iTwins"])
async def list_itwins_api(
    search: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    query = select(ITwin).order_by(ITwin.last_event_at.desc()).limit(limit)
    if search:
        query = query.where(
            ITwin.display_name.ilike(f"%{search}%") | ITwin.id.ilike(f"%{search}%")
        )
    result = await session.execute(query)
    itwins = result.scalars().all()

    event_counts_result = await session.execute(
        select(Event.itwin_id, func.count(Event.id).label("cnt"))
        .where(Event.itwin_id.isnot(None))
        .group_by(Event.itwin_id)
    )
    event_counts = {row.itwin_id: row.cnt for row in event_counts_result}

    imodel_counts_result = await session.execute(
        select(IModel.itwin_id, func.count(IModel.id).label("cnt"))
        .group_by(IModel.itwin_id)
    )
    imodel_counts = {row.itwin_id: row.cnt for row in imodel_counts_result}

    return {
        "itwins": [
            {
                "id": tw.id,
                "display_name": tw.display_name,
                "type": tw.type,
                "subclass": tw.subclass,
                "status": tw.status,
                "last_event_at": tw.last_event_at.isoformat() if tw.last_event_at else None,
                "created_at": tw.created_at.isoformat() if tw.created_at else None,
                "event_count": event_counts.get(tw.id, 0),
                "imodel_count": imodel_counts.get(tw.id, 0),
            }
            for tw in itwins
        ],
        "total": len(itwins),
    }


@router.get("/api/itwins/{itwin_id}", tags=["iTwins"])
async def get_itwin(itwin_id: str, session: AsyncSession = Depends(get_session)):
    from fastapi import HTTPException
    result = await session.execute(select(ITwin).where(ITwin.id == itwin_id))
    tw = result.scalars().first()
    if not tw:
        raise HTTPException(status_code=404, detail="iTwin not found")

    events_result = await session.execute(
        select(Event).where(Event.itwin_id == itwin_id)
        .order_by(Event.received_at.desc()).limit(20)
    )
    recent_events = events_result.scalars().all()

    imodels_result = await session.execute(
        select(IModel).where(IModel.itwin_id == itwin_id)
    )
    imodels = imodels_result.scalars().all()

    return {
        "id": tw.id,
        "display_name": tw.display_name,
        "type": tw.type,
        "last_event_at": tw.last_event_at.isoformat() if tw.last_event_at else None,
        "imodels": [{"id": m.id, "display_name": m.display_name, "state": m.state} for m in imodels],
        "recent_events": [
            {"id": e.id, "event_type": e.event_type, "severity": e.severity,
             "received_at": e.received_at.isoformat()}
            for e in recent_events
        ],
    }
