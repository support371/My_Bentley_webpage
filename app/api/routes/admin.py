import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select

from app.db.database import get_session
from app.core.security import get_optional_user, require_admin
from app.models.tenants import Tenant
from app.models.resources import AlertRule, Alert
from app.models.events import WebhookDelivery
from app.services.bentley.client import test_connection, get_access_token, list_itwins, list_webhooks, create_webhook
from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin", response_class=HTMLResponse, tags=["Admin"])
async def admin_dashboard(request: Request, user: dict = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Tenant).limit(10))
    tenants = result.scalars().all()
    delivery_result = await session.execute(
        select(WebhookDelivery).order_by(WebhookDelivery.received_at.desc()).limit(20)
    )
    recent_deliveries = delivery_result.scalars().all()
    alert_result = await session.execute(
        select(Alert).order_by(Alert.triggered_at.desc()).limit(10)
    )
    recent_alerts = alert_result.scalars().all()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
        "tenants": tenants,
        "recent_deliveries": recent_deliveries,
        "recent_alerts": recent_alerts,
        "bentley_configured": bool(settings.BENTLEY_CLIENT_ID),
        "settings": settings,
    })


@router.post("/admin/test-connection", tags=["Admin"])
async def api_test_connection(request: Request, user: dict = Depends(require_admin)):
    body = await request.json()
    result = await test_connection(
        client_id=body.get("client_id") or settings.BENTLEY_CLIENT_ID,
        client_secret=body.get("client_secret") or settings.BENTLEY_CLIENT_SECRET,
    )
    return result


@router.post("/admin/fetch-itwins", tags=["Admin"])
async def api_fetch_itwins(request: Request, user: dict = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    body = await request.json()
    cid = body.get("client_id") or settings.BENTLEY_CLIENT_ID
    csec = body.get("client_secret") or settings.BENTLEY_CLIENT_SECRET
    token = await get_access_token(cid, csec)
    if not token:
        raise HTTPException(status_code=400, detail="Could not obtain access token")
    itwins = await list_itwins(token)
    return {"count": len(itwins), "itwins": itwins[:20]}


@router.get("/admin/webhooks", tags=["Admin"])
async def api_list_webhooks(request: Request, user: dict = Depends(require_admin)):
    token = await get_access_token()
    if not token:
        raise HTTPException(status_code=400, detail="Bentley not configured")
    wh = await list_webhooks(token)
    return {"webhooks": wh}


@router.post("/admin/webhooks/create", tags=["Admin"])
async def api_create_webhook(request: Request, user: dict = Depends(require_admin)):
    body = await request.json()
    token = await get_access_token()
    if not token:
        raise HTTPException(status_code=400, detail="Bentley not configured")
    wh = await create_webhook(
        token=token,
        callback_url=body["callbackUrl"],
        secret=body.get("secret", settings.WEBHOOK_SECRET),
        event_types=body.get("eventTypes", []),
        itwin_id=body.get("iTwinId"),
    )
    return {"webhook": wh}


@router.get("/admin/alert-rules", tags=["Admin"])
async def list_alert_rules(request: Request, user: dict = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(AlertRule))
    rules = result.scalars().all()
    return {"rules": [
        {
            "id": r.id, "name": r.name, "rule_type": r.rule_type,
            "is_active": r.is_active, "created_at": r.created_at.isoformat()
        }
        for r in rules
    ]}


@router.post("/admin/alert-rules", tags=["Admin"])
async def create_alert_rule(request: Request, user: dict = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    body = await request.json()
    rule = AlertRule(
        name=body["name"],
        rule_type=body.get("rule_type", "event_type_match"),
        conditions=json.dumps(body.get("conditions", {})),
        destinations=json.dumps(body.get("destinations", [])),
    )
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return {"id": rule.id, "name": rule.name}
