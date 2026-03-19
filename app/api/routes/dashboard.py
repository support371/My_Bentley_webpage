import json
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select

from app.db.database import get_session
from app.core.security import get_optional_user
from app.services.event_processor import get_dashboard_stats
from app.models.events import Event
from app.models.resources import ITwin, IModel
from app.core.config import settings
from app.schemas.events import DashboardFeedResponse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

HOURS_MAP = {"1h": 1, "6h": 6, "24h": 24, "7d": 168, "30d": 720}


@router.get("/", response_class=HTMLResponse, tags=["Dashboard"])
async def root_redirect(request: Request):
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/dashboard")


@router.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
async def dashboard(request: Request, session: AsyncSession = Depends(get_session)):
    user = get_optional_user(request)
    stats = await get_dashboard_stats(session, hours=24)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
        "stats": stats,
    })


@router.get("/dashboard/feed", tags=["Dashboard"])
async def dashboard_feed(
    timeRange: str = Query(default="24h"),
    session: AsyncSession = Depends(get_session),
):
    hours = HOURS_MAP.get(timeRange, 24)
    stats = await get_dashboard_stats(session, hours=hours)

    total = stats["total_events"]
    top_types = sorted(stats["type_counts"].items(), key=lambda x: -x[1])[:5]

    if total > 0:
        insight = f"Received {total} events in the last {timeRange}. "
        if top_types:
            insight += f"Most common: {top_types[0][0]} ({top_types[0][1]} occurrences). "
        insight += f"Activity across {stats['unique_itwins']} iTwins and {stats['unique_imodels']} iModels."
    else:
        insight = f"No events received in the last {timeRange}. System is idle and awaiting webhook events."

    health = "healthy" if total > 0 else "idle"
    if total > 100:
        health = "busy"

    recent = []
    for e in stats["recent_events"]:
        recent.append({
            "id": e.id,
            "event_type": e.event_type,
            "event_category": e.event_category,
            "itwin_id": e.itwin_id,
            "itwin_name": e.itwin_name,
            "imodel_id": e.imodel_id,
            "imodel_name": e.imodel_name,
            "severity": e.severity,
            "received_at": e.received_at.isoformat(),
        })

    return {
        "meta": {"timeRange": timeRange, "generatedAt": __import__("datetime").datetime.utcnow().isoformat()},
        "kpis": {
            "totalEvents": total,
            "uniqueITwins": stats["unique_itwins"],
            "uniqueIModels": stats["unique_imodels"],
            "eventTypes": len(stats["type_counts"]),
        },
        "health": health,
        "recentEvents": recent,
        "insights": insight,
        "eventTypeBreakdown": stats["type_counts"],
        "categoryBreakdown": stats["cat_counts"],
    }


@router.get("/events-view", response_class=HTMLResponse, tags=["Dashboard"])
async def events_view(request: Request, session: AsyncSession = Depends(get_session)):
    user = get_optional_user(request)
    result = await session.execute(
        select(Event).order_by(Event.received_at.desc()).limit(100)
    )
    events = result.scalars().all()
    return templates.TemplateResponse("events.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
        "events": events,
    })


@router.get("/itwins-view", response_class=HTMLResponse, tags=["Dashboard"])
async def itwins_view(request: Request, session: AsyncSession = Depends(get_session)):
    user = get_optional_user(request)
    result = await session.execute(
        select(ITwin).order_by(ITwin.last_event_at.desc()).limit(100)
    )
    itwins = result.scalars().all()
    return templates.TemplateResponse("itwins.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
        "itwins": itwins,
    })
