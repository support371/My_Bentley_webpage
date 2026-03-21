# Bentley iTwin Automation Platform

A more complete FastAPI platform for Bentley iTwin webhook operations, live monitoring, and integration orchestration.

## What changed from the MVP

The original build was a live webhook dashboard. The current platform adds:

- Multi-section operations experience with overview, live operations, integrations, workflows, and rollout checklist
- Build-stage visibility so teams can see what is done, in progress, and next
- A dedicated integrations page with **Azure DevOps**, **Monday.com**, and **Atlassian Rovo AI** alongside other platform handoffs
- Workflow blueprints that show how Bentley events become delivery actions
- Expanded dashboard feed data for KPIs, priorities, integration readiness, and roadmap state

## Stack

- **Runtime**: Python 3.11
- **Framework**: FastAPI + Uvicorn
- **Storage**: In-memory event store
- **Frontend**: Vanilla HTML/CSS/JS served by FastAPI

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service entry summary |
| GET | `/api/info` | API metadata and endpoint inventory |
| GET | `/health` | Health check with event and integration counts |
| POST | `/webhook` | Receive Bentley iTwin webhook events |
| GET | `/events` | List recent events, newest first |
| GET | `/dashboard` | Full platform UI |
| GET | `/integrations` | Integration page-focused platform UI |
| GET | `/dashboard/feed` | Platform feed for dashboard rendering |
| GET | `/api/platform` | Platform summary JSON |
| GET | `/api/integrations` | Integration catalog JSON |

## Core platform sections

- **Overview**: KPI cards, AI summary, build stage, and production attention items
- **Live operations**: Event stream, source labels, priorities, and integration recommendations
- **Integrations**: Readiness cards for Bentley iTwin, Azure DevOps, Monday.com, Atlassian Rovo AI, Slack, and Power BI
- **Workflows**: Trigger-to-action blueprints for delivery automation
- **Rollout checklist**: Remaining production hardening tasks

## Quick commands

### Run the app
```bash
uvicorn main:app --host 0.0.0.0 --port 5000
```

### Run smoke tests
```bash
bash smoke-test.sh
```

### Seed demo data
```bash
bash seed.sh
```

### Verify platform health
```bash
curl http://127.0.0.1:5000/health
```

## Notes

- Events are stored in memory and reset on restart
- The integration catalog models readiness and workflow design, but outbound credentials still need to be wired for production writes
- Signature validation is optional for local testing and becomes active when a `Signature` header is supplied
