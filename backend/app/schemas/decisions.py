"""Decision schemas."""

from datetime import datetime
from typing import Optional
from app.schemas.common import OrmBase


class DecisionOut(OrmBase):
    id: str
    prediction_id: Optional[str]
    incident_id: Optional[str]
    decision: str
    reason: str
    expected_impact: str
    responsible_team: str
    eta: str
    action_type: str
    created_at: datetime
