import json
import time
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_session
from app.core.security import get_optional_user
from app.services.event_processor import get_dashboard_stats
from app.models.events import Event, WebhookDelivery
from app.models.resources import ITwin, IModel
from app.models.integrations import Integration
from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

HOURS_MAP = {"1h": 1, "6h": 6, "24h": 24, "7d": 168, "30d": 720}

_feed_cache: dict = {}
_CACHE_TTL = 5


@router.get("/", response_class=HTMLResponse, tags=["Dashboard"])
async def root_redirect(request: Request):
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/dashboard")


@router.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
async def dashboard(request: Request, session: AsyncSession = Depends(get_session)):
    user = get_optional_user(request)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
    })


@router.get("/dashboard/feed", tags=["Dashboard"])
async def dashboard_feed(
    timeRange: str = Query(default="24h"),
    session: AsyncSession = Depends(get_session),
):
    cache_key = timeRange
    now = time.time()
    if cache_key in _feed_cache and now - _feed_cache[cache_key]["ts"] < _CACHE_TTL:
        return _feed_cache[cache_key]["data"]

    hours = HOURS_MAP.get(timeRange, 24)
    stats = await get_dashboard_stats(session, hours=hours)

    integrations_connected = await session.scalar(
        select(func.count(Integration.id)).where(Integration.status == "connected")
    ) or 0

    total_webhooks = await session.scalar(select(func.count(WebhookDelivery.id))) or 0
    error_count = await session.scalar(
        select(func.count(WebhookDelivery.id)).where(WebhookDelivery.processing_status == "error")
    ) or 0
    error_rate = round((error_count / total_webhooks * 100), 1) if total_webhooks else 0.0

    total = stats["total_events"]
    top_types = sorted(stats["type_counts"].items(), key=lambda x: -x[1])[:5]

    if total > 0:
        insight = f"Received {total} events in the last {timeRange}. "
        if top_types:
            insight += f"Most common: {top_types[0][0]} ({top_types[0][1]} occurrences). "
        insight += f"Activity across {stats['unique_itwins']} iTwins and {stats['unique_imodels']} iModels."
        if integrations_connected:
            insight += f" {integrations_connected} integration(s) active."
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
            "processing_status": e.processing_status,
            "received_at": e.received_at.isoformat(),
        })

    payload = {
        "meta": {"timeRange": timeRange, "generatedAt": datetime.utcnow().isoformat(), "cached": False},
        "kpis": {
            "totalEvents": total,
            "uniqueITwins": stats["unique_itwins"],
            "uniqueIModels": stats["unique_imodels"],
            "eventTypes": len(stats["type_counts"]),
            "integrationsConnected": integrations_connected,
            "errorRate": error_rate,
        },
        "health": health,
        "recentEvents": recent,
        "insights": insight,
        "eventTypeBreakdown": stats["type_counts"],
        "categoryBreakdown": stats["cat_counts"],
    }

    _feed_cache[cache_key] = {"ts": now, "data": payload}
    return payload


@router.get("/api/stats", tags=["Dashboard"])
async def system_stats(session: AsyncSession = Depends(get_session)):
    from app.db.database import _app_start_time
    total_events = await session.scalar(select(func.count(Event.id))) or 0
    total_itwins = await session.scalar(select(func.count(ITwin.id))) or 0
    total_imodels = await session.scalar(select(func.count(IModel.id))) or 0
    total_deliveries = await session.scalar(select(func.count(WebhookDelivery.id))) or 0
    processed = await session.scalar(
        select(func.count(WebhookDelivery.id)).where(WebhookDelivery.processing_status == "processed")
    ) or 0
    errors = await session.scalar(
        select(func.count(WebhookDelivery.id)).where(WebhookDelivery.processing_status == "error")
    ) or 0
    integrations_connected = await session.scalar(
        select(func.count(Integration.id)).where(Integration.status == "connected")
    ) or 0
    uptime_seconds = int(time.time() - _app_start_time)
    hours, rem = divmod(uptime_seconds, 3600)
    minutes = rem // 60
    return {
        "total_events": total_events,
        "total_itwins": total_itwins,
        "total_imodels": total_imodels,
        "total_deliveries": total_deliveries,
        "processed_ok": processed,
        "processing_errors": errors,
        "integrations_connected": integrations_connected,
        "uptime_seconds": uptime_seconds,
        "uptime_human": f"{hours}h {minutes}m",
        "app_version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/events-view", response_class=HTMLResponse, tags=["Dashboard"])
async def events_view(request: Request, session: AsyncSession = Depends(get_session)):
    user = get_optional_user(request)
    return templates.TemplateResponse("events.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
    })


@router.get("/itwins-view", response_class=HTMLResponse, tags=["Dashboard"])
async def itwins_view(request: Request, session: AsyncSession = Depends(get_session)):
    user = get_optional_user(request)
    return templates.TemplateResponse("itwins.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
    })
