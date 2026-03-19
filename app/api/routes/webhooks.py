import json
import logging
from datetime import datetime
from fastapi import APIRouter, Request, BackgroundTasks, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import get_session
from app.core.security import verify_webhook_signature
from app.models.events import WebhookDelivery
from app.services.event_processor import process_webhook_event
from app.services.alerts.engine import evaluate_event
from app.schemas.events import WebhookIngestResponse

router = APIRouter()
logger = logging.getLogger("itwin_ops.webhook")


async def _process_in_background(raw_body: bytes, headers: dict, session: AsyncSession):
    try:
        event = await process_webhook_event(raw_body, headers, session)
        await evaluate_event(event, session)
    except Exception as e:
        logger.error(f"Background processing failed: {e}")


@router.post("/webhook", response_model=WebhookIngestResponse, tags=["Ingestion"])
async def ingest_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    raw_body = await request.body()
    headers = dict(request.headers)
    remote_ip = request.client.host if request.client else "unknown"

    sig = headers.get("signature") or headers.get("x-bentley-signature", "")
    sig_valid = verify_webhook_signature(raw_body, sig)

    delivery = WebhookDelivery(
        remote_ip=remote_ip,
        headers=json.dumps({k: v for k, v in headers.items() if k.lower() not in ("authorization",)}),
        raw_body=raw_body.decode("utf-8", errors="replace")[:10000],
        signature_valid=sig_valid,
        processing_status="received",
    )
    session.add(delivery)
    await session.commit()

    if not sig_valid:
        delivery.processing_status = "rejected"
        delivery.error_message = "Invalid signature"
        await session.commit()
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        data = json.loads(raw_body) if raw_body else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = await process_webhook_event(raw_body, headers, session)
    await evaluate_event(event, session)

    delivery.event_id = event.id
    delivery.processing_status = "processed"
    await session.commit()

    return WebhookIngestResponse(
        status="processed",
        event_id=event.id,
        event_type=event.event_type,
        timestamp=event.received_at.isoformat(),
        message_id=event.message_id,
    )
