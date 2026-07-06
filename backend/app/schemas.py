from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    display_name: Optional[str] = None
    role: str

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# Event Schemas
class EventBase(BaseModel):
    timestamp: datetime
    type: str
    source: str
    payload: Dict[str, Any]

class EventResponse(EventBase):
    id: UUID

    class Config:
        from_attributes = True

# Task Schemas
class TaskBase(BaseModel):
    title: str
    status: str = "PENDING"
    priority: str = "MEDIUM"
    incident_id: UUID
    volunteer_id: Optional[UUID] = None
    eta_minutes: Optional[int] = None

class TaskResponse(TaskBase):
    id: UUID
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Incident Schemas
class IncidentBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "ACTIVE"
    priority: str = "MEDIUM"
    sector: str
    reporter_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None

class IncidentResponse(IncidentBase):
    id: UUID
    created_at: datetime
    resolved_at: Optional[datetime] = None
    ai_summary: Optional[str] = None
    ai_root_cause: Optional[str] = None
    ai_lessons_learned: Optional[str] = None
    tasks: List[TaskResponse] = []

    class Config:
        from_attributes = True

# Telemetry Log Schemas
class TelemetryLogBase(BaseModel):
    timestamp: datetime
    metric_type: str
    sector: str
    value: Dict[str, Any]

class TelemetryLogResponse(TelemetryLogBase):
    id: int

    class Config:
        from_attributes = True
