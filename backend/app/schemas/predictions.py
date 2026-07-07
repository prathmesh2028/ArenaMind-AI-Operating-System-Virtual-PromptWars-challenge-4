"""Prediction and Recommendation schemas."""

from datetime import datetime
from typing import Any, Optional
from app.schemas.common import OrmBase


class RecommendationOut(OrmBase):
    id: str
    prediction_id: str
    title: str
    description: str
    confidence: float
    status: str
    created_at: datetime


class PredictionOut(OrmBase):
    id: str
    incident_id: Optional[str]
    type: str
    probability: float
    confidence: float
    severity: Optional[str] = None
    priority: Optional[str] = None
    reasoning: str
    predicted_outcome: Optional[str] = None
    suggested_actions: Any
    target_sector: str
    created_at: datetime
    recommendations: list[RecommendationOut] = []


class RecommendationUpdate(OrmBase):
    status: str  # ACCEPTED | REJECTED
