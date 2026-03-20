"""
Bentley platform diagnostics service.
Provides structured, actionable diagnostic results for every integration
touchpoint — credentials, OAuth, iTwins access, webhooks, security posture.

Each function returns a DiagResult dict — never raises, never logs secrets.
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

import httpx

from app.core.config import settings

logger = logging.getLogger("itwin_ops.diagnostics")


# ─── Result shape ────────────────────────────────────────────────────────────

def _result(
    ok: bool,
    check_name: str,
    short_message: str,
    technical_detail: str = "",
    recommended_fix: str = "",
    error_class: str = "",
    status_code: Optional[int] = None,
) -> Dict[str, Any]:
    return {
        "ok": ok,
        "check_name": check_name,
        "short_message": short_message,
        "technical_detail": technical_detail,
        "recommended_fix": recommended_fix,
        "error_class": error_class,
        "status_code": status_code,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


# ─── Env / credential checks ─────────────────────────────────────────────────

def check_env_configuration() -> Dict[str, Any]:
    """Check whether all required Bentley env vars are present."""
    cid = settings.BENTLEY_CLIENT_ID
    csec = settings.BENTLEY_CLIENT_SECRET

    if not cid and not csec:
        return _result(
            ok=False,
            check_name="env_configuration",
            short_message="BENTLEY_CLIENT_ID and BENTLEY_CLIENT_SECRET are both missing",
            technical_detail="Neither env var is set. The platform cannot request OAuth tokens.",
            recommended_fix=(
                "In Replit → Secrets, add:\n"
                "  BENTLEY_CLIENT_ID  = your Service Application client ID\n"
                "  BENTLEY_CLIENT_SECRET = your Service Application client secret"
            ),
            error_class="missing_credentials",
        )
    if not cid:
        return _result(
            ok=False,
            check_name="env_configuration",
            short_message="BENTLEY_CLIENT_ID is missing",
            technical_detail="BENTLEY_CLIENT_SECRET is set but BENTLEY_CLIENT_ID is absent.",
            recommended_fix="Add BENTLEY_CLIENT_ID to Replit Secrets.",
            error_class="missing_credentials",
        )
    if not csec:
        return _result(
            ok=False,
            check_name="env_configuration",
            short_message="BENTLEY_CLIENT_SECRET is missing",
            technical_detail="BENTLEY_CLIENT_ID is set but BENTLEY_CLIENT_SECRET is absent.",
            recommended_fix="Add BENTLEY_CLIENT_SECRET to Replit Secrets.",
            error_class="missing_credentials",
        )
    return _result(
        ok=True,
        check_name="env_configuration",
        short_message="Both BENTLEY_CLIENT_ID and BENTLEY_CLIENT_SECRET are present",
        technical_detail=f"Client ID: {mask_client_id(cid)}",
    )


def mask_client_id(client_id: Optional[str]) -> str:
    """Return a safely masked version of the client ID (never log full value)."""
    if not client_id:
        return "(not set)"
    if len(client_id) <= 8:
        return "****"
    return client_id[:4] + "****" + client_id[-4:]


def check_webhook_security_state() -> Dict[str, Any]:
    """Audit webhook secret and signature verification settings."""
    secret_set = bool(settings.WEBHOOK_SECRET)
    sig_verify = not settings.SKIP_SIGNATURE_VERIFY
    is_prod = settings.ENVIRONMENT == "production"

    issues = []
    if not secret_set:
        issues.append("WEBHOOK_SECRET is not set — any caller can POST to /webhook")
    if not sig_verify:
        issues.append("SKIP_SIGNATURE_VERIFY=True — Bentley signatures are NOT checked")
    if is_prod and not secret_set:
        issues.append("CRITICAL: running in production without a webhook secret")
    if is_prod and not sig_verify:
        issues.append("CRITICAL: running in production with signature verification disabled")

    if issues:
        return _result(
            ok=False,
            check_name="webhook_security",
            short_message="; ".join(issues[:1]),
            technical_detail="\n".join(issues),
            recommended_fix=(
                "In Replit Secrets, set:\n"
                "  WEBHOOK_SECRET = a random 32-char string\n"
                "  SKIP_SIGNATURE_VERIFY = False\n"
                "Bentley will HMAC-SHA256 sign each delivery using this secret."
            ),
            error_class="webhook_secret_missing" if not secret_set else "signature_verification_disabled",
        )
    return _result(
        ok=True,
        check_name="webhook_security",
        short_message="Webhook secret set and signature verification enabled",
        technical_detail="Security posture is production-ready.",
    )


# ─── OAuth token test ─────────────────────────────────────────────────────────

async def test_oauth_token(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> Dict[str, Any]:
    """Attempt to obtain a Bentley OAuth token and classify any failure."""
    cid = client_id or settings.BENTLEY_CLIENT_ID
    csec = client_secret or settings.BENTLEY_CLIENT_SECRET
    scope = getattr(settings, "BENTLEY_SCOPE", "itwins:read imodels:read webhooks:read webhooks:modify")

    if not cid or not csec:
        return _result(
            ok=False,
            check_name="oauth_token",
            short_message="Cannot test OAuth — credentials missing",
            technical_detail="BENTLEY_CLIENT_ID or BENTLEY_CLIENT_SECRET is absent.",
            recommended_fix="Set both secrets in Replit Secrets.",
            error_class="missing_credentials",
        )

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{settings.BENTLEY_AUTHORITY}/connect/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": cid,
                    "client_secret": csec,
                    "scope": scope,
                },
            )
    except httpx.TimeoutException:
        return _result(
            ok=False,
            check_name="oauth_token",
            short_message="Connection to Bentley IMS timed out",
            technical_detail=f"POST {settings.BENTLEY_AUTHORITY}/connect/token timed out after 15s.",
            recommended_fix="Check network connectivity from this Repl. Try again in a few minutes.",
            error_class="token_request_failed",
            status_code=None,
        )
    except Exception as exc:
        return _result(
            ok=False,
            check_name="oauth_token",
            short_message="Network error reaching Bentley IMS",
            technical_detail=str(exc),
            recommended_fix="Verify the Bentley authority URL and outbound network access.",
            error_class="token_request_failed",
        )

    status = resp.status_code
    if status == 200:
        try:
            data = resp.json()
            token = data.get("access_token", "")
            expires_in = data.get("expires_in", "?")
            return _result(
                ok=True,
                check_name="oauth_token",
                short_message=f"OAuth token obtained (expires in {expires_in}s)",
                technical_detail=f"Scope granted: {data.get('scope', 'unknown')}. Token length: {len(token)}.",
                status_code=200,
            )
        except Exception:
            return _result(
                ok=False,
                check_name="oauth_token",
                short_message="Token response was not valid JSON",
                technical_detail=resp.text[:300],
                recommended_fix="Unexpected Bentley IMS response format.",
                error_class="token_request_failed",
                status_code=200,
            )

    # Parse error body
    try:
        err_body = resp.json()
        error_code = err_body.get("error", "")
        error_desc = err_body.get("error_description", "")
    except Exception:
        error_code = ""
        error_desc = resp.text[:300]

    if status == 400 and error_code == "invalid_client":
        return _result(
            ok=False,
            check_name="oauth_token",
            short_message="Invalid client — client ID not recognised by Bentley IMS",
            technical_detail=f"HTTP 400 invalid_client: {error_desc}",
            recommended_fix=(
                f"Verify BENTLEY_CLIENT_ID ({mask_client_id(cid)}) is the correct "
                "Service Application client ID from the Bentley Developer Portal."
            ),
            error_class="invalid_client",
            status_code=400,
        )
    if status == 401 or (status == 400 and "secret" in error_desc.lower()):
        return _result(
            ok=False,
            check_name="oauth_token",
            short_message="Invalid secret — authentication rejected",
            technical_detail=f"HTTP {status}: {error_desc}",
            recommended_fix=(
                "Generate a new client secret in the Bentley Developer Portal and "
                "update BENTLEY_CLIENT_SECRET in Replit Secrets."
            ),
            error_class="invalid_secret",
            status_code=status,
        )
    if status == 400 and "scope" in error_desc.lower():
        return _result(
            ok=False,
            check_name="oauth_token",
            short_message="One or more requested scopes are not allowed for this client",
            technical_detail=f"HTTP 400: {error_desc}",
            recommended_fix=(
                "In the Bentley Developer Portal, ensure your Service Application "
                "has these API permissions granted:\n"
                "  itwins:read  imodels:read  webhooks:read  webhooks:modify\n"
                "Or set BENTLEY_SCOPE in Replit Secrets to a narrower scope."
            ),
            error_class="insufficient_scope",
            status_code=400,
        )
    return _result(
        ok=False,
        check_name="oauth_token",
        short_message=f"OAuth failed — HTTP {status}",
        technical_detail=f"error={error_code!r}  description={error_desc!r}",
        recommended_fix="Check the Bentley Developer Portal for your application status.",
        error_class="unknown_error",
        status_code=status,
    )


# ─── iTwins access test ───────────────────────────────────────────────────────

async def test_itwins_access(token: Optional[str] = None) -> Dict[str, Any]:
    """Test whether the token can list iTwins."""
    if not token:
        token_result = await test_oauth_token()
        if not token_result["ok"]:
            return _result(
                ok=False,
                check_name="itwins_access",
                short_message="Skipped — OAuth token not available",
                technical_detail=token_result["short_message"],
                recommended_fix=token_result["recommended_fix"],
                error_class=token_result["error_class"],
            )
        # We can't return the token from the existing structure — re-obtain inline
        from app.services.bentley.client import get_access_token as _get
        token = await _get()
        if not token:
            return _result(
                ok=False,
                check_name="itwins_access",
                short_message="Could not obtain token for iTwins test",
                error_class="token_request_failed",
            )

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{settings.BENTLEY_API_BASE}/itwins",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.bentley.itwin-platform.v1+json",
                },
                params={"$top": 1},
            )
    except httpx.TimeoutException:
        return _result(
            ok=False,
            check_name="itwins_access",
            short_message="Request to iTwins API timed out",
            error_class="token_request_failed",
        )
    except Exception as exc:
        return _result(
            ok=False,
            check_name="itwins_access",
            short_message="Network error reaching iTwins API",
            technical_detail=str(exc),
            error_class="unknown_error",
        )

    status = resp.status_code
    if status == 200:
        data = resp.json()
        count = len(data.get("iTwins", []))
        return _result(
            ok=True,
            check_name="itwins_access",
            short_message=f"iTwins API accessible — {count} iTwin(s) visible to this service app",
            technical_detail=f"GET /itwins returned HTTP 200 with {count} result(s).",
            status_code=200,
        )
    if status == 401:
        return _result(
            ok=False,
            check_name="itwins_access",
            short_message="Token rejected by iTwins API (401)",
            technical_detail="The access token was not accepted. It may have expired or be malformed.",
            recommended_fix="Re-test OAuth first. If it succeeds, retry this test immediately.",
            error_class="invalid_client",
            status_code=401,
        )
    if status == 403:
        return _result(
            ok=False,
            check_name="itwins_access",
            short_message="Forbidden — service app lacks itwins:read permission",
            technical_detail="HTTP 403 from GET /itwins.",
            recommended_fix=(
                "In the Bentley Developer Portal, grant the 'itwins:read' API permission "
                "to your Service Application. Also confirm the service app identity has "
                "been invited to the target iTwin(s)."
            ),
            error_class="insufficient_itwin_access",
            status_code=403,
        )
    return _result(
        ok=False,
        check_name="itwins_access",
        short_message=f"Unexpected response from iTwins API — HTTP {status}",
        technical_detail=resp.text[:300],
        error_class="unknown_error",
        status_code=status,
    )


# ─── Webhooks access test ─────────────────────────────────────────────────────

async def test_webhooks_access(token: Optional[str] = None) -> Dict[str, Any]:
    """Test whether the token can list Bentley webhooks."""
    if not token:
        from app.services.bentley.client import get_access_token as _get
        token = await _get()
    if not token:
        return _result(
            ok=False,
            check_name="webhooks_access",
            short_message="Skipped — could not obtain OAuth token",
            error_class="token_request_failed",
        )

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{settings.BENTLEY_API_BASE}/webhooks",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.bentley.itwin-platform.v1+json",
                },
            )
    except httpx.TimeoutException:
        return _result(
            ok=False,
            check_name="webhooks_access",
            short_message="Request to Webhooks API timed out",
            error_class="token_request_failed",
        )
    except Exception as exc:
        return _result(
            ok=False,
            check_name="webhooks_access",
            short_message="Network error reaching Webhooks API",
            technical_detail=str(exc),
            error_class="unknown_error",
        )

    status = resp.status_code
    if status == 200:
        data = resp.json()
        count = len(data.get("webhooks", []))
        return _result(
            ok=True,
            check_name="webhooks_access",
            short_message=f"Webhooks API accessible — {count} webhook(s) registered",
            technical_detail=f"GET /webhooks returned HTTP 200 with {count} result(s).",
            status_code=200,
        )
    if status == 403:
        return _result(
            ok=False,
            check_name="webhooks_access",
            short_message="Forbidden — service app lacks webhooks:read permission",
            technical_detail="HTTP 403 from GET /webhooks.",
            recommended_fix=(
                "In the Bentley Developer Portal, grant 'webhooks:read' and 'webhooks:modify' "
                "API permissions to your Service Application."
            ),
            error_class="insufficient_webhook_permissions",
            status_code=403,
        )
    return _result(
        ok=False,
        check_name="webhooks_access",
        short_message=f"Unexpected response from Webhooks API — HTTP {status}",
        technical_detail=resp.text[:300],
        error_class="unknown_error",
        status_code=status,
    )


# ─── Callback URL ─────────────────────────────────────────────────────────────

def compute_callback_url(request=None) -> Dict[str, Any]:
    """Resolve the best public URL for the /webhook callback."""
    public = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
    dev_domain = os.environ.get("REPLIT_DEV_DOMAIN", "")
    replit_domain = os.environ.get("REPLIT_DOMAIN", "")

    if public:
        url = public + "/webhook"
        source = "PUBLIC_BASE_URL env var"
    elif replit_domain:
        url = f"https://{replit_domain}/webhook"
        source = "REPLIT_DOMAIN env var"
    elif dev_domain:
        url = f"https://{dev_domain}/webhook"
        source = "REPLIT_DEV_DOMAIN env var"
    elif request is not None:
        base = str(request.base_url).rstrip("/")
        url = base + "/webhook"
        source = "request.base_url fallback"
    else:
        url = "(unknown — set PUBLIC_BASE_URL)"
        source = "none"

    is_public = (url.startswith("https://") and ".replit." in url) or (
        public and not url.startswith("http://localhost")
    )

    ok = source != "none" and "unknown" not in url

    detail = f"Source: {source}"
    fix = ""
    if not ok or "localhost" in url:
        fix = (
            "Set PUBLIC_BASE_URL in Replit Secrets to your published app URL, e.g.:\n"
            "  PUBLIC_BASE_URL = https://myapp.replit.app\n"
            "Then provide this /webhook URL when registering in the Bentley Developer Portal."
        )

    return _result(
        ok=ok,
        check_name="callback_url",
        short_message=url,
        technical_detail=detail,
        recommended_fix=fix,
        error_class="" if ok else "callback_url_not_ready",
    )


# ─── Summary ──────────────────────────────────────────────────────────────────

async def summarize_bentley_readiness(request=None) -> Dict[str, Any]:
    """Run all local checks (no network) and return a summary."""
    env_check = check_env_configuration()
    sec_check = check_webhook_security_state()
    cb_check = compute_callback_url(request)

    is_prod = settings.ENVIRONMENT == "production"
    prod_warnings = []
    if is_prod and settings.SKIP_SIGNATURE_VERIFY:
        prod_warnings.append("SKIP_SIGNATURE_VERIFY is True in production")
    if is_prod and not settings.WEBHOOK_SECRET:
        prod_warnings.append("WEBHOOK_SECRET is missing in production")

    all_ok = env_check["ok"] and sec_check["ok"] and cb_check["ok"]
    checks = [env_check, sec_check, cb_check]
    failed = [c for c in checks if not c["ok"]]

    next_actions: List[str] = []
    if not env_check["ok"]:
        next_actions.append("Set BENTLEY_CLIENT_ID and BENTLEY_CLIENT_SECRET in Replit Secrets")
    elif not all_ok:
        next_actions.append("Run 'Test OAuth' to verify credentials")
    if not sec_check["ok"]:
        next_actions.append("Set WEBHOOK_SECRET and disable SKIP_SIGNATURE_VERIFY")
    if not cb_check["ok"]:
        next_actions.append("Set PUBLIC_BASE_URL to your deployed app URL")
    if all_ok:
        next_actions.append("Register the callback URL in the Bentley Developer Portal webhook settings")

    return {
        "all_ok": all_ok,
        "environment": settings.ENVIRONMENT,
        "is_production": is_prod,
        "production_warnings": prod_warnings,
        "checks": checks,
        "failed_count": len(failed),
        "next_actions": next_actions,
        "client_id_masked": mask_client_id(settings.BENTLEY_CLIENT_ID),
        "client_secret_present": bool(settings.BENTLEY_CLIENT_SECRET),
        "webhook_secret_present": bool(settings.WEBHOOK_SECRET),
        "signature_verify_enabled": not settings.SKIP_SIGNATURE_VERIFY,
        "callback_url": cb_check["short_message"],
    }
