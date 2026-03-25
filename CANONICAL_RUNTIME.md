# CANONICAL_RUNTIME.md

## Final decision
The canonical production runtime for this repository is:

`app.main:app`

## Why
The repository contains multiple app shapes, including a legacy root-level `main.py` and the richer application stack under `app/`. To prevent deployment drift, all production execution and future implementation work must converge on the application under `app/`.

## Rules
- GitHub is the source of truth.
- Production deployments must run the canonical app only.
- Root `main.py` must be treated as legacy and must not evolve as a separate product surface.
- Azure DevOps must remain a first-class integration in the canonical application experience.
- Successful changes must be delivered by branch and pull request.

## Expected route shell
The canonical app should converge to this route model:
- `/`
- `/events`
- `/itwins`
- `/integrations`
- `/webhooks`
- `/admin`

## Immediate convergence priorities
1. Neutralize runtime drift between root `main.py` and `app.main:app`.
2. Align the canonical app to the frozen UI baseline.
3. Add Azure DevOps to the canonical integrations catalog if missing.
4. Expose only safe platform information in Admin.
5. Defer deeper backend wiring to follow-on PRs once the shell is aligned.
