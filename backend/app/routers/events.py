"""
Events Router
--------------
GET /events           — Paginated event bus log with filters
GET /events/{id}      — Single event detail
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_staff
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models import Event
from app.schemas.common import PaginatedResponse
from app.schemas.events import EventOut

logger = logging.getLogger("arenamind.routers.events")
router = APIRouter(prefix="/events", tags=["Events"])


@router.get(
    "",
    response_model=PaginatedResponse[EventOut],
    summary="List raw event bus entries",
    description="Returns a chronologically ordered, paginated list of all raw events emitted by the Digital Twin and other sources.",
)
def list_events(
    type: Optional[str] = Query(None, description="Filter by event type, e.g. CROWD_TICK"),
    source: Optional[str] = Query(None, description="Filter by source, e.g. digital_twin"),
    since: Optional[datetime] = Query(None, description="ISO datetime lower bound"),
    until: Optional[datetime] = Query(None, description="ISO datetime upper bound"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_staff),
):
    query = db.query(Event).order_by(Event.timestamp.desc())

    if type:
        query = query.filter(Event.type == type)
    if source:
        query = query.filter(Event.source == source)
    if since:
        query = query.filter(Event.timestamp >= since)
    if until:
        query = query.filter(Event.timestamp <= until)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedResponse(total=total, page=page, page_size=page_size, items=items)


@router.get(
    "/{event_id}",
    response_model=EventOut,
    summary="Get a single event by ID",
)
def get_event(
    event_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_staff),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise NotFoundError("Event", event_id)
    return event
