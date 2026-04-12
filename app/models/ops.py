from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid

class ControlPlaneModule(SQLModel, table=True):
    __tablename__ = "control_plane_modules"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    status: str
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LaunchCheck(SQLModel, table=True):
    __tablename__ = "launch_checks"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    label: str
    status: str
    detail: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
