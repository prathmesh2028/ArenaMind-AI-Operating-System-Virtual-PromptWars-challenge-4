from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, BigInteger, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=True)
    role = Column(String(50), nullable=False)  # ADMIN, OPERATIONS, VOLUNTEER, MEDICAL, SECURITY, FAN
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    reported_incidents = relationship("Incident", foreign_keys="[Incident.reporter_id]", back_populates="reporter")
    assigned_incidents = relationship("Incident", foreign_keys="[Incident.assignee_id]", back_populates="assignee")
    tasks = relationship("Task", back_populates="volunteer")


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    type = Column(String(100), nullable=False, index=True)
    source = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    status = Column(String(50), nullable=False, default="ACTIVE", index=True)  # ACTIVE, MITIGATING, RESOLVED
    priority = Column(String(50), nullable=False, default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    sector = Column(String(100), nullable=False)
    
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    ai_summary = Column(String, nullable=True)
    ai_root_cause = Column(String, nullable=True)
    ai_lessons_learned = Column(String, nullable=True)

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reported_incidents")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_incidents")
    tasks = relationship("Task", back_populates="incident", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING", index=True)  # PENDING, ACCEPTED, COMPLETED
    priority = Column(String(50), nullable=False, default="MEDIUM")
    
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    volunteer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    eta_minutes = Column(Integer, nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="tasks")
    volunteer = relationship("User", back_populates="tasks")


class TelemetryLog(Base):
    __tablename__ = "telemetry_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    metric_type = Column(String(100), nullable=False, index=True)  # CROWD_DENSITY, WATER_USAGE, POWER_LOAD, TRANSIT_GPS
    sector = Column(String(100), nullable=False)
    value = Column(JSON, nullable=False)
