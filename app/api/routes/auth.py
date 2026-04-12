from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select

from app.db.database import get_session
from app.models.auth import User
from app.models.events import AuditLog
from app.core.security import verify_password, create_token
from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


async def _write_audit(session: AsyncSession, action: str, user_id: str | None,
                       ip_address: str, detail: str = "") -> None:
    session.add(AuditLog(
        user_id=user_id,
        action=action,
        detail=detail,
        ip_address=ip_address,
    ))
    await session.commit()


@router.get("/login", response_class=HTMLResponse, tags=["Auth"])
async def login_page(request: Request):
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("login.html", {"request": request, "error": None, "app_name": settings.APP_NAME})


@router.post("/login", tags=["Auth"])
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    ip_address = request.client.host if request.client else "unknown"
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if not user or not verify_password(password, user.hashed_password):
        await _write_audit(session, "login.failed", None, ip_address, f"email={email}")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password", "app_name": settings.APP_NAME},
            status_code=401,
        )

    if not user.is_active:
        await _write_audit(session, "login.blocked", user.id, ip_address, "account disabled")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Account is disabled. Contact your admin.", "app_name": settings.APP_NAME},
            status_code=403,
        )

    user.last_login = datetime.now(timezone.utc)
    session.add(user)
    await _write_audit(session, "login.success", user.id, ip_address)

    token = create_token({"sub": user.id, "email": user.email, "role": user.role})
    response = RedirectResponse("/dashboard", status_code=302)
    response.set_cookie(
        "access_token", token,
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )
    return response


@router.get("/logout", tags=["Auth"])
async def logout(request: Request, session: AsyncSession = Depends(get_session)):
    ip_address = request.client.host if request.client else "unknown"
    token = request.cookies.get("access_token")
    actor_id = None
    if token:
        from app.core.security import decode_token
        payload = decode_token(token)
        if payload:
            actor_id = payload.get("sub")
    await _write_audit(session, "logout", actor_id, ip_address)
    response = RedirectResponse("/login")
    response.delete_cookie("access_token")
    return response


# ── User Management API ────────────────────────────────────────────────────────

@router.get("/api/users", tags=["Users"])
async def list_users(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(User).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ],
        "total": len(users),
    }


@router.post("/api/users", tags=["Users"])
async def create_user(request: Request, session: AsyncSession = Depends(get_session)):
    body = await request.json()
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")
    if not email or not password:
        raise HTTPException(status_code=422, detail="email and password are required")
    existing = await session.execute(select(User).where(User.email == email))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="A user with that email already exists")
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=body.get("full_name", ""),
        role=body.get("role", "viewer"),
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role}


@router.put("/api/users/{user_id}", tags=["Users"])
async def update_user(user_id: str, request: Request, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    body = await request.json()
    if "full_name" in body:
        user.full_name = body["full_name"]
    if "role" in body and body["role"] in ("admin", "operator", "viewer"):
        user.role = body["role"]
    if "is_active" in body:
        user.is_active = bool(body["is_active"])
    session.add(user)
    await session.commit()
    return {"id": user.id, "email": user.email, "role": user.role, "is_active": user.is_active}


@router.post("/api/users/{user_id}/reset-password", tags=["Users"])
async def reset_password(user_id: str, request: Request, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    body = await request.json()
    new_password = body.get("password", "")
    if len(new_password) < 6:
        raise HTTPException(status_code=422, detail="Password must be at least 6 characters")
    user.hashed_password = hash_password(new_password)
    session.add(user)
    await session.commit()
    return {"ok": True, "message": f"Password reset for {user.email}"}


@router.delete("/api/users/{user_id}", tags=["Users"])
async def delete_user(user_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)
    await session.commit()
    return {"deleted": user_id}
