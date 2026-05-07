from datetime import datetime
from typing import Optional, List, Dict, Any
import json
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text


VALID_STAGES = [
    "registration", "planning", "development",
    "review", "testing", "deployment", "complete"
]
VALID_PRIORITIES = ["Critical", "High", "Medium", "Low"]


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: str = Field(primary_key=True)
    title: str = Field(index=True)
    desc: Optional[str] = Field(default="", sa_column=Column(Text))
    stage: str = Field(default="registration", index=True)
    priority: str = Field(default="Medium")
    tags: Optional[str] = Field(default="[]", sa_column=Column(Text))
    assignee: Optional[str] = Field(default="")
    comments: Optional[str] = Field(default="[]", sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    def tags_list(self) -> List[str]:
        try:
            return json.loads(self.tags or "[]")
        except Exception:
            return []

    def comments_list(self) -> List[str]:
        try:
            return json.loads(self.comments or "[]")
        except Exception:
            return []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "desc": self.desc or "",
            "stage": self.stage,
            "priority": self.priority,
            "tags": self.tags_list(),
            "assignee": self.assignee or "",
            "comments": self.comments_list(),
            "created": self.created_at.strftime("%Y-%m-%d") if self.created_at else "",
            "updated": self.updated_at.strftime("%Y-%m-%d") if self.updated_at else "",
        }
