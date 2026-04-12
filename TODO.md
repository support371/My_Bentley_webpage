# TODO.md

## Bentley platform execution TODO

This file is the active execution list for the repository.
It should be read together with `CLAUDE.md`.

## Recently Completed

### 1. Backend Routes & Service Wiring
- [x] implemented `/health` with database check
- [x] implemented `/dashboard/feed` and `/dashboard/test-webhook`
- [x] implemented `/api/events`, `/api/itwins`, `/api/imodels`, `/api/integrations`
- [x] implemented `/api/admin/summary` and `/api/mobile/summary`
- [x] implemented `/api/launch-readiness` and `/api/control-plane`
- [x] implemented `/api/agent/explain-health`

### 2. Model & Data Hardening
- [x] added `ControlPlaneModule` and `LaunchCheck` SQLModel tables
- [x] enhanced `app/db/seed.py` with robust initial data for all modules
- [x] replaced weak stubs with database-driven service layers

### 3. Launch Readiness & Control Plane
- [x] built full backend logic for Launch Readiness checks
- [x] added Control Plane sub-pages (Website Studio, Infrastructure, Environments)
- [x] wired frontend templates to new backend services

### 4. Documentation & Cleanup
- [x] aligned `README.md` and `TODO.md` with the current modular FastAPI app
- [x] removed stale prototype files and extraction directories

## Remaining / Future Priority

### 1. Advanced Service Configuration
- [ ] add deeper admin controls for browser notification setup
- [ ] expand observability provider integrations (Sentry/Datadog)
- [ ] add support for client delivery and marketplace billing surfaces

### 2. UI/UX Refinement
- [ ] improve real-time updates for the dashboard feed using WebSockets
- [ ] enhance mobile-responsive views for complex data tables
- [ ] add more interactive charts to the Infrastructure Console

### 3. Deployment & CI/CD
- [ ] refine Helm templates for production-grade AKS deployment
- [ ] add integration tests for third-party webhook signature verification

## Product rules

- [x] preserve Bentley-native operations identity
- [x] preserve modular `app/` runtime structure
- [x] do not collapse the app into a single landing page
- [x] keep admin, integrations, Mobile Ops, and deployment surfaces visible in the platform
