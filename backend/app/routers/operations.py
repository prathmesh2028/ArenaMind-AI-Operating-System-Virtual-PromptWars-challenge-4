"""
Operations Center Router
-------------------------
High-level summary endpoints for operations managers and admins.

GET /operations/overview         — All active/mitigating incidents + sector summary
GET /operations/crowd/history    — Last N crowd metric snapshots per sector
GET /operations/transport        — Full transport status with all vehicles
GET /operations/energy           — Energy consumption across all grid zones
GET /operations/carbon           — Carbon emission summary with breakdown
GET /operations/users            — User roster (admin only)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_admin, require_operations
from app.database import get_db
from app.models import Carbon, CrowdMetric, Energy, Incident, Parking, Transport, User

logger = logging.getLogger("arenamind.routers.operations")
router = APIRouter(prefix="/operations", tags=["Operations Center"])


@router.get(
    "/overview",
    summary="Active incident + sector overview for operations managers",
)
def operations_overview(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_operations),
):
    # Active + mitigating incidents
    active_incidents = (
        db.query(Incident)
        .filter(Incident.status.in_(["ACTIVE", "MITIGATING"]))
        .order_by(Incident.priority.asc(), Incident.created_at.desc())
        .all()
    )

    # Latest crowd snapshot per sector
    subq = (
        db.query(CrowdMetric.sector, func.max(CrowdMetric.timestamp).label("max_ts"))
        .group_by(CrowdMetric.sector)
        .subquery()
    )
    sector_rows = (
        db.query(CrowdMetric)
        .join(subq, (CrowdMetric.sector == subq.c.sector) & (CrowdMetric.timestamp == subq.c.max_ts))
        .all()
    )

    return {
        "active_incident_count": len(active_incidents),
        "active_incidents": [
            {
                "id": str(i.id),
                "title": i.title,
                "status": i.status,
                "priority": i.priority,
                "sector": i.sector,
                "created_at": i.created_at.isoformat(),
            }
            for i in active_incidents
        ],
        "sectors": [
            {
                "sector": r.sector,
                "density": round(r.density * 100, 1),
                "count": r.count,
                "wait_time_seconds": r.wait_time_seconds,
                "velocity": r.velocity,
                "status": "CRITICAL" if r.density >= 0.95 else "WARNING" if r.density >= 0.85 else "NORMAL",
            }
            for r in sector_rows
        ],
    }


@router.get(
    "/crowd/history",
    summary="Historical crowd metrics per sector",
)
def crowd_history(
    sector: Optional[str] = Query(None, description="Filter by sector name"),
    limit: int = Query(100, ge=10, le=1000, description="Max records to return"),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_operations),
):
    query = db.query(CrowdMetric).order_by(CrowdMetric.timestamp.desc())
    if sector:
        query = query.filter(CrowdMetric.sector == sector)
    rows = query.limit(limit).all()

    return {
        "count": len(rows),
        "records": [
            {
                "sector": r.sector,
                "timestamp": r.timestamp.isoformat(),
                "count": r.count,
                "density": round(r.density * 100, 1),
                "velocity": r.velocity,
                "wait_time_seconds": r.wait_time_seconds,
            }
            for r in rows
        ],
    }


@router.get(
    "/transport",
    summary="Full transport fleet status",
)
def transport_status(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_operations),
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

    delayed = [r for r in rows if r.status == "DELAYED"]
    return {
        "total_vehicles": len(rows),
        "delayed_count": len(delayed),
        "vehicles": [
            {
                "vehicle_id": r.vehicle_id,
                "route": r.route_name,
                "type": r.type,
                "status": r.status,
                "occupancy_pct": r.occupancy_percentage,
                "current_stop": r.current_stop,
                "lat": r.latitude,
                "lon": r.longitude,
            }
            for r in rows
        ],
    }


@router.get(
    "/energy",
    summary="Energy consumption across all grid zones",
)
def energy_status(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_operations),
):
    subq = (
        db.query(Energy.grid_zone, func.max(Energy.timestamp).label("max_ts"))
        .group_by(Energy.grid_zone)
        .subquery()
    )
    rows = (
        db.query(Energy)
        .join(subq, (Energy.grid_zone == subq.c.grid_zone) & (Energy.timestamp == subq.c.max_ts))
        .all()
    )

    total_kw = sum(r.active_power_kw for r in rows)
    return {
        "total_active_power_kw": round(total_kw, 2),
        "zones": [
            {
                "zone": r.grid_zone,
                "active_power_kw": r.active_power_kw,
                "load_pct": r.load_percentage,
                "voltage": r.voltage,
                "carbon_offset_kg": r.carbon_offset_kg,
                "status": "HIGH_LOAD" if r.load_percentage >= 90 else "NORMAL",
            }
            for r in rows
        ],
    }


@router.get(
    "/carbon",
    summary="Carbon emission summary by source and category",
)
def carbon_summary(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_operations),
):
    rows = (
        db.query(
            Carbon.emission_source,
            Carbon.category,
            func.sum(Carbon.amount_kg).label("total_kg"),
        )
        .group_by(Carbon.emission_source, Carbon.category)
        .order_by(func.sum(Carbon.amount_kg).desc())
        .all()
    )

    by_category: dict = {}
    total = 0.0
    for row in rows:
        by_category.setdefault(row.category, 0.0)
        by_category[row.category] = round(by_category[row.category] + row.total_kg, 2)
        total += row.total_kg

    return {
        "total_kg": round(total, 2),
        "by_category": by_category,
        "by_source": [
            {"source": r.emission_source, "category": r.category, "total_kg": round(r.total_kg, 2)}
            for r in rows
        ],
    }


@router.get(
    "/users",
    summary="Stadium personnel user roster (admin only)",
)
def user_roster(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_admin),
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return {
        "total": len(users),
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "display_name": u.display_name,
                "role": u.role.name if u.role else None,
            }
            for u in users
        ],
    }
