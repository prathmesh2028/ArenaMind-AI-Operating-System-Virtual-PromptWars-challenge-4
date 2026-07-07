"""Incident schemas — CRUD + status transitions."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.common import OrmBase


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    description: Optional[str] = None
    priority: str = Field(default="MEDIUM", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    sector: str = Field(..., min_length=1, max_length=100)
    assignee_id: Optional[str] = None


class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(ACTIVE|MITIGATING|RESOLVED)$")
    priority: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    assignee_id: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_root_cause: Optional[str] = None
    ai_lessons_learned: Optional[str] = None


class IncidentOut(OrmBase):
    id: str
    title: str
    description: Optional[str]
    status: str
    priority: str
    sector: str
    reporter_id: Optional[str]
    assignee_id: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]
    ai_summary: Optional[str]
    ai_root_cause: Optional[str]
    ai_lessons_learned: Optional[str]
