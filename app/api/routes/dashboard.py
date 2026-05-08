import json
import time
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, func, text

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


# ─── PRIMARY ROUTES (canonical URL shell) ────────────────

@router.get("/", response_class=HTMLResponse, tags=["Dashboard"])
async def root(request: Request, session: AsyncSession = Depends(get_session)):
    """Dashboard at root — canonical entry point."""
    user = get_optional_user(request)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
        "page_title": "Dashboard",
    })


@router.get("/events", response_class=HTMLResponse, tags=["Events"])
async def events_page(request: Request, session: AsyncSession = Depends(get_session)):
    user = get_optional_user(request)
    return templates.TemplateResponse("events.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
        "page_title": "Event Stream",
    })


@router.get("/itwins", response_class=HTMLResponse, tags=["iTwins"])
async def itwins_page(request: Request, session: AsyncSession = Depends(get_session)):
    user = get_optional_user(request)
    return templates.TemplateResponse("itwins.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
        "page_title": "iTwins Explorer",
    })


@router.get("/webhooks", response_class=HTMLResponse, tags=["Webhooks"])
async def webhooks_page(request: Request, session: AsyncSession = Depends(get_session)):
    user = get_optional_user(request)
    # Load recent webhook deliveries for the UI table
    result = await session.execute(
        select(WebhookDelivery).order_by(WebhookDelivery.received_at.desc()).limit(100)
    )
    deliveries = result.scalars().all()

    total = await session.scalar(select(func.count(WebhookDelivery.id))) or 0
    processed = await session.scalar(
        select(func.count(WebhookDelivery.id)).where(WebhookDelivery.processing_status == "processed")
    ) or 0
    errors = await session.scalar(
        select(func.count(WebhookDelivery.id)).where(WebhookDelivery.processing_status == "error")
    ) or 0
    invalid_sig = await session.scalar(
        select(func.count(WebhookDelivery.id)).where(WebhookDelivery.signature_valid == False)  # noqa: E712
    ) or 0

    success_rate = round((processed / total * 100), 1) if total else 0.0

    return templates.TemplateResponse("webhooks.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
        "page_title": "Webhooks",
        "deliveries": deliveries,
        "stats": {
            "total": total,
            "processed": processed,
            "errors": errors,
            "invalid_sig": invalid_sig,
            "success_rate": success_rate,
        },
    })


# ─── BACKWARDS-COMPAT REDIRECTS ──────────────────────────

@router.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
async def dashboard_compat(request: Request):
    """Redirect legacy /dashboard to / for backwards compatibility."""
    return RedirectResponse("/", status_code=301)


@router.get("/events-view", response_class=HTMLResponse, tags=["Events"])
async def events_view_compat(request: Request):
    return RedirectResponse("/events", status_code=301)


@router.get("/itwins-view", response_class=HTMLResponse, tags=["iTwins"])
async def itwins_view_compat(request: Request):
    return RedirectResponse("/itwins", status_code=301)


# ─── DASHBOARD FEED (real backend data) ──────────────────

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

    total_events_alltime = await session.scalar(select(func.count(Event.id))) or 0
    total_itwins = await session.scalar(select(func.count(ITwin.id))) or 0
    total_imodels = await session.scalar(select(func.count(IModel.id))) or 0

    integrations_connected = await session.scalar(
        select(func.count(Integration.id)).where(Integration.status == "connected")
    ) or 0

    total_webhooks = await session.scalar(select(func.count(WebhookDelivery.id))) or 0
    error_count = await session.scalar(
        select(func.count(WebhookDelivery.id)).where(WebhookDelivery.processing_status == "error")
    ) or 0
    error_rate = round((error_count / total_webhooks * 100), 1) if total_webhooks else 0.0

    windowed_total = stats["total_events"]
    top_types = sorted(stats["type_counts"].items(), key=lambda x: -x[1])[:5]

    if total_events_alltime > 0:
        if windowed_total > 0:
            insight = f"Received {windowed_total} events in the last {timeRange}. "
            if top_types:
                insight += f"Most common: {top_types[0][0]} ({top_types[0][1]} occurrences). "
            insight += f"Activity across {stats['unique_itwins']} iTwins and {stats['unique_imodels']} iModels."
        else:
            insight = f"No events in the last {timeRange}. {total_events_alltime:,} total events on record."
        if integrations_connected:
            insight += f" {integrations_connected} integration(s) active."
    else:
        insight = "No events received yet. Use ⚡ Test Event to inject demo data."

    health = "healthy" if windowed_total > 0 else "idle"
    if windowed_total > 100:
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

    from app.services.launch_readiness import get_launch_readiness
    readiness = get_launch_readiness()

    payload = {
        "meta": {"timeRange": timeRange, "generatedAt": datetime.utcnow().isoformat(), "cached": False},
        "kpis": {
            "totalEvents": total_events_alltime,
            "uniqueITwins": total_itwins,
            "uniqueIModels": total_imodels,
            "eventTypes": len(stats["type_counts"]),
            "integrationsConnected": integrations_connected,
            "errorRate": error_rate,
        },
        "health": health,
        "recentEvents": recent,
        "insights": insight,
        "eventTypeBreakdown": stats["type_counts"],
        "categoryBreakdown": stats["cat_counts"],
        "systemStatus": {
            "overall": readiness["overall"],
            "checks": readiness["summary"]
        }
    }

    _feed_cache[cache_key] = {"ts": now, "data": payload}
    return payload


# ─── API ALIAS: /api/dashboard/summary ───────────────────

@router.get("/api/dashboard/summary", tags=["Dashboard"])
async def dashboard_summary(
    timeRange: str = Query(default="24h"),
    session: AsyncSession = Depends(get_session),
):
    """Alias for /dashboard/feed — canonical API endpoint for UI backend wiring."""
    return await dashboard_feed(timeRange=timeRange, session=session)


# ─── CHART & STATS ENDPOINTS ─────────────────────────────

@router.get("/api/charts/trend", tags=["Dashboard"])
async def chart_trend(
    timeRange: str = Query(default="24h"),
    session: AsyncSession = Depends(get_session),
):
    hours = HOURS_MAP.get(timeRange, 24)
    since = datetime.utcnow() - timedelta(hours=hours)
    now = datetime.utcnow()

    if hours <= 2:
        bucket = "minute"
        trunc = "strftime('%Y-%m-%d %H:%M', received_at)"
    elif hours <= 72:
        bucket = "hour"
        trunc = "strftime('%Y-%m-%d %H', received_at)"
    else:
        bucket = "day"
        trunc = "strftime('%Y-%m-%d', received_at)"

    q = text(f"SELECT {trunc} AS bucket, COUNT(*) AS cnt FROM events WHERE received_at >= :since GROUP BY bucket ORDER BY bucket")
    result = await session.execute(q, {"since": since})
    rows = result.fetchall()
        trunc_sql = "to_timestamp(floor(extract(epoch from received_at) / 300) * 300) AT TIME ZONE 'UTC'"
        step = timedelta(minutes=5)
        fmt = "%H:%M"
    elif hours <= 168:
        trunc_sql = "date_trunc('hour', received_at)"
        step = timedelta(hours=1)
        fmt = "%a %H:%M" if hours > 24 else "%H:%M"
    else:
        trunc_sql = "date_trunc('day', received_at)"
        step = timedelta(days=1)
        fmt = "%b %d"

    result = await session.execute(
        text(f"SELECT {trunc_sql} AS bucket, COUNT(*) AS cnt FROM events WHERE received_at >= :since GROUP BY bucket ORDER BY bucket"),
        {"since": since},
    )
    cat_rows = categories_result.fetchall()

    labels = [row.bucket for row in rows]
    counts = [int(row.cnt) for row in rows]

    current = since.replace(second=0, microsecond=0)
    if step == timedelta(minutes=5):
        current = current.replace(minute=(current.minute // 5) * 5)
    elif step == timedelta(hours=1):
        current = current.replace(minute=0)
    else:
        current = current.replace(hour=0, minute=0)

    labels, data = [], []
    while current <= now:
        labels.append(current.strftime(fmt))
        data.append(actual.get(current, 0))
        current += step

    return {"labels": labels, "data": data, "timeRange": timeRange, "total": sum(data)}


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
    hours_up, rem = divmod(uptime_seconds, 3600)
    minutes_up = rem // 60
    return {
        "total_events": total_events,
        "total_itwins": total_itwins,
        "total_imodels": total_imodels,
        "total_deliveries": total_deliveries,
        "processed_ok": processed,
        "processing_errors": errors,
        "integrations_connected": integrations_connected,
        "uptime_seconds": uptime_seconds,
        "uptime_human": f"{hours_up}h {minutes_up}m",
        "app_version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
