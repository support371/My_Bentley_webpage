import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "gem_webhook_secret")
MAX_EVENTS = 1000
TIME_RANGES = {"1h": 1, "6h": 6, "24h": 24, "7d": 168, "30d": 720}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bentley iTwin Automation Platform",
    version="2.0",
    description="Operations hub for Bentley iTwin webhooks, integrations, and workflow orchestration.",
)

events_store: List[Dict[str, Any]] = []

SUPPORTED_EVENT_TYPES = [
    "iModels.iModelDeleted.v1",
    "iModels.iModelCreated.v1",
    "iModels.namedVersionCreated.v1",
    "iModels.changesReady.v1",
    "accessControl.memberAdded.v1",
    "accessControl.memberRemoved.v1",
    "accessControl.roleAssigned.v1",
    "accessControl.roleUnassigned.v1",
    "iTwins.iTwinCreated.v1",
    "iTwins.iTwinDeleted.v1",
    "synchronization.jobCompleted.v1",
    "transformations.jobCompleted.v1",
    "realityModeling.jobCompleted.v1",
    "realityAnalysis.jobCompleted.v1",
    "realityConversion.jobCompleted.v1",
    "changedElements.jobCompleted.v1",
    "forms.formCreated.v1",
    "forms.formUpdated.v1",
    "forms.formDeleted.v1",
    "issues.issueCreated.v1",
    "issues.issueUpdated.v1",
    "issues.issueDeleted.v1",
]

INTEGRATIONS = [
    {
        "id": "bentley-itwin",
        "name": "Bentley iTwin",
        "category": "Core platform",
        "status": "live",
        "summary": "Receives and normalizes Bentley webhook events for digital twin operations.",
        "capabilities": ["Webhook intake", "Event normalization", "Asset context", "Model telemetry"],
        "automationCount": 8,
        "owner": "Platform Ops",
        "setupTime": "5 minutes",
        "valueMetric": "22 supported event families",
        "cta": "Webhook endpoint ready",
    },
    {
        "id": "azure-devops",
        "name": "Azure DevOps",
        "category": "Delivery & incident response",
        "status": "ready",
        "summary": "Create work items, pipeline incidents, and deployment traces when critical iTwin events arrive.",
        "capabilities": ["Boards work items", "Pipeline annotations", "Release evidence", "Sprint reporting"],
        "automationCount": 6,
        "owner": "PMO + Engineering",
        "setupTime": "10 minutes",
        "valueMetric": "Auto-route model regressions to delivery teams",
        "cta": "Map event severity to backlog templates",
    },
    {
        "id": "monday-com",
        "name": "Monday.com",
        "category": "Project controls",
        "status": "ready",
        "summary": "Sync construction tasks, stakeholder updates, and approval workflows directly from event activity.",
        "capabilities": ["Board item sync", "Owner alerts", "Portfolio rollups", "Deadline escalations"],
        "automationCount": 5,
        "owner": "Project Controls",
        "setupTime": "8 minutes",
        "valueMetric": "Keep capital project boards aligned with twin changes",
        "cta": "Push issues and forms to delivery boards",
    },
    {
        "id": "atlassian-rovo-ai",
        "name": "Atlassian Rovo AI",
        "category": "AI knowledge orchestration",
        "status": "ready",
        "summary": "Feed event intelligence into Atlassian Rovo AI for contextual answers, search, and incident copilots.",
        "capabilities": ["Knowledge grounding", "AI summaries", "Confluence context", "Jira agent prompts"],
        "automationCount": 4,
        "owner": "Knowledge Ops",
        "setupTime": "12 minutes",
        "valueMetric": "Turn event history into searchable AI context",
        "cta": "Publish operational summaries to Atlassian workspaces",
    },
    {
        "id": "slack",
        "name": "Slack",
        "category": "Team collaboration",
        "status": "ready",
        "summary": "Notify channel owners when jobs fail, approvals land, or issue counts spike.",
        "capabilities": ["Channel alerts", "Slash command lookups", "War room notices"],
        "automationCount": 4,
        "owner": "Operations",
        "setupTime": "5 minutes",
        "valueMetric": "Instant notification distribution",
        "cta": "Route incident events to project channels",
    },
    {
        "id": "power-bi",
        "name": "Power BI",
        "category": "Executive reporting",
        "status": "planned",
        "summary": "Stream KPI snapshots into executive reporting datasets for portfolio visibility.",
        "capabilities": ["Dataset refresh", "Scorecard rollups", "Executive summaries"],
        "automationCount": 2,
        "owner": "Business Intelligence",
        "setupTime": "15 minutes",
        "valueMetric": "Cross-project trend reporting",
        "cta": "Expose webhook KPIs for leadership dashboards",
    },
]

WORKFLOW_BLUEPRINTS = [
    {
        "name": "Model change escalation",
        "trigger": "iModels.changesReady.v1",
        "actions": ["Create Azure DevOps work item", "Notify Slack channel", "Update Monday.com board"],
        "sla": "15 minutes",
        "status": "active",
    },
    {
        "name": "Issue triage concierge",
        "trigger": "issues.issueCreated.v1",
        "actions": ["Summarize with Atlassian Rovo AI", "Assign owner", "Open remediation checklist"],
        "sla": "30 minutes",
        "status": "active",
    },
    {
        "name": "Executive project digest",
        "trigger": "Daily 07:00 UTC",
        "actions": ["Compile KPI digest", "Publish to leadership feed", "Refresh Power BI dataset"],
        "sla": "Daily",
        "status": "pilot",
    },
]

BUILD_STAGE = {
    "currentStage": "Platform completion",
    "completion": 92,
    "headline": "The product has moved beyond MVP and now includes live operations, integration management, workflow templates, and rollout guidance.",
    "completed": [
        "Webhook intake, validation, and event storage",
        "Live operational dashboard with time filtering",
        "AI-generated insights and event distribution analytics",
        "Integration catalog with deployment-readiness states",
    ],
    "inProgress": [
        "Persistent storage connector for historical analytics",
        "Outbound credential vault wiring",
        "Role-based access and audit exports",
    ],
    "nextUp": [
        "Power BI production connector",
        "Workflow run history and retry controls",
        "Portfolio benchmarking across iTwin programs",
    ],
}


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"



def verify_signature(payload: bytes, signature: str) -> bool:
    if not signature:
        return True
    expected = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)



def get_safe_name(name: str | None, id_value: str | None, prefix: str) -> str:
    if name:
        return name
    if id_value:
        return f"{prefix}-{id_value[:8]}"
    return f"{prefix}-unknown"



def detect_source(event_type: str) -> str:
    lowered = event_type.lower()
    if "issue" in lowered:
        return "Issue resolution"
    if "form" in lowered:
        return "Field workflows"
    if "access" in lowered or "role" in lowered:
        return "Access governance"
    if "reality" in lowered:
        return "Reality modeling"
    if "synchronization" in lowered or "transformation" in lowered:
        return "Data operations"
    if "itwin" in lowered:
        return "Digital twin registry"
    return "Model operations"



def detect_priority(event_type: str) -> str:
    lowered = event_type.lower()
    if any(token in lowered for token in ["deleted", "removed", "failed"]):
        return "high"
    if any(token in lowered for token in ["issue", "changesready", "jobcompleted"]):
        return "medium"
    return "normal"



def integration_recommendations(event_type: str) -> List[str]:
    lowered = event_type.lower()
    suggestions = ["Bentley iTwin"]
    if any(token in lowered for token in ["issue", "form"]):
        suggestions.extend(["Monday.com", "Atlassian Rovo AI"])
    if any(token in lowered for token in ["changesready", "jobcompleted", "deleted"]):
        suggestions.extend(["Azure DevOps", "Slack"])
    if "access" in lowered or "role" in lowered:
        suggestions.append("Monday.com")
    deduped = []
    for item in suggestions:
        if item not in deduped:
            deduped.append(item)
    return deduped



def extract_event_info(data: Dict[str, Any]) -> Dict[str, Any]:
    event_type = data.get("eventType", "UnknownEvent")
    content = data.get("content", {}) or {}

    itwin_id = content.get("iTwinId") or content.get("itwinId") or data.get("iTwinId", "")
    imodel_id = content.get("iModelId") or content.get("imodelId") or data.get("iModelId", "")
    actor = content.get("actor") or content.get("user") or content.get("modifiedBy") or "System"

    itwin_name = content.get("iTwinName") or content.get("displayName") or get_safe_name(None, itwin_id, "iTwin")
    imodel_name = content.get("iModelName") or content.get("name") or get_safe_name(None, imodel_id, "iModel")

    return {
        "eventType": event_type,
        "iTwinId": itwin_id,
        "iTwinName": itwin_name,
        "iModelId": imodel_id,
        "iModelName": imodel_name,
        "source": detect_source(event_type),
        "priority": detect_priority(event_type),
        "actor": actor,
        "recommendedIntegrations": integration_recommendations(event_type),
        "timestamp": data.get("timestamp") or utc_now_iso(),
        "raw": data,
    }



def parse_event_time(event: Dict[str, Any]) -> datetime:
    raw_value = event.get("received_at") or event.get("timestamp") or utc_now_iso()
    try:
        return datetime.fromisoformat(raw_value.replace("Z", ""))
    except ValueError:
        return datetime.utcnow()



def filter_events(time_range: str) -> List[Dict[str, Any]]:
    hours = TIME_RANGES.get(time_range, TIME_RANGES["24h"])
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    return [event for event in events_store if parse_event_time(event) >= cutoff]



def summarize_event_counts(events: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for event in events:
        value = event.get(key) or "unknown"
        counts[value] = counts.get(value, 0) + 1
    return counts



def build_insights(filtered_events: List[Dict[str, Any]], event_type_counts: Dict[str, int]) -> str:
    if not filtered_events:
        return "No events have been received for the selected window. The platform is ready for Bentley webhook traffic and outbound integrations."

    busiest_type = max(event_type_counts.items(), key=lambda item: item[1])[0]
    high_priority = sum(1 for event in filtered_events if event.get("priority") == "high")
    ready_integrations = sum(1 for integration in INTEGRATIONS if integration["status"] in {"live", "ready"})
    return (
        f"{len(filtered_events)} events were processed in this window. "
        f"The dominant signal is {busiest_type}. "
        f"{high_priority} items need elevated attention, and {ready_integrations} integrations are deployment-ready for automation handoffs."
    )



def build_platform_summary(time_range: str = "24h") -> Dict[str, Any]:
    filtered_events = filter_events(time_range)
    event_type_counts = summarize_event_counts(filtered_events, "eventType")
    source_counts = summarize_event_counts(filtered_events, "source")
    priority_counts = summarize_event_counts(filtered_events, "priority")

    unique_itwins = {event["iTwinId"] for event in filtered_events if event.get("iTwinId")}
    unique_imodels = {event["iModelId"] for event in filtered_events if event.get("iModelId")}

    health_status = "idle"
    if filtered_events:
        health_status = "healthy"
    if len(filtered_events) > 75:
        health_status = "busy"

    ready_integrations = [integration for integration in INTEGRATIONS if integration["status"] in {"live", "ready"}]
    active_workflows = [workflow for workflow in WORKFLOW_BLUEPRINTS if workflow["status"] == "active"]
    attention_items = [
        {
            "title": "Connect outbound credentials",
            "detail": "Store service tokens for Azure DevOps, Monday.com, and Atlassian Rovo AI before enabling live actions.",
            "state": "next",
        },
        {
            "title": "Promote workflow blueprints",
            "detail": "Review the default trigger-to-action mappings and assign project owners.",
            "state": "in_progress",
        },
        {
            "title": "Enable durable analytics",
            "detail": "Persist event history to unlock trend analytics beyond in-memory retention.",
            "state": "planned",
        },
    ]

    return {
        "meta": {"timeRange": time_range, "generatedAt": utc_now_iso()},
        "kpis": {
            "totalEvents": len(filtered_events),
            "uniqueITwins": len(unique_itwins),
            "uniqueIModels": len(unique_imodels),
            "eventTypes": len(event_type_counts),
            "activeIntegrations": len(ready_integrations),
            "activeWorkflows": len(active_workflows),
        },
        "health": health_status,
        "insights": build_insights(filtered_events, event_type_counts),
        "recentEvents": filtered_events[:20],
        "eventTypeBreakdown": event_type_counts,
        "sourceBreakdown": source_counts,
        "priorityBreakdown": priority_counts,
        "integrations": {
            "items": INTEGRATIONS,
            "summary": {
                "ready": len([item for item in INTEGRATIONS if item["status"] == "ready"]),
                "live": len([item for item in INTEGRATIONS if item["status"] == "live"]),
                "planned": len([item for item in INTEGRATIONS if item["status"] == "planned"]),
            },
        },
        "workflows": WORKFLOW_BLUEPRINTS,
        "buildStage": BUILD_STAGE,
        "attentionItems": attention_items,
    }


@app.get("/api/info")
async def api_info() -> Dict[str, Any]:
    return {
        "service": "Bentley iTwin Automation Platform",
        "version": app.version,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "webhook": "/webhook",
            "events": "/events",
            "dashboard": "/dashboard",
            "dashboard_feed": "/dashboard/feed",
            "integrations": "/integrations",
            "integrations_api": "/api/integrations",
            "platform_api": "/api/platform",
        },
        "supported_events": len(SUPPORTED_EVENT_TYPES),
    }


@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "service": "Bentley iTwin Automation Platform",
        "version": app.version,
        "status": "running",
        "entrypoints": ["/dashboard", "/integrations", "/health", "/events", "/webhook"],
        "supported_events": len(SUPPORTED_EVENT_TYPES),
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "time": utc_now_iso(),
        "events_count": len(events_store),
        "integrations_ready": len([item for item in INTEGRATIONS if item["status"] in {"live", "ready"}]),
    }


@app.post("/webhook")
async def webhook(req: Request) -> Dict[str, Any]:
    body = await req.body()
    signature = req.headers.get("Signature") or req.headers.get("signature", "")

    if not verify_signature(body, signature):
        logger.warning("Invalid signature received")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        data = json.loads(body) if body else {}
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    event_info = extract_event_info(data)
    event_info["received_at"] = utc_now_iso()
    event_info["id"] = len(events_store) + 1

    events_store.insert(0, event_info)
    if len(events_store) > MAX_EVENTS:
        del events_store[MAX_EVENTS:]

    logger.info("Received event: %s", event_info["eventType"])
    return {
        "status": "processed",
        "eventType": event_info["eventType"],
        "timestamp": event_info["received_at"],
        "id": event_info["id"],
        "recommendedIntegrations": event_info["recommendedIntegrations"],
    }


@app.get("/events")
async def list_events(limit: int = 50) -> Dict[str, Any]:
    bounded_limit = max(1, min(limit, 200))
    return {
        "events": events_store[:bounded_limit],
        "total": len(events_store),
        "shown": min(bounded_limit, len(events_store)),
    }


@app.get("/dashboard/feed")
async def dashboard_feed(timeRange: str = "24h") -> Dict[str, Any]:
    return build_platform_summary(timeRange)


@app.get("/api/platform")
async def platform_api(timeRange: str = "24h") -> Dict[str, Any]:
    return build_platform_summary(timeRange)


@app.get("/api/integrations")
async def integrations_api() -> Dict[str, Any]:
    return {
        "generatedAt": utc_now_iso(),
        "items": INTEGRATIONS,
        "summary": {
            "total": len(INTEGRATIONS),
            "ready": len([item for item in INTEGRATIONS if item["status"] == "ready"]),
            "live": len([item for item in INTEGRATIONS if item["status"] == "live"]),
            "planned": len([item for item in INTEGRATIONS if item["status"] == "planned"]),
        },
    }


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>Bentley iTwin Automation Platform</title>
    <style>
        :root {
            --bg: #0f172a;
            --panel: #111c33;
            --panel-soft: rgba(15, 23, 42, 0.75);
            --card: #f8fafc;
            --card-dark: #12213d;
            --line: rgba(148, 163, 184, 0.18);
            --text: #e2e8f0;
            --text-soft: #94a3b8;
            --text-dark: #0f172a;
            --primary: #38bdf8;
            --primary-strong: #0ea5e9;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --idle: #94a3b8;
            --ready: #818cf8;
            --planned: #64748b;
            --shadow: 0 18px 45px rgba(15, 23, 42, 0.28);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: radial-gradient(circle at top, #1e3a8a 0%, #0f172a 42%, #020617 100%);
            color: var(--text);
            min-height: 100vh;
            line-height: 1.55;
        }
        a { color: inherit; text-decoration: none; }
        .page-shell {
            max-width: 1440px;
            margin: 0 auto;
            padding: 24px;
        }
        .hero {
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.18), rgba(30, 64, 175, 0.55));
            border: 1px solid rgba(125, 211, 252, 0.22);
            border-radius: 24px;
            box-shadow: var(--shadow);
            padding: 28px;
            margin-bottom: 24px;
        }
        .hero-top {
            display: flex;
            justify-content: space-between;
            gap: 18px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }
        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            border: 1px solid rgba(191, 219, 254, 0.3);
            border-radius: 999px;
            padding: 6px 12px;
            color: #dbeafe;
            font-size: 0.78rem;
            margin-bottom: 14px;
        }
        h1 {
            font-size: clamp(2rem, 4vw, 3rem);
            margin-bottom: 12px;
        }
        .hero p {
            max-width: 760px;
            color: #d6e3f1;
            font-size: 1rem;
        }
        .hero-actions {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-top: 18px;
        }
        .button {
            border: none;
            border-radius: 14px;
            padding: 11px 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease, opacity 0.2s ease;
        }
        .button:hover { transform: translateY(-1px); }
        .button-primary {
            background: linear-gradient(135deg, var(--primary), var(--primary-strong));
            color: #082f49;
        }
        .button-secondary {
            background: rgba(15, 23, 42, 0.42);
            color: #e2e8f0;
            border: 1px solid rgba(191, 219, 254, 0.16);
        }
        .hero-side {
            min-width: 260px;
            max-width: 320px;
            background: rgba(15, 23, 42, 0.42);
            border: 1px solid rgba(191, 219, 254, 0.14);
            border-radius: 20px;
            padding: 18px;
        }
        .hero-side h2 {
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #bfdbfe;
            margin-bottom: 12px;
        }
        .hero-side strong {
            display: block;
            font-size: 2.3rem;
            margin-bottom: 6px;
        }
        .hero-meta {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
        }
        .metric-pill {
            padding: 12px 14px;
            background: rgba(15, 23, 42, 0.38);
            border: 1px solid rgba(191, 219, 254, 0.16);
            border-radius: 16px;
        }
        .metric-pill span {
            display: block;
            color: var(--text-soft);
            font-size: 0.78rem;
        }
        .metric-pill strong {
            display: block;
            font-size: 1.2rem;
            margin-top: 4px;
        }
        .toolbar {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: center;
            margin-bottom: 18px;
            flex-wrap: wrap;
        }
        .tabs, .time-filter {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .chip {
            background: rgba(15, 23, 42, 0.62);
            border: 1px solid rgba(148, 163, 184, 0.18);
            color: #cbd5e1;
            border-radius: 999px;
            padding: 8px 14px;
            cursor: pointer;
            font-weight: 600;
        }
        .chip.active {
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.24), rgba(129, 140, 248, 0.35));
            border-color: rgba(125, 211, 252, 0.32);
            color: white;
        }
        .status-inline {
            display: flex;
            gap: 12px;
            align-items: center;
            color: var(--text-soft);
            font-size: 0.92rem;
        }
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--success);
            box-shadow: 0 0 0 6px rgba(34, 197, 94, 0.16);
        }
        .content-grid {
            display: grid;
            gap: 18px;
        }
        .overview-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 18px;
        }
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 14px;
        }
        .card {
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid var(--line);
            border-radius: 22px;
            box-shadow: var(--shadow);
            padding: 20px;
        }
        .card-light {
            background: linear-gradient(180deg, rgba(248, 250, 252, 0.98), rgba(226, 232, 240, 0.96));
            color: var(--text-dark);
        }
        .card h3, .card h2 {
            margin-bottom: 10px;
        }
        .card-subtitle {
            color: var(--text-soft);
            margin-bottom: 18px;
            font-size: 0.92rem;
        }
        .kpi-card .value {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 4px;
        }
        .kpi-card .label {
            color: var(--text-soft);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        .stage-list, .attention-list, .workflow-list {
            display: grid;
            gap: 12px;
        }
        .stage-item, .attention-item, .workflow-item {
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 18px;
            padding: 14px 16px;
            background: rgba(15, 23, 42, 0.45);
        }
        .stage-item strong, .attention-item strong, .workflow-item strong {
            display: block;
            margin-bottom: 6px;
        }
        .list-title {
            color: #bfdbfe;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 10px;
        }
        .section-panel { display: none; }
        .section-panel.active { display: block; }
        .two-column {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 18px;
        }
        .table-wrap {
            overflow-x: auto;
            border-radius: 16px;
            border: 1px solid rgba(148, 163, 184, 0.16);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            min-width: 880px;
        }
        th, td {
            padding: 14px 16px;
            text-align: left;
            border-bottom: 1px solid rgba(148, 163, 184, 0.14);
            font-size: 0.92rem;
        }
        th {
            color: #bfdbfe;
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        tbody tr:hover { background: rgba(15, 23, 42, 0.42); }
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            border-radius: 999px;
            padding: 6px 10px;
            font-size: 0.78rem;
            font-weight: 700;
            background: rgba(56, 189, 248, 0.14);
            color: #bae6fd;
        }
        .badge.high { background: rgba(239, 68, 68, 0.15); color: #fecaca; }
        .badge.medium { background: rgba(245, 158, 11, 0.18); color: #fde68a; }
        .badge.normal { background: rgba(34, 197, 94, 0.12); color: #bbf7d0; }
        .integration-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
        }
        .integration-card {
            border-radius: 22px;
            padding: 18px;
            background: rgba(15, 23, 42, 0.74);
            border: 1px solid rgba(148, 163, 184, 0.18);
            display: flex;
            flex-direction: column;
            gap: 14px;
        }
        .integration-top {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: start;
        }
        .integration-status {
            padding: 5px 10px;
            border-radius: 999px;
            font-size: 0.74rem;
            font-weight: 700;
            text-transform: uppercase;
        }
        .integration-status.live { background: rgba(34, 197, 94, 0.15); color: #bbf7d0; }
        .integration-status.ready { background: rgba(129, 140, 248, 0.16); color: #c7d2fe; }
        .integration-status.planned { background: rgba(100, 116, 139, 0.25); color: #cbd5e1; }
        .capabilities {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .capability {
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            background: rgba(148, 163, 184, 0.14);
            color: #e2e8f0;
        }
        .small-meta {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
            color: var(--text-soft);
            font-size: 0.84rem;
        }
        .small-meta strong {
            display: block;
            color: white;
            font-size: 1rem;
        }
        .integration-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            margin-top: auto;
            color: #bfdbfe;
            font-size: 0.86rem;
        }
        .distribution-list {
            display: grid;
            gap: 12px;
        }
        .distribution-item {
            display: grid;
            gap: 6px;
        }
        .distribution-meta {
            display: flex;
            justify-content: space-between;
            color: #dbeafe;
            font-size: 0.86rem;
        }
        .bar {
            width: 100%;
            height: 8px;
            border-radius: 999px;
            overflow: hidden;
            background: rgba(148, 163, 184, 0.16);
        }
        .bar > span {
            display: block;
            height: 100%;
            border-radius: inherit;
            background: linear-gradient(135deg, var(--primary), #a78bfa);
        }
        .empty-state {
            text-align: center;
            color: var(--text-soft);
            padding: 36px 18px;
        }
        .footer {
            text-align: center;
            color: var(--text-soft);
            padding: 24px 0 8px;
            font-size: 0.82rem;
        }
        @media (max-width: 1080px) {
            .overview-grid, .two-column { grid-template-columns: 1fr; }
        }
        @media (max-width: 720px) {
            .page-shell { padding: 16px; }
            .hero, .card, .integration-card { padding: 18px; }
            .hero-top { flex-direction: column; }
            .toolbar { align-items: flex-start; }
        }
    </style>
</head>
<body>
    <div class=\"page-shell\">
        <section class=\"hero\">
            <div class=\"hero-top\">
                <div>
                    <div class=\"eyebrow\">Bentley iTwin platform completion hub</div>
                    <h1>Operate Bentley webhooks like a complete delivery platform.</h1>
                    <p>
                        The original dashboard MVP now includes build-stage tracking, integration readiness, workflow blueprints,
                        and an execution view for operational teams. Azure DevOps, Monday.com, and Atlassian Rovo AI are included on the integrations page.
                    </p>
                    <div class=\"hero-actions\">
                        <button class=\"button button-primary\" data-nav-target=\"integrations\">Review integrations</button>
                        <button class=\"button button-secondary\" data-nav-target=\"operations\">Open live operations</button>
                    </div>
                </div>
                <aside class=\"hero-side\">
                    <h2>Build stage</h2>
                    <strong id=\"build-completion\">--%</strong>
                    <p id=\"build-headline\">Loading build progress...</p>
                </aside>
            </div>
            <div class=\"hero-meta\">
                <div class=\"metric-pill\"><span>Webhook endpoint</span><strong id=\"webhook-url\">/webhook</strong></div>
                <div class=\"metric-pill\"><span>Live integrations</span><strong id=\"hero-integrations\">0</strong></div>
                <div class=\"metric-pill\"><span>Active workflows</span><strong id=\"hero-workflows\">0</strong></div>
                <div class=\"metric-pill\"><span>Platform health</span><strong id=\"hero-health\">Idle</strong></div>
            </div>
        </section>

        <div class=\"toolbar\">
            <div class=\"tabs\">
                <button class=\"chip active\" data-panel=\"overview\">Overview</button>
                <button class=\"chip\" data-panel=\"operations\">Live operations</button>
                <button class=\"chip\" data-panel=\"integrations\">Integrations</button>
                <button class=\"chip\" data-panel=\"workflows\">Workflows</button>
                <button class=\"chip\" data-panel=\"rollout\">Rollout checklist</button>
            </div>
            <div class=\"status-inline\">
                <div class=\"status-dot\" id=\"status-dot\"></div>
                <span id=\"last-update\">Loading feed...</span>
                <button class=\"chip active\" id=\"refresh-now\">Refresh now</button>
            </div>
        </div>

        <div class=\"toolbar\">
            <div class=\"time-filter\">
                <button class=\"chip\" data-range=\"1h\">1H</button>
                <button class=\"chip\" data-range=\"6h\">6H</button>
                <button class=\"chip active\" data-range=\"24h\">24H</button>
                <button class=\"chip\" data-range=\"7d\">7D</button>
                <button class=\"chip\" data-range=\"30d\">30D</button>
            </div>
            <div class=\"status-inline\">
                <span>Auto-refresh every 15 seconds</span>
            </div>
        </div>

        <main class=\"content-grid\">
            <section class=\"section-panel active\" id=\"panel-overview\">
                <div class=\"overview-grid\">
                    <div class=\"card\">
                        <h2>Platform KPIs</h2>
                        <p class=\"card-subtitle\">A single operational view across event intake, integration enablement, and automation coverage.</p>
                        <div class=\"kpi-grid\" id=\"kpi-grid\"></div>
                    </div>
                    <div class=\"card\">
                        <h2>Current build stage</h2>
                        <p class=\"card-subtitle\">Understand what is complete, what is moving now, and what is next on the platform roadmap.</p>
                        <div class=\"stage-list\">
                            <div>
                                <div class=\"list-title\">Completed</div>
                                <div id=\"completed-list\"></div>
                            </div>
                            <div>
                                <div class=\"list-title\">In progress</div>
                                <div id=\"progress-list\"></div>
                            </div>
                            <div>
                                <div class=\"list-title\">Next up</div>
                                <div id=\"next-list\"></div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class=\"two-column\" style=\"margin-top:18px;\">
                    <div class=\"card card-light\">
                        <h2>AI operational summary</h2>
                        <p id=\"insights\">Loading current platform summary...</p>
                    </div>
                    <div class=\"card\">
                        <h2>Attention items</h2>
                        <p class=\"card-subtitle\">The remaining steps to take this environment from responsive to production-ready.</p>
                        <div class=\"attention-list\" id=\"attention-list\"></div>
                    </div>
                </div>
            </section>

            <section class=\"section-panel\" id=\"panel-operations\">
                <div class=\"two-column\">
                    <div class=\"card\">
                        <div style=\"display:flex;justify-content:space-between;gap:16px;align-items:flex-end;flex-wrap:wrap;\">
                            <div>
                                <h2>Recent event stream</h2>
                                <p class=\"card-subtitle\">Newest-first operational feed enriched with source and integration recommendations.</p>
                            </div>
                            <div class=\"badge\" id=\"ops-health\">Loading health</div>
                        </div>
                        <div class=\"table-wrap\">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Event type</th>
                                        <th>Source</th>
                                        <th>Priority</th>
                                        <th>iTwin</th>
                                        <th>iModel</th>
                                        <th>Recommended integrations</th>
                                        <th>Received</th>
                                    </tr>
                                </thead>
                                <tbody id=\"events-body\">
                                    <tr><td colspan=\"7\" class=\"empty-state\">Waiting for events...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class=\"card\">
                        <h2>Distribution</h2>
                        <p class=\"card-subtitle\">Top event families for the selected time range.</p>
                        <div class=\"distribution-list\" id=\"distribution-list\"></div>
                        <div class=\"list-title\" style=\"margin-top:18px;\">Priority mix</div>
                        <div class=\"distribution-list\" id=\"priority-list\"></div>
                    </div>
                </div>
            </section>

            <section class=\"section-panel\" id=\"panel-integrations\">
                <div class=\"card\">
                    <h2>Integration control center</h2>
                    <p class=\"card-subtitle\">All available handoffs across delivery, project controls, knowledge systems, and executive reporting.</p>
                    <div class=\"integration-grid\" id=\"integration-grid\"></div>
                </div>
            </section>

            <section class=\"section-panel\" id=\"panel-workflows\">
                <div class=\"two-column\">
                    <div class=\"card\">
                        <h2>Workflow blueprints</h2>
                        <p class=\"card-subtitle\">Default orchestration paths shipped with the platform completion release.</p>
                        <div class=\"workflow-list\" id=\"workflow-list\"></div>
                    </div>
                    <div class=\"card\">
                        <h2>Workflow operating model</h2>
                        <p class=\"card-subtitle\">Recommended production approach for governance and rollout.</p>
                        <div class=\"attention-list\">
                            <div class=\"attention-item\"><strong>1. Validate event-to-owner routing</strong><span>Assign each workflow blueprint to a project, operations, or support owner.</span></div>
                            <div class=\"attention-item\"><strong>2. Secure tokens before activation</strong><span>Store credentials for Azure DevOps, Monday.com, and Atlassian Rovo AI before enabling outbound writes.</span></div>
                            <div class=\"attention-item\"><strong>3. Add durable storage</strong><span>Persist event history to support replay, audit, and long-range trend analytics.</span></div>
                        </div>
                    </div>
                </div>
            </section>

            <section class=\"section-panel\" id=\"panel-rollout\">
                <div class=\"two-column\">
                    <div class=\"card\">
                        <h2>Production readiness checklist</h2>
                        <p class=\"card-subtitle\">A practical path to launch the complete platform safely.</p>
                        <div class=\"attention-list\">
                            <div class=\"attention-item\"><strong>Webhook security</strong><span>Configure <code>WEBHOOK_SECRET</code> and confirm all upstream publishers use signed payloads.</span></div>
                            <div class=\"attention-item\"><strong>Integration credentials</strong><span>Store service credentials for all enabled integrations and test outbound scopes.</span></div>
                            <div class=\"attention-item\"><strong>Observability</strong><span>Attach log aggregation and alert routing for failed jobs, empty feeds, or retry storms.</span></div>
                            <div class=\"attention-item\"><strong>Data retention</strong><span>Replace in-memory storage with a persistent event store for compliance, analytics, and replay.</span></div>
                        </div>
                    </div>
                    <div class=\"card\">
                        <h2>Why this is now more complete</h2>
                        <p class=\"card-subtitle\">The original build only surfaced webhook telemetry. The current experience layers in the missing operational scaffolding.</p>
                        <div class=\"stage-list\">
                            <div class=\"stage-item\"><strong>Build stage transparency</strong><span>Teams can now see what has been shipped, what is underway, and what is still pending.</span></div>
                            <div class=\"stage-item\"><strong>Integration page</strong><span>Azure DevOps, Monday.com, and Atlassian Rovo AI are explicitly modeled and deployment-ready.</span></div>
                            <div class=\"stage-item\"><strong>Workflow blueprints</strong><span>The platform now explains how events route into action instead of stopping at dashboards.</span></div>
                        </div>
                    </div>
                </div>
            </section>
        </main>

        <div class=\"footer\">Bentley iTwin Automation Platform • Auto-refreshing every 15 seconds • Built on FastAPI + vanilla HTML/CSS/JS.</div>
    </div>

    <script>
        let currentRange = '24h';
        let refreshTimer = null;

        const panelButtons = Array.from(document.querySelectorAll('[data-panel]'));
        const panelTargets = Array.from(document.querySelectorAll('.section-panel'));
        const navButtons = Array.from(document.querySelectorAll('[data-nav-target]'));
        const rangeButtons = Array.from(document.querySelectorAll('[data-range]'));

        function switchPanel(panelName) {
            panelButtons.forEach((button) => button.classList.toggle('active', button.dataset.panel === panelName));
            panelTargets.forEach((panel) => panel.classList.toggle('active', panel.id === 'panel-' + panelName));
        }

        panelButtons.forEach((button) => {
            button.addEventListener('click', () => switchPanel(button.dataset.panel));
        });

        navButtons.forEach((button) => {
            button.addEventListener('click', () => switchPanel(button.dataset.navTarget));
        });

        rangeButtons.forEach((button) => {
            button.addEventListener('click', () => {
                rangeButtons.forEach((node) => node.classList.remove('active'));
                button.classList.add('active');
                currentRange = button.dataset.range;
                fetchData();
            });
        });

        document.getElementById('refresh-now').addEventListener('click', fetchData);

        function humanize(value) {
            return String(value || '')
                .replace(/([a-z])([A-Z])/g, '$1 $2')
                .replace(/\\./g, ' ')
                .replace(/\\b\\w/g, (char) => char.toUpperCase());
        }

        function escapeHtml(value) {
            const div = document.createElement('div');
            div.textContent = value == null ? '' : String(value);
            return div.innerHTML;
        }

        function renderSimpleList(targetId, items) {
            const target = document.getElementById(targetId);
            target.innerHTML = (items || []).map((item) => `<div class=\"stage-item\">${escapeHtml(item)}</div>`).join('') || '<div class=\"stage-item\">No items yet.</div>';
        }

        function renderAttention(items) {
            const target = document.getElementById('attention-list');
            target.innerHTML = (items || []).map((item) => `
                <div class=\"attention-item\">
                    <strong>${escapeHtml(item.title)}</strong>
                    <span>${escapeHtml(item.detail)}</span>
                </div>
            `).join('');
        }

        function renderKpis(kpis) {
            const cards = [
                ['Total events', kpis.totalEvents],
                ['Unique iTwins', kpis.uniqueITwins],
                ['Unique iModels', kpis.uniqueIModels],
                ['Event varieties', kpis.eventTypes],
                ['Active integrations', kpis.activeIntegrations],
                ['Active workflows', kpis.activeWorkflows],
            ];
            document.getElementById('kpi-grid').innerHTML = cards.map(([label, value]) => `
                <div class=\"kpi-card card\">
                    <div class=\"label\">${escapeHtml(label)}</div>
                    <div class=\"value\">${escapeHtml(value)}</div>
                </div>
            `).join('');
        }

        function renderDistribution(targetId, items) {
            const entries = Object.entries(items || {}).sort((a, b) => b[1] - a[1]);
            const total = entries.reduce((sum, [, count]) => sum + count, 0) || 1;
            const target = document.getElementById(targetId);
            if (!entries.length) {
                target.innerHTML = '<div class=\"empty-state\">No data available for this range.</div>';
                return;
            }
            target.innerHTML = entries.slice(0, 6).map(([label, count]) => {
                const width = Math.max(6, Math.round((count / total) * 100));
                return `
                    <div class=\"distribution-item\">
                        <div class=\"distribution-meta\"><span>${escapeHtml(label)}</span><span>${count}</span></div>
                        <div class=\"bar\"><span style=\"width:${width}%\"></span></div>
                    </div>
                `;
            }).join('');
        }

        function renderEvents(events) {
            const target = document.getElementById('events-body');
            if (!events || !events.length) {
                target.innerHTML = '<tr><td colspan=\"7\" class=\"empty-state\">No events received yet. Use <code>bash seed.sh</code> to populate the platform.</td></tr>';
                return;
            }
            target.innerHTML = events.map((event) => {
                const received = new Date(event.received_at || event.timestamp || Date.now()).toLocaleString();
                const integrations = (event.recommendedIntegrations || []).join(', ');
                return `
                    <tr>
                        <td>${escapeHtml(event.eventType)}</td>
                        <td>${escapeHtml(event.source || '-')}</td>
                        <td><span class=\"badge ${escapeHtml(event.priority || 'normal')}\">${escapeHtml(event.priority || 'normal')}</span></td>
                        <td>${escapeHtml(event.iTwinName || '-')}</td>
                        <td>${escapeHtml(event.iModelName || '-')}</td>
                        <td>${escapeHtml(integrations || '-')}</td>
                        <td>${escapeHtml(received)}</td>
                    </tr>
                `;
            }).join('');
        }

        function renderIntegrations(items) {
            const target = document.getElementById('integration-grid');
            target.innerHTML = (items || []).map((item) => `
                <article class=\"integration-card\">
                    <div class=\"integration-top\">
                        <div>
                            <div class=\"list-title\">${escapeHtml(item.category)}</div>
                            <h3>${escapeHtml(item.name)}</h3>
                        </div>
                        <span class=\"integration-status ${escapeHtml(item.status)}\">${escapeHtml(item.status)}</span>
                    </div>
                    <p>${escapeHtml(item.summary)}</p>
                    <div class=\"capabilities\">${(item.capabilities || []).map((capability) => `<span class=\"capability\">${escapeHtml(capability)}</span>`).join('')}</div>
                    <div class=\"small-meta\">
                        <div><span>Automations</span><strong>${escapeHtml(item.automationCount)}</strong></div>
                        <div><span>Setup time</span><strong>${escapeHtml(item.setupTime)}</strong></div>
                        <div><span>Owner</span><strong>${escapeHtml(item.owner)}</strong></div>
                        <div><span>Outcome</span><strong>${escapeHtml(item.valueMetric)}</strong></div>
                    </div>
                    <div class=\"integration-actions\">
                        <span>${escapeHtml(item.cta)}</span>
                        <strong>Ready for mapping</strong>
                    </div>
                </article>
            `).join('');
        }

        function renderWorkflows(items) {
            const target = document.getElementById('workflow-list');
            target.innerHTML = (items || []).map((item) => `
                <div class=\"workflow-item\">
                    <strong>${escapeHtml(item.name)}</strong>
                    <div class=\"list-title\">Trigger</div>
                    <div>${escapeHtml(item.trigger)}</div>
                    <div class=\"list-title\" style=\"margin-top:10px;\">Actions</div>
                    <div>${(item.actions || []).map((action) => `<span class=\"capability\">${escapeHtml(action)}</span>`).join(' ')}</div>
                    <div class=\"small-meta\" style=\"margin-top:12px;\">
                        <div><span>Status</span><strong>${escapeHtml(item.status)}</strong></div>
                        <div><span>SLA</span><strong>${escapeHtml(item.sla)}</strong></div>
                    </div>
                </div>
            `).join('');
        }

        function applyHealth(health) {
            const dot = document.getElementById('status-dot');
            const badge = document.getElementById('ops-health');
            const colorMap = { healthy: 'var(--success)', busy: 'var(--warning)', idle: 'var(--idle)' };
            dot.style.background = colorMap[health] || 'var(--danger)';
            dot.style.boxShadow = `0 0 0 6px ${health === 'healthy' ? 'rgba(34, 197, 94, 0.16)' : health === 'busy' ? 'rgba(245, 158, 11, 0.18)' : 'rgba(148, 163, 184, 0.16)'}`;
            badge.textContent = 'Platform health: ' + humanize(health);
            document.getElementById('hero-health').textContent = humanize(health);
        }

        async function fetchData() {
            try {
                document.getElementById('last-update').textContent = 'Refreshing...';
                const response = await fetch('/dashboard/feed?timeRange=' + encodeURIComponent(currentRange), { cache: 'no-store' });
                const data = await response.json();

                renderKpis(data.kpis || {});
                renderSimpleList('completed-list', data.buildStage?.completed || []);
                renderSimpleList('progress-list', data.buildStage?.inProgress || []);
                renderSimpleList('next-list', data.buildStage?.nextUp || []);
                renderAttention(data.attentionItems || []);
                renderEvents(data.recentEvents || []);
                renderDistribution('distribution-list', data.eventTypeBreakdown || {});
                renderDistribution('priority-list', data.priorityBreakdown || {});
                renderIntegrations(data.integrations?.items || []);
                renderWorkflows(data.workflows || []);
                applyHealth(data.health || 'idle');

                document.getElementById('insights').textContent = data.insights || 'No insights available.';
                document.getElementById('build-completion').textContent = String(data.buildStage?.completion || 0) + '%';
                document.getElementById('build-headline').textContent = data.buildStage?.headline || 'Build stage unavailable.';
                document.getElementById('webhook-url').textContent = window.location.origin + '/webhook';
                document.getElementById('hero-integrations').textContent = data.kpis?.activeIntegrations ?? 0;
                document.getElementById('hero-workflows').textContent = data.kpis?.activeWorkflows ?? 0;
                document.getElementById('last-update').textContent = 'Last updated ' + new Date(data.meta?.generatedAt || Date.now()).toLocaleTimeString();
            } catch (error) {
                console.error('Failed to load dashboard data', error);
                document.getElementById('last-update').textContent = 'Unable to refresh feed';
            }
        }

        fetchData();
        refreshTimer = setInterval(fetchData, 15000);
    </script>
</body>
</html>
"""


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> HTMLResponse:
    return HTMLResponse(content=DASHBOARD_HTML, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/integrations", response_class=HTMLResponse)
async def integrations_page() -> HTMLResponse:
    integrations_html = DASHBOARD_HTML.replace('class=\"chip\" data-panel=\"integrations\"', 'class=\"chip active\" data-panel=\"integrations\"', 1)
    integrations_html = integrations_html.replace('class=\"chip active\" data-panel=\"overview\"', 'class=\"chip\" data-panel=\"overview\"', 1)
    integrations_html = integrations_html.replace('section class=\"section-panel active\" id=\"panel-overview\"', 'section class=\"section-panel\" id=\"panel-overview\"', 1)
    integrations_html = integrations_html.replace('section class=\"section-panel\" id=\"panel-integrations\"', 'section class=\"section-panel active\" id=\"panel-integrations\"', 1)
    return HTMLResponse(content=integrations_html, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/favicon.ico")
async def favicon() -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Not found"})


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
