# Bentley Mobile Ops Integration Handoff

## Objective
Integrate the 12-screen mobile monitoring experience into the ongoing **Bentley iTwin Operations Center** as a **mobile-first operational module**, not as a separate clone product.

This document is written for a senior developer or coding agent who needs to understand:
- how the screens map into the current Bentley repo
- what features/pages/flows should exist
- how the module should fit the current architecture
- what should be reused versus newly created

---

## 1) Repository fit assessment

The Bentley repo is not a static landing page project. It is already a **modular FastAPI application** with:
- app bootstrap in `app/main.py`
- route modules in `app/api/routes/`
- Jinja templates in `app/templates/`
- shared static assets in `app/static/`
- DB initialization and models already present
- event, admin, integrations, auth, and Bentley iTwin resource flows already implemented

### Current active application structure
The real application entrypoint is:
- `app/main.py`

It already registers these route groups:
- auth
- dashboard
- events
- webhooks
- admin
- integrations
- itwins

### Implication
The mobile monitoring experience should be added as a **new module inside the current app**, not as a separate cloned app and not as an extension of the legacy root prototype.

### Canonical implementation location
Add the new work under:
- `app/api/routes/mobile.py`
- `app/templates/mobile/*`
- `app/static/css/mobile.css`
- `app/static/js/mobile.js`

---

## 2) Product interpretation of the 12 screens

The screenshots do **not** describe a generic marketing page.
They describe a **mobile operations / monitoring application** with:
- tab-based navigation
- service alarms
- monitor setup/onboarding
- reports and SLA settings
- admin governance modules
- more/settings utilities
- third-party integrations marketplace
- AI integration hooks

So the correct Bentley translation is:

# Bentley Mobile Ops Module
A mobile-first control surface layered into Bentley iTwin Operations Center for:
- event/alert visibility
- monitor setup flows
- operational reporting
- admin control shortcuts
- integrations management
- mobile user actions

---

## 3) Target navigation model

## Bottom navigation from reference
The screenshots clearly indicate 5 main tabs:
- **Alarms**
- **Monitors**
- **Reports**
- **Admin**
- **More**

### Recommended Bentley route mapping
- `/mobile/alarms`
- `/mobile/monitors`
- `/mobile/reports`
- `/mobile/admin`
- `/mobile/more`

### Related integrations surface
- `/mobile/integrations`

### Recommended API support layer
- `/api/mobile/summary`
- `/api/mobile/alarms`
- `/api/mobile/monitors`
- `/api/mobile/reports`
- `/api/mobile/admin-summary`
- `/api/mobile/more-summary`
- `/api/mobile/integrations`

---

## 4) Full screen-to-feature translation

# A. Welcome / intro screen
### Original role
Intro/onboarding screen with monitoring value proposition and CTA.

### Bentley translation
This should become a **Mobile Ops intro / launch state**, not a marketing clone.

### Recommended content
- Bentley / iTwin Operations branding
- subtitle like: `Mobile-first monitoring, alerting, and operations visibility`
- CTA options:
  - `Open Mobile Ops`
  - `View Integrations`
  - `Go to Dashboard`

### Recommended implementation
This can be:
- omitted as a standalone route in phase 1, and
- replaced by redirecting `/mobile` -> `/mobile/alarms`

That is the fastest repo-fitting move.

---

# B. Alarms tab
### What the reference implies
A tab for monitoring alarms, state changes, and alert-driven operational awareness.

### Bentley mapping
Use the **existing event stream** as the alarm basis.

### Repo reuse
From the current repo you already have:
- `Event`
- `WebhookDelivery`
- dashboard feed stats
- event listing APIs
- severity information

### What the mobile Alarms page should show
- recent alerts/events
- severity chip
- event type
- iTwin / project name
- iModel / asset context if present
- received time
- processing status

### Recommended API source
- `GET /api/mobile/alarms`

### Internal logic
This route should query recent `Event` rows and normalize them into a mobile payload.

### Recommended flow
1. User opens **Alarms**
2. sees recent Bentley event-driven alarms
3. filters mentally by severity and project
4. taps through to desktop event stream if deeper inspection is needed

---

# C. Monitors tab
### What the reference implies
A monitor onboarding/setup experience with domain input and auto-discovery behavior.

### Bentley translation
Bentley is not a generic website uptime tool, so this must be translated intelligently.

### Correct Bentley interpretation
This tab becomes a **resource monitoring / asset setup / endpoint monitoring** surface.

### What should appear
#### Section 1: Setup new monitoring
Fields:
- domain / endpoint URL
- label / monitor name
- environment
- monitor type

#### Section 2: Existing monitored resources
Show:
- iTwins
- iModels
- event-active resources
- future external monitor records if introduced later

### Repo reuse
Use current Bentley resource data for phase 1:
- `ITwin`
- `IModel`
- event activity counts

### Important implementation principle
Do **not** fake real auto-discovery.
In phase 1, create a **monitor discovery stub**:
- accepts URL/domain input
- acknowledges request
- returns structured preview object
- optionally stores lightweight temp state later

### Recommended API
- `GET /api/mobile/monitors`
- `POST /api/mobile/monitors/discover`

### Recommended flow
1. user opens **Monitors**
2. sees setup card
3. submits URL/domain/resource label
4. app returns acknowledgment/pending state
5. existing Bentley resources render below

---

# D. Reports tab
### What the reference implies
Scheduled reports, custom reports, SLA-style settings, reporting control.

### Bentley translation
This should be a **compact reporting command surface**.

### What it should include
- Scheduled Reports
- Customize Report
- SLA Settings
- Export actions
- operational summary cards

### Repo reuse
The repo already has:
- dashboard KPIs
- `/api/stats`
- event exports
- integrations count
- uptime / processing metrics

### Recommended mobile reports content
- cards with summary values
- export shortcut
- status of report-related capabilities
- proxy SLA/error-rate surface until a more formal SLA model exists

### Recommended API
- `GET /api/mobile/reports`

### Recommended flow
1. open Reports
2. review operational metrics
3. export event/report data if needed
4. use as lightweight reporting surface on mobile

---

# E. Admin tab
### What the reference implies
This is the most feature-dense screen family.
The screenshots show grouped admin domains.

### Bentley translation
A **mobile admin summary console** that maps onto the existing admin capabilities.

## Admin groups observed and Bentley mapping

### 1. Inventory
Original entries:
- Monitors
- Monitor Groups

Bentley translation:
- Monitors -> current mobile monitors/resources count
- Monitor Groups -> placeholder / planned grouping concept or future grouping layer

### 2. User Management
Original entries:
- User
- User Groups

Bentley mapping:
- reuse existing `/api/users`
- render user count and role control summaries
- leave user groups as planned if not yet modeled

### 3. Configuration Profiles
Original entries:
- Location Profile
- Threshold and Availability
- Notification Profile
- Email Template

Bentley mapping:
- threshold/availability -> alert rules / event severity logic
- notification profile -> integration/alert routing logic
- email template -> placeholder or future enhancement

### 4. Server Monitor
Original entries:
- Resource Check Profile
- Settings

Bentley mapping:
- render as readiness/config section, likely phase-2 depth

### 5. Poller
Original entries:
- On-Premise Poller
- Mobile Network Poller

Bentley mapping:
- roadmap/planned cards unless a poller subsystem is added later

### 6. Operations
Original entries:
- Scheduled Maintenance
- Log Report
- Alert Logs

Bentley mapping:
- event history
- alert logs
- operational state
- future maintenance windows

### 7. Report Settings
Original entries:
- Scheduled Reports
- Customize Report
- SLA Settings

Bentley mapping:
- direct correspondence with mobile Reports surface

### 8. Share
Original entries:
- Uptime Button
- Operations Dashboard
- Public Reports

Bentley mapping:
- desktop dashboard links
- export/public-sharing roadmap items

### 9. Developer
Original entry:
- Device Key

Bentley mapping:
- developer/system key placeholder or future device credential feature

### 10. IT Automation
Original entry:
- IT Automation Templates

Bentley mapping:
- route through to future workflow templates / automation hooks / integrations logic

### Repo reuse
The current repo already supports a strong admin backbone:
- Bentley connection testing
- webhook listing/creation
- alert rules
- user management
- stats
- integrations

### Recommended implementation
The mobile Admin tab should be **summary-first**:
- grouped cards
- section counts / readiness states
- deep links where sensible
- admin-protected route

### Recommended API
- `GET /api/mobile/admin-summary`

### Security rule
Keep `/mobile/admin` and `/api/mobile/admin-summary` behind admin auth.

---

# F. More tab
### What the reference implies
This is the utility/personalization/status area.

### Bentley translation
This should contain:
- service status
- test alert shortcut
- timezone preference
- tab customization
- settings summary
- account add shortcut stub

### What should appear
- Service Status
- Trigger Test Alert
- Timezone
- Tab Customization
- Alert Notifications
- App Settings
- Integrations count / shortcuts

### Repo reuse
Use:
- `/health`
- current integrations count
- current alert test logic patterns

### Recommended APIs
- `GET /api/mobile/more-summary`
- `POST /api/mobile/test-alert`
- `POST /api/mobile/timezone`
- `POST /api/mobile/tab-customization`
- `POST /api/mobile/account/add`

### Implementation note
In phase 1, timezone/tab/account actions can use lightweight cookie or stub persistence.

---

# G. Integrations marketplace
### What the reference implies
A large filterable third-party integrations marketplace.

### Bentley mapping
The current Bentley repo already has the right base:
- integrations catalog
- DB-backed integration state
- connect/update/test/disconnect flows

So mobile should not create a second connector platform.

### Correct strategy
Reuse existing integrations and add **mobile grouping**.

### Mobile groups to present
- Collaboration
- Incident Response / On-call
- ITSM / Service Desk
- Workflow / Eventing
- Analytics
- AI
- Application Monitoring
- Other

### Recommended route
- `/mobile/integrations`

### Recommended API
- `GET /api/mobile/integrations`

### Flow
1. user opens Integrations
2. sees grouped cards
3. searches/filter client-side
4. moves to desktop integrations page if deeper configuration is needed

---

## 5) Data model / reuse principles

## Reuse first
### Existing platform models and flows should be reused wherever possible:
- `Event`
- `WebhookDelivery`
- `Integration`
- `User`
- `AlertRule`
- `Alert`
- `ITwin`
- `IModel`

## Avoid
Do not create:
- a second admin subsystem
- a second integrations persistence layer
- fake permanent monitor persistence without a real model
- a cloned non-Bentley UI stack disconnected from the live app

## Allowed phase-1 stubs
It is acceptable to stub:
- monitor discovery
- timezone persistence
- tab customization persistence
- account add workflow

As long as the API response is honest and implementation-ready.

---

## 6) Template and asset plan

## Templates
Create:
- `app/templates/mobile/base_mobile.html`
- `app/templates/mobile/_bottom_nav.html`
- `app/templates/mobile/alarms.html`
- `app/templates/mobile/monitors.html`
- `app/templates/mobile/reports.html`
- `app/templates/mobile/admin.html`
- `app/templates/mobile/more.html`
- `app/templates/mobile/integrations.html`

## CSS
Create:
- `app/static/css/mobile.css`

### Style direction
- dark theme
- rounded cards
- large tap targets
- bottom navigation
- compact, decision-grade UI

## JS
Create:
- `app/static/js/mobile.js`

### Responsibilities
- fetch mobile summary
- fetch page-specific feeds
- submit monitor discovery form
- trigger test alert
- save lightweight preferences
- client-side integration filtering

---

## 7) Exact implementation principles for a developer or agent

1. **Build in the active app only.**
2. **Reuse current models and route logic.**
3. **Do not introduce parallel systems.**
4. **Preserve admin auth boundaries.**
5. **Prefer honest stubs over fake completeness.**
6. **Ship in mergeable increments.**
7. **Update smoke coverage with each new route.**

---

## 8) Delivery expectation

The first shippable Bentley Mobile Ops milestone should include:
- page shell for all mobile tabs
- real alarm/event feed
- real monitor resource list
- real report summary cards
- admin summary groups
- more/settings summary
- grouped integrations marketplace
- smoke test updates

That is enough for a real first merge.

---

## 9) Final instruction to the developer/agent

Implement this as a **Bentley-native mobile operations module**.

Do not spend time cloning the old visual reference literally.
Do not build outside `app/`.
Do not fork the current platform behavior.

Build a reusable mobile layer on top of the live Bentley iTwin Operations Center.
