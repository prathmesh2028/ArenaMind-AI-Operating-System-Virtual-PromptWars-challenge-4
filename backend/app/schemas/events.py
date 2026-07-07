"""Event schemas."""

from datetime import datetime
from typing import Any, Optional
from pydantic import Field
from app.schemas.common import OrmBase


class EventOut(OrmBase):
    """Raw event bus entry response."""
    id: str
    timestamp: datetime
    type: str
    source: str
    payload: Any


class EventListFilters(OrmBase):
    """Query filter params for events listing."""
    type: Optional[str] = None
    source: Optional[str] = None
    sector: Optional[str] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
