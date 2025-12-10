#!/usr/bin/env bash
set -e

echo "=============================================="
echo "Minimal Dashboard UI Add-On (Non-Destructive)"
echo "=============================================="

# 1) Create a minimalist static dashboard page
mkdir -p public

cat > public/dashboard.html << 'HTML'
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>iTwin Activity Monitor (MVP)</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; background: #0b1020; color: #eef2ff; }
    .wrap { max-width: 1100px; margin: 0 auto; padding: 28px 20px 60px; }
    .header { display: flex; justify-content: space-between; align-items: baseline; gap: 16px; }
    .title { font-size: 28px; font-weight: 700; letter-spacing: .3px; }
    .sub { opacity: .7; font-size: 12px; }
    .bar { display: flex; gap: 8px; margin: 18px 0 22px; flex-wrap: wrap; }
    .btn { background: #111833; border: 1px solid #22305c; color: #dbeafe; padding: 8px 12px; border-radius: 8px; cursor: pointer; font-size: 12px; }
    .btn.active { background: #2563eb; border-color: #2563eb; color: white; }
    .grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
    @media (max-width: 900px){ .grid{ grid-template-columns: repeat(2, minmax(0, 1fr)); } }
    @media (max-width: 520px){ .grid{ grid-template-columns: 1fr; } }
    .card { background: linear-gradient(180deg, #0f1733, #0b1228); border: 1px solid #22305c; border-radius: 14px; padding: 16px; }
    .k-title { font-size: 12px; opacity: .7; }
    .k-value { font-size: 34px; font-weight: 700; margin-top: 6px; }
    .k-sub { font-size: 11px; opacity: .65; margin-top: 2px; }
    .section { margin-top: 18px; }
    .sec-title { font-size: 14px; font-weight: 600; margin-bottom: 10px; }
    .row { display: grid; grid-template-columns: 2fr 1fr; gap: 12px; }
    @media (max-width: 900px){ .row{ grid-template-columns: 1fr; } }
    table { width: 100%; border-collapse: collapse; font-size: 12px; }
    th, td { padding: 10px 8px; border-bottom: 1px solid #22305c; text-align: left; }
    th { opacity: .75; font-weight: 600; }
    .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 10px; border: 1px solid #22305c; }
    .healthy { background: #052e1a; color: #86efac; }
    .warning { background: #2a1b05; color: #fde68a; }
    .critical { background: #2a0b0b; color: #fca5a5; }
    .muted { opacity: .6; }
    .footer { margin-top: 22px; font-size: 11px; opacity: .6; }
    .error { background: #2a0b0b; border: 1px solid #7f1d1d; padding: 10px 12px; border-radius: 10px; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <div>
        <div class="title">iTwin Activity Monitor (MVP)</div>
        <div class="sub">Webhooks V2 → Events → Computed Feed</div>
      </div>
      <div class="sub">Last updated: <span id="lastUpdated">-</span></div>
    </div>

    <div class="bar" id="rangeBar">
      <button class="btn active" data-range="24h">24h</button>
      <button class="btn" data-range="48h">48h</button>
      <button class="btn" data-range="72h">72h</button>
      <button class="btn" data-range="7d">7d</button>
    </div>

    <div class="grid" id="kpis">
      <div class="card"><div class="k-title">iModels Created</div><div class="k-value">-</div><div class="k-sub muted">awaiting feed</div></div>
      <div class="card"><div class="k-title">iModels Deleted</div><div class="k-value">-</div><div class="k-sub muted">awaiting feed</div></div>
      <div class="card"><div class="k-title">Named Versions</div><div class="k-value">-</div><div class="k-sub muted">awaiting feed</div></div>
      <div class="card"><div class="k-title">Changes Ready</div><div class="k-value">-</div><div class="k-sub muted">awaiting feed</div></div>
    </div>

    <div class="section row">
      <div class="card">
        <div class="sec-title">Recent Events (from /events)</div>
        <div id="eventsErr"></div>
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Event Type</th>
              <th>iTwin</th>
              <th>iModel</th>
              <th>User</th>
            </tr>
          </thead>
          <tbody id="eventsBody">
            <tr><td colspan="5" class="muted">Loading...</td></tr>
          </tbody>
        </table>
      </div>

      <div class="card">
        <div class="sec-title">Health Snapshot (from /dashboard/health if available)</div>
        <div id="healthBox" class="muted">Loading...</div>
        <div class="sec-title" style="margin-top:14px;">AI Summary (from /ai/insights if available)</div>
        <div id="aiBox" class="muted">Loading...</div>
      </div>
    </div>

    <div class="footer">
      This MVP UI expects your backend to expose /events and ideally /dashboard/feed and /dashboard/health.
      If those endpoints are not present in this repl, the UI will still render using raw events.
    </div>
  </div>

<script>
  let currentRange = "24h";

  function setActive(btn){
    document.querySelectorAll("#rangeBar .btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
  }

  document.querySelectorAll("#rangeBar .btn").forEach(btn => {
    btn.addEventListener("click", () => {
      setActive(btn);
      currentRange = btn.dataset.range;
      loadAll();
    });
  });

  function fmtName(payload, prefix){
    if (!payload) return `${prefix}-unknown`;
    const name = payload[`${prefix}Name`];
    const id = payload[`${prefix}Id`];
    if (name) return name;
    if (id) return `${prefix}-${String(id).slice(0,8)}`;
    return `${prefix}-unknown`;
  }

  function fmtUser(payload){
    return (payload && payload.user) ? payload.user : "System";
  }

  async function loadFeed(){
    // Feed is optional. If not present, we won't fail the UI.
    try {
      const r = await fetch(`/dashboard/feed?timeRange=${currentRange}`);
      if (!r.ok) return null;
      return await r.json();
    } catch { return null; }
  }

  async function loadHealth(){
    try {
      const r = await fetch(`/dashboard/health?period=${currentRange}`);
      if (!r.ok) return null;
      return await r.json();
    } catch { return null; }
  }

  async function loadAI(){
    try {
      const r = await fetch(`/ai/insights`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ timeRange: currentRange })
      });
      if (!r.ok) return null;
      return await r.json();
    } catch { return null; }
  }

  async function loadEvents(){
    try {
      const r = await fetch(`/events?limit=20`);
      if (!r.ok) throw new Error("events fetch failed");
      return await r.json();
    } catch (e) {
      document.getElementById("eventsErr").innerHTML =
        `<div class="error">/events not reachable in this repl.</div>`;
      return { events: [] };
    }
  }

  function renderKPIsFromFeed(feed){
    const cards = document.querySelectorAll("#kpis .card");
    const map = [
      ["iModels Created", feed?.kpis?.iModelsCreated ?? "-",
       `Net ${feed?.kpis?.netGrowth ?? "-"}`],
      ["iModels Deleted", feed?.kpis?.iModelsDeleted ?? "-", "MVP scope"],
      ["Named Versions", feed?.kpis?.namedVersions ?? "-",
       `Ratio ${feed?.kpis?.versionRatio ?? "-"}`],
      ["Changes Ready", feed?.kpis?.changesReady ?? "-",
       `${feed?.kpis?.percentVersioned ?? "-"}% versioned`],
    ];
    cards.forEach((c, i) => {
      c.innerHTML = `
        <div class="k-title">${map[i][0]}</div>
        <div class="k-value">${map[i][1]}</div>
        <div class="k-sub">${map[i][2]}</div>
      `;
    });
  }

  function renderEvents(ev){
    const body = document.getElementById("eventsBody");
    const list = ev?.events ?? [];
    if (!list.length){
      body.innerHTML = `<tr><td colspan="5" class="muted">No events yet.</td></tr>`;
      return;
    }
    body.innerHTML = list.map(e => {
      const t = new Date(e.timestamp || Date.now()).toLocaleTimeString();
      const p = e.payload || {};
      const itwin = fmtName(p, "iTwin");
      const imodel = fmtName(p, "iModel");
      const user = fmtUser(p);
      return `
        <tr>
          <td>${t}</td>
          <td>${e.eventType || e.type || "unknown"}</td>
          <td>${itwin}</td>
          <td>${imodel}</td>
          <td>${user}</td>
        </tr>
      `;
    }).join("");
  }

  function renderHealth(h){
    const box = document.getElementById("healthBox");
    if (!h){
      box.innerHTML = `<span class="muted">/dashboard/health not available in this repl.</span>`;
      return;
    }
    const score = h.overallScore ?? h.score ?? h.overall ?? 0;
    const status = (h.status || "healthy").toLowerCase();
    const cls = status.includes("crit") ? "critical" : status.includes("warn") ? "warning" : "healthy";
    box.innerHTML = `
      <div style="font-size:36px;font-weight:700;">${score}/100</div>
      <span class="pill ${cls}">${status.toUpperCase()}</span>
    `;
  }

  function renderAI(ai){
    const box = document.getElementById("aiBox");
    if (!ai){
      box.innerHTML = `<span class="muted">/ai/insights not available in this repl.</span>`;
      return;
    }
    const s = ai.summary24h || ai.summary || "AI response received.";
    box.innerHTML = `<div>${s}</div>`;
  }

  function setLastUpdated(ts){
    document.getElementById("lastUpdated").textContent =
      ts ? new Date(ts).toLocaleTimeString() : new Date().toLocaleTimeString();
  }

  async function loadAll(){
    const [feed, events, health, ai] = await Promise.all([
      loadFeed(), loadEvents(), loadHealth(), loadAI()
    ]);
    renderKPIsFromFeed(feed);
    renderEvents(events);
    renderHealth(health);
    renderAI(ai);
    setLastUpdated(feed?.meta?.lastUpdated || feed?.lastUpdated);
  }

  loadAll();
  setInterval(loadAll, 15000);
</script>
</body>
</html>
HTML

echo "✅ Created public/dashboard.html"

# 2) Detect stack + main file candidates
NODE_FILES=("index.js" "server.js" "app.js")
PY_FILES=("main.py" "app.py")

node_main=""
py_main=""

for f in "${NODE_FILES[@]}"; do
  if [ -f "$f" ]; then node_main="$f"; break; fi
done

for f in "${PY_FILES[@]}"; do
  if [ -f "$f" ]; then py_main="$f"; break; fi
done

# 3) Non-destructive patch for Node/Express
patch_node() {
  local f="$1"
  echo "----------------------------------------------"
  echo "Detected Node entrypoint: $f"
  echo "Creating backup: $f.bak"
  cp "$f" "$f" "$f.bak"

  # Add static serving if not present
  if ! grep -q "express.static" "$f"; then
    # Try to insert after express initialization
    # We'll append a safe block near top if we can’t match patterns.
    echo "Patching express.static for /public..."
    # naive insert after app.use(express.json()) if present
    if grep -q "app.use(express.json" "$f"; then
      awk '
        {print}
        /app.use\(express.json/ && !x {
          print "app.use(express.static(\\\"public\\\"));";
          x=1
        }
      ' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
    else
      # fallback append near top
      sed -i '1i\// Added by add_dashboard_ui.sh\n' "$f" 2>/dev/null || true
      # Best-effort append after app creation line
      awk '
        {print}
        /const app = express\(\)/ && !x {
          print "app.use(express.static(\\\"public\\\"));";
          x=1
        }
      ' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
    fi
  fi

  # Add /dashboard route only if not present
  if ! grep -q "app.get('/dashboard'" "$f" && ! grep -q 'app.get("/dashboard"' "$f"; then
    echo "Adding /dashboard route..."
    cat >> "$f" <<'JS'

/* ============================================
   Minimal Dashboard UI route (non-destructive)
   Added by add_dashboard_ui.sh
   Serves static MVP UI without changing core logic
============================================ */
app.get('/dashboard', (req, res) => {
  res.sendFile(require('path').join(__dirname, 'public', 'dashboard.html'));
});
JS
  fi

  echo "✅ Node patch applied to $f"
}

# 4) Non-destructive patch for Python/FastAPI
patch_fastapi() {
  local f="$1"
  echo "----------------------------------------------"
  echo "Detected Python entrypoint: $f"
  echo "Creating backup: $f.bak"
  cp "$f" "$f" "$f.bak"

  # Only patch if FastAPI import appears
  if grep -q "FastAPI" "$f"; then
    echo "FastAPI detected. Adding static mount + /dashboard route if missing."

    if ! grep -q "StaticFiles" "$f"; then
      # Add import for StaticFiles
      # Insert after FastAPI import line if possible
      awk '
        {print}
        /from fastapi import FastAPI/ && !x {
          print "from fastapi.staticfiles import StaticFiles";
          x=1
        }
      ' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
    fi

    # Mount static if not present
    if ! grep -q "app.mount" "$f"; then
      # Insert mount right after app creation
      awk '
        {print}
        /app = FastAPI\(/ && !x {
          print "app.mount(\"/public\", StaticFiles(directory=\"public\"), name=\"public\")";
          x=1
        }
      ' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
    fi

    # Add /dashboard route if not present
    if ! grep -q "@app.get(\"/dashboard\")" "$f" && ! grep -q "@app.get('/dashboard')" "$f"; then
      cat >> "$f" <<'PY'

# ============================================
# Minimal Dashboard UI route (non-destructive)
# Added by add_dashboard_ui.sh
# Serves static MVP UI without changing core logic
# ============================================
from fastapi.responses import HTMLResponse

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_ui():
    with open("public/dashboard.html", "r", encoding="utf-8") as f:
        return f.read()
PY
    fi

    echo "✅ FastAPI patch applied to $f"
  else
    echo "FastAPI not clearly detected in $f. No Python patch applied."
  fi
}

# 5) Execute the appropriate patch
if [ -n "$node_main" ] && [ -f "package.json" ]; then
  patch_node "$node_main"
elif [ -n "$py_main" ] && ([ -f "requirements.txt" ] || [ -f "pyproject.toml" ]); then
  patch_fastapi "$py_main"
else
  echo "----------------------------------------------"
  echo "Could not confidently detect Node or FastAPI entrypoint."
  echo "Dashboard UI file was created at: public/dashboard.html"
  echo "You can serve it by adding a /dashboard route in your stack."
fi

echo "----------------------------------------------"
echo "Done."
echo "What you should have now:"
echo " - public/dashboard.html"
echo " - A minimal /dashboard route if Node/Express or FastAPI was detected"
echo "----------------------------------------------"
