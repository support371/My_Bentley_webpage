import json
import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select

from app.db.database import get_session
from app.core.security import get_optional_user
from app.models.tenants import Tenant
from app.models.resources import AlertRule, Alert
from app.models.events import WebhookDelivery
from app.services.bentley.client import test_connection, get_access_token, list_itwins, list_webhooks, create_webhook
from app.services.bentley import diagnostics as diag
from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin", response_class=HTMLResponse, tags=["Admin"])
async def admin_dashboard(request: Request, session: AsyncSession = Depends(get_session)):
    user = get_optional_user(request)
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

    summary = await diag.summarize_bentley_readiness(request)

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
        "tenants": tenants,
        "recent_deliveries": recent_deliveries,
        "recent_alerts": recent_alerts,
        "bentley_configured": bool(settings.BENTLEY_CLIENT_ID),
        "settings": settings,
        "diag_summary": summary,
    })


@router.get("/admin/diagnostics", response_class=HTMLResponse, tags=["Admin"])
async def admin_diagnostics_page(request: Request, session: AsyncSession = Depends(get_session)):
    user = get_optional_user(request)
    summary = await diag.summarize_bentley_readiness(request)
    return templates.TemplateResponse("admin_diagnostics.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
        "summary": summary,
        "settings": settings,
    })


# ─── Diagnostics API ─────────────────────────────────────────────────────────

@router.get("/api/admin/diagnostics/summary", tags=["Admin Diagnostics"])
async def diagnostics_summary(request: Request):
    return await diag.summarize_bentley_readiness(request)


@router.post("/api/admin/diagnostics/test-oauth", tags=["Admin Diagnostics"])
async def diagnostics_test_oauth(request: Request):
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    cid = body.get("client_id") or settings.BENTLEY_CLIENT_ID
    csec = body.get("client_secret") or settings.BENTLEY_CLIENT_SECRET
    return await diag.test_oauth_token(cid, csec)


@router.post("/api/admin/diagnostics/test-itwins", tags=["Admin Diagnostics"])
async def diagnostics_test_itwins(request: Request):
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    token = await get_access_token(
        body.get("client_id") or settings.BENTLEY_CLIENT_ID,
        body.get("client_secret") or settings.BENTLEY_CLIENT_SECRET,
    )
    return await diag.test_itwins_access(token)


@router.post("/api/admin/diagnostics/test-webhooks", tags=["Admin Diagnostics"])
async def diagnostics_test_webhooks(request: Request):
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    token = await get_access_token(
        body.get("client_id") or settings.BENTLEY_CLIENT_ID,
        body.get("client_secret") or settings.BENTLEY_CLIENT_SECRET,
    )
    return await diag.test_webhooks_access(token)


@router.get("/api/admin/diagnostics/callback-url", tags=["Admin Diagnostics"])
async def diagnostics_callback_url(request: Request):
    return diag.compute_callback_url(request)


@router.get("/api/admin/diagnostics/security-state", tags=["Admin Diagnostics"])
async def diagnostics_security_state():
    env_check = diag.check_env_configuration()
    sec_check = diag.check_webhook_security_state()
    is_prod = settings.ENVIRONMENT == "production"
    warnings = []
    if is_prod and settings.SKIP_SIGNATURE_VERIFY:
        warnings.append("SKIP_SIGNATURE_VERIFY is True in production")
    if is_prod and not settings.WEBHOOK_SECRET:
        warnings.append("WEBHOOK_SECRET missing in production")
    if is_prod and not settings.COOKIE_SECURE:
        warnings.append("COOKIE_SECURE is False in production")
    return {
        "environment": settings.ENVIRONMENT,
        "is_production": is_prod,
        "bentley_client_id_present": bool(settings.BENTLEY_CLIENT_ID),
        "bentley_client_id_masked": diag.mask_client_id(settings.BENTLEY_CLIENT_ID),
        "bentley_client_secret_present": bool(settings.BENTLEY_CLIENT_SECRET),
        "webhook_secret_present": bool(settings.WEBHOOK_SECRET),
        "signature_verify_enabled": not settings.SKIP_SIGNATURE_VERIFY,
        "cookie_secure": settings.COOKIE_SECURE,
        "production_warnings": warnings,
        "env_check": env_check,
        "security_check": sec_check,
    }


# ─── Bentley connection (original routes, hardened) ───────────────────────────

@router.post("/admin/test-connection", tags=["Admin"])
async def api_test_connection(request: Request):
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    result = await test_connection(
        client_id=body.get("client_id") or settings.BENTLEY_CLIENT_ID,
        client_secret=body.get("client_secret") or settings.BENTLEY_CLIENT_SECRET,
    )
    return result


@router.post("/admin/fetch-itwins", tags=["Admin"])
async def api_fetch_itwins(request: Request, session: AsyncSession = Depends(get_session)):
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    cid = body.get("client_id") or settings.BENTLEY_CLIENT_ID
    csec = body.get("client_secret") or settings.BENTLEY_CLIENT_SECRET
    token = await get_access_token(cid, csec)
    if not token:
        raise HTTPException(status_code=400, detail="Could not obtain access token — check BENTLEY_CLIENT_ID and BENTLEY_CLIENT_SECRET in Replit Secrets")
    itwins = await list_itwins(token)
    return {"count": len(itwins), "itwins": itwins[:20]}


@router.get("/admin/webhooks", tags=["Admin"])
async def api_list_webhooks():
    token = await get_access_token()
    if not token:
        raise HTTPException(status_code=400, detail="Bentley not configured — set credentials in Replit Secrets")
    wh = await list_webhooks(token)
    return {"webhooks": wh}


@router.post("/admin/webhooks/create", tags=["Admin"])
async def api_create_webhook(request: Request):
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
async def list_alert_rules(session: AsyncSession = Depends(get_session)):
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
async def create_alert_rule(request: Request, session: AsyncSession = Depends(get_session)):
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


@router.delete("/admin/alert-rules/{rule_id}", tags=["Admin"])
async def delete_alert_rule(rule_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalars().first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await session.delete(rule)
    await session.commit()
    return {"deleted": rule_id}


@router.post("/admin/alert-rules/{rule_id}/toggle", tags=["Admin"])
async def toggle_alert_rule(rule_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalars().first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.is_active = not rule.is_active
    session.add(rule)
    await session.commit()
    return {"id": rule_id, "is_active": rule.is_active}


@router.post("/admin/alerts/test-delivery", tags=["Admin"])
async def test_alert_delivery(request: Request):
    from app.services.alerts.engine import test_delivery
    body = await request.json()
    dest = body.get("destination", {})
    if not dest.get("type"):
        raise HTTPException(status_code=422, detail="destination.type is required")
    result = await test_delivery(dest)
    return result
