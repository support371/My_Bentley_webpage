from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text
from typing import Optional
from datetime import datetime
import uuid


class ITwin(SQLModel, table=True):
    __tablename__ = "itwins"

    id: str = Field(primary_key=True)
    tenant_id: Optional[str] = None
    display_name: Optional[str] = None
    number: Optional[str] = None
    type: Optional[str] = None
    subclass: Optional[str] = None
    status: Optional[str] = None
    class_: Optional[str] = Field(default=None, alias="class")
    raw_data: Optional[str] = Field(default=None, sa_column=Column(Text))
    last_event_at: Optional[datetime] = None
    synced_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class IModel(SQLModel, table=True):
    __tablename__ = "imodels"

    id: str = Field(primary_key=True)
    itwin_id: Optional[str] = Field(default=None, foreign_key="itwins.id")
    tenant_id: Optional[str] = None
    display_name: Optional[str] = None
    name: Optional[str] = None
    state: Optional[str] = None
    raw_data: Optional[str] = Field(default=None, sa_column=Column(Text))
    last_event_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AlertRule(SQLModel, table=True):
    __tablename__ = "alert_rules"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    tenant_id: Optional[str] = None
    rule_type: str = "event_type_match"
    conditions: Optional[str] = Field(default=None, sa_column=Column(Text))
    destinations: Optional[str] = Field(default=None, sa_column=Column(Text))
    is_active: bool = True
    muted_until: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Alert(SQLModel, table=True):
    __tablename__ = "alerts"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    rule_id: Optional[str] = Field(default=None, foreign_key="alert_rules.id")
    tenant_id: Optional[str] = None
    title: str
    message: Optional[str] = None
    severity: str = "info"
    status: str = "open"
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
