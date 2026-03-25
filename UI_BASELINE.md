# UI_BASELINE.md

## Purpose
This document freezes the Bentley Operations Center UI reference captured from the Replit mockup so the canonical Python/FastAPI app can converge to it without further layout churn.

## Canonical information architecture
The target navigation uses a persistent, collapsible left sidebar and the following primary routes:
- `/` — Dashboard
- `/events` — Event Stream
- `/itwins` — iTwins Explorer
- `/integrations` — Integrations
- `/webhooks` — Webhooks
- `/admin` — Admin

## Page purposes
### Dashboard
High-level system overview with KPI cards, recent activity, and system health.

### Event Stream
Searchable and filterable event table for Bentley iTwin activity.

### iTwins Explorer
Directory of active digital twin projects and models.

### Integrations
Control center for outbound connected services with Azure DevOps as a first-class integration.

### Webhooks
Operational view of configured webhook endpoints, success rates, and retry actions.

### Admin
Safe administrative surface for non-sensitive platform settings, SSO status, Bentley connections, and system health.

## Key components by page
### Dashboard
- KPI cards for total webhooks, latency, active integrations, and failed deliveries
- recent activity feed
- system health panel for Bentley API, Azure DevOps, and webhook delivery services

### Event Stream
- filter bar for event type, category, and iTwin ID
- data table with event type, category, iTwin/iModel, severity, and timestamp

### iTwins Explorer
- grid cards with iTwin name, facility type, GUID, active iModels, daily event count, and last activity

### Integrations
- integration cards with service name, description, icon, and active/inactive toggle
- Azure DevOps must remain explicitly visible here

### Webhooks
- data table with target URL, subscriptions, delivery state, success rate, and retry/edit actions

### Admin
- tabs for General, Auth, API, and System
- masked or read-only identifiers only; no secret exposure

## Visual system
- persistent left sidebar with collapsed and expanded states
- Inter typography
- professional high-contrast design with primary blue active states
- cards, tables, and pill badges as core primitives
- subtle transitions and motion only

## Mock-data replacement map
The following areas are still mock-driven in the Replit reference and must be wired to the canonical backend:
- dashboard KPIs, system health, and recent activity
- events table and filters
- iTwins cards and sync behavior
- integrations state and toggles
- webhooks list and retry actions
- admin form values and connection tests

## Implementation note
This file is design reference only. The production implementation must live in the canonical Python/FastAPI application and be pushed through GitHub PRs.
