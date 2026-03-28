from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_session
from app.core.security import get_optional_user
from app.core.config import settings
from app.models.events import Event
from app.models.resources import ITwin, IModel

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/imodels-view", response_class=HTMLResponse, tags=["iModels"])
async def imodels_view(request: Request):
    user = get_optional_user(request)
    return templates.TemplateResponse("imodels.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
    })


@router.get("/api/imodels", tags=["iModels"])
async def list_imodels(
    search: Optional[str] = None,
    itwin_id: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = Query(default=200, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
):
    query = select(IModel).order_by(IModel.last_event_at.desc().nullslast(), IModel.created_at.desc()).limit(limit)

    if search:
        query = query.where(
            IModel.display_name.ilike(f"%{search}%") | IModel.id.ilike(f"%{search}%")
        )
    if itwin_id:
        query = query.where(IModel.itwin_id == itwin_id)
    if state:
        query = query.where(IModel.state == state)

    result = await session.execute(query)
    imodels = result.scalars().all()

    event_counts_result = await session.execute(
        select(Event.imodel_id, func.count(Event.id).label("cnt"))
        .where(Event.imodel_id.isnot(None))
        .group_by(Event.imodel_id)
    )
    event_counts = {row.imodel_id: row.cnt for row in event_counts_result}

    itwin_ids = list({m.itwin_id for m in imodels if m.itwin_id})
    itwin_names: dict = {}
    if itwin_ids:
        tw_result = await session.execute(
            select(ITwin.id, ITwin.display_name).where(ITwin.id.in_(itwin_ids))
        )
        itwin_names = {row.id: row.display_name for row in tw_result}

    states = sorted({m.state for m in imodels if m.state})

    return {
        "imodels": [
            {
                "id": m.id,
                "display_name": m.display_name or m.name,
                "name": m.name,
                "state": m.state,
                "itwin_id": m.itwin_id,
                "itwin_name": itwin_names.get(m.itwin_id or "") or m.itwin_id,
                "event_count": event_counts.get(m.id, 0),
                "last_event_at": m.last_event_at.isoformat() if m.last_event_at else None,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in imodels
        ],
        "total": len(imodels),
        "states": states,
    }
