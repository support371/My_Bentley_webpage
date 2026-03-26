# Mobile Architecture Guide

## Intent

Bentley Mobile Ops is an extension of the active FastAPI platform. It is not a separate application and should not be implemented against the legacy root prototype.

## Canonical runtime

Build against:
- `app/main.py`
- `app/api/routes/`
- `app/templates/`
- `app/static/`

The application runtime is already wired to `app.main:app`, so all mobile work should stay inside the `app/` tree.

## Module shape

Recommended structure:
- `app/api/routes/mobile.py`
- `app/templates/mobile/`
- `app/static/css/mobile.css`
- `app/static/js/mobile.js`

## Core principle

Reuse existing Bentley platform capabilities first:
- dashboard summaries
- event stream
- iTwin and iModel inventory
- integrations catalog
- admin and user governance

Do not create a second admin system, a second integrations store, or a parallel monitoring stack.

## Data reuse map

### Alarms
Use existing event and delivery data as the basis for mobile alarms.

### Monitors
Use existing iTwin and iModel resources for current monitor surfaces. External monitor discovery can remain a stub until a durable model is introduced.

### Reports
Use existing stats, summaries, and export flows.

### Admin
Use the current admin routes and access controls. Mobile admin is a compact surface, not a replacement for desktop admin.

### Integrations
Reuse the existing integration catalog and group entries with a mobile-specific presentation layer.

## Security model

- keep `/mobile/admin` admin-protected
- keep `/api/mobile/admin-summary` admin-protected
- keep authenticated mobile POST actions behind current auth dependencies
- do not bypass current user or admin helpers

## Delivery model

Add the mobile module as a bounded feature set that can be merged incrementally:
1. shell and navigation
2. read APIs
3. mobile templates and assets
4. lightweight actions
5. hardening and persistence improvements
