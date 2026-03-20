# iTwin Ops Center

## Overview
A production-capable Bentley iTwin webhook Operations Center built with FastAPI + Python, PostgreSQL (Replit-managed), Jinja2 templates, session-based JWT auth, and a mobile-first multi-page dashboard. No React/Vue — vanilla HTML/CSS/JS only.

## Current State
- All endpoints functional, DB healthy, dashboard live
- 27-integration hub with per-category search/filter and connect/disconnect UI
- PostgreSQL via asyncpg with SSL disabled (Replit environment)
- Admin user auto-seeded on first startup
- Auto-refresh dashboard (15s), dark mode, mobile-first layout

## Project Structure
```
/
├── app/
│   ├── main.py                    # FastAPI app, lifespan, middleware, routes
│   ├── core/
│   │   ├── config.py              # Env-based settings, ASYNC_DATABASE_URL
│   │   ├── security.py            # JWT, password hashing, session cookies
│   │   └── logging_config.py      # Structured logging
│   ├── db/
│   │   ├── database.py            # Async engine (asyncpg), get_session
│   │   └── seed.py                # Initial admin user seed
│   ├── models/
│   │   ├── events.py              # Event, WebhookDelivery, ITwin, IModel
│   │   ├── auth.py                # User, Tenant
│   │   ├── resources.py           # AlertRule, Alert
│   │   ├── tenants.py             # Tenant extras
│   │   └── integrations.py        # Integration (27+ services)
│   ├── api/routes/
│   │   ├── auth.py                # Login/logout, JWT session
│   │   ├── dashboard.py           # Dashboard feed, events-view, itwins-view
│   │   ├── events.py              # Events listing + detail API
│   │   ├── webhooks.py            # POST /webhook ingestion pipeline
│   │   ├── admin.py               # Admin UI, alert rules, Bentley config
│   │   └── integrations.py        # /integrations page + /api/integrations CRUD
│   ├── services/
│   │   ├── event_processor.py     # Webhook normalization + DB persistence
│   │   ├── bentley/client.py      # Bentley API adapter stubs
│   │   └── alerts/engine.py       # Alert rule evaluation
│   ├── templates/
│   │   ├── base.html              # Mobile-first nav (Overview/Events/iTwins/Integrations/Admin)
│   │   ├── dashboard.html         # KPI cards + event stream
│   │   ├── events.html            # Events table with filters
│   │   ├── itwins.html            # iTwins grid
│   │   ├── integrations.html      # 27-service integration hub
│   │   ├── admin.html             # Admin panel
│   │   └── login.html             # Auth page
│   └── static/
│       ├── css/app.css            # Full mobile-first CSS, dark mode
│       └── js/                    # Dashboard auto-refresh, theme toggle
├── run.py                         # Uvicorn entrypoint
├── seed.py                        # Manual seed script
├── requirements.txt               # All Python deps
├── smoke-test.sh                  # Endpoint smoke tests
└── .env.example                   # All env vars documented
```

## Key Endpoints
- `GET /` — Service info JSON
- `GET /health` — Health check (DB status)
- `POST /webhook` — iTwin event ingestion
- `GET /dashboard` — Live dashboard (HTML)
- `GET /dashboard/feed` — Dashboard JSON data
- `GET /events-view` — Events table (HTML)
- `GET /itwins-view` — iTwins grid (HTML)
- `GET /integrations` — Integration hub (HTML)
- `GET/POST /api/integrations` — Integration CRUD
- `POST /api/integrations/{slug}/test` — Test a connection
- `DELETE /api/integrations/{slug}` — Disconnect
- `GET /api/integrations/catalog` — Full service catalog
- `GET /admin` — Admin panel (HTML)
- `GET /login` `POST /login` — Auth

## Integration Catalog (27 services)
**Source Control**: GitHub, GitLab, GitBucket, Bitbucket
**Cloud & Deploy**: Vercel, Railway, Cloudflare, Azure
**AI & LLM**: ChatGPT/OpenAI, Gemini, GitHub Copilot, DeepSeek AI, Cursor, Devin, v0 by Vercel
**Dev Tools**: VS Code, Replit, Lovable
**CI/CD**: CircleCI
**Community**: Dev.to
**Notifications**: Slack, Discord, PagerDuty
**Project Mgmt**: Jira, Linear
**Observability**: Datadog, Sentry

## Database
- Replit-provided PostgreSQL (`postgresql://...?sslmode=disable`)
- Config auto-converts to `postgresql+asyncpg://` and strips sslmode
- `ssl=False` passed as connect_args for asyncpg
- All tables created via SQLModel.metadata.create_all on startup

## Critical Patterns
- **Async sessions**: Always use `await session.execute(select(...)).scalars().all()` — NEVER `session.exec()` (asyncpg incompatibility)
- **Count queries**: `await session.scalar(select(func.count(...)))`
- **bcrypt**: Pinned at 4.0.1 for passlib compatibility

## Auth
- Default credentials: admin@example.com / admin123
- Override via env: INITIAL_ADMIN_EMAIL / INITIAL_ADMIN_PASSWORD
- JWT stored in HttpOnly session cookie

## URLs
- Dev: https://55bc6d55-3c35-4124-9fe6-7ce4d37d4700-00-2zwv0ssihz8qe.picard.replit.dev/dashboard
- GitHub: https://github.com/support371/My_Bentley_webpage

## User Preferences
- No React/Vue — vanilla HTML/CSS/JS only
- Keep implementation simple and lightweight
- In-memory-style UX (PostgreSQL for persistence)
- Mobile-first, dark mode support
