import os
import hmac
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "gem_webhook_secret")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bentley iTwin Webhooks Dashboard MVP",
    version="1.0",
    description="Webhook service for Bentley iTwin with dashboard"
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


def verify_signature(payload: bytes, signature: str) -> bool:
    if not signature:
        return True
    expected = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def get_safe_name(name: str | None, id_val: str | None, prefix: str = "Resource") -> str:
    if name:
        return name
    if id_val:
        return f"{prefix}-{id_val[:8]}"
    return f"{prefix}-unknown"


def extract_event_info(data: dict) -> dict:
    event_type = data.get("eventType", "UnknownEvent")
    content = data.get("content", {})
    
    itwin_id = content.get("iTwinId") or content.get("itwinId") or data.get("iTwinId", "")
    imodel_id = content.get("iModelId") or content.get("imodelId") or data.get("iModelId", "")
    
    itwin_name = content.get("iTwinName") or content.get("displayName") or get_safe_name(None, itwin_id, "iTwin")
    imodel_name = content.get("iModelName") or content.get("name") or get_safe_name(None, imodel_id, "iModel")
    
    return {
        "eventType": event_type,
        "iTwinId": itwin_id,
        "iTwinName": itwin_name,
        "iModelId": imodel_id,
        "iModelName": imodel_name,
        "timestamp": data.get("timestamp") or datetime.utcnow().isoformat() + "Z",
        "raw": data
    }


@app.get("/")
async def root():
    return {
        "service": "Bentley iTwin Webhooks Dashboard MVP",
        "version": "1.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "webhook": "/webhook",
            "events": "/events",
            "dashboard": "/dashboard",
            "dashboard_feed": "/dashboard/feed"
        },
        "supported_events": len(SUPPORTED_EVENT_TYPES)
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "time": datetime.utcnow().isoformat() + "Z",
        "events_count": len(events_store)
    }


@app.post("/webhook")
async def webhook(req: Request):
    body = await req.body()
    sig = req.headers.get("Signature") or req.headers.get("signature", "")
    
    if not verify_signature(body, sig):
        logger.warning("Invalid signature received")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        data = json.loads(body) if body else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    event_info = extract_event_info(data)
    event_info["received_at"] = datetime.utcnow().isoformat() + "Z"
    event_info["id"] = len(events_store) + 1
    
    events_store.insert(0, event_info)
    
    if len(events_store) > 1000:
        events_store[:] = events_store[:1000]
    
    logger.info(f"Received event: {event_info['eventType']}")
    
    return {
        "status": "processed",
        "eventType": event_info["eventType"],
        "timestamp": event_info["received_at"],
        "id": event_info["id"]
    }


@app.get("/events")
async def list_events(limit: int = 50):
    return {
        "events": events_store[:limit],
        "total": len(events_store),
        "shown": min(limit, len(events_store))
    }


@app.get("/dashboard/feed")
async def dashboard_feed(timeRange: str = "24h"):
    hours_map = {"1h": 1, "6h": 6, "24h": 24, "7d": 168, "30d": 720}
    hours = hours_map.get(timeRange, 24)
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    filtered_events = []
    for e in events_store:
        try:
            ts = datetime.fromisoformat(e["received_at"].replace("Z", ""))
            if ts >= cutoff:
                filtered_events.append(e)
        except:
            filtered_events.append(e)
    
    event_type_counts = {}
    for e in filtered_events:
        et = e.get("eventType", "unknown")
        event_type_counts[et] = event_type_counts.get(et, 0) + 1
    
    unique_itwins = set()
    unique_imodels = set()
    for e in filtered_events:
        if e.get("iTwinId"):
            unique_itwins.add(e["iTwinId"])
        if e.get("iModelId"):
            unique_imodels.add(e["iModelId"])
    
    kpis = {
        "totalEvents": len(filtered_events),
        "uniqueITwins": len(unique_itwins),
        "uniqueIModels": len(unique_imodels),
        "eventTypes": len(event_type_counts)
    }
    
    health_status = "healthy" if len(filtered_events) > 0 else "idle"
    if len(filtered_events) > 100:
        health_status = "busy"
    
    top_events = sorted(event_type_counts.items(), key=lambda x: -x[1])[:5]
    
    if filtered_events:
        insights = f"Received {kpis['totalEvents']} events in the last {timeRange}. "
        if top_events:
            insights += f"Most common: {top_events[0][0]} ({top_events[0][1]} occurrences). "
        insights += f"Activity across {kpis['uniqueITwins']} iTwins and {kpis['uniqueIModels']} iModels."
    else:
        insights = f"No events received in the last {timeRange}. System is idle and awaiting webhook events."
    
    return {
        "meta": {
            "timeRange": timeRange,
            "generatedAt": datetime.utcnow().isoformat() + "Z"
        },
        "kpis": kpis,
        "health": health_status,
        "recentEvents": filtered_events[:20],
        "insights": insights,
        "eventTypeBreakdown": event_type_counts
    }


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bentley iTwin Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #333;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #1a5276 0%, #2980b9 100%);
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { font-size: 1.5rem; font-weight: 600; }
        .header .status {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.9rem;
        }
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #2ecc71;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .time-filter {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .time-filter button {
            padding: 8px 16px;
            border: 1px solid #ddd;
            background: white;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s;
        }
        .time-filter button.active {
            background: #2980b9;
            color: white;
            border-color: #2980b9;
        }
        .time-filter button:hover:not(.active) { background: #f0f0f0; }
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .kpi-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .kpi-card h3 {
            font-size: 0.85rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        .kpi-card .value {
            font-size: 2rem;
            font-weight: 700;
            color: #2980b9;
        }
        .insights-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .insights-card h3 {
            font-size: 0.9rem;
            opacity: 0.9;
            margin-bottom: 10px;
        }
        .insights-card p { font-size: 1rem; line-height: 1.5; }
        .health-bar {
            background: white;
            border-radius: 12px;
            padding: 15px 20px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .health-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }
        .health-indicator.healthy { background: #2ecc71; }
        .health-indicator.busy { background: #f39c12; }
        .health-indicator.idle { background: #95a5a6; }
        .events-table {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .events-table h3 {
            padding: 15px 20px;
            border-bottom: 1px solid #eee;
            font-size: 1rem;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px 20px;
            text-align: left;
            border-bottom: 1px solid #f0f0f0;
        }
        th {
            background: #fafafa;
            font-weight: 600;
            font-size: 0.8rem;
            text-transform: uppercase;
            color: #666;
        }
        td { font-size: 0.9rem; }
        tr:hover { background: #f9f9f9; }
        .event-type {
            display: inline-block;
            padding: 4px 10px;
            background: #e8f4fd;
            color: #2980b9;
            border-radius: 4px;
            font-size: 0.8rem;
            font-family: monospace;
        }
        .timestamp { color: #888; font-size: 0.85rem; }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #888;
        }
        .empty-state h3 { margin-bottom: 10px; }
        .last-update {
            text-align: center;
            color: #888;
            font-size: 0.8rem;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Bentley iTwin Webhooks Dashboard</h1>
        <div class="status">
            <div class="status-dot"></div>
            <span>Live</span>
        </div>
    </div>
    <div class="container">
        <div class="time-filter">
            <button data-range="1h">1 Hour</button>
            <button data-range="6h">6 Hours</button>
            <button data-range="24h" class="active">24 Hours</button>
            <button data-range="7d">7 Days</button>
            <button data-range="30d">30 Days</button>
        </div>
        <div class="kpi-grid" id="kpis">
            <div class="kpi-card">
                <h3>Total Events</h3>
                <div class="value" id="kpi-total">-</div>
            </div>
            <div class="kpi-card">
                <h3>Unique iTwins</h3>
                <div class="value" id="kpi-itwins">-</div>
            </div>
            <div class="kpi-card">
                <h3>Unique iModels</h3>
                <div class="value" id="kpi-imodels">-</div>
            </div>
            <div class="kpi-card">
                <h3>Event Types</h3>
                <div class="value" id="kpi-types">-</div>
            </div>
        </div>
        <div class="health-bar">
            <div class="health-indicator" id="health-dot"></div>
            <span id="health-text">System Status: Loading...</span>
        </div>
        <div class="insights-card">
            <h3>AI Summary</h3>
            <p id="insights">Loading insights...</p>
        </div>
        <div class="events-table">
            <h3>Recent Events</h3>
            <table>
                <thead>
                    <tr>
                        <th>Event Type</th>
                        <th>iTwin</th>
                        <th>iModel</th>
                        <th>Received</th>
                    </tr>
                </thead>
                <tbody id="events-body">
                    <tr><td colspan="4" class="empty-state">Loading...</td></tr>
                </tbody>
            </table>
        </div>
        <p class="last-update" id="last-update"></p>
    </div>
    <script>
        let currentRange = '24h';
        
        async function fetchData() {
            try {
                const res = await fetch('/dashboard/feed?timeRange=' + currentRange);
                const data = await res.json();
                
                document.getElementById('kpi-total').textContent = data.kpis.totalEvents;
                document.getElementById('kpi-itwins').textContent = data.kpis.uniqueITwins;
                document.getElementById('kpi-imodels').textContent = data.kpis.uniqueIModels;
                document.getElementById('kpi-types').textContent = data.kpis.eventTypes;
                
                const healthDot = document.getElementById('health-dot');
                healthDot.className = 'health-indicator ' + data.health;
                document.getElementById('health-text').textContent = 
                    'System Status: ' + data.health.charAt(0).toUpperCase() + data.health.slice(1);
                
                document.getElementById('insights').textContent = data.insights;
                
                const tbody = document.getElementById('events-body');
                if (data.recentEvents.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" class="empty-state"><h3>No Events Yet</h3><p>Webhook events will appear here when received</p></td></tr>';
                } else {
                    tbody.innerHTML = data.recentEvents.map(e => {
                        const date = new Date(e.received_at);
                        const timeStr = date.toLocaleTimeString() + ' ' + date.toLocaleDateString();
                        return '<tr>' +
                            '<td><span class="event-type">' + escapeHtml(e.eventType) + '</span></td>' +
                            '<td>' + escapeHtml(e.iTwinName || '-') + '</td>' +
                            '<td>' + escapeHtml(e.iModelName || '-') + '</td>' +
                            '<td class="timestamp">' + timeStr + '</td>' +
                        '</tr>';
                    }).join('');
                }
                
                document.getElementById('last-update').textContent = 
                    'Last updated: ' + new Date().toLocaleTimeString();
            } catch (err) {
                console.error('Failed to fetch data:', err);
            }
        }
        
        function escapeHtml(str) {
            if (!str) return '';
            return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }
        
        document.querySelectorAll('.time-filter button').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.time-filter button').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentRange = btn.dataset.range;
                fetchData();
            });
        });
        
        fetchData();
        setInterval(fetchData, 15000);
    </script>
</body>
</html>"""


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(content=DASHBOARD_HTML, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
