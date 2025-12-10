import os, hmac, hashlib, json, requests, logging, asyncio, re
from fastapi import FastAPI, Request, HTTPException
from datetime import datetime
from pathlib import Path

BENTLEY_CLIENT_ID     = os.getenv("BENTLEY_CLIENT_ID")
BENTLEY_CLIENT_SECRET = os.getenv("BENTLEY_CLIENT_SECRET")
DEEPSEEK_API_KEY      = os.getenv("DEEPSEEK_API_KEY")
WEBHOOK_SECRET        = os.getenv("WEBHOOK_SECRET", "gem_webhook_secret")
CALLBACK_URL          = os.getenv("CALLBACK_URL", "https://your-repl-url.repl.co/webhook")

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    filename=LOG_DIR / "agent.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)

app = FastAPI(
    title="GEM AI Agent for Bentley",
    version="2.0",
    description="Webhook service integrating Bentley iTwin with DeepSeek AI"
)

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
        return False
    expected = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

def call_deepseek(prompt: str) -> str:
    if not DEEPSEEK_API_KEY:
        logging.warning("DEEPSEEK_API_KEY not configured")
        return "AI analysis unavailable - API key not configured."
    try:
        r = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an AI assistant specialized in analyzing Bentley iTwin platform events. Provide concise, actionable summaries of webhook events including key details like affected resources, user actions, and potential impacts."
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.4
            },
            timeout=30
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        logging.error("DeepSeek API timeout")
        return "AI analysis unavailable - request timed out."
    except requests.exceptions.RequestException as e:
        logging.error(f"DeepSeek API error: {e}")
        return f"AI analysis unavailable - API error."
    except Exception as e:
        logging.error(f"DeepSeek unexpected error: {e}")
        return "AI analysis unavailable."

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^\w\-.]', '_', name)

def log_event(event_type: str, summary: str, payload: dict):
    safe_event = sanitize_filename(event_type)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = LOG_DIR / f"{timestamp}_{safe_event}.md"
    content = f"""# Event: {event_type}

**Received**: {datetime.utcnow().isoformat()}Z

## AI Summary

{summary}

---

## Raw Payload

```json
{json.dumps(payload, indent=2)}
```
"""
    filename.write_text(content)
    logging.info(f"Logged event {event_type} to {filename}")

@app.get("/")
async def root():
    return {
        "service": "GEM AI Agent for Bentley",
        "version": "2.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "webhook": "/webhook"
        },
        "supported_events": len(SUPPORTED_EVENT_TYPES)
    }

@app.get("/health")
async def health():
    return {
        "status": "running",
        "time": datetime.utcnow().isoformat(),
        "deepseek_configured": bool(DEEPSEEK_API_KEY),
        "bentley_configured": bool(BENTLEY_CLIENT_ID and BENTLEY_CLIENT_SECRET)
    }

@app.post("/webhook")
async def webhook(req: Request):
    body = await req.body()
    sig = req.headers.get("Signature") or req.headers.get("signature", "")
    
    if not verify_signature(body, sig):
        logging.warning(f"Invalid signature received from {req.client.host if req.client else 'unknown'}")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        data = await req.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    event_type = data.get("eventType", "UnknownEvent")
    logging.info(f"Received event: {event_type}")
    
    prompt = f"""Analyze this Bentley iTwin webhook event and provide a concise summary:

Event Type: {event_type}

Full Event Data:
{json.dumps(data, indent=2)}

Please summarize:
1. What happened (the action/event)
2. Key resources affected (IDs, names if available)
3. Any important metadata or context
4. Potential follow-up actions if applicable"""

    summary = await asyncio.to_thread(call_deepseek, prompt)
    await asyncio.to_thread(log_event, event_type, summary, data)
    
    return {
        "status": "processed",
        "eventType": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "summary": summary
    }

@app.get("/events")
async def list_events():
    event_files = sorted(LOG_DIR.glob("*.md"), reverse=True)[:20]
    events = []
    for f in event_files:
        events.append({
            "filename": f.name,
            "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        })
    return {"recent_events": events, "total_shown": len(events)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
