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
    version="1.1",
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
        "version": "1.1",
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
        :root {
            --primary: #2980b9;
            --primary-dark: #1a5276;
            --bg: #f5f7fa;
            --card-bg: #ffffff;
            --text: #333;
            --text-muted: #666;
            --success: #2ecc71;
            --warning: #f39c12;
            --danger: #e74c3c;
            --idle: #95a5a6;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            line-height: 1.6;
        }
        .header {
            background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
            color: white;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .header h1 { font-size: 1.25rem; font-weight: 600; }
        .header .status {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.85rem;
            background: rgba(255,255,255,0.1);
            padding: 4px 12px;
            border-radius: 20px;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
            box-shadow: 0 0 8px var(--success);
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.2); }
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 1.5rem; }
        
        .dashboard-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .time-filter {
            display: flex;
            gap: 0.5rem;
            background: white;
            padding: 4px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .time-filter button {
            padding: 6px 14px;
            border: none;
            background: transparent;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--text-muted);
            transition: all 0.2s;
        }
        .time-filter button.active {
            background: var(--primary);
            color: white;
        }
        .time-filter button:hover:not(.active) { background: #f0f0f0; }
        
        .refresh-control {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.8rem;
            color: var(--text-muted);
        }
        .btn-refresh {
            background: white;
            border: 1px solid #ddd;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 5px;
            transition: all 0.2s;
        }
        .btn-refresh:hover { background: #f9f9f9; border-color: var(--primary); }

        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .kpi-card {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border-top: 4px solid var(--primary);
            transition: transform 0.2s;
        }
        .kpi-card:hover { transform: translateY(-3px); }
        .kpi-card h3 {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 0.75rem;
        }
        .kpi-card .value {
            font-size: 2.25rem;
            font-weight: 800;
            color: var(--primary);
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 350px;
            gap: 1.5rem;
        }
        @media (max-width: 1024px) {
            .main-content { grid-template-columns: 1fr; }
        }
        
        .content-section {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .insights-card {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .insights-card h3 {
            font-size: 0.9rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .insights-card p { font-size: 0.95rem; font-weight: 500; }
        
        .health-card {
            background: white;
            border-radius: 12px;
            padding: 1.25rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .health-info { display: flex; align-items: center; gap: 12px; }
        .health-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }
        .health-indicator.healthy { background: var(--success); box-shadow: 0 0 8px var(--success); }
        .health-indicator.busy { background: var(--warning); box-shadow: 0 0 8px var(--warning); }
        .health-indicator.idle { background: var(--idle); }
        .health-label { font-weight: 600; font-size: 0.9rem; }
        
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }
        
        .distribution-card {
            background: white;
            border-radius: 12px;
            padding: 1.25rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .distribution-card h3 {
            font-size: 0.85rem;
            margin-bottom: 1rem;
            color: var(--text-muted);
            text-transform: uppercase;
        }
        .dist-item {
            margin-bottom: 0.75rem;
        }
        .dist-info {
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            margin-bottom: 4px;
        }
        .dist-bar-bg {
            height: 6px;
            background: #eee;
            border-radius: 3px;
            overflow: hidden;
        }
        .dist-bar-fg {
            height: 100%;
            background: var(--primary);
            border-radius: 3px;
        }

        .events-table-card {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        .events-table-card .card-header {
            padding: 1.25rem;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .events-table-card h3 { font-size: 1rem; font-weight: 600; }
        
        .table-container {
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            min-width: 600px;
        }
        th, td {
            padding: 1rem 1.25rem;
            text-align: left;
            border-bottom: 1px solid #f0f0f0;
        }
        th {
            background: #fafafa;
            font-weight: 600;
            font-size: 0.75rem;
            text-transform: uppercase;
            color: var(--text-muted);
            letter-spacing: 0.5px;
        }
        td { font-size: 0.85rem; }
        tr:hover { background: #f9fbfe; }
        tr:last-child td { border-bottom: none; }
        
        .event-badge {
            display: inline-block;
            padding: 3px 8px;
            background: #eef2f7;
            color: #4a5568;
            border-radius: 4px;
            font-size: 0.75rem;
            font-family: 'SFMono-Regular', Consolas, monospace;
            font-weight: 500;
        }
        .event-badge.imodel { background: #e0f2fe; color: #0369a1; }
        .event-badge.itwin { background: #fef3c7; color: #92400e; }
        .event-badge.access { background: #fce7f3; color: #9d174d; }
        
        .timestamp { color: var(--text-muted); font-size: 0.8rem; }
        
        .empty-state {
            text-align: center;
            padding: 4rem 2rem;
            color: var(--text-muted);
        }
        .empty-state svg { width: 48px; height: 48px; margin-bottom: 1rem; opacity: 0.3; }
        
        .footer {
            text-align: center;
            margin-top: 2rem;
            padding-bottom: 2rem;
            font-size: 0.75rem;
            color: var(--text-muted);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Bentley iTwin Webhooks Dashboard</h1>
        <div class="status">
            <div class="status-dot"></div>
            <span>Live Stream</span>
        </div>
    </div>
    
    <div class="container">
        <div class="dashboard-actions">
            <div class="time-filter">
                <button data-range="1h">1H</button>
                <button data-range="6h">6H</button>
                <button data-range="24h" class="active">24H</button>
                <button data-range="7d">7D</button>
                <button data-range="30d">30D</button>
            </div>
            
            <div class="refresh-control">
                <span id="last-update-time">Just now</span>
                <button class="btn-refresh" id="manual-refresh">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 4v6h-6"></path><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
                    Refresh
                </button>
            </div>
        </div>

        <div class="kpi-grid" id="kpis">
            <div class="kpi-card">
                <h3>Total Events</h3>
                <div class="value" id="kpi-total">0</div>
            </div>
            <div class="kpi-card">
                <h3>Unique iTwins</h3>
                <div class="value" id="kpi-itwins">0</div>
            </div>
            <div class="kpi-card">
                <h3>Unique iModels</h3>
                <div class="value" id="kpi-imodels">0</div>
            </div>
            <div class="kpi-card">
                <h3>Event Varieties</h3>
                <div class="value" id="kpi-types">0</div>
            </div>
        </div>

        <div class="main-content">
            <div class="content-section">
                <div class="insights-card">
                    <h3>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>
                        AI Insights Summary
                    </h3>
                    <p id="insights">Analyzing your webhook data stream...</p>
                </div>

                <div class="events-table-card">
                    <div class="card-header">
                        <h3>Recent Event Feed</h3>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Event Type</th>
                                    <th>iTwin Resource</th>
                                    <th>iModel Context</th>
                                    <th>Received At</th>
                                </tr>
                            </thead>
                            <tbody id="events-body">
                                <tr><td colspan="4" class="empty-state">Waiting for events...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="sidebar">
                <div class="health-card">
                    <div class="health-info">
                        <div class="health-indicator" id="health-dot"></div>
                        <span class="health-label" id="health-text">Loading...</span>
                    </div>
                    <span style="font-size: 0.7rem; color: #888;">System Status</span>
                </div>

                <div class="distribution-card">
                    <h3>Event Distribution</h3>
                    <div id="distribution-body">
                        <!-- Filled by JS -->
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            Bentley iTwin Webhooks Dashboard MVP v1.1 &bull; Auto-refreshing every 15s
        </div>
    </div>

    <script>
        let currentRange = '24h';
        let refreshInterval;
        
        async function fetchData() {
            try {
                const manualBtn = document.getElementById('manual-refresh');
                manualBtn.style.opacity = '0.5';
                manualBtn.disabled = true;

                const res = await fetch('/dashboard/feed?timeRange=' + currentRange);
                const data = await res.json();
                
                // Update KPIs
                animateValue('kpi-total', data.kpis.totalEvents);
                animateValue('kpi-itwins', data.kpis.uniqueITwins);
                animateValue('kpi-imodels', data.kpis.uniqueIModels);
                animateValue('kpi-types', data.kpis.eventTypes);
                
                // Update Health
                const healthDot = document.getElementById('health-dot');
                healthDot.className = 'health-indicator ' + data.health;
                document.getElementById('health-text').textContent = data.health.toUpperCase();
                
                // Update Insights
                document.getElementById('insights').textContent = data.insights;
                
                // Update Table
                const tbody = document.getElementById('events-body');
                if (data.recentEvents.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" class="empty-state"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg><h3>No Events Found</h3><p>Configure your Bentley webhooks to start receiving data.</p></td></tr>';
                } else {
                    tbody.innerHTML = data.recentEvents.map(e => {
                        const date = new Date(e.received_at);
                        const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                        const badgeClass = getBadgeClass(e.eventType);
                        return `<tr>
                            <td><span class="event-badge ${badgeClass}">${escapeHtml(e.eventType)}</span></td>
                            <td>${escapeHtml(e.iTwinName || '-')}</td>
                            <td>${escapeHtml(e.iModelName || '-')}</td>
                            <td class="timestamp">${timeStr}</td>
                        </tr>`;
                    }).join('');
                }
                
                // Update Distribution
                const distBody = document.getElementById('distribution-body');
                const total = data.kpis.totalEvents || 1;
                const sortedTypes = Object.entries(data.eventTypeBreakdown || {}).sort((a,b) => b[1] - a[1]).slice(0, 5);
                
                if (sortedTypes.length === 0) {
                    distBody.innerHTML = '<p style="font-size: 0.8rem; color: #888;">No data available</p>';
                } else {
                    distBody.innerHTML = sortedTypes.map(([type, count]) => {
                        const percent = Math.round((count / total) * 100);
                        return `<div class="dist-item">
                            <div class="dist-info">
                                <span>${type.split('.').slice(-2).join('.')}</span>
                                <span>${count} (${percent}%)</span>
                            </div>
                            <div class="dist-bar-bg">
                                <div class="dist-bar-fg" style="width: ${percent}%"></div>
                            </div>
                        </div>`;
                    }).join('');
                }
                
                document.getElementById('last-update-time').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
                
                setTimeout(() => {
                    manualBtn.style.opacity = '1';
                    manualBtn.disabled = false;
                }, 500);

            } catch (err) {
                console.error('Fetch error:', err);
                document.getElementById('health-text').textContent = 'OFFLINE';
                document.getElementById('health-dot').className = 'health-indicator busy';
            }
        }
        
        function getBadgeClass(type) {
            type = type.toLowerCase();
            if (type.includes('imodel')) return 'imodel';
            if (type.includes('itwin')) return 'itwin';
            if (type.includes('access') || type.includes('role')) return 'access';
            return '';
        }
        
        function animateValue(id, end) {
            const obj = document.getElementById(id);
            const start = parseInt(obj.textContent) || 0;
            if (start === end) return;
            
            const duration = 500;
            let startTimestamp = null;
            const step = (timestamp) => {
                if (!startTimestamp) startTimestamp = timestamp;
                const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                obj.textContent = Math.floor(progress * (end - start) + start);
                if (progress < 1) {
                    window.requestAnimationFrame(step);
                }
            };
            window.requestAnimationFrame(step);
        }
        
        function escapeHtml(str) {
            if (!str) return '';
            const div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
        }
        
        document.querySelectorAll('.time-filter button').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.time-filter button').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentRange = btn.dataset.range;
                fetchData();
            });
        });
        
        document.getElementById('manual-refresh').addEventListener('click', fetchData);
        
        fetchData();
        refreshInterval = setInterval(fetchData, 15000);
    </script>
</body>
</html>"""


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(content=DASHBOARD_HTML, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
