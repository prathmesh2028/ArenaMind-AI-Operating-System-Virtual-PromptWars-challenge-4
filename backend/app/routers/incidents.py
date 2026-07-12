"""
Incidents Router
-----------------
GET    /incidents           — Paginated list with filters
POST   /incidents           — Create a new incident
GET    /incidents/{id}      — Single incident with predictions/tasks
PATCH  /incidents/{id}      — Update incident fields (status, priority, assignee)
DELETE /incidents/{id}      — Admin-only hard delete
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.deps import CurrentUser, require_operations, require_staff, require_admin, get_current_user
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models import Incident
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.incidents import IncidentCreate, IncidentOut, IncidentUpdate

logger = logging.getLogger("arenamind.routers.incidents")
router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get(
    "",
    response_model=PaginatedResponse[IncidentOut],
    summary="List incidents with optional filters",
)
def list_incidents(
    status: Optional[str] = Query(None, description="ACTIVE | MITIGATING | RESOLVED"),
    priority: Optional[str] = Query(None, description="LOW | MEDIUM | HIGH | CRITICAL"),
    sector: Optional[str] = Query(None),
    since: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_staff),
):
    query = db.query(Incident).order_by(Incident.created_at.desc())

    if status:
        query = query.filter(Incident.status == status)
    if priority:
        query = query.filter(Incident.priority == priority)
    if sector:
        query = query.filter(Incident.sector == sector)
    if since:
        query = query.filter(Incident.created_at >= since)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=items)


@router.post(
    "",
    response_model=IncidentOut,
    status_code=201,
    summary="Manually report a new incident",
)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    incident = Incident(
        id=__import__("uuid").uuid4().__str__(),
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        sector=payload.sector,
        status="ACTIVE",
        reporter_id=current_user.id,
        assignee_id=payload.assignee_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    logger.info(f"Incident created: {incident.id} by {current_user.email}")

    # Publish incident.raised to Event Bus so Decision Engine can react
    try:
        from app.bus.core import bus
        from app.bus.schemas import BusEvent
        bus.publish_sync(BusEvent(
            topic="INCIDENT_RAISED",
            source="router.incidents",
            sector=payload.sector,
            payload={
                "incident_id": incident.id,
                "sector": payload.sector,
                "priority": payload.priority,
                "incident_type": "MANUAL",
                "title": payload.title,
                "description": payload.description or ""
            }
        ))
    except Exception as e_bus:
        logger.warning(f"Failed to publish incident.raised for manual incident: {e_bus}")

    return incident


@router.get(
    "/{incident_id}",
    response_model=IncidentOut,
    summary="Get full incident detail",
)
def get_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_staff),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise NotFoundError("Incident", incident_id)
    return incident


@router.patch(
    "/{incident_id}",
    response_model=IncidentOut,
    summary="Update incident status, priority, or assignee",
)
def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_operations),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise NotFoundError("Incident", incident_id)

    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(incident, field, value)

    # Auto-set resolved_at if status transitions to RESOLVED
    if payload.status == "RESOLVED" and not incident.resolved_at:
        incident.resolved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(incident)
    logger.info(f"Incident {incident_id} updated by {current_user.email}: {update_data}")
    return incident


@router.delete(
    "/{incident_id}",
    response_model=MessageResponse,
    summary="Hard delete an incident (admin only)",
)
def delete_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_admin),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise NotFoundError("Incident", incident_id)

    db.delete(incident)
    db.commit()
    return MessageResponse(message=f"Incident {incident_id} permanently deleted.")
