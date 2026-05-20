# Bentley iTwin Operations Center - Complete Platform

A modern, full-stack application for Bentley iTwin webhook operations, event intelligence, and enterprise integration orchestration with a modern React-based frontend.

## Stack

### Backend
- **Runtime**: Python 3.11+ / FastAPI + Uvicorn
- **Database**: SQLite (dev) / PostgreSQL (production) via SQLModel + asyncpg/aiosqlite
- **Auth**: JWT cookie sessions with role-based access (admin / viewer)
- **WebSockets**: Real-time event streaming and notifications
- **Deployment**: Docker / Azure Kubernetes Service (AKS) + Helm / Vercel (Node proxy)

### Frontend (NEW)
- **Framework**: Next.js 16 with React 19 and TypeScript
- **Styling**: Tailwind CSS v4 with custom dark theme
- **State Management**: Zustand for auth and UI state
- **API Client**: Axios with interceptors
- **Real-time**: WebSocket integration for live updates
- **Charts**: Recharts for data visualization
- **Components**: Custom shadcn/ui components

## Platform Surfaces

### Frontend (React/Next.js)
| Surface | URL | Description |
|---------|-----|-------------|
| Login | `/auth/login` | Modern authentication with OAuth support |
| Dashboard | `/dashboard` | Real-time KPIs, charts, and event feed |
| Projects | `/projects` | Project management with detail views |
| iModels | `/imodels` | iModel catalog with sync status |
| iTwins | `/itwins` | Digital twin management |
| Events | `/events` | Real-time event log with filtering |
| Settings | `/settings` | User preferences and account |
| Admin | `/admin` | User management, audit logs, platform settings |

### Backend (FastAPI) - Legacy URLs Still Supported
| Surface | URL | Description |
|---------|-----|-------------|
| Dashboard Feed | `/dashboard/feed` | Legacy API endpoint for data |
| Events API | `/api/events` | Event endpoints (also consumed by React) |
| Mobile Ops | `/mobile` | Mobile-optimized view (legacy) |
| Control Plane | `/control-plane` | Enterprise execution layer |

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

### Frontend (Next.js)

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Start development server
npm run dev
```

Frontend runs on `http://localhost:3000`

### Backend (FastAPI)

```bash
# Install dependencies
pip install -r requirements.txt

# Start (dev)
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

# Or via run.py
python run.py
```

Backend API runs on `http://localhost:5000`

**Default credentials** (dev seed): `admin@example.com` / `admin123`

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

### Frontend (Next.js + React)

```
/app                          # Next.js App Router
├── (dashboard)/              # Protected dashboard routes
│   ├── dashboard/            # Main dashboard with KPIs
│   ├── projects/             # Project management
│   │   └── [id]/             # Project detail page
│   ├── imodels/              # iModel catalog
│   ├── itwins/               # Digital twin management
│   ├── events/               # Real-time event log
│   ├── admin/                # Admin panel
│   ├── settings/             # User settings
│   └── layout.tsx            # Dashboard wrapper layout
├── auth/login/               # Public login page
├── page.tsx                  # Root redirect
└── layout.tsx                # Root layout with notifications

/components                   # Reusable React components
├── ui/                       # shadcn/ui components
│   ├── button.tsx
│   ├── input.tsx
│   ├── card.tsx
│   └── dialog.tsx
├── sidebar.tsx               # Navigation sidebar
├── header.tsx                # Top navigation
├── project-card.tsx          # Project card
├── stat-card.tsx             # Stats display
└── notification-center.tsx   # Toast notifications

/lib                          # Utilities
├── api.ts                    # Axios API client
├── store.ts                  # Zustand state stores
├── websocket.ts              # WebSocket client
├── notifications.ts          # Notification system
└── utils.ts                  # Helpers
```

### Backend (FastAPI)

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
│   ├── admin.py               # Admin endpoints
│   ├── auth.py                # Authentication
│   ├── dashboard.py           # Dashboard data
│   ├── events.py              # Event management
│   ├── imodels.py             # iModel endpoints
│   ├── itwins.py              # iTwin endpoints
│   └── webhooks.py            # Webhook intake
├── services/
│   ├── alerts/engine.py       # Alert dispatch
│   ├── bentley/               # Bentley API integration
│   └── event_processor.py     # Event aggregation
└── templates/                 # Legacy Jinja2 templates
```
