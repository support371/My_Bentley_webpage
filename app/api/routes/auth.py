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
