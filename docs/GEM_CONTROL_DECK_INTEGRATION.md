# Bentley ↔ GEM Control Deck: approved integration boundary

## Canonical applications
- Bentley: `support371/My_Bentley_webpage` and the modular FastAPI app `app.main:app` only. The root `main.py` is legacy.
- GEM Control Deck: separate static PWA at https://gem-control-deck.vercel.app/.
- Keep the Bentley-specific digital-twin, events, alerts, webhooks, mobile, and administrative data model in Bentley. Do **not** merge Bentley's persistent database with the Control Deck's browser-local incident notes.

## Navigation / phase 1
- Bentley's main navigation links to its already-implemented `/mobile` module and the external Control Deck.
- Control Deck presents Bentley's public deployment URL, mobile dashboard and repository as links without claiming an authenticated connection.
- Pling is the iOS SSH/SFTP and remote-host application (https://plingpush.com/), not the Pleng self-hosting platform. Pling/Yomo/Working Copy are independent clients, not always-on servers.
- Neither app should store SSH keys, wallet recovery secrets, account passwords, API tokens, payment data or identity documents in browser localStorage.

## Phase 2 — read-only capability contract (NOT active)
Only after owner approval and explicit authorization / secure credentials:
1. Bentley provides a limited origin-restricted status feed, **not** an admin session export or raw database endpoint.
2. Control Deck fetches it via authenticated, origin-verified backend-to-backend integration; never embed a bearer token or Vercel admin credential in public JS.
3. Data contracts include `verified_at`, `source`, `status`, `error`, and `last_success_at`; show "unverified" rather than invented health.
4. Deployments and project ownership remain separate. No cross-project writes, financial transactions, KYC bypasses, or automatic account changes.
5. Only owner-approved, auditable commands can later be attached to any remote host.

## Blocking security issues from root audit
- The user-management API originally exposed routes lacking `require_admin` dependencies. The accompanying change adds them and a regression test. **Review and test before merging.**
- `app/core/config.py` contains development defaults for admin credentials, JWT key, webhook signature bypass, and cookies. Do not ship those defaults in a production environment. Configure strong secret values, signature verification and Secure cookies before enabling external access. Check actual environment keys/status without displaying values.
- `app/db/seed.py` seeds an admin identity; use a unique owner-approved password before production database provisioning.
- `app/api/routes/control_plane.py` contains illustrative infrastructure and traffic values. Do not represent them as live telemetry.
- `app/api/routes/mobile.py` still includes placeholder endpoints for monitor discovery and account addition. These are not completed backend workflows, even if the route returns HTTP 200.

## Acceptance gates
- `pytest tests/test_admin_route_guards.py` passes in configured project environment.
- `pytest tests/` and `bash smoke-test.sh` pass; login/logout, admin authorization and deny-by-default tests verified.
- Canonical Bentley production deployment uses the reviewed main branch and correct Vercel team; `/health`, `/mobile`, admin routes, webhooks and mobile JSON APIs checked in production with actual auth context.
- Check runtime database persistence; serverless temporary SQLite is not a production durable datastore.
- Validate official Pling SSH/Tailscale onboarding with a real authorized host before advertising live host control.
- Keep the pull request unmerged until owner has reviewed auth impact and the corresponding environment is ready.
