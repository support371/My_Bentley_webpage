from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.routes.integrations import INTEGRATION_CATALOG
from app.core.config import settings
from app.core.security import get_optional_user, require_admin, require_auth
from app.db.database import _app_start_time, get_session
from app.models.auth import User
from app.models.events import Event, WebhookDelivery
from app.models.integrations import Integration
from app.models.resources import Alert, AlertRule, IModel, ITwin
from app.services.event_processor import get_dashboard_stats

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

HOURS_MAP = {"1h": 1, "6h": 6, "24h": 24, "7d": 168, "30d": 720}
MOBILE_CATEGORY_MAP = {
    "slack": "Collaboration",
    "discord": "Collaboration",
    "pagerduty": "Incident Response / On-call",
    "jira": "ITSM / Service Desk",
    "linear": "ITSM / Service Desk",
    "github": "Workflow / Eventing",
    "gitlab": "Workflow / Eventing",
    "bitbucket": "Workflow / Eventing",
    "gitbucket": "Workflow / Eventing",
    "vercel": "Application Monitoring",
    "railway": "Application Monitoring",
    "cloudflare": "Application Monitoring",
    "azure": "Analytics",
    "openai": "AI",
    "gemini": "AI",
    "copilot": "AI",
    "deepseek": "AI",
    "cursor": "AI",
    "devin": "AI",
    "v0": "AI",
    "datadog": "Analytics",
    "sentry": "Analytics",
}
MOBILE_GROUP_ORDER = [
    "Collaboration",
    "Incident Response / On-call",
    "ITSM / Service Desk",
    "Workflow / Eventing",
    "Analytics",
    "AI",
    "Application Monitoring",
    "Other",
]


def _human_uptime() -> str:
    uptime_seconds = int(time.time() - _app_start_time)
    hours, rem = divmod(uptime_seconds, 3600)
    minutes = rem // 60
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


async def _count_alerts(session: AsyncSession) -> int:
    try:
        alert_count = await session.scalar(select(func.count(Alert.id))) or 0
    except Exception:
        alert_count = 0
    if alert_count:
        return int(alert_count)
    return int(
        await session.scalar(
            select(func.count(Event.id)).where(Event.severity.in_(["error", "warning"]))
        )
        or 0
    )


async def _integration_items(session: AsyncSession) -> List[Dict[str, Any]]:
    result = await session.execute(select(Integration))
    connected_rows = {row.slug: row for row in result.scalars().all()}
    items: List[Dict[str, Any]] = []
    for item in INTEGRATION_CATALOG:
        row = connected_rows.get(item["slug"])
        status = row.status if row else "disconnected"
        items.append(
            {
                "slug": item["slug"],
                "name": item["name"],
                "description": item["description"],
                "category": item["category"],
                "mobile_category": MOBILE_CATEGORY_MAP.get(item["slug"], "Other"),
                "status": status,
                "is_enabled": bool(row.is_enabled) if row else False,
                "has_credentials": bool((row.api_key or row.webhook_url)) if row else False,
                "icon_emoji": item.get("icon_emoji", "🔌"),
                "icon_color": item.get("icon_color", "#64748b"),
                "docs_url": item.get("docs_url"),
                "last_tested_at": row.last_tested_at.isoformat() if row and row.last_tested_at else None,
                "last_test_result": row.last_test_result if row else None,
            }
        )
    return items


async def build_mobile_summary(session: AsyncSession, time_range: str = "24h") -> Dict[str, Any]:
    hours = HOURS_MAP.get(time_range, 24)
    stats = await get_dashboard_stats(session, hours=hours)
    integrations_connected = int(
        await session.scalar(select(func.count(Integration.id)).where(Integration.status == "connected")) or 0
    )
    total_events = int(await session.scalar(select(func.count(Event.id))) or 0)
    total_itwins = int(await session.scalar(select(func.count(ITwin.id))) or 0)
    total_imodels = int(await session.scalar(select(func.count(IModel.id))) or 0)
    alert_count = await _count_alerts(session)

    health = "healthy" if stats["total_events"] > 0 else ("idle" if total_events > 0 else "idle")
    if stats["total_events"] > 100:
        health = "busy"

    return {
        "meta": {"timeRange": time_range, "generatedAt": datetime.utcnow().isoformat() + "Z"},
        "health": health,
        "serviceStatus": "operational" if health in {"healthy", "busy", "idle"} else "degraded",
        "kpis": {
            "totalEvents": total_events,
            "windowEvents": stats["total_events"],
            "openAlerts": alert_count,
            "integrationsConnected": integrations_connected,
            "activeITwins": total_itwins,
            "activeIModels": total_imodels,
            "uptime": _human_uptime(),
        },
        "tabs": ["alarms", "monitors", "reports", "admin", "more"],
        "insight": (
            f"{stats['total_events']} events landed in the last {time_range}. "
            f"The platform is tracking {total_itwins} iTwins, {total_imodels} iModels, and {integrations_connected} connected integrations."
        ),
    }


async def build_mobile_alarms(session: AsyncSession, limit: int = 20) -> Dict[str, Any]:
    result = await session.execute(select(Event).order_by(Event.received_at.desc()).limit(limit))
    events = result.scalars().all()
    items: List[Dict[str, Any]] = []
    for event in events:
        severity = event.severity or "info"
        items.append(
            {
                "id": str(event.id),
                "title": event.event_type,
                "severity": severity,
                "status": event.processing_status or "processed",
                "category": event.event_category or "General",
                "project": event.itwin_name or event.itwin_id or "Unassigned",
                "model": event.imodel_name or event.imodel_id or "—",
                "receivedAt": event.received_at.isoformat() if event.received_at else None,
            }
        )
    return {"items": items, "total": len(items)}


async def build_mobile_monitors(session: AsyncSession, limit: int = 20) -> Dict[str, Any]:
    result = await session.execute(select(ITwin).order_by(ITwin.last_event_at.desc()).limit(limit))
    itwins = result.scalars().all()
    items: List[Dict[str, Any]] = []
    for tw in itwins:
        imodel_count = int(
            await session.scalar(select(func.count(IModel.id)).where(IModel.itwin_id == tw.id)) or 0
        )
        event_count = int(
            await session.scalar(select(func.count(Event.id)).where(Event.itwin_id == tw.id)) or 0
        )
        items.append(
            {
                "id": tw.id,
                "name": tw.display_name or tw.id,
                "status": tw.status or "active",
                "type": tw.type or "iTwin",
                "imodelCount": imodel_count,
                "eventCount": event_count,
                "lastEventAt": tw.last_event_at.isoformat() if tw.last_event_at else None,
            }
        )
    return {"items": items, "total": len(items)}


async def build_mobile_reports(session: AsyncSession) -> Dict[str, Any]:
    total_deliveries = int(await session.scalar(select(func.count(WebhookDelivery.id))) or 0)
    processed = int(
        await session.scalar(select(func.count(WebhookDelivery.id)).where(WebhookDelivery.processing_status == "processed"))
        or 0
    )
    errors = int(
        await session.scalar(select(func.count(WebhookDelivery.id)).where(WebhookDelivery.processing_status == "error"))
        or 0
    )
    error_rate = round((errors / total_deliveries) * 100, 1) if total_deliveries else 0.0
    return {
        "cards": [
            {"title": "Scheduled Reports", "value": "Ready", "detail": "Use platform exports and scheduled delivery patterns."},
            {"title": "Customize Report", "value": f"{processed}", "detail": "Processed deliveries available for operational reporting."},
            {"title": "SLA Settings", "value": f"{error_rate}%", "detail": "Current delivery error-rate proxy."},
            {"title": "CSV Export", "value": "/events/export", "detail": "Download event history for offline reporting."},
        ]
    }


async def build_mobile_admin_summary(session: AsyncSession) -> Dict[str, Any]:
    user_count = int(await session.scalar(select(func.count(User.id))) or 0)
    rule_count = int(await session.scalar(select(func.count(AlertRule.id))) or 0)
    integration_count = int(await session.scalar(select(func.count(Integration.id))) or 0)
    items = [
        {"section": "Inventory", "items": [{"label": "Monitors", "value": int(await session.scalar(select(func.count(ITwin.id))) or 0)}, {"label": "Monitor Groups", "value": "Planned"}]},
        {"section": "User Management", "items": [{"label": "Users", "value": user_count}, {"label": "User Groups", "value": "Phase 2"}]},
        {"section": "Configuration Profiles", "items": [{"label": "Location Profile", "value": "Ready"}, {"label": "Threshold & Availability", "value": rule_count}]},
        {"section": "Server Monitor", "items": [{"label": "Resource Check Profile", "value": "Ready"}, {"label": "Settings", "value": "Ready"}]},
        {"section": "Poller", "items": [{"label": "On-Premise Poller", "value": "Planned"}, {"label": "Mobile Network Poller", "value": "Planned"}]},
        {"section": "Operations", "items": [{"label": "Scheduled Maintenance", "value": "Ready"}, {"label": "Alert Logs", "value": rule_count}]},
        {"section": "Report Settings", "items": [{"label": "Scheduled Reports", "value": "Ready"}, {"label": "SLA Settings", "value": "Ready"}]},
        {"section": "Share", "items": [{"label": "Public Reports", "value": "Ready"}, {"label": "Operations Dashboard", "value": "Ready"}]},
        {"section": "Developer", "items": [{"label": "Device Key", "value": "Planned"}, {"label": "Integrations", "value": integration_count}]},
        {"section": "IT Automation", "items": [{"label": "Templates", "value": "Ready"}]},
    ]
    return {"groups": items}


async def build_mobile_more_summary(session: AsyncSession) -> Dict[str, Any]:
    integrations_connected = int(
        await session.scalar(select(func.count(Integration.id)).where(Integration.status == "connected")) or 0
    )
    return {
        "serviceStatus": "Operational",
        "items": [
            {"label": "Alert Notifications", "value": "Ready"},
            {"label": "Custom Dashboards", "value": "Ready"},
            {"label": "Scheduled Maintenance", "value": "Ready"},
            {"label": "Newsletter", "value": "Optional"},
            {"label": "Service Status", "value": "Operational"},
            {"label": "Tab Customization", "value": "Enabled"},
            {"label": "Trigger Test Alert", "value": "Ready"},
            {"label": "App Settings", "value": f"{integrations_connected} integrations"},
        ],
    }


async def build_mobile_integrations(session: AsyncSession) -> Dict[str, Any]:
    items = await _integration_items(session)
    groups: List[Dict[str, Any]] = []
    for group_name in MOBILE_GROUP_ORDER:
        group_items = [item for item in items if item["mobile_category"] == group_name]
        if group_items:
            groups.append({"name": group_name, "items": group_items})
    return {"groups": groups, "total": len(items)}


@router.get("/mobile", response_class=HTMLResponse, tags=["Mobile"])
async def mobile_root() -> RedirectResponse:
    return RedirectResponse("/mobile/alarms")


@router.get("/mobile/alarms", response_class=HTMLResponse, tags=["Mobile"])
async def mobile_alarms_page(request: Request, session: AsyncSession = Depends(get_session)):
    user = get_optional_user(request)
    return templates.TemplateResponse("mobile/alarms.html", {"request": request, "user": user, "app_name": settings.APP_NAME, "active_mobile_tab": "alarms"})


@router.get("/mobile/monitors", response_class=HTMLResponse, tags=["Mobile"])
async def mobile_monitors_page(request: Request, session: AsyncSession = Depends(get_session)):
    user = get_optional_user(request)
    return templates.TemplateResponse("mobile/monitors.html", {"request": request, "user": user, "app_name": settings.APP_NAME, "active_mobile_tab": "monitors"})


@router.get("/mobile/reports", response_class=HTMLResponse, tags=["Mobile"])
async def mobile_reports_page(request: Request, session: AsyncSession = Depends(get_session)):
    user = get_optional_user(request)
    return templates.TemplateResponse("mobile/reports.html", {"request": request, "user": user, "app_name": settings.APP_NAME, "active_mobile_tab": "reports"})


@router.get("/mobile/admin", response_class=HTMLResponse, tags=["Mobile"])
async def mobile_admin_page(request: Request, user: dict = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    return templates.TemplateResponse("mobile/admin.html", {"request": request, "user": user, "app_name": settings.APP_NAME, "active_mobile_tab": "admin"})


@router.get("/mobile/more", response_class=HTMLResponse, tags=["Mobile"])
async def mobile_more_page(request: Request, session: AsyncSession = Depends(get_session)):
    user = get_optional_user(request)
    return templates.TemplateResponse("mobile/more.html", {"request": request, "user": user, "app_name": settings.APP_NAME, "active_mobile_tab": "more"})


@router.get("/mobile/integrations", response_class=HTMLResponse, tags=["Mobile"])
async def mobile_integrations_page(request: Request, session: AsyncSession = Depends(get_session)):
    user = get_optional_user(request)
    return templates.TemplateResponse("mobile/integrations.html", {"request": request, "user": user, "app_name": settings.APP_NAME, "active_mobile_tab": "integrations"})


@router.get("/api/mobile/summary", tags=["Mobile"])
async def mobile_summary(timeRange: str = Query(default="24h"), session: AsyncSession = Depends(get_session)):
    return await build_mobile_summary(session, timeRange)


@router.get("/api/mobile/alarms", tags=["Mobile"])
async def mobile_alarms(limit: int = Query(default=20, ge=1, le=100), session: AsyncSession = Depends(get_session)):
    return await build_mobile_alarms(session, limit)


@router.get("/api/mobile/monitors", tags=["Mobile"])
async def mobile_monitors(limit: int = Query(default=20, ge=1, le=100), session: AsyncSession = Depends(get_session)):
    return await build_mobile_monitors(session, limit)


@router.get("/api/mobile/reports", tags=["Mobile"])
async def mobile_reports(session: AsyncSession = Depends(get_session)):
    return await build_mobile_reports(session)


@router.get("/api/mobile/admin-summary", tags=["Mobile"])
async def mobile_admin_summary(user: dict = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    return await build_mobile_admin_summary(session)


@router.get("/api/mobile/more-summary", tags=["Mobile"])
async def mobile_more_summary(session: AsyncSession = Depends(get_session)):
    return await build_mobile_more_summary(session)


@router.get("/api/mobile/integrations", tags=["Mobile"])
async def mobile_integrations(session: AsyncSession = Depends(get_session)):
    return await build_mobile_integrations(session)


@router.post("/api/mobile/monitors/discover", tags=["Mobile"])
async def mobile_discover_monitor(
    request: Request,
    user: dict = Depends(require_auth),
    payload: Dict[str, Any] = Body(default={}),
):
    url = (payload.get("url") or payload.get("domain") or "").strip()
    label = (payload.get("label") or payload.get("name") or "External Monitor").strip() or "External Monitor"
    env = (payload.get("environment") or "production").strip() or "production"
    if not url:
        return JSONResponse(status_code=400, content={"detail": "url is required"})
    return {
        "ok": True,
        "message": "Monitor discovery stub accepted.",
        "item": {
            "id": f"discover-{int(time.time())}",
            "name": label,
            "target": url,
            "environment": env,
            "status": "pending_verification",
            "nextStep": "Map this to Bentley/iTwin resources or a future persistent monitor model.",
        },
    }


@router.post("/api/mobile/test-alert", tags=["Mobile"])
async def mobile_test_alert(request: Request, user: dict = Depends(require_auth)):
    return {
        "ok": True,
        "message": "Mobile test alert acknowledged.",
        "alert": {
            "title": "Mobile test alert",
            "severity": "info",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    }


@router.post("/api/mobile/tab-customization", tags=["Mobile"])
async def mobile_tab_customization(
    request: Request,
    user: dict = Depends(require_auth),
    payload: Dict[str, Any] = Body(default={}),
):
    tabs = payload.get("tabs") or []
    response = JSONResponse({"ok": True, "tabs": tabs})
    response.set_cookie("mobile_tabs", ",".join(tabs), httponly=False, samesite="lax")
    return response


@router.post("/api/mobile/timezone", tags=["Mobile"])
async def mobile_timezone(
    request: Request,
    user: dict = Depends(require_auth),
    payload: Dict[str, Any] = Body(default={}),
):
    timezone = payload.get("timezone") or "UTC"
    response = JSONResponse({"ok": True, "timezone": timezone})
    response.set_cookie("mobile_timezone", timezone, httponly=False, samesite="lax")
    return response


@router.post("/api/mobile/account/add", tags=["Mobile"])
async def mobile_account_add(
    request: Request,
    user: dict = Depends(require_auth),
    payload: Dict[str, Any] = Body(default={}),
):
    return {
        "ok": True,
        "message": "Account add flow stub accepted.",
        "account": {
            "name": payload.get("name") or "New Account",
            "email": payload.get("email") or user.get("email"),
            "status": "pending_validation",
        },
    }
