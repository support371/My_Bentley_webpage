from datetime import datetime, timezone
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.security import get_optional_user
from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _imodel_payload() -> dict:
    now = datetime.now(timezone.utc).isoformat()
    imodels = [
        {
            "id": "civil-infrastructure-hub",
            "display_name": "Civil Infrastructure Hub",
            "name": "Civil Infrastructure Hub",
            "state": "initialized",
            "itwin_id": "smart-city-alpha",
            "itwin_name": "Smart City Alpha",
            "event_count": 18,
            "last_event_at": now,
            "created_at": now,
        },
        {
            "id": "roads-bridges-network",
            "display_name": "Roads & Bridges Network",
            "name": "Roads & Bridges Network",
            "state": "initialized",
            "itwin_id": "transport-grid",
            "itwin_name": "Transport Grid",
            "event_count": 11,
            "last_event_at": now,
            "created_at": now,
        },
        {
            "id": "digital-twin-facility-a",
            "display_name": "Digital Twin Facility A",
            "name": "Digital Twin Facility A",
            "state": "initialized",
            "itwin_id": "bentley-connect",
            "itwin_name": "Bentley Connect",
            "event_count": 7,
            "last_event_at": now,
            "created_at": now,
        },
    ]
    return {
        "imodels": imodels,
        "total": len(imodels),
        "states": ["initialized"],
        "source": "safe-static-runtime",
        "degraded": False,
        "error": None,
    }


@router.get("/imodels-view", response_class=HTMLResponse, tags=["iModels"])
async def imodels_view(request: Request):
    user = get_optional_user(request)
    return templates.TemplateResponse("imodels.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
    })


@router.get("/api/imodels", tags=["iModels"])
async def list_imodels():
    return _imodel_payload()
