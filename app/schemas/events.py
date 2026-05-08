from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str
    event_category: str
    itwin_id: Optional[str] = None
    itwin_name: Optional[str] = None
    imodel_id: Optional[str] = None
    imodel_name: Optional[str] = None
    severity: str
    processing_status: str
    received_at: datetime
    event_timestamp: Optional[datetime] = None


class EventsResponse(BaseModel):
    events: List[EventOut]
    total: int
    page: int
    page_size: int


class DashboardFeedResponse(BaseModel):
    meta: Dict[str, Any]
    kpis: Dict[str, Any]
    health: str
    recentEvents: List[Dict[str, Any]]
    insights: str
    eventTypeBreakdown: Dict[str, int]
    categoryBreakdown: Dict[str, int]


class WebhookIngestResponse(BaseModel):
    status: str
    event_id: Optional[str] = None
    event_type: Optional[str] = None
    timestamp: str
    message_id: Optional[str] = None
