import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

IMODELS = [
    {"id":"civil-infrastructure-hub","display_name":"Civil Infrastructure Hub","state":"initialized","itwin_name":"Smart City Alpha","event_count":18},
    {"id":"roads-bridges-network","display_name":"Roads & Bridges Network","state":"initialized","itwin_name":"Transport Grid","event_count":11},
    {"id":"digital-twin-facility-a","display_name":"Digital Twin Facility A","state":"initialized","itwin_name":"Bentley Connect","event_count":7},
]

STYLE = "body{margin:0;background:#080d1d;color:#eef3ff;font-family:Inter,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif}.top{height:78px;display:flex;align-items:center;gap:22px;padding:0 24px;background:#050917;border-bottom:1px solid #1b2740}.brand{font-size:24px;font-weight:900}.nav{margin-left:auto;display:flex;gap:12px}.nav a{color:#dbe7ff;text-decoration:none;background:#121b33;border:1px solid #263654;padding:12px 16px;border-radius:10px}.wrap{max-width:1080px;margin:auto;padding:46px 28px}.title{font-size:50px;margin:0 0 22px}.subtitle{font-size:24px;color:#9aa8c0;margin:0 0 38px}.btn{background:#4f86f7;color:white;padding:15px 24px;border-radius:10px;text-decoration:none;font-weight:800;display:inline-block}.toolbar{display:flex;gap:18px;flex-wrap:wrap;margin:34px 0}.input,.select{background:#172235;border:1px solid #2b3751;color:#eef3ff;border-radius:12px;padding:18px 22px;font-size:20px}.tabs{display:flex;gap:14px;align-items:center;margin-bottom:28px}.tab{background:#111827;border:1px solid #2b3751;color:#9aa8c0;border-radius:10px;padding:14px 24px}.tab.active{background:#4f86f7;color:#fff}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:22px}.card{background:#182234;border:1px solid #2b3751;border-radius:16px;padding:26px}.card h3{margin:0 0 12px;font-size:24px}.card p{color:#9aa8c0;line-height:1.5}.badge{display:inline-block;background:#0b1329;border-radius:18px;padding:7px 12px;color:#cdd9ee;font-size:14px}.row{display:flex;justify-content:space-between;color:#9aa8c0;margin-top:10px}.row b{color:#eef3ff}.pill{background:#153264;color:#8fb9ff;padding:3px 9px;border-radius:999px}@media(max-width:720px){.title{font-size:36px}.subtitle{font-size:22px}.input,.select{width:100%;font-size:18px}.nav{overflow-x:auto}.nav a{padding:10px 12px}.wrap{padding:38px 22px}}"


def json_body(obj):
    return json.dumps(obj).encode("utf-8")


def page(body, title="iTwin Ops"):
    nav = "<header class='top'><div class='brand'>iTwin Ops</div><nav class='nav'><a href='/imodels-view'>iModels</a><a href='/integrations'>Integrations</a><a href='/login'>Sign in</a></nav></header>"
    return ("<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>"+title+"</title><style>"+STYLE+"</style></head><body>"+nav+body+"</body></html>").encode("utf-8")


def imodels_html():
    cards = ""
    for m in IMODELS:
        cards += "<article class='card'><h3>"+m["display_name"]+"</h3><span class='badge'>"+m["state"]+"</span><p>Digital model linked to "+m["itwin_name"]+".</p><div class='row'><span>ID</span><b>"+m["id"]+"</b></div><div class='row'><span>iTwin</span><b>"+m["itwin_name"]+"</b></div><div class='row'><span>Events</span><b class='pill'>"+str(m["event_count"])+"</b></div></article>"
    body = "<main class='wrap'><h1 class='title'>iModel Explorer</h1><p class='subtitle'>Digital models linked to iTwin projects</p><a class='btn' href='/imodels-view'>Refresh</a><div class='toolbar'><input class='input' placeholder='Search iModels...'><select class='select'><option>All States</option></select></div><div class='tabs'><span class='tab active'>Recent</span><span class='tab'>Name</span><span class='tab'>Events</span><span>"+str(len(IMODELS))+" iModels</span></div><section class='grid'>"+cards+"</section></main>"
    return page(body, "iModel Explorer")


def integrations_html():
    names = ["GitHub","Vercel","OpenAI","Gemini","GitHub Copilot","DeepSeek AI","Cursor","Azure DevOps","Slack","Jira"]
    cards = "".join(["<article class='card'><h3>"+n+"</h3><span class='badge'>Not connected</span><p>Integration connector available for the iTwin Ops platform.</p><div class='row'><span>Docs</span><b>Open</b></div></article>" for n in names])
    return page("<main class='wrap'><h1 class='title'>Integrations</h1><p class='subtitle'>Connect GitHub, Vercel, AI, DevOps, notifications, and project management services.</p><section class='grid'>"+cards+"</section></main>", "Integrations")


class handler(BaseHTTPRequestHandler):
    def send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path in ["/", "/dashboard", "/imodels-view"]:
            return self.send(200, imodels_html(), "text/html; charset=utf-8")
        if path == "/integrations":
            return self.send(200, integrations_html(), "text/html; charset=utf-8")
        if path == "/login":
            return self.send(200, page("<main class='wrap'><h1 class='title'>iTwin Operations Center</h1><p class='subtitle'>Bentley Platform Intelligence</p><a class='btn' href='/imodels-view'>Sign In</a></main>", "Sign In"), "text/html; charset=utf-8")
        if path == "/health":
            return self.send(200, json_body({"status":"healthy","service":"iTwin Ops","timestamp":datetime.now(timezone.utc).isoformat()}), "application/json; charset=utf-8")
        if path == "/api/imodels":
            now = datetime.now(timezone.utc).isoformat()
            payload = {"imodels":[{**m,"last_event_at":now,"created_at":now} for m in IMODELS],"total":len(IMODELS),"states":["initialized"],"source":"vercel-recovered-shell","degraded":False,"error":None}
            return self.send(200, json_body(payload), "application/json; charset=utf-8")
        return self.send(404, page("<main class='wrap'><h1 class='title'>Page not found</h1><a class='btn' href='/imodels-view'>Open iModel Explorer</a></main>", "Not Found"), "text/html; charset=utf-8")
