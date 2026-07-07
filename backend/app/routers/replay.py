"""
Replay Router
--------------
GET /replay/sessions                       — List all distinct replay sessions
GET /replay/sessions/{session_id}/events   — Events in a specific replay session
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_operations
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models import ReplayLog
from app.schemas.common import PaginatedResponse
from app.schemas.replay import ReplayEventOut, ReplaySessionSummary

logger = logging.getLogger("arenamind.routers.replay")
router = APIRouter(prefix="/replay", tags=["Replay"])


@router.get(
    "/sessions",
    response_model=list[ReplaySessionSummary],
    summary="List all available replay sessions",
    description="Returns one summary entry per distinct replay session ID, including event count and time range.",
)
def list_sessions(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_operations),
):
    rows = (
        db.query(
            ReplayLog.replay_session_id,
            func.count(ReplayLog.id).label("event_count"),
            func.min(ReplayLog.timestamp).label("first_event_at"),
            func.max(ReplayLog.timestamp).label("last_event_at"),
        )
        .group_by(ReplayLog.replay_session_id)
        .order_by(func.min(ReplayLog.timestamp).desc())
        .all()
    )

    return [
        ReplaySessionSummary(
            replay_session_id=row.replay_session_id,
            event_count=row.event_count,
            first_event_at=row.first_event_at,
            last_event_at=row.last_event_at,
        )
        for row in rows
    ]


@router.get(
    "/sessions/{session_id}/events",
    response_model=PaginatedResponse[ReplayEventOut],
    summary="Get all events in a replay session",
    description="Returns the full chronological event stream for a replay scenario. Use this to replay match-day scenarios step by step.",
)
def get_session_events(
    session_id: str,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_operations),
):
    query = (
        db.query(ReplayLog)
        .filter(ReplayLog.replay_session_id == session_id)
        .order_by(ReplayLog.timestamp.asc())
    )

    if event_type:
        query = query.filter(ReplayLog.event_type == event_type)

    total = query.count()
    if total == 0:
        raise NotFoundError("ReplaySession", session_id)

    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=items)
