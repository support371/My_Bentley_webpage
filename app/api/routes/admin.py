import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select

from app.db.database import get_session
from app.core.security import get_optional_user, require_admin
from app.models.tenants import Tenant
from app.models.resources import AlertRule, Alert
from app.models.auth import User
from app.models.events import WebhookDelivery
from app.services.bentley.client import test_connection, get_access_token, list_itwins, list_webhooks, create_webhook
from app.core.config import settings
from app.core.security import hash_password

logger = logging.getLogger("itwin_ops.admin")
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
        "platform_info": {
            "APP_VERSION": settings.APP_VERSION,
            "ENVIRONMENT": settings.ENVIRONMENT,
            "DATABASE_URL": "sqlite" if "sqlite" in settings.DATABASE_URL else "postgresql",
            "SKIP_SIGNATURE_VERIFY": settings.SKIP_SIGNATURE_VERIFY,
            "JWT_EXPIRE_MINUTES": settings.JWT_EXPIRE_MINUTES,
            "WEBHOOK_SECRET_SET": bool(settings.WEBHOOK_SECRET),
        },
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


# ── Alert Rules ──────────────────────────────────────────────────────────────

@router.get("/admin/alert-rules", tags=["Admin"])
async def list_alert_rules(request: Request, user: dict = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(AlertRule).order_by(AlertRule.created_at.desc()))
    rules = result.scalars().all()
    return {"rules": [
        {
            "id": r.id, "name": r.name, "rule_type": r.rule_type,
            "is_active": r.is_active,
            "conditions": json.loads(r.conditions) if r.conditions else {},
            "destinations": json.loads(r.destinations) if r.destinations else [],
            "created_at": r.created_at.isoformat(),
        }
        for r in rules
    ]}


@router.post("/admin/alert-rules", tags=["Admin"])
async def create_alert_rule(request: Request, user: dict = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    body = await request.json()
    if not body.get("name"):
        raise HTTPException(status_code=422, detail="Rule name is required")
    rule = AlertRule(
        name=body["name"],
        rule_type=body.get("rule_type", "event_type_match"),
        conditions=json.dumps(body.get("conditions", {})),
        destinations=json.dumps(body.get("destinations", [])),
        is_active=True,
    )
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return {"id": rule.id, "name": rule.name, "is_active": rule.is_active}


@router.delete("/admin/alert-rules/{rule_id}", tags=["Admin"])
async def delete_alert_rule(rule_id: str, request: Request, user: dict = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalars().first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await session.delete(rule)
    await session.commit()
    return {"deleted": rule_id}


@router.post("/admin/alert-rules/{rule_id}/toggle", tags=["Admin"])
async def toggle_alert_rule(rule_id: str, request: Request, user: dict = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalars().first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.is_active = not rule.is_active
    session.add(rule)
    await session.commit()
    return {"id": rule_id, "is_active": rule.is_active}


@router.post("/admin/alerts/test-delivery", tags=["Admin"])
async def test_alert_delivery(request: Request, user: dict = Depends(require_admin)):
    body = await request.json()
    dest = body.get("destination", {})
    dtype = dest.get("type", "webhook")
    import httpx
    test_payload = {
        "text": "✅ iTwin Ops Center — test delivery successful",
        "event_type": "test.delivery",
        "severity": "info",
        "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        if dtype in ("slack", "discord", "webhook"):
            url = dest.get("url", "")
            if not url:
                return {"ok": False, "error": "No URL provided"}
            async with httpx.AsyncClient(timeout=5) as client:
                if dtype == "slack":
                    r = await client.post(url, json={"text": test_payload["text"]})
                elif dtype == "discord":
                    r = await client.post(url, json={"content": test_payload["text"]})
                else:
                    r = await client.post(url, json=test_payload)
            return {"ok": r.status_code < 400, "status": r.status_code}
        else:
            return {"ok": True, "message": f"Test for {dtype} noted (no external call needed)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── User Management ───────────────────────────────────────────────────────────

@router.get("/api/users", tags=["Users"])
async def list_users(request: Request, user: dict = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return {
        "total": len(users),
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name or "",
                "role": u.role,
                "is_active": u.is_active,
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
    }


@router.post("/api/users", tags=["Users"])
async def create_user(request: Request, user: dict = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    body = await request.json()
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")
    if not email or not password:
        raise HTTPException(status_code=422, detail="email and password are required")
    existing = await session.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")
    new_user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=body.get("full_name", ""),
        role=body.get("role", "viewer"),
        is_active=True,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return {"id": new_user.id, "email": new_user.email, "role": new_user.role}


@router.put("/api/users/{user_id}", tags=["Users"])
async def update_user(user_id: str, request: Request, user: dict = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    body = await request.json()
    result = await session.execute(select(User).where(User.id == user_id))
    target = result.scalars().first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if "full_name" in body:
        target.full_name = body["full_name"]
    if "role" in body:
        target.role = body["role"]
    if "is_active" in body:
        target.is_active = bool(body["is_active"])
    session.add(target)
    await session.commit()
    return {"id": target.id, "email": target.email, "role": target.role, "is_active": target.is_active}


@router.post("/api/users/{user_id}/reset-password", tags=["Users"])
async def reset_user_password(user_id: str, request: Request, user: dict = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    body = await request.json()
    new_pw = body.get("password", "")
    if len(new_pw) < 6:
        raise HTTPException(status_code=422, detail="Password must be at least 6 characters")
    result = await session.execute(select(User).where(User.id == user_id))
    target = result.scalars().first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.hashed_password = hash_password(new_pw)
    session.add(target)
    await session.commit()
    return {"ok": True}


@router.delete("/api/users/{user_id}", tags=["Users"])
async def delete_user(user_id: str, request: Request, user: dict = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    if user.get("sub") == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    result = await session.execute(select(User).where(User.id == user_id))
    target = result.scalars().first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(target)
    await session.commit()
    return {"deleted": user_id}
