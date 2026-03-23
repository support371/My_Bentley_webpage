# iTwin Ops Center

## Overview
A production-capable Bentley iTwin webhook Operations Center built with FastAPI + Python, PostgreSQL (Replit-managed), Jinja2 templates, session-based JWT auth, and a mobile-first multi-page dashboard. No React/Vue — vanilla HTML/CSS/JS only.

## Current State
- All 7 pages and API endpoints fully functional (200 on all routes)
- 27-integration hub with per-category search/filter and connect/disconnect UI
- PostgreSQL via asyncpg with SSL disabled (Replit environment)
- Admin user auto-seeded on first startup
- Auto-refresh dashboard (15s), dark mode, mobile-first layout
- GZip compression middleware + request ID middleware (X-Request-ID, X-Response-Time headers)
- Toast notification system, keyboard shortcuts (Alt+D/E/I/G/A), / to focus search
- 5-KPI overview (events, iTwins, iModels, event types, integrations)
- iTwins explorer with event counts, iModel counts, time-ago, status dot
- Events table: pagination, multi-filter (category, severity, search, iTwin ID), CSV export
- Events detail modal with Formatted / Raw JSON / Metadata tabs + Copy JSON
- Admin panel: system stats bar, alert rule creation, data management (seed/purge/export)
- Demo event seeder (POST /api/events/demo), old event purge (DELETE /api/events/old)

## Project Structure
```
/
├── app/
│   ├── main.py                    # FastAPI app, lifespan, GZip, request ID middleware, all routers
│   ├── core/
│   │   ├── config.py              # Env-based settings, ASYNC_DATABASE_URL
│   │   ├── security.py            # JWT, password hashing, session cookies
│   │   └── logging_config.py      # Structured logging
│   ├── db/
│   │   ├── database.py            # Async engine (asyncpg), get_session, _app_start_time
│   │   └── seed.py                # Initial admin user seed
│   ├── models/
│   │   ├── events.py              # Event, WebhookDelivery, ITwin, IModel
│   │   ├── auth.py                # User, Tenant
│   │   ├── resources.py           # AlertRule, Alert
│   │   ├── tenants.py             # Tenant extras
│   │   └── integrations.py        # Integration (27+ services)
│   ├── api/routes/
│   │   ├── auth.py                # Login/logout, JWT session
│   │   ├── dashboard.py           # Dashboard feed (5s cache), /api/stats
│   │   ├── events.py              # Events listing + detail + CSV export + demo seed + purge
│   │   ├── itwins.py              # /api/itwins — iTwins list with event/iModel counts
│   │   ├── webhooks.py            # POST /webhook ingestion pipeline
│   │   ├── admin.py               # Admin UI, alert rules, Bentley config
│   │   └── integrations.py        # /integrations page + /api/integrations CRUD
│   ├── services/
│   │   ├── event_processor.py     # Webhook normalization + DB persistence
│   │   ├── bentley/client.py      # Bentley API adapter stubs
│   │   └── alerts/engine.py       # Alert rule evaluation
│   ├── templates/
│   │   ├── base.html              # Mobile-first nav + toast container
│   │   ├── dashboard.html         # 5-KPI grid + event feed + test event modal + time filters
│   │   ├── events.html            # Events table: pagination, filters, detail modal
│   │   ├── itwins.html            # iTwins grid: search, sort, status dots, event counts
│   │   ├── integrations.html      # 27-service integration hub
│   │   ├── admin.html             # System stats + Bentley config + alert rules + data mgmt
│   │   └── login.html             # Auth page
│   └── static/
│       ├── css/app.css            # Full mobile-first CSS, dark mode, skeleton loaders, scrollbar
│       └── js/app.js              # theme, _showToast, keyboard shortcuts, _copyText, _timeAgo, _numFmt
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
- `GET /dashboard/feed` — Dashboard JSON data (5s cache)
- `GET /events-view` — Events table (HTML)
- `GET /events` — Events JSON API (pagination + filters)
- `GET /events/{id}` — Single event detail
- `GET /events/export` — CSV download
- `POST /api/events/demo` — Seed demo events
- `DELETE /api/events/old` — Purge old events
- `GET /itwins-view` — iTwins grid (HTML)
- `GET /api/itwins` — iTwins JSON API (with event/iModel counts)
- `GET /integrations` — Integration hub (HTML)
- `GET/POST /api/integrations` — Integration CRUD
- `POST /api/integrations/{slug}/test` — Test a connection
- `DELETE /api/integrations/{slug}` — Disconnect
- `GET /api/integrations/catalog` — Full service catalog
- `GET /admin` — Admin panel (HTML)
- `GET /api/stats` — Platform stats (events, itwins, imodels, uptime, integrations)
- `GET /login` `POST /login` — Auth
- `GET /api/docs` — Interactive API documentation

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
- **process_webhook_event**: Takes `(raw_body: bytes, headers: dict, session, tenant_id?)` — returns `Event` object
- **Demo events**: Call `process_webhook_event` directly — it commits internally, don't double-commit

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
