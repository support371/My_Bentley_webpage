# Bentley iTwin Webhooks Dashboard MVP

A lightweight webhook service for Bentley iTwin platform with a live dashboard.

## Stack

- **Runtime**: Python 3.11
- **Framework**: FastAPI + Uvicorn
- **Storage**: In-memory event store

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service info and supported events |
| GET | `/health` | Health check with event count |
| POST | `/webhook` | Receive iTwin webhook events |
| GET | `/events` | List recent events (newest first) |
| GET | `/dashboard` | Live dashboard UI with auto-refresh |
| GET | `/dashboard/feed` | JSON feed for dashboard data |

## URLs

### Development (Preview)
```
https://gem-ai-agentzip--suarezcarolina8.replit.dev/dashboard
```

### Production (Deployed)
```
https://gem-ai-agentzip--suarezcarolina8.replit.app/dashboard
```

## Quick Commands

### Run Smoke Test
```bash
bash smoke-test.sh
```

### Seed Test Data
```bash
bash seed.sh
```

### Verify Health
```bash
curl http://127.0.0.1:5000/health
```

## Dashboard Features

- **KPI Cards**: Total events, unique iTwins, unique iModels, event types
- **Health Status**: Visual indicator (healthy/busy/idle)
- **AI Summary**: Insights based on recent activity
- **Events Table**: Last 20 events with details
- **Time Filters**: 1h, 6h, 24h, 7d, 30d
- **Auto-refresh**: Updates every 15 seconds

## Webhook Integration

Register your webhook URL with Bentley iTwin:
```
https://gem-ai-agentzip--suarezcarolina8.replit.dev/webhook
```

Supported event types include:
- iModels (created, deleted, versioned, changes ready)
- iTwins (created, deleted)
- Access Control (member added/removed, role assigned/unassigned)
- Jobs (synchronization, transformations, reality modeling)
- Forms and Issues (created, updated, deleted)

## Environment Variables (Optional)

- `WEBHOOK_SECRET` - Secret for signature validation (default: gem_webhook_secret)

## Security Note

For MVP/testing purposes, the webhook endpoint accepts requests without signature validation to enable easy testing with `seed.sh`. For production use with Bentley iTwin, configure `WEBHOOK_SECRET` to match your Bentley webhook configuration. When a signature header is provided, it will be validated.

## Notes

- Importing to a new Replit account changes the domain
- Events are stored in-memory and reset on restart
- Dashboard uses no external dependencies (vanilla HTML/CSS/JS)
