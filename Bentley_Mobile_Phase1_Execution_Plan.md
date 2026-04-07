# Bentley Mobile Ops — Phase 1 Execution Plan

## Objective

Add the 12-screen mobile monitoring experience into the **active Bentley platform architecture** as a new module, reusing the existing FastAPI routers, SQLModel-backed data, Jinja templates, and shared static assets.

This plan is intentionally implementation-first. It is designed for a senior developer or coding agent to start shipping immediately with minimal ambiguity.

---

## 1) Build against the active app, not the legacy root file

### Active runtime surface
- `app/main.py`
- routers in `app/api/routes/`
- templates in `app/templates/`
- shared CSS/JS in `app/static/`

### Do not extend first
- root-level `main.py`

Reason:
- `.replit` runs `uvicorn app.main:app`
- the active app already includes dashboard, admin, integrations, events, and iTwin routers
- the active app already uses database-backed models and Jinja templates

---

## 2) Recommended integration strategy

Create the mobile experience as a **new bounded module** inside the existing product:

### New route layer
- `app/api/routes/mobile.py`

### New template layer
- `app/templates/mobile/`
  - `index.html`
  - `alarms.html`
  - `monitors.html`
  - `reports.html`
  - `admin.html`
  - `more.html`
  - `integrations.html`

### New static assets
- `app/static/css/mobile.css`
- `app/static/js/mobile.js`

### Optional shared partials
- `app/templates/mobile/_bottom_nav.html`
- `app/templates/mobile/_card_list.html`
- `app/templates/mobile/_status_chip.html`

This avoids contaminating the desktop dashboard while still letting both surfaces use the same backend and data model.

---

## 3) Initial route map

## Pages
- `GET /mobile` -> mobile landing / default tab redirect
- `GET /mobile/alarms`
- `GET /mobile/monitors`
- `GET /mobile/reports`
- `GET /mobile/admin`
- `GET /mobile/more`
- `GET /mobile/integrations`

## JSON feeds
- `GET /api/mobile/summary`
- `GET /api/mobile/alarms`
- `GET /api/mobile/monitors`
- `GET /api/mobile/reports`
- `GET /api/mobile/admin-summary`
- `GET /api/mobile/more-summary`
- `GET /api/mobile/integrations`

## Actions
- `POST /api/mobile/monitors/discover`
- `POST /api/mobile/test-alert`
- `POST /api/mobile/tab-customization`
- `POST /api/mobile/timezone`
- `POST /api/mobile/account/add`

Phase 1 can stub the lower-risk actions while fully wiring the read endpoints.

---

## 4) Source-of-truth reuse map

## Alarms
Reuse:
- event stream from `app/api/routes/events.py`
- dashboard feed and health from `app/api/routes/dashboard.py`
- alert rules and test delivery from `app/api/routes/admin.py`

### Mapping
- screenshot “Alarms” -> event-driven alarms list
- source tables: `Event`, `WebhookDelivery`, optional `Alert`

---

## Monitors
Reuse:
- iTwin and iModel data from `app/api/routes/itwins.py`
- Bentley fetch/setup concepts already exposed in admin routes

### Mapping
- screenshot monitor onboarding -> domain/URL discovery form
- in Bentley context, this should be framed as:
  - external endpoint monitor
  - webhook target monitor
  - project/digital twin monitor bootstrap

### Phase 1 practical compromise
Create a discovery form that:
- accepts URL / resource label / environment
- stores request as a “monitor seed” payload or mock object
- returns a preview card
- does not promise full auto-discovery yet

---

## Reports
Reuse:
- existing KPI aggregation from `dashboard_feed`
- CSV export endpoint from `/events/export`
- integration count and uptime metrics from `/api/stats`

### Mapping
- scheduled reports
- customized reports
- SLA-style summaries
- exported operational views

---

## Admin
Reuse heavily:
- `/admin/test-connection`
- `/admin/fetch-itwins`
- `/admin/webhooks`
- `/admin/webhooks/create`
- `/admin/alert-rules`
- `/api/users`
- `/api/stats`
- integration settings from `/api/integrations`

### Mobile admin sections to represent
- Inventory
- User management
- Configuration profiles
- Server monitor
- Poller
- Operations
- Report settings
- Share
- Developer
- IT automation

### Phase 1 note
Not every card needs deep functionality on day one. The first release can surface:
- live counts
- quick links
- status cards
- route-through actions into already working admin endpoints

---

## More
Reuse:
- service health from `/health`
- integrations count from `/api/integrations`
- alert test from `/admin/alerts/test-delivery`

### Mobile “More” module should hold
- account shortcuts
- timezone
- alert notifications
- custom dashboards
- scheduled maintenance
- newsletter
- service status
- tab customization
- trigger test alert
- app settings

---

## Integrations
Reuse directly:
- `app/api/routes/integrations.py`
- `app/templates/integrations.html` behavior model

### Extension
Add category grouping that matches the screenshot reference:
- Collaboration
- Incident Response / On-call
- ITSM / Service Desk
- Workflow / Eventing
- Analytics
- AI
- Application Monitoring

### Important product decision
Do not fork the integration data model.
Instead:
- keep the existing `Integration` table and CRUD/test flows
- add a `mobile_category` mapping in code for grouped presentation
- optionally expand the catalog later with more Site24x7-like vendor coverage

---

## 5) Suggested file-by-file implementation plan

## A. `app/api/routes/mobile.py`
Responsibilities:
- page rendering routes
- mobile summary APIs
- thin adapter layer over existing services and route logic

Recommended structure:
- `build_mobile_summary(session)`
- `build_mobile_alarms(session, limit=20)`
- `build_mobile_monitors(session)`
- `build_mobile_reports(session)`
- `build_mobile_admin_summary(session)`
- `build_mobile_more_summary(session)`
- `build_mobile_integrations(session)`

Guideline:
Do not duplicate SQL if a current service or router output can be reused safely.

---

## B. `app/main.py`
Changes:
- import `mobile` router
- `app.include_router(mobile.router)`

---

## C. `app/templates/base.html`
Changes:
- add a top-nav entry for Mobile Ops, or
- add a secondary launch button under dashboard/admin

Recommended label:
- `Mobile Ops`

Route target:
- `/mobile`

---

## D. `app/static/css/mobile.css`
Responsibilities:
- dark mobile-first theme
- large radius cards
- bottom tab bar
- icon row / list row system
- status chip styling
- integration card styling
- safe responsive behavior on desktop widths too

Design direction:
- keep Bentley brand coherence
- do not hard-clone the screenshot brand
- preserve dark-glass mobile presentation

---

## E. `app/static/js/mobile.js`
Responsibilities:
- tab navigation state
- fetch `/api/mobile/*` feeds
- trigger test alert
- monitor discovery submission
- client-side filters for integrations
- optional localStorage for tab customization

---

## 6) Phase 1 sprint sequence

## Sprint 0 — Foundation
Goal:
- mobile router compiles
- blank mobile templates render
- nav entry added
- CSS/JS linked

Definition of done:
- `/mobile` and 6 subroutes return HTTP 200
- smoke tests updated

---

## Sprint 1 — Read-only operating shell
Goal:
- mobile summary API
- alarms feed
- monitors list
- integrations list
- admin summary cards
- more/service status cards

Definition of done:
- all tabs load real data
- no dead-end blank screens
- mobile shell is visually coherent

---

## Sprint 2 — First actions
Goal:
- test alert action
- basic monitor discovery submission
- timezone update stub
- tab customization persistence
- connect/test integration handoff from mobile integrations page

Definition of done:
- at least 3 mobile actions work end-to-end

---

## Sprint 3 — Operational hardening
Goal:
- auth checks
- empty states
- error states
- loading states
- seed coverage
- QA pass on 390–430px widths

Definition of done:
- stable demoable mobile module

---

## 7) Acceptance criteria by tab

## Alarms
- shows recent event-driven alarms
- displays severity/status/time
- supports empty state
- links through to fuller event view where appropriate

## Monitors
- shows onboarding form
- submit returns a visible result
- list view shows seeded or existing monitor-like entities
- does not break when no data exists

## Reports
- shows operational summary metrics
- exposes export/report actions
- scheduled/custom/SLA cards are visible even if some are phase-2 stubs

## Admin
- shows grouped cards mirroring reference taxonomy
- key actions route to live platform capabilities
- user/admin stats render from real APIs

## More
- shows service status
- test alert action works
- tab customization persists in local storage or user preference stub
- app settings entry exists

## Integrations
- supports filtering
- renders grouped vendor cards
- uses existing connect/test/disconnect flows
- can open detail/config modal

---

## 8) Data contract suggestions

## `/api/mobile/summary`
```json
{
  "health": "healthy",
  "serviceStatus": "operational",
  "kpis": {
    "totalEvents": 120,
    "openAlerts": 7,
    "integrationsConnected": 5,
    "uptime": "12h 14m"
  },
  "tabs": [
    "alarms",
    "monitors",
    "reports",
    "admin",
    "more"
  ]
}
```

## `/api/mobile/alarms`
```json
{
  "items": [
    {
      "id": "evt_123",
      "title": "Synchronization run failed",
      "severity": "error",
      "category": "Synchronization",
      "project": "Design Hub Alpha",
      "receivedAt": "2026-03-10T12:00:00Z"
    }
  ]
}
```

## `/api/mobile/integrations`
```json
{
  "groups": [
    {
      "name": "Collaboration",
      "items": [
        {
          "slug": "slack",
          "name": "Slack",
          "status": "connected",
          "description": "Post alerts and event summaries to channels."
        }
      ]
    }
  ]
}
```

---

## 9) Technical guardrails

- do not duplicate desktop admin logic inside the mobile templates
- do not create a second integrations persistence layer
- do not bypass existing auth dependencies
- do not wire new features into root `main.py`
- do not promise full external monitor auto-discovery until backend support exists
- prefer progressive enablement over screenshot-perfect dead UI

---

## 10) Priority backlog for the developer or agent

## P0
1. Create `mobile.py` router
2. Add `/mobile` routes
3. Register router in `app/main.py`
4. Create template shell and bottom nav
5. Add `mobile.css` and `mobile.js`
6. Add smoke-test coverage for mobile routes

## P1
7. Build `/api/mobile/summary`
8. Build `/api/mobile/alarms`
9. Build `/api/mobile/integrations`
10. Build `/api/mobile/admin-summary`

## P2
11. Build monitor onboarding stub
12. Build `/api/mobile/test-alert`
13. Add tab customization persistence
14. Add grouped admin cards and deep links
15. Add report summary/export cards

## P3
16. Add vendor-category enrichment for integration catalog
17. Add refined loading/empty/error states
18. Add mobile-specific seed/demo cases
19. Add QA polish for narrow screens
20. Add role-aware visibility rules

---

## 11) Suggested coding-agent prompt

Use this prompt with a senior coding agent:

> Extend the active Bentley platform in `app/`, not the root legacy file. Create a new FastAPI mobile module with routes under `app/api/routes/mobile.py`, templates under `app/templates/mobile/`, and assets under `app/static/css/mobile.css` and `app/static/js/mobile.js`. Reuse existing platform capabilities from dashboard, events, integrations, admin, and iTwin APIs. Add `/mobile`, `/mobile/alarms`, `/mobile/monitors`, `/mobile/reports`, `/mobile/admin`, `/mobile/more`, `/mobile/integrations`, plus `/api/mobile/summary`, `/api/mobile/alarms`, `/api/mobile/integrations`, and `/api/mobile/admin-summary`. Keep the UI mobile-first, dark themed, and operationally aligned with the handoff spec. Do not introduce a duplicate data model if existing Event, Integration, User, AlertRule, ITwin, or IModel structures already support the flow. Update smoke tests and ensure all new routes return HTTP 200.

---

## 12) Final recommendation

The fastest path is not “build everything.”  
The fastest path is:

1. get the mobile shell rendering
2. connect it to real Bentley platform data
3. wire only the highest-value actions
4. iterate section depth after the shell is stable

That gives Bentley an integrated mobile operations surface without destabilizing the current platform.
