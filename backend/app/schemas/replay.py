"""Replay session schemas."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel
from app.schemas.common import OrmBase


class ReplayEventOut(OrmBase):
    id: str
    replay_session_id: str
    timestamp: datetime
    event_type: str
    payload: Any
    created_at: datetime


class ReplaySessionSummary(BaseModel):
    """Aggregated metadata for a single replay session."""
    replay_session_id: str
    event_count: int
    first_event_at: datetime
    last_event_at: datetime
