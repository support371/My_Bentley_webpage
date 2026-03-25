from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_session
from app.core.security import get_optional_user
from app.models.events import IModel, Event
from app.models.resources import ITwin
from app.core.config import settings

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
    search: str = Query(default=""),
    state: str = Query(default=""),
    sort: str = Query(default="recent"),
    limit: int = Query(default=200),
    session: AsyncSession = Depends(get_session),
):
    q = select(IModel)
    if search:
        term = f"%{search}%"
        from sqlalchemy import or_
        q = q.where(or_(IModel.display_name.ilike(term), IModel.name.ilike(term)))
    if state:
        q = q.where(IModel.state == state)

    if sort == "name":
        q = q.order_by(IModel.display_name)
    else:
        q = q.order_by(IModel.last_event_at.desc().nullslast(), IModel.created_at.desc())

    q = q.limit(limit)
    result = await session.execute(q)
    imodels = result.scalars().all()

    event_counts_result = await session.execute(
        select(Event.imodel_id, func.count(Event.id).label("cnt"))
        .where(Event.imodel_id.isnot(None))
        .group_by(Event.imodel_id)
    )
    event_counts = {row.imodel_id: row.cnt for row in event_counts_result}

    itwin_ids = list({m.itwin_id for m in imodels if m.itwin_id})
    itwin_names = {}
    if itwin_ids:
        from sqlalchemy import or_
        it_result = await session.execute(
            select(ITwin.id, ITwin.display_name).where(ITwin.id.in_(itwin_ids))
        )
        itwin_names = {row.id: row.display_name for row in it_result}

    total = await session.scalar(select(func.count(IModel.id))) or 0

    items = []
    for m in imodels:
        items.append({
            "id": m.id,
            "display_name": m.display_name or m.name or m.id,
            "name": m.name or "",
            "state": m.state or "ready",
            "itwin_id": m.itwin_id,
            "itwin_name": itwin_names.get(m.itwin_id, ""),
            "event_count": event_counts.get(m.id, 0),
            "last_event_at": m.last_event_at.isoformat() if m.last_event_at else None,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        })

    return {"total": total, "shown": len(items), "items": items}
