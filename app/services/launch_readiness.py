"""
Platform launch-readiness service.
Evaluates every production blocker across: domain, Bentley creds, webhook security,
cookie security, database, alert routing, observability, and legal pages.

Each check returns a ReadinessItem dict. No network calls — purely config-based.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import settings


# ── Item shape ─────────────────────────────────────────────────────────────────

def _item(
    key: str,
    label: str,
    ok: bool,
    status: str,          # "ok" | "warning" | "error" | "info"
    detail: str,
    fix: str = "",
    category: str = "",
) -> Dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "ok": ok,
        "status": status,
        "detail": detail,
        "fix": fix,
        "category": category,
    }


# ── Individual checks ──────────────────────────────────────────────────────────

def check_domain() -> Dict[str, Any]:
    pub = (settings.PUBLIC_BASE_URL or "").strip()
    is_prod = settings.ENVIRONMENT == "production"

    if not pub:
        return _item(
            key="domain",
            label="Custom Domain",
            ok=False,
            status="warning",
            detail="PUBLIC_BASE_URL is not set. Webhook callback URLs will use fallback detection.",
            fix="Set PUBLIC_BASE_URL=https://your-domain.com in environment variables.",
            category="Infrastructure",
        )
    if "localhost" in pub or "127.0.0.1" in pub:
        return _item(
            key="domain",
            label="Custom Domain",
            ok=False,
            status="error" if is_prod else "warning",
            detail=f"PUBLIC_BASE_URL points to localhost ({pub}). Not suitable for production.",
            fix="Set PUBLIC_BASE_URL to a publicly reachable HTTPS URL.",
            category="Infrastructure",
        )
    if not pub.startswith("https://"):
        return _item(
            key="domain",
            label="Custom Domain",
            ok=False,
            status="warning",
            detail=f"PUBLIC_BASE_URL ({pub}) does not use HTTPS.",
            fix="Use an HTTPS URL for production. Bentley webhooks require HTTPS callback URLs.",
            category="Infrastructure",
        )
    return _item(
        key="domain",
        label="Custom Domain",
        ok=True,
        status="ok",
        detail=f"PUBLIC_BASE_URL: {pub}",
        category="Infrastructure",
    )


def check_bentley_credentials() -> Dict[str, Any]:
    cid = settings.BENTLEY_CLIENT_ID
    csec = settings.BENTLEY_CLIENT_SECRET
    if cid and csec:
        masked = cid[:4] + "****" + cid[-4:] if len(cid) > 8 else "****"
        return _item(
            key="bentley_creds",
            label="Bentley API Credentials",
            ok=True,
            status="ok",
            detail=f"BENTLEY_CLIENT_ID ({masked}) and BENTLEY_CLIENT_SECRET are set.",
            category="Bentley Integration",
        )
    missing = []
    if not cid:
        missing.append("BENTLEY_CLIENT_ID")
    if not csec:
        missing.append("BENTLEY_CLIENT_SECRET")
    return _item(
        key="bentley_creds",
        label="Bentley API Credentials",
        ok=False,
        status="error",
        detail=f"Missing: {', '.join(missing)}",
        fix="Add BENTLEY_CLIENT_ID and BENTLEY_CLIENT_SECRET from the Bentley Developer Portal.",
        category="Bentley Integration",
    )


def check_webhook_security() -> Dict[str, Any]:
    secret_set = bool(settings.WEBHOOK_SECRET)
    sig_ok = not settings.SKIP_SIGNATURE_VERIFY
    is_prod = settings.ENVIRONMENT == "production"

    if secret_set and sig_ok:
        return _item(
            key="webhook_security",
            label="Webhook Signature Verification",
            ok=True,
            status="ok",
            detail="WEBHOOK_SECRET is set and SKIP_SIGNATURE_VERIFY=False.",
            category="Security",
        )
    issues = []
    if not secret_set:
        issues.append("WEBHOOK_SECRET is not set")
    if not sig_ok:
        issues.append("SKIP_SIGNATURE_VERIFY=True (signatures not checked)")
    severity = "error" if is_prod else "warning"
    return _item(
        key="webhook_security",
        label="Webhook Signature Verification",
        ok=False,
        status=severity,
        detail="; ".join(issues),
        fix="Set WEBHOOK_SECRET to a random 32-char string. Set SKIP_SIGNATURE_VERIFY=False.",
        category="Security",
    )


def check_secret_key() -> Dict[str, Any]:
    key = settings.SECRET_KEY or ""
    default = "dev-secret-key-change-in-production"
    is_prod = settings.ENVIRONMENT == "production"

    if default in key:
        return _item(
            key="secret_key",
            label="JWT Secret Key",
            ok=False,
            status="error" if is_prod else "warning",
            detail="SECRET_KEY is using the default development value.",
            fix="Generate a random 64-char string and set it as SECRET_KEY.",
            category="Security",
        )
    if len(key) < 32:
        return _item(
            key="secret_key",
            label="JWT Secret Key",
            ok=False,
            status="warning",
            detail=f"SECRET_KEY is only {len(key)} chars (minimum recommended: 32).",
            fix="Use a longer random string for SECRET_KEY.",
            category="Security",
        )
    return _item(
        key="secret_key",
        label="JWT Secret Key",
        ok=True,
        status="ok",
        detail=f"SECRET_KEY is set ({len(key)} chars).",
        category="Security",
    )


def check_cookie_security() -> Dict[str, Any]:
    is_prod = settings.ENVIRONMENT == "production"
    if settings.COOKIE_SECURE:
        return _item(
            key="cookie_secure",
            label="Secure Cookie Flag",
            ok=True,
            status="ok",
            detail="COOKIE_SECURE=True — session cookies require HTTPS.",
            category="Security",
        )
    return _item(
        key="cookie_secure",
        label="Secure Cookie Flag",
        ok=False,
        status="error" if is_prod else "warning",
        detail="COOKIE_SECURE=False — cookies can be transmitted over HTTP.",
        fix="Set COOKIE_SECURE=True in production to prevent cookie theft.",
        category="Security",
    )


def check_database() -> Dict[str, Any]:
    db_url = settings.DATABASE_URL or ""
    is_prod = settings.ENVIRONMENT == "production"

    if not db_url:
        return _item(
            key="database",
            label="Database",
            ok=False,
            status="error",
            detail="DATABASE_URL is not set.",
            fix="Set DATABASE_URL to a PostgreSQL connection string for production.",
            category="Infrastructure",
        )
    if "sqlite" in db_url:
        return _item(
            key="database",
            label="Database",
            ok=not is_prod,
            status="warning" if not is_prod else "error",
            detail="Using SQLite — data does not persist across restarts in some environments.",
            fix="Set DATABASE_URL to a PostgreSQL connection string for production.",
            category="Infrastructure",
        )
    masked = db_url.split("@")[-1] if "@" in db_url else db_url
    return _item(
        key="database",
        label="Database",
        ok=True,
        status="ok",
        detail=f"PostgreSQL configured: {masked}",
        category="Infrastructure",
    )


def check_alert_routing() -> Dict[str, Any]:
    smtp = getattr(settings, "ALERT_EMAIL_SMTP", "") or ""
    if smtp:
        return _item(
            key="alert_routing",
            label="Admin Alert Routing",
            ok=True,
            status="ok",
            detail=f"Email alerts configured via {smtp}.",
            category="Alerting",
        )
    return _item(
        key="alert_routing",
        label="Admin Alert Routing",
        ok=False,
        status="info",
        detail="No email SMTP configured. Alerts can still be delivered via Slack, Discord, PagerDuty, or webhook.",
        fix="Set ALERT_EMAIL_SMTP, ALERT_EMAIL_USER, ALERT_EMAIL_PASS if you want email alerts.",
        category="Alerting",
    )


def check_environment() -> Dict[str, Any]:
    env = settings.ENVIRONMENT
    if env == "production":
        return _item(
            key="environment",
            label="Environment",
            ok=True,
            status="ok",
            detail="ENVIRONMENT=production",
            category="Infrastructure",
        )
    return _item(
        key="environment",
        label="Environment",
        ok=False,
        status="warning",
        detail=f"ENVIRONMENT={env}. Some security defaults are relaxed in non-production mode.",
        fix="Set ENVIRONMENT=production when deploying to production.",
        category="Infrastructure",
    )


def check_observability() -> Dict[str, Any]:
    # Check for common observability env vars (Sentry, Datadog, etc.)
    sentry_dsn = getattr(settings, "SENTRY_DSN", None) or ""
    dd_key = getattr(settings, "DD_API_KEY", None) or ""

    if sentry_dsn or dd_key:
        provider = "Sentry" if sentry_dsn else "Datadog"
        return _item(
            key="observability",
            label="Observability / Error Tracking",
            ok=True,
            status="ok",
            detail=f"{provider} configured.",
            category="Observability",
        )
    return _item(
        key="observability",
        label="Observability / Error Tracking",
        ok=False,
        status="info",
        detail="No observability provider configured (Sentry, Datadog, etc.).",
        fix="Add SENTRY_DSN or integrate with a logging/monitoring backend for production error tracking.",
        category="Observability",
    )


def check_rate_limiting() -> Dict[str, Any]:
    limit = getattr(settings, "RATE_LIMIT_PER_MINUTE", 0)
    if limit and int(limit) > 0:
        return _item(
            key="rate_limiting",
            label="Webhook Rate Limiting",
            ok=True,
            status="ok",
            detail=f"Rate limit: {limit} requests/minute per IP on /webhook.",
            category="Security",
        )
    return _item(
        key="rate_limiting",
        label="Webhook Rate Limiting",
        ok=False,
        status="warning",
        detail="RATE_LIMIT_PER_MINUTE is zero or not set — /webhook has no rate limit.",
        fix="Set RATE_LIMIT_PER_MINUTE in config (default 60).",
        category="Security",
    )


# ── Summary ────────────────────────────────────────────────────────────────────

def get_launch_readiness() -> Dict[str, Any]:
    """Run all launch-readiness checks and return a structured summary."""
    checks = [
        check_environment(),
        check_domain(),
        check_bentley_credentials(),
        check_webhook_security(),
        check_secret_key(),
        check_cookie_security(),
        check_database(),
        check_alert_routing(),
        check_rate_limiting(),
        check_observability(),
    ]

    errors = [c for c in checks if c["status"] == "error"]
    warnings = [c for c in checks if c["status"] == "warning"]
    ok_count = len([c for c in checks if c["status"] == "ok"])
    info_count = len([c for c in checks if c["status"] == "info"])

    if errors:
        overall = "not_ready"
    elif warnings:
        overall = "ready_with_warnings"
    else:
        overall = "ready"

    # Group by category
    categories: Dict[str, List] = {}
    for c in checks:
        cat = c["category"] or "Other"
        categories.setdefault(cat, []).append(c)

    return {
        "overall": overall,
        "environment": settings.ENVIRONMENT,
        "is_production": settings.ENVIRONMENT == "production",
        "summary": {
            "total": len(checks),
            "ok": ok_count,
            "warnings": len(warnings),
            "errors": len(errors),
            "info": info_count,
        },
        "checks": checks,
        "by_category": categories,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
