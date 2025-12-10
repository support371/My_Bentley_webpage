#!/usr/bin/env bash
set -e

echo "================================================"
echo "Add /seed Test Endpoint (Non-Destructive, MVP)"
echo "================================================"

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

read -r -d '' NODE_SEED_SNIPPET <<'JS'

// ============================================================
// Dev-only /seed endpoint (MVP)
// Added by add_seed_endpoint.sh
//
// Purpose:
// - Generate synthetic events to validate /events, /dashboard/feed,
//   /dashboard/health, and the /dashboard UI.
// - Non-destructive: uses existing `events` array if present,
//   else uses global.__GEM_EVENTS__ fallback.
//
// Security note:
// - This is intended for development environments only.
// - You can disable it by setting DISABLE_SEED=true
// ============================================================

const SEED_DISABLED = String(process.env.DISABLE_SEED || "").toLowerCase() === "true";

global.__GEM_EVENTS__ = global.__GEM_EVENTS__ || [];
const __seedStore = (typeof events !== "undefined") ? events : global.__GEM_EVENTS__;

const __MVP_TYPES = [
  "iModels.iModelCreated.v1",
  "iModels.iModelDeleted.v1",
  "iModels.namedVersionCreated.v1",
  "iModels.changesReady.v1"
];

function __mkId() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function __seedEvent(eventType, iTwinId, iModelId, iTwinName, iModelName, user, versionName) {
  return {
    id: __mkId(),
    eventType,
    timestamp: new Date().toISOString(),
    payload: {
      iTwinId,
      iModelId,
      iTwinName,
      iModelName,
      user,
      versionName: versionName || undefined,
      changeSetId: "changeset-" + Math.random().toString(36).slice(2, 10)
    }
  };
}

/**
 * POST /seed
 * Body (all optional):
 * {
 *   count: number (default 8),
 *   iTwinId: string,
 *   iModelId: string,
 *   iTwinName: string,
 *   iModelName: string,
 *   user: string
 * }
 *
 * Response:
 * { inserted, sampleIds[] }
 */
app.post("/seed", (req, res) => {
  try {
    if (SEED_DISABLED) {
      return res.status(403).json({ error: "seed_disabled" });
    }

    const {
      count = 8,
      iTwinId = "itwin-seed-001",
      iModelId = "imodel-seed-001",
      iTwinName = "Seed iTwin",
      iModelName = "Seed iModel",
      user = "seed@local"
    } = req.body || {};

    const n = Math.max(1, Math.min(50, Number(count) || 8));
    const ids = [];

    for (let i = 0; i < n; i++) {
      const type = __MVP_TYPES[i % __MVP_TYPES.length];
      const versionName = type === "iModels.namedVersionCreated.v1"
        ? `v${1 + (i % 3)}.${i}`
        : undefined;

      const ev = __seedEvent(type, iTwinId, iModelId, iTwinName, iModelName, user, versionName);
      __seedStore.push(ev);
      ids.push(ev.id);
    }

    res.json({ inserted: n, sampleIds: ids.slice(0, 5), totalStored: __seedStore.length });
  } catch (err) {
    res.status(500).json({ error: "seed_failed", message: String(err?.message || err) });
  }
});

/**
 * GET /seed
 * Quick sanity check
 */
app.get("/seed", (req, res) => {
  if (SEED_DISABLED) return res.status(403).json({ error: "seed_disabled" });
  res.json({
    status: "ready",
    disabled: SEED_DISABLED,
    supportedTypes: __MVP_TYPES
  });
});
JS


read -r -d '' FASTAPI_SEED_SNIPPET <<'PY'

# ============================================================
# Dev-only /seed endpoint (MVP)
# Added by add_seed_endpoint.sh
#
# Purpose:
# - Generate synthetic events to validate /events,
#   /dashboard/feed, /dashboard/health, and UI.
#
# Security note:
# - Intended for development only.
# - Disable with DISABLE_SEED=true
# ============================================================

import os
import random
from datetime import datetime
from fastapi import Body
from fastapi.responses import JSONResponse

SEED_DISABLED = str(os.getenv("DISABLE_SEED", "")).lower() == "true"

try:
    __seedStore = events  # type: ignore
except Exception:
    if not hasattr(app.state, "gem_events"):
        app.state.gem_events = []
    __seedStore = app.state.gem_events

__MVP_TYPES = [
    "iModels.iModelCreated.v1",
    "iModels.iModelDeleted.v1",
    "iModels.namedVersionCreated.v1",
    "iModels.changesReady.v1"
]

def __mk_id():
    return f"{random.randint(100000,999999)}-{int(datetime.utcnow().timestamp()*1000)}"

def __seed_event(eventType, iTwinId, iModelId, iTwinName, iModelName, user, versionName=None):
    payload = {
        "iTwinId": iTwinId,
        "iModelId": iModelId,
        "iTwinName": iTwinName,
        "iModelName": iModelName,
        "user": user,
        "changeSetId": f"changeset-{random.randint(1000,9999)}"
    }
    if versionName:
        payload["versionName"] = versionName

    return {
        "id": __mk_id(),
        "eventType": eventType,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": payload
    }

@app.get("/seed")
def seed_status():
    if SEED_DISABLED:
        return JSONResponse(status_code=403, content={"error": "seed_disabled"})
    return {
        "status": "ready",
        "disabled": SEED_DISABLED,
        "supportedTypes": __MVP_TYPES
    }

@app.post("/seed")
def seed_events(body: dict = Body(default={})):
    if SEED_DISABLED:
        return JSONResponse(status_code=403, content={"error": "seed_disabled"})

    count = int(body.get("count", 8))
    count = max(1, min(50, count))

    iTwinId = body.get("iTwinId", "itwin-seed-001")
    iModelId = body.get("iModelId", "imodel-seed-001")
    iTwinName = body.get("iTwinName", "Seed iTwin")
    iModelName = body.get("iModelName", "Seed iModel")
    user = body.get("user", "seed@local")

    ids = []
    for i in range(count):
        et = __MVP_TYPES[i % len(__MVP_TYPES)]
        versionName = f"v{1 + (i % 3)}.{i}" if et == "iModels.namedVersionCreated.v1" else None
        ev = __seed_event(et, iTwinId, iModelId, iTwinName, iModelName, user, versionName)
        __seedStore.append(ev)
        ids.append(ev["id"])

    return {
        "inserted": count,
        "sampleIds": ids[:5],
        "totalStored": len(__seedStore)
    }
PY


patch_node() {
  local f="$1"
  echo "----------------------------------------------"
  echo "Detected Node entrypoint: $f"
  echo "Creating backup: $f.bak"
  cp "$f" "$f.bak"

  if grep -q "app.post(\"/seed\"" "$f" || grep -q "app.post('/seed'" "$f"; then
    echo "ℹ️  /seed already exists in $f. Skipping Node patch."
    return
  fi

  if ! grep -q "express" "$f" || ! grep -q "const app" "$f"; then
    echo "⚠️  Express pattern not confirmed in $f. Skipping."
    return
  fi

  echo "Injecting /seed endpoints into $f..."
  cat >> "$f" <<JS
$NODE_SEED_SNIPPET
JS

  echo "✅ Node /seed patch applied."
}

patch_fastapi() {
  local f="$1"
  echo "----------------------------------------------"
  echo "Detected Python entrypoint: $f"
  echo "Creating backup: $f.bak"
  cp "$f" "$f.bak"

  if ! grep -q "FastAPI" "$f"; then
    echo "⚠️  FastAPI not detected in $f. Skipping."
    return
  fi

  if grep -q "@app.post(\"/seed\")" "$f" || grep -q "@app.post('/seed')" "$f"; then
    echo "ℹ️  /seed already exists in $f. Skipping Python patch."
    return
  fi

  echo "Injecting FastAPI /seed endpoints into $f..."
  cat >> "$f" <<PY
$FASTAPI_SEED_SNIPPET
PY

  echo "✅ FastAPI /seed patch applied."
}

if [ -n "$node_main" ] && [ -f "package.json" ]; then
  patch_node "$node_main"
elif [ -n "$py_main" ] && ([ -f "requirements.txt" ] || [ -f "pyproject.toml" ]); then
  patch_fastapi "$py_main"
else
  echo "----------------------------------------------"
  echo "Could not confidently detect Node/Express or FastAPI entrypoint."
  echo "No /seed patch applied."
fi

echo "----------------------------------------------"
echo "Finished."
echo "Use /seed only in development."
echo "Disable any time with: DISABLE_SEED=true"
echo "----------------------------------------------"
