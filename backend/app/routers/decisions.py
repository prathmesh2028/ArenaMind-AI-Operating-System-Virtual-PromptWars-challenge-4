"""
Decisions Router
-----------------
GET /decisions       — List decisions with paginated filter options
GET /decisions/{id}  — Fetch details of a single operations decision
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_staff
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models import Decision
from app.schemas.common import PaginatedResponse
from app.schemas.decisions import DecisionOut

logger = logging.getLogger("arenamind.routers.decisions")
router = APIRouter(prefix="/decisions", tags=["Decisions"])


@router.get(
    "",
    response_model=PaginatedResponse[DecisionOut],
    summary="List Decision Engine logs and mitigations",
)
def list_decisions(
    action_type: Optional[str] = Query(None, description="e.g. DISPATCH_VOLUNTEERS"),
    responsible_team: Optional[str] = Query(None, description="e.g. OPERATIONS"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_staff),
):
    query = db.query(Decision).order_by(Decision.created_at.desc())

    if action_type:
        query = query.filter(Decision.action_type == action_type)
    if responsible_team:
        query = query.filter(Decision.responsible_team == responsible_team)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=items)


@router.get(
    "/{decision_id}",
    response_model=DecisionOut,
    summary="Get single decision log details",
)
def get_decision(
    decision_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_staff),
):
    decision = db.query(Decision).filter(Decision.id == decision_id).first()
    if not decision:
        raise NotFoundError("Decision", decision_id)
    return decision
