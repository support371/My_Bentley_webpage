# RUNBOOK.md

## Purpose
This runbook gives a fast path for operating, validating, and reviewing the Bentley dashboard repository.

## Core workflows
### Local start
- install dependencies from `requirements.txt`
- run the FastAPI app with the repo's standard startup command
- verify the application port matches the repo configuration

### Minimum validation
Run the highest-value checks available before merge:
1. targeted tests for changed areas
2. full test suite
3. smoke test script if present
4. manual endpoint spot checks for `/health` and `/dashboard`

### High-signal endpoints
- `/health`
- `/dashboard`
- `/webhook`
- `/events`
- `/admin`

## Change checklist
Before opening a PR:
- confirm scope is limited to the stated goal
- update docs if behavior changed
- note risk level
- note validation performed
- note anything blocked in the current environment

## Incident triage
If the app is not behaving correctly:
1. check startup errors
2. confirm dependency install completed cleanly
3. verify the expected port and base URL settings
4. hit `/health`
5. inspect recent changes in webhook, admin, and dashboard paths
6. confirm tests still pass

## Deployment caution areas
Use extra care when touching:
- CORS behavior
- admin settings exposure
- webhook handling
- API response contracts
- runtime configuration

## Merge readiness
A change is ready when:
- the requested change is complete
- validation notes are included
- user-visible impact is clear
- rollback path is simple
