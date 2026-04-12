# CLAUDE.md

## Purpose

This repository is the working codebase for the **Bentley operations platform** and its broader enterprise SaaS evolution.

Any assistant working in this repository must treat the current modular app as the baseline and continue building from that reality.
Do **not** rebuild the app as a generic landing page or revert it to the older single-file prototype described by stale docs.

## Current repo truth

The app is now a **modular FastAPI platform** centered on `app/main.py`.
It already includes route modules and UI surfaces for:

- authentication
- dashboard
- events
- webhooks
- admin
- integrations
- iTwins / iModels resource views
- Bentley Mobile Ops

The navigation pattern should remain centered on:

- Overview
- Events
- iTwins
- iModels
- Integrations
- Mobile Ops
- Admin

## Product direction

This app is not just a webhook demo.
It should continue evolving into a **Bentley-native operations and enterprise control platform** with these layers:

### 1. Bentley operations core
Preserve and improve:
- webhook intake
- event intelligence
- iTwin and iModel visibility
- integration status
- admin controls
- mobile-first operational views

### 2. Mobile Ops
Maintain and expand the mobile module with:
- alarms
- monitors
- reports
- admin
- more
- integrations

Treat Mobile Ops as a presentation layer over the existing platform primitives, not a separate product.

### 3. Launch readiness / production readiness
The app should expose a launch-readiness surface that evaluates:
- custom domain readiness
- Bentley credentials readiness
- webhook signature verification
- secure cookie readiness
- database readiness
- admin alert routing
- website chat readiness
- browser notification readiness
- observability readiness
- privacy / terms page readiness

### 4. Control plane / enterprise expansion
The app should continue growing toward a control-plane model with visible product surfaces for:
- Website Studio
- Infrastructure Console
- Cloudflare Security
- Billing and Wallet
- Marketplace and News
- Client Delivery
- Operations / platform flow

These modules may be partial or seeded at first, but they should be represented clearly in the UI and architecture.

### 5. Deployment and DevOps layer
The platform direction includes a production delivery layer based on:
- Dockerized app runtime
- Azure DevOps CI/CD
- AKS deployment flow
- Helm chart deployment
- environment promotion
- secrets / config readiness

The repo may contain partial scaffold files for this. Continue from them instead of starting over.

## Working principles for Claude

1. **Preserve the modular architecture.**
   Prefer extending `app/` routes, templates, services, models, and static assets.

2. **Do not flatten the platform.**
   Keep product areas distinct instead of collapsing everything into one page.

3. **Favor production-minded UX.**
   Admin-friendly forms, seeded data, status cards, tables, charts, and operations dashboards are preferred over placeholder marketing copy.

4. **Use the real repo state over stale documentation.**
   If code and docs disagree, trust the code and then fix the docs.

5. **Extend, don’t fork.**
   New modules should integrate into the existing navbar, templates, and service layer.

6. **Keep Bentley identity intact.**
   This should still feel like a Bentley operations platform even as enterprise modules expand.

7. **Be honest about partial implementation.**
   It is acceptable for deeper workflows to be scaffolded or mocked initially, as long as the structure is clean and future-ready.

## Immediate build priorities

When continuing work, prioritize in this order:

1. align stale documentation with the modular app
2. strengthen launch-readiness and admin service configuration
3. improve Mobile Ops UX and data depth
4. deepen integrations and observability surfaces
5. expand control-plane modules
6. harden deployment and Azure DevOps / AKS readiness

## Do not do these things

- do not replace the modular app with a fresh prototype
- do not remove Mobile Ops
- do not turn the repository into only a marketing site
- do not bypass the existing `app/` runtime with a duplicate stack
- do not assume old README text is the source of truth

## Short instruction

If you are Claude working in VS Code on this repo:
**study the current `app/` runtime first, preserve the Bentley operations baseline, and then continue building the full enterprise control-plane vision on top of it.**
