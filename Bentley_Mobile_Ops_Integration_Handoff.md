# Bentley Mobile Ops Integration Handoff

## Objective
Integrate the 12-screen mobile monitoring experience into the ongoing **Bentley iTwin Operations Center** as a **mobile-first operational module**, not as a separate clone product.

This handoff converts the screenshot reference set into a Bentley-specific implementation plan that fits the current repository architecture, navigation, data model direction, and UI delivery pattern.

---

## Executive decision
Build this as a **new mobile operations module inside the existing FastAPI + Jinja + vanilla JS platform**.

Do **not** implement it as:
- a separate standalone website
- a separate React app unless the platform is being re-platformed intentionally
- an extension of the legacy root `main.py`

Do implement it as:
- new routes under the existing modular `app/` structure
- new Jinja templates and static assets
- new API surfaces that reuse current Bentley event, alert, integration, and admin foundations
- a mobile-first UI shell that complements the existing desktop Overview / Integrations / Admin experience

---

## What this should become inside Bentley
The screenshot set maps cleanly to a new product slice:

**Bentley Mobile Ops / Field Operations Shell**

This should provide:
- alarm and event triage
- resource / asset monitoring setup
- reporting and SLA surfaces
- mobile admin controls
- personal settings / service utilities
- third-party operational integrations marketplace

The Bentley adaptation is not a generic IT monitor. It is a **Bentley digital twin operations surface**.

That means:
- “Monitors” becomes monitoring of **iTwins, iModels, jobs, forms, issues, access changes, and downstream operational automations**
- “Alarms” becomes Bentley operational incidents, alert rules, failed jobs, issue spikes, webhook anomalies, and downstream notification events
- “Reports” becomes operational reporting, SLA / event summaries, exports, scheduled reports, and leadership status packs
- “Admin” becomes configuration, Bentley connection, webhook management, user management, thresholding, notification profiles, polling/agent configuration, integrations, and automation templates
- “More” becomes user preferences, account context, service status, dashboard customization, test alerting, and app settings

---

## Repository-fit assessment

### Current target architecture
Use the modular application under `app/`, not the root legacy file.

**Canonical execution path**
- `app/main.py`
- mounted static assets under `app/static`
- routers under `app/api/routes`
- templates under `app/templates`

### Existing platform strengths to reuse
1. **Dashboard foundation**
   - KPI feed, health state, recent events, category/type breakdowns, insights, and supporting HTML page already exist.

2. **Integrations foundation**
   - A catalog-driven integrations page already exists with categories, connect/disconnect flows, custom integrations, and test-connection logic.

3. **Admin foundation**
   - Bentley connection, webhook setup, alert rules, data management, and user management already exist.

4. **Event layer**
   - There is already an event model, filtering/export, demo event seeding, and event-detail access.

5. **iTwin resource layer**
   - iTwin and iModel listing/detail endpoints already exist and can anchor the “Monitors” experience.

### Architectural warning
The repository contains both:
- a **legacy root-level** single-file app
- the **current modular** `app/` implementation

All new work should target the modular implementation only.

---

## Non-negotiable implementation rules
1. **Do not add this feature set into the root `main.py`.**
2. **Do not fork the UX into a separate product unless product leadership explicitly requests it.**
3. **Do not duplicate existing Integrations or Admin logic. Extend it.**
4. **Keep the desktop shell intact and add a mobile shell alongside it.**
5. **Use Bentley domain language where possible; use the screenshot language only where it maps cleanly.**
6. **Preserve current FastAPI + Jinja + vanilla JS architecture unless a broader front-end migration is already underway.**

---

## Recommended information architecture

### Existing top-level desktop shell
- Overview
- Events
- iTwins
- iModels
- Integrations
- Admin

### New top-level mobile module
Introduce a dedicated route group:
- `/mobile`
- `/mobile/alarms`
- `/mobile/monitors`
- `/mobile/reports`
- `/mobile/admin`
- `/mobile/more`
- `/mobile/integrations`

### Why this works
It allows:
- mobile-first navigation without breaking the desktop navbar
- reuse of the same session/auth model
- reuse of current APIs and DB models
- future packaging into a PWA without re-architecting the backend

---

## Proposed file structure

```text
app/
  api/
    routes/
      mobile.py                 # new mobile routes
      mobile_api.py             # optional, if API split is preferred
  services/
    mobile_dashboard.py         # aggregation logic for mobile views
    alerting.py                 # extend existing alert logic if needed
    report_scheduler.py         # scheduled reports if added now
  models/
    monitor_profiles.py         # new
    maintenance.py              # new
    reports.py                  # new
    preferences.py              # new
    pollers.py                  # new
    automation_templates.py     # new
  templates/
    mobile/
      base_mobile.html
      alarms.html
      monitors.html
      reports.html
      admin.html
      more.html
      integrations.html
      monitor_detail.html
      alarm_detail.html
      report_detail.html
  static/
    css/
      mobile.css
    js/
      mobile.js
      mobile_alarms.js
      mobile_monitors.js
      mobile_reports.js
      mobile_admin.js
      mobile_integrations.js
```

---

## Screen-to-platform mapping

## 1. Welcome / intro screen
### Screenshot intent
- splash / onboarding
- short positioning statement
- CTA entry into the app

### Bentley fit
Use this as an optional **mobile entry / launch screen** only if product wants a branded mobile landing experience.

### Recommendation
Do **not** prioritize this screen first.

Ship first:
- authenticated mobile shell
- alarms
- monitors
- reports
- admin
- more

Add the splash later only if needed for PWA/app-store-style presentation.

---

## 2. Alarms tab
### Bentley translation
This is the **operational incident surface**.

### Data sources to use
- `Alert`
- `AlertRule`
- `Event`
- `WebhookDelivery`
- integration test failures / notification errors

### What should be visible
- active alarms
- severity
- source event type
- Bentley asset context
- affected iTwin / iModel
- triggered time
- owner / escalation state
- notification routing status
- acknowledge / mute / resolve actions

### Route
- `/mobile/alarms`
- `/mobile/alarms/{alarm_id}`

### Supporting APIs
- `GET /api/mobile/alarms`
- `GET /api/mobile/alarms/{alarm_id}`
- `POST /api/mobile/alarms/{alarm_id}/ack`
- `POST /api/mobile/alarms/{alarm_id}/resolve`
- `POST /api/mobile/alarms/test`

### Reuse
- current alert rule system from Admin
- current event severity and processing state concepts

---

## 3. Monitors tab
### Bentley translation
This becomes **resource monitoring setup** for Bentley resources and connected operational assets.

### Screenshot behavior translated
The screenshot shows URL/domain discovery. In Bentley this should become one or both of the following:

#### Option A: Bentley-native setup
User enters:
- iTwin ID / iTwin name
- iModel ID / iModel name
- webhook scope
- job family
- integration watch targets

#### Option B: Hybrid setup
User enters:
- project URL / external endpoint / webhook consumer URL
- Bentley resource context
- monitor type

### Recommended monitor types
- iTwin activity monitor
- iModel change monitor
- synchronization job monitor
- transformation job monitor
- reality processing monitor
- issue activity monitor
- form workflow monitor
- access governance monitor
- webhook delivery health monitor
- integration delivery monitor

### Route
- `/mobile/monitors`
- `/mobile/monitors/{monitor_id}`
- `/mobile/monitors/groups`

### Supporting APIs
- `GET /api/mobile/monitors`
- `POST /api/mobile/monitors`
- `GET /api/mobile/monitor-groups`
- `POST /api/mobile/monitor-groups`
- `GET /api/mobile/monitors/{monitor_id}`

### Existing repo alignment
This should leverage existing iTwin/iModel listing APIs and event telemetry rather than introducing a separate monitoring domain disconnected from Bentley.

---

## 4. Reports tab
### Bentley translation
This becomes **operational reporting and SLA visibility**.

### What should be included
- scheduled reports
- custom report builder
- SLA settings
- exportable operational summaries
- public or shared reports where allowed
- incident / event trend summaries
- health summaries by iTwin / iModel / category / integration

### Route
- `/mobile/reports`
- `/mobile/reports/scheduled`
- `/mobile/reports/customize`
- `/mobile/reports/sla`
- `/mobile/reports/{report_id}`

### Supporting APIs
- `GET /api/mobile/reports/summary`
- `GET /api/mobile/reports/scheduled`
- `POST /api/mobile/reports/scheduled`
- `POST /api/mobile/reports/customize`
- `POST /api/mobile/reports/sla`

### Existing repo alignment
Reuse and extend:
- `/dashboard/feed`
- `/api/charts/trend`
- `/api/stats`
- `/events/export`

---

## 5. Admin tab
### Bentley translation
This is an extension of the existing admin system, but organized into a mobile card/list interface.

### Existing admin already covers part of this
Current repo already has:
- Bentley connection
- webhook endpoint management
- alert rules
- data management
- user management
- platform info

### Add these mobile-admin groups
#### Inventory
- Monitors
- Monitor Groups

#### User Management
- Users
- User Groups

#### Configuration Profiles
- Location Profile
- Threshold and Availability
- Notification Profile
- Email Template

#### Server / Resource Monitor
- Resource Check Profile
- Settings

#### Poller
- On-Premise Poller
- Mobile Network Poller

#### Operations
- Scheduled Maintenance
- Log Report
- Alert Logs

#### Report Settings
- Scheduled Reports
- Customize Report
- SLA Settings

#### Share
- Uptime Button
- Operations Dashboard
- Public Reports

#### Developer
- Device Key

#### IT Automation
- IT Automation Templates

### Route
- `/mobile/admin`
- `/mobile/admin/{section}`

### Supporting APIs
- keep current `/admin/*` endpoints where practical
- add mobile API wrappers only when mobile output shape differs significantly

### Recommendation
Do not create a second admin backend. Create mobile-optimized views over the same admin services.

---

## 6. More tab
### Bentley translation
This is the user utilities and app-level preferences area.

### Features to include
- account context
- tenant / project switcher if multi-tenant
- timezone settings
- alert notification preferences
- custom dashboards
- scheduled maintenance shortcut
- newsletter / release digest preference
- service status
- tab customization
- trigger test alert
- app settings

### Route
- `/mobile/more`

### Supporting APIs
- `GET /api/mobile/preferences`
- `PUT /api/mobile/preferences`
- `GET /api/mobile/service-status`
- `POST /api/mobile/test-alert`

---

## 7. Third-party Integrations marketplace
### Bentley translation
This should become the mobile extension of the current integrations catalog.

### Existing repo fit
This is the **best alignment point** in the current codebase.

The repo already has:
- integration catalog metadata
- category grouping
- connection states
- custom integrations
- connection testing
- connect/disconnect lifecycle

### New category model to support the screenshot reference
Layer these categories onto the existing integration catalog:
- Collaboration
- Incident Response / On-Call
- ITSM / Service Desk
- Workflow / Eventing
- Analytics
- AI Integrations
- Application Monitoring
- Existing technical categories can remain for desktop views

### Target vendors to add or normalize
#### Collaboration
- Slack
- Microsoft Teams
- Telegram
- Discord
- Zoho Cliq

#### Incident / On-call
- PagerDuty
- Opsgenie
- Splunk On-Call
- iLert
- BigPanda
- Moogsoft
- AlarmsOne

#### ITSM / Service Desk
- Jira
- Jira Service Management
- ServiceNow
- Zendesk
- Freshdesk
- Freshservice
- Zoho Desk
- ServiceDesk Plus variants
- ConnectWise Manage

#### Workflow / Eventing
- Webhooks
- Zapier
- Google Cloud Pub/Sub

#### Analytics / Reporting
- Analytics Plus
- Power BI
- Application Manager

#### AI
- Bring Your Own Key (BYOK)
- Azure OpenAI
- OpenAI
- Gemini
- Atlassian Rovo AI

### Route
- `/mobile/integrations`

### Recommendation
Keep a single source of truth for integration metadata and state. Render it differently for desktop and mobile, but do not create parallel catalogs.

---

## Suggested data model additions

## New models to add
### MonitorProfile
Tracks what is being monitored.
- id
- name
- monitor_type
- target_type (`itwin`, `imodel`, `job`, `issue`, `form`, `access`, `webhook`, `integration`)
- target_id
- target_name
- group_id
- threshold_profile_id
- notification_profile_id
- is_enabled
- created_at
- updated_at

### MonitorGroup
Groups related monitors.
- id
- name
- description
- owner_id
- created_at

### ThresholdProfile
- id
- name
- severity_mapping_json
- availability_rules_json
- response_windows_json

### NotificationProfile
- id
- name
- destinations_json
- quiet_hours_json
- escalation_policy_json

### ScheduledMaintenance
- id
- title
- description
- start_at
- end_at
- scope_json
- created_by

### ScheduledReport
- id
- name
- frequency
- target_audience_json
- filters_json
- delivery_destinations_json
- is_enabled

### PublicReport / SharedStatusAsset
- id
- name
- asset_type (`uptime_button`, `operations_dashboard`, `public_report`)
- config_json
- is_public
- public_token

### Poller
- id
- name
- poller_type (`on_prem`, `mobile_network`)
- status
- config_json
- last_seen_at

### DeviceKey
- id
- name
- key_hash
- owner_id
- created_at
- revoked_at

### AutomationTemplate
- id
- name
- trigger_type
- trigger_config_json
- action_config_json
- is_enabled

### UserPreference
- id
- user_id
- timezone
- tabs_json
- notification_prefs_json
- dashboard_prefs_json
- app_settings_json

### ServiceStatusSnapshot
- id
- status (`operational`, `degraded`, `incident`, `maintenance`)
- summary
- details_json
- created_at

## Existing models to reuse heavily
- `Event`
- `WebhookDelivery`
- `Integration`
- `AlertRule`
- `Alert`
- `User`
- `Tenant`
- `ITwin`
- `IModel`

---

## API design recommendation

## Reuse existing endpoints where possible
Keep using existing endpoints for:
- dashboard stats
- charts/trends
- integration state
- user management
- alert rule admin
- Bentley webhook management
- event export
- iTwin listing/detail

## Add a mobile-focused API surface only where needed
Recommended mobile API namespace:

```text
GET    /api/mobile/home
GET    /api/mobile/alarms
GET    /api/mobile/alarms/{id}
POST   /api/mobile/alarms/{id}/ack
POST   /api/mobile/alarms/{id}/resolve
POST   /api/mobile/alarms/test

GET    /api/mobile/monitors
POST   /api/mobile/monitors
GET    /api/mobile/monitors/{id}
PUT    /api/mobile/monitors/{id}
GET    /api/mobile/monitor-groups
POST   /api/mobile/monitor-groups

GET    /api/mobile/reports/summary
GET    /api/mobile/reports/scheduled
POST   /api/mobile/reports/scheduled
PUT    /api/mobile/reports/scheduled/{id}
POST   /api/mobile/reports/customize
POST   /api/mobile/reports/sla

GET    /api/mobile/admin/sections
GET    /api/mobile/admin/service-status
GET    /api/mobile/preferences
PUT    /api/mobile/preferences
GET    /api/mobile/integrations
```

---

## UI composition plan

## Shared mobile shell
Create `base_mobile.html` with:
- top title bar
- bottom tab bar
- shared dark theme tokens
- floating support/help button only if product wants it
- shared panel/card/list primitives

## Mobile components to standardize
- mobile section card
- settings row with chevron
- status badge
- alarm severity chip
- integration card
- list filter/dropdown
- empty-state setup form
- bottom navigation item
- modal sheet / drawer

## Theme direction
Use the screenshot style direction, but align with Bentley brand constraints:
- dark primary theme
- high-radius cards
- soft glass overlays only if performance stays acceptable
- green accent for success/selected states
- white typography with muted secondary text

Do not hard-clone third-party branding. Recast it into Bentley-compatible visual language.

---

## Build phases

## Phase 1 — Mobile shell and route scaffolding
### Deliverables
- `mobile.py` router
- `base_mobile.html`
- bottom navigation shell
- placeholder pages for Alarms / Monitors / Reports / Admin / More / Integrations
- mobile CSS/JS foundation

### Acceptance
- pages render
- auth/session works
- navigation works on mobile sizes
- no impact to desktop routes

---

## Phase 2 — Bentley-backed Alarms and Monitors
### Deliverables
- alarms feed
- alarm detail
- monitor setup
- monitor grouping
- monitor detail
- notification / threshold profile foundation

### Acceptance
- alarms read real or demo event/alert data
- monitor records persist in DB
- a user can create and view monitors from mobile shell

---

## Phase 3 — Reports + More
### Deliverables
- mobile reports summary
- scheduled reports list/create
- SLA settings UI
- preferences / timezone / service status / test alert

### Acceptance
- reports summarize real platform data
- preferences persist per user
- test alert works

---

## Phase 4 — Admin mobile extension
### Deliverables
- mobile admin section map
- reuse existing admin APIs where possible
- add maintenance, poller, device key, automation template support as needed

### Acceptance
- core admin actions can be performed in mobile UI
- no duplicate business logic

---

## Phase 5 — Marketplace expansion
### Deliverables
- mobile integrations marketplace
- category alignment to collaboration / ITSM / incident / AI / workflow model
- integration detail sheet
- connect/test/disconnect flow reuse

### Acceptance
- current integrations continue working
- mobile marketplace can surface existing integration state

---

## Phase 6 — Production hardening
### Deliverables
- permissions review
- audit trail additions where needed
- persistent storage for all new entities
- test coverage
- responsive QA
- PWA enhancements if desired

---

## Screen-by-screen feature backlog

## Mobile Home / Launch
- optional splash / intro
- quick links to Alarms / Monitors / Reports
- health/status summary

## Alarms
- alarm feed
- severity tabs
- search/filter
- alarm detail
- acknowledge / resolve
- escalation target visibility

## Monitors
- empty-state setup
- create monitor form
- monitor list
- monitor groups
- monitor detail
- threshold / notification assignment

## Reports
- scheduled reports
- customize report
- SLA settings
- report history
- export action

## Admin
- Inventory
- User Management
- Configuration Profiles
- Poller
- Operations
- Report Settings
- Share
- Developer
- IT Automation

## More
- account switch
- timezone
- alert notifications
- custom dashboards
- scheduled maintenance shortcut
- newsletter toggle
- service status
- tab customization
- trigger test alert
- app settings

## Integrations
- category filter
- searchable cards
- detail sheet
- connect
- test
- disconnect

---

## Exact repo integration points

## Route registration
Add the new router in `app/main.py`.

## Template inheritance
Use a new `app/templates/mobile/base_mobile.html` rather than forcing the desktop `base.html` to behave like a mobile shell.

## Shared styling
Keep shared primitives in `app/static/css/app.css` only if they are truly global. Put mobile-specific styling in `app/static/css/mobile.css`.

## Desktop/mobile coexistence
- desktop stays on current top nav pages
- mobile module lives under `/mobile/*`
- avoid conditional logic that makes the same template render both experiences unless there is a proven maintenance benefit

## Integration reuse
Extend the current integration catalog system rather than replacing it.

## Admin reuse
Keep current admin endpoints as the operational source of truth and add mobile views on top.

---

## Risks and technical debt to address

### 1. Legacy vs current app confusion
The repo contains both a root app and a modular app. This can cause wasted implementation effort if an agent edits the wrong surface.

**Action:** treat `app/` as authoritative.

### 2. README drift
The README and root file history may not match the active modular architecture.

**Action:** update README after this module lands.

### 3. Existing nav references an iModels page
The desktop base template links `/imodels-view`. Ensure the route/template exists and is stable before borrowing that pattern for mobile.

### 4. Data model sprawl
The mobile admin and monitoring scope can explode quickly.

**Action:** phase the data model; do not build all screenshot nouns at once without usage priority.

### 5. Security for outbound calls
Integration testing and webhook delivery flows must maintain current SSRF-safe behavior and credential handling.

---

## Definition of done
This module is done when:
- mobile shell exists under `/mobile/*`
- alarms, monitors, reports, admin, more, and integrations pages render and navigate correctly
- alarms and monitors are backed by real Bentley platform data or stable demo data
- integrations mobile view reuses the current integration catalog and state model
- admin mobile view reuses current admin logic rather than duplicating it
- preferences persist
- scheduled reports and maintenance flows exist at least at MVP depth
- desktop experience remains unaffected
- smoke test coverage is extended for new routes

---

## Recommended immediate implementation order
1. Create `/mobile/*` shell and templates
2. Reuse current dashboard and event data to power **Alarms**
3. Reuse current iTwin/iModel data to power **Monitors**
4. Reuse current integrations catalog for **Mobile Integrations**
5. Reuse current admin APIs for **Mobile Admin**
6. Add reports/preferences models last

---

## Copy-paste build brief for a developer or coding agent

**Build a new mobile-first Bentley module inside the current FastAPI/Jinja platform. Do not use the legacy root main.py. Use the modular app/ architecture only. Create a new router group under /mobile with pages for alarms, monitors, reports, admin, more, and integrations. Reuse existing Bentley event, iTwin, iModel, integration, alert rule, alert, user, and admin capabilities wherever possible. Extend the current integrations marketplace rather than replacing it. Extend the current admin system rather than duplicating it. Use a dark mobile UI with a bottom tab bar and high-radius cards, inspired by the supplied mobile monitoring screenshots, but translate the experience into Bentley iTwin Operations Center language and flows. Prioritize alarms, monitors, and mobile integrations first. Keep desktop routes unchanged.**

---

## Final recommendation
This should be positioned internally as:

**“Bentley Mobile Ops extension for the existing iTwin Operations Center.”**

That framing is the cleanest architectural fit, the lowest-risk implementation path, and the most credible story for product continuity.
