from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select

from app.db.database import get_session
from app.core.security import get_optional_user
from app.core.config import settings
from app.models.ops import ControlPlaneModule
from app.models.integrations import Integration

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/control-plane", response_class=HTMLResponse, tags=["Enterprise"])
async def control_plane_page(request: Request, session: AsyncSession = Depends(get_session)):
    user = get_optional_user(request)
    result = await session.execute(select(ControlPlaneModule))
    modules = result.scalars().all()

    integrations_result = await session.execute(select(Integration).limit(5))
    integrations = integrations_result.scalars().all()

    return templates.TemplateResponse("control.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
        "modules": modules,
        "integrations": integrations,
        "environments": [
            {"name": "Development", "path": "/control-plane/env/development"},
            {"name": "Marketing", "path": "/control-plane/env/marketing"},
            {"name": "Automation", "path": "/control-plane/env/automation"},
            {"name": "Operations", "path": "/control-plane/env/operations"}
        ]
    })

@router.get("/control-plane/website-studio", response_class=HTMLResponse, tags=["Enterprise"])
async def website_studio_page(request: Request):
    user = get_optional_user(request)
    return templates.TemplateResponse("control/website_studio.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
        "sites": [
            {"name": "Bentley Main Site", "url": "bentley.com", "status": "Published", "visitors": "1.2M / mo", "type": "Marketing"},
            {"name": "Developer Docs", "url": "docs.bentley.com", "status": "Published", "visitors": "450K / mo", "type": "Documentation"},
            {"name": "Partner Portal", "url": "partners.bentley.com", "status": "Draft", "visitors": "-", "type": "Portal"}
        ]
    })

@router.get("/control-plane/infrastructure", response_class=HTMLResponse, tags=["Enterprise"])
async def infrastructure_console_page(request: Request):
    user = get_optional_user(request)
    return templates.TemplateResponse("control/infrastructure.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
        "metrics": {
            "total_compute": "2,048 vCPUs",
            "memory_allocated": "16.4 TB",
            "cloud_spend": "$142.5k",
            "active_nodes": 44
        },
        "clusters": [
            {"name": "Azure East US", "status": "Healthy", "region": "US East", "nodes": 24, "cpu": 65, "mem": 72, "provider": "Azure AKS"},
            {"name": "AWS West Europe", "status": "Healthy", "region": "EU West", "nodes": 12, "cpu": 42, "mem": 48, "provider": "AWS EKS"},
            {"name": "GCP Asia Southeast", "status": "Warning", "region": "Asia SE", "nodes": 8, "cpu": 88, "mem": 92, "provider": "GCP GKE"}
        ]
    })

@router.get("/control-plane/env/{env_name}", response_class=HTMLResponse, tags=["Enterprise"])
async def environment_page(request: Request, env_name: str):
    user = get_optional_user(request)
    env_title = env_name.replace("-", " ").title()
    return templates.TemplateResponse("control/environment.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
        "env_name": env_name,
        "env_title": env_title
    })

@router.get("/api/control-plane", tags=["Enterprise"])
async def api_control_plane(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(ControlPlaneModule))
    modules = result.scalars().all()
    return {
        "modules": [{"name": m.name, "status": m.status, "summary": m.summary} for m in modules],
        "environments": ["Development", "Marketing", "Automation", "Operations"]
    }
