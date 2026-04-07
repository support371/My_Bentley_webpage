# Bentley iTwin Operations Center

A modular FastAPI platform for Bentley iTwin webhook operations, event intelligence, and enterprise integration orchestration.

## Stack

- **Runtime**: Python 3.11+ / FastAPI + Uvicorn
- **Database**: SQLite (dev) / PostgreSQL (production) via SQLModel + asyncpg/aiosqlite
- **Auth**: JWT cookie sessions with role-based access (admin / viewer)
- **Frontend**: Jinja2 templates + Vanilla JS (no build step required)
- **Deployment**: Docker / Azure Kubernetes Service (AKS) + Helm / Vercel (Node proxy)

## Platform Surfaces

| Surface | URL | Description |
|---------|-----|-------------|
| Dashboard | `/dashboard` | Event KPIs, trend chart, recent events feed |
| Events | `/events-view` | Full event table with filters |
| iTwins | `/itwins-view` | Connected iTwin registry |
| iModels | `/imodels-view` | iModel explorer with state filters |
| Integrations | `/integrations` | 28-service integration catalog |
| Mobile Ops | `/mobile` | Mobile-optimized ops view (alarms, monitors, reports) |
| Admin | `/admin` | Alert rules, user management, Bentley diagnostics |
| Launch Readiness | `/admin/launch-readiness` | Platform production checklist |
| Control Plane | `/control-plane` | Enterprise execution layer (Website Studio, Infra) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhook` | Receive Bentley iTwin webhook events |
| GET | `/dashboard/feed` | Dashboard KPI + recent events JSON |
| GET | `/api/charts/trend` | Time-bucketed event trend data |
| GET | `/api/stats` | System stats (events, uptime, deliveries) |
| GET | `/api/events` | Paginated event list with filters |
| GET | `/api/itwins` | iTwin list |
| GET | `/api/imodels` | iModel list with search/filter |
| GET | `/api/integrations` | Integration catalog JSON |
| GET | `/api/mobile/summary` | Mobile ops summary |
| GET | `/api/mobile/alarms` | Active alarms |
| GET | `/api/mobile/monitors` | Monitor status |
| POST | `/api/mobile/test-alert` | Fire a test mobile alert |
| GET | `/admin/alert-rules` | List alert rules |
| POST | `/admin/alert-rules` | Create alert rule |
| POST | `/admin/alerts/test-delivery` | Test alert delivery to a channel |
| GET | `/api/users` | List users (admin only) |
| POST | `/api/users` | Create user (admin only) |
| GET | `/api/admin/diagnostics/summary` | Bentley integration readiness |
| GET | `/health` | Service health check |

## Alert Channels

Rules-based alert engine supports multi-channel delivery:
- **Slack** — incoming webhook
- **Discord** — embed webhook
- **Email** — SMTP (with STARTTLS)
- **PagerDuty** — Events API v2
- **Generic Webhook** — JSON POST to any URL

## Required Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@host/db   # or sqlite+aiosqlite:///./itwin_ops.db

# Security
SECRET_KEY=<min-32-char-random-string>
COOKIE_SECURE=true                            # set true in production
WEBHOOK_SECRET=<bentley-webhook-secret>
SKIP_SIGNATURE_VERIFY=false                   # set false in production

# Bentley API
BENTLEY_CLIENT_ID=<your-client-id>
BENTLEY_CLIENT_SECRET=<your-client-secret>

# Alert email (optional)
ALERT_EMAIL_SMTP=smtp.example.com
ALERT_EMAIL_PORT=587
ALERT_EMAIL_USER=alerts@example.com
ALERT_EMAIL_PASS=<password>
ALERT_EMAIL_FROM=alerts@example.com

# App
ENVIRONMENT=production
PUBLIC_BASE_URL=https://your-domain.com
```

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start (dev)
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

# Or via run.py
python run.py
```

Default admin credentials (dev seed): `admin@example.com` / `admin123`

## Docker

```bash
docker build -t bentley-ops .
docker run -p 5000:5000 --env-file .env bentley-ops
```

## Tests

```bash
pytest tests/
```

Includes unit tests for the Bentley diagnostics service (`tests/test_diagnostics.py`).

## Smoke Test

```bash
bash smoke-test.sh
```

## Project Structure

```
app/
├── main.py                    # FastAPI app, middleware, error handlers
├── core/
│   ├── config.py              # Settings (pydantic-settings)
│   └── security.py            # JWT, password hashing, auth guards
├── db/
│   ├── database.py            # Async engine, session factory
│   └── seed.py                # Dev seed data
├── models/                    # SQLModel table definitions
├── api/routes/                # FastAPI route modules
│   ├── admin.py               # Admin, alert rules, user management
│   ├── auth.py                # Login/logout
│   ├── dashboard.py           # Dashboard + chart endpoints
│   ├── events.py              # Event ingestion and listing
│   ├── imodels.py             # iModel explorer
│   ├── integrations.py        # Integration catalog
│   ├── itwins.py              # iTwin registry
│   ├── launch_readiness.py    # Production readiness checks
│   ├── mobile.py              # Mobile Ops pages + API
│   ├── control_plane.py       # Enterprise control plane routes
│   └── webhooks.py            # Webhook intake
├── services/
│   ├── alerts/engine.py       # Multi-channel alert dispatch
│   ├── bentley/               # Bentley API client + diagnostics
│   └── event_processor.py     # Dashboard stats aggregation
└── templates/                 # Jinja2 HTML templates
```
