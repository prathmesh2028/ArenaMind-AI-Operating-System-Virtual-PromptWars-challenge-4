from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, BigInteger, Float, Boolean, JSON, func, Table
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False, index=True)  # ADMIN, OPERATIONS, VOLUNTEER, MEDICAL, SECURITY, FAN
    description = Column(String(255), nullable=True)

    # Relationships
    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    role = relationship("Role", back_populates="users")
    reported_incidents = relationship("Incident", foreign_keys="[Incident.reporter_id]", back_populates="reporter")
    assigned_incidents = relationship("Incident", foreign_keys="[Incident.assignee_id]", back_populates="assignee")
    tasks = relationship("Task", back_populates="volunteer")
    notifications = relationship("Notification", back_populates="recipient", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    type = Column(String(100), nullable=False, index=True)  # GATE_CONGESTION, MEDICAL_ALERT, etc.
    source = Column(String(100), nullable=False, index=True)
    payload = Column(JSON, nullable=False)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    status = Column(String(50), nullable=False, default="ACTIVE", index=True)  # ACTIVE, MITIGATING, RESOLVED
    priority = Column(String(50), nullable=False, default="MEDIUM", index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    sector = Column(String(100), nullable=False, index=True)
    
    reporter_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assignee_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    ai_summary = Column(String, nullable=True)
    ai_root_cause = Column(String, nullable=True)
    ai_lessons_learned = Column(String, nullable=True)

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reported_incidents")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_incidents")
    tasks = relationship("Task", back_populates="incident", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="incident", cascade="all, delete-orphan")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True, index=True)
    type = Column(String(100), nullable=False, index=True)  # CROWD_CONGESTION, TRANSPORT_DELAY, etc.
    probability = Column(Float, nullable=False)  # 0.0 to 1.0
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    severity = Column(String(50), nullable=True)  # LOW, MEDIUM, HIGH, CRITICAL
    priority = Column(String(50), nullable=True)  # LOW, MEDIUM, HIGH, CRITICAL
    reasoning = Column(String, nullable=False)
    predicted_outcome = Column(String, nullable=True)
    suggested_actions = Column(JSON, nullable=False)
    target_sector = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    incident = relationship("Incident", back_populates="predictions")
    recommendations = relationship("Recommendation", back_populates="prediction", cascade="all, delete-orphan")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prediction_id = Column(String(36), ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    status = Column(String(50), nullable=False, default="PENDING", index=True)  # PENDING, ACCEPTED, REJECTED
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    prediction = relationship("Prediction", back_populates="recommendations")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    status = Column(String(50), nullable=False, default="PENDING", index=True)  # PENDING, ACCEPTED, COMPLETED
    priority = Column(String(50), nullable=False, default="MEDIUM", index=True)
    
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    volunteer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    eta_minutes = Column(Integer, nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="tasks")
    volunteer = relationship("User", back_populates="tasks")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(String, nullable=False)
    read = Column(Boolean, default=False, nullable=False, index=True)
    priority = Column(String(50), nullable=False, default="MEDIUM", index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    type = Column(String(100), nullable=False, index=True)  # SYSTEM, TASK_ASSIGNMENT, INCIDENT_ALERT
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    recipient = relationship("User", back_populates="notifications")


# --- TELEMETRY & DIGITAL TWIN STRUCTURAL TABLES ---

class CrowdMetric(Base):
    __tablename__ = "crowd_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    sector = Column(String(100), nullable=False, index=True)
    count = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False)
    density = Column(Float, nullable=False)  # count / capacity
    velocity = Column(Float, nullable=False)  # average movement speed
    wait_time_seconds = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class Transport(Base):
    __tablename__ = "transport"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    route_name = Column(String(100), nullable=False, index=True)
    vehicle_id = Column(String(100), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # SHUTTLE, BUS, TRAIN
    status = Column(String(50), nullable=False, default="ON_TIME", index=True)  # ON_TIME, DELAYED
    current_stop = Column(String(100), nullable=True)
    occupancy_percentage = Column(Integer, nullable=False)  # 0 to 100
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class Parking(Base):
    __tablename__ = "parking"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    lot_name = Column(String(100), nullable=False, index=True)
    total_spots = Column(Integer, nullable=False)
    occupied_spots = Column(Integer, nullable=False)
    occupancy_percentage = Column(Integer, nullable=False)  # 0 to 100
    status = Column(String(50), nullable=False, default="OPEN", index=True)  # OPEN, FULL
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class Energy(Base):
    __tablename__ = "energy"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    grid_zone = Column(String(100), nullable=False, index=True)
    active_power_kw = Column(Float, nullable=False)
    reactive_power_kvar = Column(Float, nullable=False)
    voltage = Column(Float, nullable=False)
    load_percentage = Column(Float, nullable=False)
    carbon_offset_kg = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class Carbon(Base):
    __tablename__ = "carbon"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    emission_source = Column(String(100), nullable=False, index=True)  # GRID_ENERGY, SHUTTLE_DIESEL, etc.
    amount_kg = Column(Float, nullable=False)
    category = Column(String(100), nullable=False, index=True)  # ENERGY, TRANSPORT, FOOD_WASTE
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class ReplayLog(Base):
    __tablename__ = "replay_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    replay_session_id = Column(String(36), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    sector = Column(String(100), nullable=False, index=True)
    value = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prediction_id = Column(String(36), ForeignKey("predictions.id", ondelete="SET NULL"), nullable=True, index=True)
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    decision = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    expected_impact = Column(String, nullable=False)
    responsible_team = Column(String(100), nullable=False)  # OPERATIONS, MEDICAL, SECURITY, VOLUNTEER, etc.
    eta = Column(String(50), nullable=False)  # e.g. "3 minutes", "10 minutes"
    action_type = Column(String(100), nullable=False, index=True)  # DISPATCH_VOLUNTEERS, OPEN_GATES, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    prediction = relationship("Prediction")
    incident = relationship("Incident")
