# Bentley iTwin Automation Platform

A complete FastAPI platform for Bentley iTwin webhook operations, live monitoring, and integration orchestration.

## Stack
- **Runtime**: Python 3.11+
- **Framework**: FastAPI + Uvicorn
- **Storage**: In-memory event store (resets on restart)
- **Frontend**: Vanilla HTML/CSS/JS served directly by FastAPI

## Core Features
- **Multi-section Operations Dashboard**: Overview, Live operations, Integrations, Workflows, and Rollout checklist.
- **Webhook Intake**: Endpoint for receiving and validating Bentley iTwin webhook events.
- **Integration Readiness**: Built-in support and guidance for Azure DevOps, Monday.com, and Atlassian Rovo AI.
- **Workflow Blueprints**: Trigger-to-action templates for automated delivery.

## Supported Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service entry summary |
| GET | `/health` | Health check with event and integration counts |
| POST | `/webhook` | Receive Bentley iTwin webhook events |
| GET | `/events` | List recent events (newest first) |
| GET | `/dashboard` | Main operations dashboard UI |
| GET | `/dashboard/feed` | Platform feed for dashboard rendering (JSON) |
| GET | `/integrations` | Integration-focused platform UI |
| GET | `/api/info` | API metadata and inventory |
| GET | `/api/platform` | Detailed platform summary JSON |
| GET | `/api/integrations` | Integration catalog JSON |

## Getting Started

### 1. Run the application
The application is configured to run on port 5000 by default.
```bash
uvicorn main:app --host 0.0.0.0 --port 5000
```

### 2. Run Smoke Tests
Verify all endpoints are functioning correctly.
```bash
bash smoke-test.sh
```

### 3. Seed Demo Data
Populate the dashboard with 20 varied test events.
```bash
bash seed.sh
```

### 4. Verify Health
```bash
curl http://127.0.0.1:5000/health
```

## Public URLs
- **Dev/Preview**: `https://<REPL_SLUG>.<REPL_OWNER>.replit.dev/dashboard`
- **Prod/App**: `https://<REPL_SLUG>.<REPL_OWNER>.replit.app/dashboard`

## Production Notes
- **Security**: Configure the `WEBHOOK_SECRET` environment variable for signed payload validation.
- **Persistence**: For production use, replace the in-memory `events_store` with a persistent database.
- **Credentials**: Store outbound service tokens securely before enabling live integration actions.
