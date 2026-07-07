"""
Fan Portal Router
------------------
Read-only fan-facing endpoints accessible to all authenticated users.

GET /fan/crowd-status         — Live crowd density per sector
GET /fan/transport            — Live transport status
GET /fan/parking              — Live parking availability
GET /fan/notifications        — Fan's personal unread notifications
PATCH /fan/notifications/{id} — Mark a notification as read
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_current_user
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models import CrowdMetric, Notification, Parking, Transport
from app.schemas.dashboard import ParkingSnapshot, SectorSnapshot, TransportSnapshot

logger = logging.getLogger("arenamind.routers.fan")
router = APIRouter(prefix="/fan", tags=["Fan Portal"])


@router.get(
    "/crowd-status",
    summary="Live crowd density per stadium sector",
    description="Fan-safe view showing which sectors are busy. Color-coded: NORMAL, WARNING, or CRITICAL.",
)
def fan_crowd_status(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    subq = (
        db.query(CrowdMetric.sector, func.max(CrowdMetric.timestamp).label("max_ts"))
        .group_by(CrowdMetric.sector)
        .subquery()
    )
    rows = (
        db.query(CrowdMetric)
        .join(subq, (CrowdMetric.sector == subq.c.sector) & (CrowdMetric.timestamp == subq.c.max_ts))
        .all()
    )

    return {
        "sectors": [
            {
                "sector": r.sector,
                "status": "CRITICAL" if r.density >= 0.95 else "WARNING" if r.density >= 0.85 else "NORMAL",
                "wait_time_seconds": r.wait_time_seconds,
                "density_pct": round(r.density * 100, 1),
            }
            for r in rows
        ]
    }


@router.get(
    "/transport",
    summary="Live transport arrivals and shuttle status",
)
def fan_transport(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    subq = (
        db.query(Transport.vehicle_id, func.max(Transport.timestamp).label("max_ts"))
        .group_by(Transport.vehicle_id)
        .subquery()
    )
    rows = (
        db.query(Transport)
        .join(subq, (Transport.vehicle_id == subq.c.vehicle_id) & (Transport.timestamp == subq.c.max_ts))
        .all()
    )

    return {
        "vehicles": [
            {
                "route": r.route_name,
                "type": r.type,
                "status": r.status,
                "current_stop": r.current_stop,
                "seats_available": 100 - r.occupancy_percentage,
            }
            for r in rows
        ]
    }


@router.get(
    "/parking",
    summary="Live parking lot availability",
)
def fan_parking(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    subq = (
        db.query(Parking.lot_name, func.max(Parking.timestamp).label("max_ts"))
        .group_by(Parking.lot_name)
        .subquery()
    )
    rows = (
        db.query(Parking)
        .join(subq, (Parking.lot_name == subq.c.lot_name) & (Parking.timestamp == subq.c.max_ts))
        .all()
    )

    return {
        "parking_lots": [
            {
                "name": r.lot_name,
                "available_spots": r.total_spots - r.occupied_spots,
                "status": r.status,
                "occupancy_pct": r.occupancy_percentage,
            }
            for r in rows
        ]
    }


@router.get(
    "/notifications",
    summary="Get my personal notifications",
)
def fan_notifications(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    notifications = (
        db.query(Notification)
        .filter(Notification.recipient_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "unread_count": sum(1 for n in notifications if not n.read),
        "notifications": [
            {
                "id": str(n.id),
                "title": n.title,
                "message": n.message,
                "read": n.read,
                "priority": n.priority,
                "type": n.type,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ],
    }


@router.patch(
    "/notifications/{notification_id}/read",
    summary="Mark a notification as read",
)
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.recipient_id == current_user.id)
        .first()
    )
    if not notif:
        raise NotFoundError("Notification", notification_id)
    notif.read = True
    db.commit()
    return {"message": "Notification marked as read.", "id": notification_id}
