from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text
from typing import Optional
from datetime import datetime, timezone
import uuid


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    message_id: Optional[str] = Field(default=None, index=True)
    event_type: str = Field(index=True)
    event_category: str = Field(default="other", index=True)
    tenant_id: Optional[str] = Field(default=None, index=True)
    itwin_id: Optional[str] = Field(default=None, index=True)
    itwin_name: Optional[str] = None
    imodel_id: Optional[str] = Field(default=None, index=True)
    imodel_name: Optional[str] = None
    raw_payload: Optional[str] = Field(default=None, sa_column=Column(Text))
    normalized_payload: Optional[str] = Field(default=None, sa_column=Column(Text))
    source_webhook_id: Optional[str] = None
    processing_status: str = Field(default="processed")
    processing_error: Optional[str] = None
    severity: str = Field(default="info")
    received_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    event_timestamp: Optional[datetime] = None


class WebhookDelivery(SQLModel, table=True):
    __tablename__ = "webhook_deliveries"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    event_id: Optional[str] = None
    remote_ip: Optional[str] = None
    http_method: str = "POST"
    headers: Optional[str] = Field(default=None, sa_column=Column(Text))
    raw_body: Optional[str] = Field(default=None, sa_column=Column(Text))
    signature_valid: bool = True
    processing_status: str = "ok"
    error_message: Optional[str] = None
    received_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    detail: Optional[str] = Field(default=None, sa_column=Column(Text))
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
