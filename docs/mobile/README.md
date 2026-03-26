# Bentley Mobile Ops

This folder documents the Bentley Mobile Ops extension added to the active FastAPI application under `app/`.

## Scope
- mobile alarms
- mobile monitors
- mobile reports
- mobile admin summary
- mobile more / service status
- mobile integrations catalog

## Runtime fit
Build against:
- `app/main.py`
- `app/api/routes/`
- `app/templates/`
- `app/static/`

Do not build against the legacy root prototype.

## Files added by the mobile module
- `app/api/routes/mobile.py`
- `app/templates/mobile/`
- `app/static/css/mobile.css`
- `app/static/js/mobile.js`

## Route map
Pages:
- `/mobile`
- `/mobile/alarms`
- `/mobile/monitors`
- `/mobile/reports`
- `/mobile/admin`
- `/mobile/more`
- `/mobile/integrations`

APIs:
- `/api/mobile/summary`
- `/api/mobile/alarms`
- `/api/mobile/monitors`
- `/api/mobile/reports`
- `/api/mobile/admin-summary`
- `/api/mobile/more-summary`
- `/api/mobile/integrations`

Actions:
- `/api/mobile/monitors/discover`
- `/api/mobile/test-alert`
- `/api/mobile/tab-customization`
- `/api/mobile/timezone`
- `/api/mobile/account/add`

## Reuse principles
- reuse existing events, iTwins, iModels, integrations, admin, and user models
- do not create a parallel integrations or admin system
- keep `/mobile/admin` admin-protected
- use lightweight stubs where persistence is not yet modeled

## Delivery principle
Extend the real Bentley platform. Do not fork it.
