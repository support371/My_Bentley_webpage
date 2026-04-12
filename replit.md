# iTwin Ops Center

## Overview
A production-capable Bentley iTwin webhook Operations Center built with FastAPI + Python, PostgreSQL (Replit-managed), Jinja2 templates, session-based JWT auth, and a mobile-first multi-page dashboard. No React/Vue — vanilla HTML/CSS/JS only.

## Current State
- All 9 pages and API endpoints fully functional (200 on all routes)
- 28-integration hub with per-category search/filter and connect/disconnect UI
- PostgreSQL via asyncpg with SSL disabled (Replit environment)
- Admin user auto-seeded on first startup
- Auto-refresh dashboard (15s), dark mode, mobile-first layout
- GZip compression middleware + request ID middleware (X-Request-ID, X-Response-Time headers)
- Webhook rate limiting (60 req/min per IP, configurable via RATE_LIMIT_PER_MINUTE)
- Custom HTML 404/403/500/429 error pages (JSON for /api routes)
- Toast notification system, keyboard shortcuts (Alt+D/E/I/G/A), / to focus search
- 5-KPI overview (events, iTwins, iModels, event types, integrations)
- Dashboard analytics charts: event volume trend (Chart.js area chart) + category doughnut
- iTwins explorer with event counts, iModel counts, time-ago, status dot
- iModel Explorer page (/imodels-view): search, sort, state filter, event counts, iTwin links
- Events table: pagination, multi-filter (category, severity, search, iTwin ID), CSV export
- Events detail modal with Formatted / Raw JSON / Metadata tabs + Copy JSON
- Admin panel: system stats bar, alert rule creation+delete+toggle, data management (seed/purge/export)
- Alert delivery: Slack (rich blocks), Discord (embeds), Email (SMTP), PagerDuty, generic webhook
- Alert test delivery button (⚡ Test delivery) before saving a rule
- User management: invite/edit/delete users, role management, password reset, enable/disable
- Demo event seeder (POST /api/events/demo), old event purge (DELETE /api/events/old)

## Project Structure
```
/
├── app/
│   ├── main.py                    # FastAPI app, rate limiting, error handlers, all routers
│   ├── core/
│   │   ├── config.py              # Env-based settings, email config, ASYNC_DATABASE_URL
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
│   │   └── integrations.py        # Integration (28 services)
│   ├── api/routes/
│   │   ├── auth.py                # Login/logout, JWT session + full User Management API
│   │   ├── dashboard.py           # Dashboard feed (5s cache), /api/stats, /api/charts/trend
│   │   ├── events.py              # Events listing + detail + CSV export + demo seed + purge
│   │   ├── itwins.py              # /api/itwins — iTwins list with event/iModel counts
│   │   ├── imodels.py             # /imodels-view + /api/imodels (new)
│   │   ├── webhooks.py            # POST /webhook ingestion pipeline
│   │   ├── admin.py               # Admin UI, alert rules CRUD+toggle, Bentley config, test delivery
│   │   └── integrations.py        # /integrations page + /api/integrations CRUD
│   ├── services/
│   │   ├── event_processor.py     # Webhook normalization + DB persistence
│   │   ├── bentley/client.py      # Bentley API adapter stubs
│   │   ├── bentley/diagnostics.py # Bentley readiness diagnostics
│   │   └── alerts/engine.py       # Alert evaluation + Slack/Discord/Email/PagerDuty/Webhook dispatch
│   ├── templates/
│   │   ├── base.html              # Mobile-first nav (incl. iModels link) + toast container
│   │   ├── dashboard.html         # 5-KPI + trend chart + category donut + event feed
│   │   ├── events.html            # Events table: pagination, filters, detail modal
│   │   ├── itwins.html            # iTwins grid: search, sort, status dots, event counts
│   │   ├── imodels.html           # iModels grid: search, sort, state filter (new)
│   │   ├── integrations.html      # 28-service integration hub
│   │   ├── admin.html             # Stats + User Mgmt + Alert Rules + Data Mgmt + Diagnostics
│   │   ├── admin_diagnostics.html # Full Bentley diagnostics page
│   │   ├── error.html             # Custom error page (404/403/500/429) (new)
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
- `GET /` — Redirect to /dashboard
- `GET /health` — Health check (DB status)
- `POST /webhook` — iTwin event ingestion (rate limited 60/min per IP)
- `GET /dashboard` — Live dashboard with charts (HTML)
- `GET /dashboard/feed` — Dashboard JSON data (5s cache)
- `GET /api/charts/trend` — Time-bucketed event counts for trend chart
- `GET /events-view` — Events table (HTML)
- `GET /events` — Events JSON API (pagination + filters)
- `GET /events/{id}` — Single event detail
- `GET /events/export` — CSV download
- `POST /api/events/demo` — Seed demo events
- `DELETE /api/events/old` — Purge old events
- `GET /itwins-view` — iTwins grid (HTML)
- `GET /api/itwins` — iTwins JSON API (with event/iModel counts)
- `GET /imodels-view` — iModels grid (HTML) — new
- `GET /api/imodels` — iModels JSON API (search, state filter) — new
- `GET /integrations` — Integration hub (HTML)
- `GET/POST /api/integrations` — Integration CRUD
- `POST /api/integrations/{slug}/test` — Test a connection
- `DELETE /api/integrations/{slug}` — Disconnect
- `GET /api/integrations/catalog` — Full service catalog
- `GET /admin` — Admin panel (HTML)
- `GET /admin/diagnostics` — Bentley diagnostics page
- `GET /api/stats` — Platform stats
- `GET /api/users` — List users — new
- `POST /api/users` — Create user — new
- `PUT /api/users/{id}` — Update user role/name/active — new
- `POST /api/users/{id}/reset-password` — Reset password — new
- `DELETE /api/users/{id}` — Delete user — new
- `GET /admin/alert-rules` — List alert rules
- `POST /admin/alert-rules` — Create alert rule
- `DELETE /admin/alert-rules/{id}` — Delete rule — new
- `POST /admin/alert-rules/{id}/toggle` — Pause/resume rule — new
- `POST /admin/alerts/test-delivery` — Test delivery config — new
- `GET /login` `POST /login` — Auth
- `GET /api/docs` — Interactive API documentation

## Integration Catalog (28 services)
**Source Control**: GitHub, GitLab, GitBucket, Bitbucket
**Cloud & Deploy**: Vercel, Railway, Cloudflare, Azure, Azure DevOps
**AI & LLM**: ChatGPT/OpenAI, Gemini, GitHub Copilot, DeepSeek AI, Cursor, Devin, v0 by Vercel
**Dev Tools**: VS Code, Replit, Lovable
**CI/CD**: CircleCI
**Community**: Dev.to
**Notifications**: Slack, Discord, PagerDuty
**Project Mgmt**: Jira, Linear
**Observability**: Datadog, Sentry

## Alert Delivery
Supported destination types in alert rules:
- `slack` — Slack Incoming Webhook (rich blocks with severity colors)
- `discord` — Discord Webhook (embeds with color coding)
- `email` — SMTP email (HTML template, configurable per-rule or via env secrets)
- `pagerduty` — PagerDuty Events API v2 (routing_key per rule)
- `webhook` — Generic HTTP POST with JSON payload
Use POST /admin/alerts/test-delivery with `{"destination": {...}}` to test before saving.

## Email Config (env secrets)
- `ALERT_EMAIL_SMTP` — SMTP hostname (e.g. smtp.gmail.com)
- `ALERT_EMAIL_PORT` — Port (default: 587)
- `ALERT_EMAIL_USER` — SMTP username
- `ALERT_EMAIL_PASS` — SMTP password (app password for Gmail)
- `ALERT_EMAIL_FROM` — From address

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
- User roles: admin, operator, viewer

## URLs
- Dev: https://55bc6d55-3c35-4124-9fe6-7ce4d37d4700-00-2zwv0ssihz8qe.picard.replit.dev/dashboard
- GitHub: https://github.com/support371/My_Bentley_webpage

## User Preferences
- No React/Vue — vanilla HTML/CSS/JS only
- Keep implementation simple and lightweight
- In-memory-style UX (PostgreSQL for persistence)
- Mobile-first, dark mode support
