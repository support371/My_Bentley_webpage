"""
Rules-based alert engine.
Evaluates incoming events against stored alert rules and dispatches notifications.
"""
import json
import logging
import httpx
from datetime import datetime
from typing import Optional

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
            await session.commit()

            destinations = json.loads(rule.destinations or "[]")
            for dest in destinations:
                await dispatch_alert(dest, alert, event)


async def dispatch_alert(dest: dict, alert: Alert, event: Event):
    dest_type = dest.get("type")
    if dest_type == "slack":
        await send_slack(dest.get("url"), alert, event)
    elif dest_type == "webhook":
        await send_generic_webhook(dest.get("url"), alert, event)
    else:
        logger.info(f"Alert triggered: {alert.title} (no dispatch configured)")


async def send_slack(url: Optional[str], alert: Alert, event: Event):
    if not url:
        return
    payload = {
        "text": f"*{alert.title}*\n{alert.message}\nEvent: `{event.event_type}` | iTwin: `{event.itwin_name or event.itwin_id or '-'}`"
    }
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.warning(f"Slack alert failed: {e}")


async def send_generic_webhook(url: Optional[str], alert: Alert, event: Event):
    if not url:
        return
    payload = {
        "alert_id": str(alert.id),
        "title": alert.title,
        "message": alert.message,
        "severity": alert.severity,
        "event_type": event.event_type,
        "triggered_at": alert.triggered_at.isoformat(),
    }
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.warning(f"Webhook alert failed: {e}")
