from fastapi import APIRouter, Body, Depends
from typing import Dict, Any
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.database import get_session
from app.core.security import require_auth

router = APIRouter()

@router.post("/api/agent/explain-health", tags=["Agent"])
async def explain_health(
    payload: Dict[str, Any] = Body(default={}),
    user: Dict[str, Any] = Depends(require_auth),
    session: AsyncSession = Depends(get_session)
):
    from app.services.event_processor import get_dashboard_stats
    stats = await get_dashboard_stats(session, hours=24)

    total = stats["total_events"]
    errors = sum(1 for e in stats["recent_events"] if e.severity == "error")
    warnings = sum(1 for e in stats["recent_events"] if e.severity == "warning")

    if total == 0:
        summary = "The platform is currently idle. No events have been received in the last 24 hours."
        actions = ["Verify Bentley webhook configuration", "Check integration status"]
    elif errors > 0:
        summary = f"Platform health is degraded. Detected {errors} error(s) and {warnings} warning(s) in the last 24 hours out of {total} total events."
        actions = ["Investigate recent synchronization failures", "Review error logs for affected iModels"]
    else:
        summary = f"Platform health is stable. Processing {total} events with no recent errors detected."
        actions = ["Monitor version publication rate", "Optimize alert rules for high-volume iTwins"]

    return {
        "summary": summary,
        "recommended_actions": actions,
        "stats": {
            "window_total": total,
            "errors": errors,
            "warnings": warnings
        }
    }
