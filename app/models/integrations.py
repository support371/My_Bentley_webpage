from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import uuid


class Integration(SQLModel, table=True):
    __tablename__ = "integrations"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    slug: str = Field(index=True)
    name: str
    category: str
    description: Optional[str] = None
    icon_emoji: Optional[str] = None
    icon_color: Optional[str] = None
    docs_url: Optional[str] = None

    status: str = Field(default="disconnected")
    is_enabled: bool = Field(default=False)

    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    webhook_url: Optional[str] = None
    base_url: Optional[str] = None
    custom_fields: Optional[str] = None

    last_tested_at: Optional[datetime] = None
    last_test_result: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
