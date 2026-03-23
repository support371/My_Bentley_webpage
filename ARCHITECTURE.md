# ARCHITECTURE.md

## System overview
This repository is a FastAPI-based Bentley operations dashboard focused on webhook intake, event visibility, and admin-facing configuration views.

## Main building blocks
- FastAPI application entrypoint
- dashboard and admin views
- webhook ingestion path
- event retrieval endpoints
- tests and smoke scripts

## Request flow
1. the service starts the FastAPI app
2. incoming requests hit API or HTML routes
3. webhook traffic is accepted and processed by server-side handlers
4. dashboard and admin routes render current state to the UI

## Key risk surfaces
- webhook handling and authenticity assumptions
- admin-facing settings exposure
- CORS behavior
- runtime configuration
- API contract stability

## Design principles
- keep public behavior explicit
- keep security-sensitive logic server-side
- prefer small, reviewable changes
- document user-visible behavior changes
- preserve rollback simplicity

## Change guidance
For changes to auth, secrets, deployment, schema, or public API behavior, use approval-gated review.
