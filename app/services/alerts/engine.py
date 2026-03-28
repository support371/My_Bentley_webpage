"""
Rules-based alert engine.
Evaluates incoming events against stored alert rules and dispatches notifications.
Supported destination types: slack, discord, email, pagerduty, webhook
"""
import asyncio
import json
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Optional

import httpx
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select

from app.models.events import Event
from app.models.resources import AlertRule, Alert

logger = logging.getLogger("itwin_ops.alerts")


async def evaluate_event(event: Event, session: AsyncSession):
    result = await session.execute(
        select(AlertRule).where(AlertRule.is_active == True)
    )
    rules = result.scalars().all()

    matched_alerts = []

    for rule in rules:
        if rule.muted_until and rule.muted_until > datetime.utcnow():
            continue
        try:
            conditions = json.loads(rule.conditions or "{}")
        except Exception:
            continue

        matched = False
        if rule.rule_type == "event_type_match":
            matched = event.event_type in (conditions.get("event_types") or [])
        elif rule.rule_type == "category_match":
            matched = event.event_category in (conditions.get("categories") or [])
        elif rule.rule_type == "severity_match":
            matched = event.severity in (conditions.get("severities") or [])

        if matched:
            alert = Alert(
                rule_id=rule.id,
                tenant_id=event.tenant_id,
                title=f"Alert: {rule.name}",
                message=f"Event {event.event_type} triggered rule '{rule.name}'",
                severity=event.severity,
            )
            session.add(alert)
            try:
                destinations = json.loads(rule.destinations or "[]")
            except Exception:
                destinations = []
            matched_alerts.append((alert, destinations))

    if not matched_alerts:
        return

    # Single commit for all matched alerts per event
    await session.commit()

    # Dispatch notifications after commit — failures here don't roll back alerts
    for alert, destinations in matched_alerts:
        for dest in destinations:
            try:
                await dispatch_alert(dest, alert, event)
            except Exception as e:
                logger.warning(f"Alert dispatch failed for {alert.id}: {e}")


async def dispatch_alert(dest: dict, alert: Alert, event: Event):
    dest_type = dest.get("type")
    try:
        if dest_type == "slack":
            await send_slack(dest.get("url"), alert, event)
        elif dest_type == "discord":
            await send_discord(dest.get("url"), alert, event)
        elif dest_type == "email":
            await send_email(dest, alert, event)
        elif dest_type == "pagerduty":
            await send_pagerduty(dest.get("routing_key"), alert, event)
        elif dest_type == "webhook":
            await send_generic_webhook(dest.get("url"), alert, event)
        else:
            logger.info(f"Alert triggered: {alert.title} (no dispatch configured for type '{dest_type}')")
    except Exception as e:
        logger.error(f"Alert dispatch failed [{dest_type}]: {e}")


# ── Slack ──────────────────────────────────────────────────────────────────────

async def send_slack(url: Optional[str], alert: Alert, event: Event):
    if not url:
        logger.warning("Slack dispatch skipped: no URL configured")
        return
    sev_emoji = {"error": "🔴", "warning": "🟡", "success": "🟢"}.get(alert.severity, "🔵")
    payload = {
        "text": f"{sev_emoji} *{alert.title}*",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"{sev_emoji} {alert.title}"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*Event Type:*\n`{event.event_type}`"},
                {"type": "mrkdwn", "text": f"*Severity:*\n{alert.severity}"},
                {"type": "mrkdwn", "text": f"*iTwin:*\n{event.itwin_name or event.itwin_id or '—'}"},
                {"type": "mrkdwn", "text": f"*Triggered:*\n{alert.triggered_at.strftime('%Y-%m-%d %H:%M UTC')}"},
            ]},
            {"type": "section", "text": {"type": "mrkdwn", "text": alert.message}},
        ],
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(url, json=payload, timeout=10)
        r.raise_for_status()
    logger.info(f"Slack alert sent: {alert.title}")


# ── Discord ────────────────────────────────────────────────────────────────────

async def send_discord(url: Optional[str], alert: Alert, event: Event):
    if not url:
        logger.warning("Discord dispatch skipped: no URL configured")
        return
    color_map = {"error": 0xef4444, "warning": 0xf59e0b, "success": 0x22c55e, "info": 0x3b82f6}
    color = color_map.get(alert.severity, 0x3b82f6)
    payload = {
        "embeds": [{
            "title": alert.title,
            "description": alert.message,
            "color": color,
            "fields": [
                {"name": "Event Type", "value": f"`{event.event_type}`", "inline": True},
                {"name": "Severity", "value": alert.severity, "inline": True},
                {"name": "iTwin", "value": event.itwin_name or event.itwin_id or "—", "inline": True},
            ],
            "footer": {"text": "Bentley iTwin Operations Center"},
            "timestamp": alert.triggered_at.isoformat() + "Z",
        }]
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(url, json=payload, timeout=10)
        r.raise_for_status()
    logger.info(f"Discord alert sent: {alert.title}")


# ── Email ──────────────────────────────────────────────────────────────────────

async def send_email(dest: dict, alert: Alert, event: Event):
    from app.core.config import settings

    smtp_host = dest.get("smtp_host") or settings.ALERT_EMAIL_SMTP
    smtp_port = int(dest.get("smtp_port") or settings.ALERT_EMAIL_PORT)
    smtp_user = dest.get("smtp_user") or settings.ALERT_EMAIL_USER
    smtp_pass = dest.get("smtp_pass") or settings.ALERT_EMAIL_PASS
    from_addr = dest.get("from") or settings.ALERT_EMAIL_FROM or smtp_user
    to_addr = dest.get("to")

    if not smtp_host or not to_addr:
        logger.warning(f"Email dispatch skipped: missing smtp_host or to address (host={smtp_host}, to={to_addr})")
        return

    sev_label = alert.severity.upper()
    subject = f"[{sev_label}] {alert.title}"
    body_html = f"""
    <html><body style="font-family:sans-serif;color:#0f172a;max-width:600px;margin:0 auto;">
      <div style="background:#3b82f6;color:#fff;padding:16px 24px;border-radius:8px 8px 0 0;">
        <h2 style="margin:0;">{alert.title}</h2>
      </div>
      <div style="border:1px solid #e2e8f0;border-top:none;padding:20px 24px;border-radius:0 0 8px 8px;">
        <p>{alert.message}</p>
        <table style="width:100%;border-collapse:collapse;margin-top:12px;">
          <tr><td style="padding:6px;border-bottom:1px solid #e2e8f0;font-weight:600;width:40%;">Event Type</td>
              <td style="padding:6px;border-bottom:1px solid #e2e8f0;font-family:monospace;">{event.event_type}</td></tr>
          <tr><td style="padding:6px;border-bottom:1px solid #e2e8f0;font-weight:600;">Severity</td>
              <td style="padding:6px;border-bottom:1px solid #e2e8f0;">{alert.severity}</td></tr>
          <tr><td style="padding:6px;border-bottom:1px solid #e2e8f0;font-weight:600;">iTwin</td>
              <td style="padding:6px;border-bottom:1px solid #e2e8f0;">{event.itwin_name or event.itwin_id or "—"}</td></tr>
          <tr><td style="padding:6px;font-weight:600;">Time</td>
              <td style="padding:6px;">{alert.triggered_at.strftime("%Y-%m-%d %H:%M UTC")}</td></tr>
        </table>
        <p style="color:#64748b;font-size:.85rem;margin-top:20px;">Bentley iTwin Operations Center</p>
      </div>
    </body></html>
    """

    def _send():
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg.attach(MIMEText(body_html, "html"))
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.ehlo()
            if smtp_port != 465:
                server.starttls()
                server.ehlo()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.sendmail(from_addr, [to_addr], msg.as_string())

    await asyncio.to_thread(_send)
    logger.info(f"Email alert sent to {to_addr}: {alert.title}")


# ── PagerDuty ─────────────────────────────────────────────────────────────────

async def send_pagerduty(routing_key: Optional[str], alert: Alert, event: Event):
    if not routing_key:
        logger.warning("PagerDuty dispatch skipped: no routing_key configured")
        return
    sev_map = {"error": "critical", "warning": "warning", "success": "info", "info": "info"}
    payload = {
        "routing_key": routing_key,
        "event_action": "trigger",
        "dedup_key": str(alert.id),
        "payload": {
            "summary": alert.title,
            "source": "Bentley iTwin Operations Center",
            "severity": sev_map.get(alert.severity, "info"),
            "custom_details": {
                "event_type": event.event_type,
                "itwin": event.itwin_name or event.itwin_id or "—",
                "message": alert.message,
            },
        },
    }
    async with httpx.AsyncClient() as client:
        r = await client.post("https://events.pagerduty.com/v2/enqueue", json=payload, timeout=15)
        r.raise_for_status()
    logger.info(f"PagerDuty alert sent: {alert.title}")


# ── Generic webhook ────────────────────────────────────────────────────────────

async def send_generic_webhook(url: Optional[str], alert: Alert, event: Event):
    if not url:
        logger.warning("Webhook dispatch skipped: no URL configured")
        return
    payload = {
        "alert_id": str(alert.id),
        "title": alert.title,
        "message": alert.message,
        "severity": alert.severity,
        "event_type": event.event_type,
        "itwin_id": event.itwin_id,
        "itwin_name": event.itwin_name,
        "triggered_at": alert.triggered_at.isoformat(),
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(url, json=payload, timeout=10)
        r.raise_for_status()
    logger.info(f"Webhook alert sent: {alert.title}")


# ── Test delivery ──────────────────────────────────────────────────────────────

async def test_delivery(dest: dict) -> dict:
    """Send a synthetic test alert to a destination config. Returns {ok, message}."""
    from datetime import datetime
    import uuid

    test_alert = Alert(
        id=str(uuid.uuid4()),
        rule_id=None,
        tenant_id=None,
        title="Test Alert: iTwin Ops Center",
        message="This is a test notification from Bentley iTwin Operations Center.",
        severity="info",
        triggered_at=datetime.utcnow(),
    )
    test_event = Event(
        id=str(uuid.uuid4()),
        event_type="test.notification.v1",
        event_category="Test",
        itwin_id="test-itwin-id",
        itwin_name="Test iTwin",
        severity="info",
        received_at=datetime.utcnow(),
    )
    try:
        await dispatch_alert(dest, test_alert, test_event)
        return {"ok": True, "message": f"Test {dest.get('type', 'notification')} sent successfully."}
    except Exception as e:
        return {"ok": False, "message": str(e)}
