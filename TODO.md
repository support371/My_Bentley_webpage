# TODO.md

## Bentley platform execution TODO

This file is the active execution list for the repository.
It should be read together with `CLAUDE.md`.

## Highest priority

### 1. Documentation alignment
- [ ] update README so it matches the current modular FastAPI app
- [ ] document the real route map and current product surfaces
- [ ] remove or rewrite stale references to the old single-file MVP

### 2. Launch readiness
- [ ] add or improve a launch-readiness page and API
- [ ] show blockers for domain, Bentley credentials, webhook security, cookies, DB backend, observability, legal pages, and alert routing
- [ ] make launch readiness visible from the main admin / operations flow

### 3. Mobile Ops hardening
- [ ] improve the Mobile Ops screens for alarms, monitors, reports, admin, more, and integrations
- [ ] replace weak stubs with stronger seeded data and richer operational summaries
- [ ] keep Mobile Ops tightly linked to the existing event / resource / integration models

### 4. Admin and service configuration
- [ ] expose clearer admin controls for service setup
- [ ] support website chat provider readiness
- [ ] support browser notification readiness
- [ ] support admin alert delivery readiness
- [ ] support observability provider readiness

### 5. Control plane expansion
- [ ] add or deepen Website Studio
- [ ] add or deepen Infrastructure Console
- [ ] add or deepen Marketplace and News
- [ ] add or deepen Client Delivery
- [ ] add or deepen platform flow / operations status

### 6. Deployment readiness
- [ ] keep Docker runtime aligned with `app.main:app`
- [ ] keep Azure DevOps / AKS scaffold files coherent
- [ ] improve Helm templates where they are still baseline-only
- [ ] document required secrets, service connections, and environment setup

## Product rules

- [ ] preserve Bentley-native operations identity
- [ ] preserve modular `app/` runtime structure
- [ ] do not collapse the app into a single landing page
- [ ] keep admin, integrations, Mobile Ops, and deployment surfaces visible in the platform

## Nice-to-have after core stabilization

- [ ] improve charts and visual analytics
- [ ] add deeper client portal concepts
- [ ] expand marketplace / news surfaces
- [ ] expand billing / wallet / monetization concepts
- [ ] expand Cloudflare / security control surfaces

## Working note for Claude / VS Code assistants

Before changing architecture, first inspect:
- `app/main.py`
- `app/api/routes/`
- `app/templates/`
- `app/static/`
- `CLAUDE.md`
- this `TODO.md`

Then continue from the current platform reality instead of restarting the project.
