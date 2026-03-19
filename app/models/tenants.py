from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid


class Tenant(SQLModel, table=True):
    __tablename__ = "tenants"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True)
    slug: str = Field(unique=True, index=True)
    bentley_client_id: Optional[str] = None
    bentley_client_secret_enc: Optional[str] = None
    webhook_secret: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
