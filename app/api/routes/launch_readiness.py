from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select

from app.db.database import get_session
from app.core.security import require_admin
from app.core.config import settings
from app.services.launch_readiness import get_launch_readiness as get_readiness_logic
from app.models.ops import LaunchCheck

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin/launch-readiness", response_class=HTMLResponse, tags=["Admin"])
async def launch_readiness_page(request: Request, user: dict = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    readiness = get_readiness_logic()
    result = await session.execute(select(LaunchCheck))
    db_checks = result.scalars().all()

    return templates.TemplateResponse("admin_launch_readiness.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
        "readiness": readiness,
        "db_checks": db_checks
    })

@router.get("/api/launch-readiness", tags=["Admin"])
async def api_launch_readiness(user: dict = Depends(require_admin)):
    readiness = get_readiness_logic()
    return readiness
