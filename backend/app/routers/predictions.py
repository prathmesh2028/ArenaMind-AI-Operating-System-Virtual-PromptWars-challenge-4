"""
Predictions Router
-------------------
GET   /predictions                           — Paginated list with sector/type filters
GET   /predictions/{id}                      — Single prediction with recommendations
PATCH /predictions/{id}/recommendations/{r}  — Accept or reject a recommendation
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_operations, require_staff
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models import Prediction, Recommendation
from app.schemas.common import PaginatedResponse
from app.schemas.predictions import PredictionOut, RecommendationOut, RecommendationUpdate

logger = logging.getLogger("arenamind.routers.predictions")
router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get(
    "",
    response_model=PaginatedResponse[PredictionOut],
    summary="List AI predictions with filters",
)
def list_predictions(
    type: Optional[str] = Query(None, description="e.g. CROWD_CONGESTION"),
    sector: Optional[str] = Query(None),
    min_probability: float = Query(0.0, ge=0.0, le=1.0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_staff),
):
    query = db.query(Prediction).order_by(Prediction.created_at.desc())

    if type:
        query = query.filter(Prediction.type == type)
    if sector:
        query = query.filter(Prediction.target_sector == sector)
    if min_probability > 0:
        query = query.filter(Prediction.probability >= min_probability)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=items)


@router.get(
    "/{prediction_id}",
    response_model=PredictionOut,
    summary="Get a single prediction with its recommendations",
)
def get_prediction(
    prediction_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_staff),
):
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not prediction:
        raise NotFoundError("Prediction", prediction_id)
    return prediction


@router.patch(
    "/{prediction_id}/recommendations/{recommendation_id}",
    response_model=RecommendationOut,
    summary="Accept or reject an AI recommendation",
)
def update_recommendation(
    prediction_id: str,
    recommendation_id: str,
    payload: RecommendationUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_operations),
):
    rec = (
        db.query(Recommendation)
        .filter(
            Recommendation.id == recommendation_id,
            Recommendation.prediction_id == prediction_id,
        )
        .first()
    )
    if not rec:
        raise NotFoundError("Recommendation", recommendation_id)

    if payload.status not in ("ACCEPTED", "REJECTED"):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="status must be ACCEPTED or REJECTED",
        )

    rec.status = payload.status
    db.commit()
    db.refresh(rec)
    logger.info(f"Recommendation {recommendation_id} → {payload.status} by {current_user.email}")
    return rec
