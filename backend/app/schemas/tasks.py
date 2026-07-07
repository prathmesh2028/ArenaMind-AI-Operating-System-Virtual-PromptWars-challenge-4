"""Task schemas — volunteer dispatch & status management."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.common import OrmBase


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    priority: str = Field(default="MEDIUM", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    incident_id: str
    volunteer_id: Optional[str] = None
    eta_minutes: Optional[int] = Field(None, ge=1, le=480)


class TaskUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(PENDING|ACCEPTED|COMPLETED)$")
    volunteer_id: Optional[str] = None
    eta_minutes: Optional[int] = Field(None, ge=1, le=480)


class TaskOut(OrmBase):
    id: str
    title: str
    description: Optional[str]
    status: str
    priority: str
    incident_id: str
    volunteer_id: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    eta_minutes: Optional[int]
