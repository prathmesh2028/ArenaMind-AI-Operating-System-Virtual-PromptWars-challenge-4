"""
Dashboard Router
-----------------
GET /dashboard — Comprehensive real-time stadium operations snapshot.

Aggregates data from the Digital Twin state + DB into a single payload
designed to power the Operations Command Center frontend.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from app.bus.schemas import BusEvent
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_staff
from app.database import get_db
from app.engine.twin import get_twin_status
from app.models import CrowdMetric, Energy, Incident, Notification, Parking, Transport
from app.schemas.dashboard import (
    CarbonSnapshot,
    DashboardResponse,
    EnergySnapshot,
    IncidentSummary,
    ParkingSnapshot,
    SectorSnapshot,
    TransportSnapshot,
)

logger = logging.getLogger("arenamind.routers.dashboard")
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

SECTOR_CAPACITY = 8000


def _latest_crowd_metrics(db: Session) -> list[SectorSnapshot]:
    """Return the most recent crowd metric per sector."""
    subquery = (
        db.query(
            CrowdMetric.sector,
            func.max(CrowdMetric.timestamp).label("max_ts"),
        )
        .group_by(CrowdMetric.sector)
        .subquery()
    )
    rows = (
        db.query(CrowdMetric)
        .join(
            subquery,
            (CrowdMetric.sector == subquery.c.sector)
            & (CrowdMetric.timestamp == subquery.c.max_ts),
        )
        .all()
    )

    snapshots = []
    for row in rows:
        if row.density >= 0.95:
            status = "CRITICAL"
        elif row.density >= 0.85:
            status = "WARNING"
        else:
            status = "NORMAL"

        snapshots.append(
            SectorSnapshot(
                sector=row.sector,
                count=row.count,
                capacity=row.capacity,
                density=row.density,
                status=status,
            )
        )
    return snapshots


def _latest_parking(db: Session) -> list[ParkingSnapshot]:
    subquery = (
        db.query(
            Parking.lot_name,
            func.max(Parking.timestamp).label("max_ts"),
        )
        .group_by(Parking.lot_name)
        .subquery()
    )
    rows = (
        db.query(Parking)
        .join(
            subquery,
            (Parking.lot_name == subquery.c.lot_name)
            & (Parking.timestamp == subquery.c.max_ts),
        )
        .all()
    )
    return [
        ParkingSnapshot(
            lot_name=r.lot_name,
            total_spots=r.total_spots,
            occupied_spots=r.occupied_spots,
            occupancy_percentage=r.occupancy_percentage,
            status=r.status,
        )
        for r in rows
    ]


def _latest_transport(db: Session) -> list[TransportSnapshot]:
    subquery = (
        db.query(
            Transport.vehicle_id,
            func.max(Transport.timestamp).label("max_ts"),
        )
        .group_by(Transport.vehicle_id)
        .subquery()
    )
    rows = (
        db.query(Transport)
        .join(
            subquery,
            (Transport.vehicle_id == subquery.c.vehicle_id)
            & (Transport.timestamp == subquery.c.max_ts),
        )
        .all()
    )
    return [
        TransportSnapshot(
            vehicle_id=r.vehicle_id,
            route_name=r.route_name,
            type=r.type,
            status=r.status,
            occupancy_percentage=r.occupancy_percentage,
            latitude=r.latitude,
            longitude=r.longitude,
            current_stop=r.current_stop,
        )
        for r in rows
    ]


def _latest_energy(db: Session) -> list[EnergySnapshot]:
    subquery = (
        db.query(
            Energy.grid_zone,
            func.max(Energy.timestamp).label("max_ts"),
        )
        .group_by(Energy.grid_zone)
        .subquery()
    )
    rows = (
        db.query(Energy)
        .join(
            subquery,
            (Energy.grid_zone == subquery.c.grid_zone)
            & (Energy.timestamp == subquery.c.max_ts),
        )
        .all()
    )
    return [
        EnergySnapshot(
            grid_zone=r.grid_zone,
            active_power_kw=r.active_power_kw,
            load_percentage=r.load_percentage,
        )
        for r in rows
    ]


def _carbon_summary(db: Session) -> CarbonSnapshot:
    from app.models import Carbon
    from sqlalchemy import func as f

    rows = (
        db.query(Carbon.category, f.sum(Carbon.amount_kg).label("total"))
        .group_by(Carbon.category)
        .all()
    )
    by_cat = {r.category: round(r.total, 2) for r in rows}
    return CarbonSnapshot(
        total_kg=round(sum(by_cat.values()), 2),
        by_category=by_cat,
    )


@router.get(
    "",
    response_model=DashboardResponse,
    summary="Complete real-time stadium operations dashboard",
    description=(
        "Single endpoint that returns the full stadium operations snapshot: "
        "crowd metrics, incidents, transport, parking, energy, carbon, and twin status."
    ),
)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_staff),
):
    # Incident counts
    incident_counts = (
        db.query(Incident.status, func.count(Incident.id))
        .group_by(Incident.status)
        .all()
    )
    status_map = {s: c for s, c in incident_counts}
    critical_count = (
        db.query(func.count(Incident.id))
        .filter(Incident.priority == "CRITICAL", Incident.status != "RESOLVED")
        .scalar()
    )
    unread = (
        db.query(func.count(Notification.id))
        .filter(Notification.read == False)
        .scalar()
    )

    return DashboardResponse(
        timestamp=datetime.now(timezone.utc).isoformat(),
        twin_status=get_twin_status(),
        incidents=IncidentSummary(
            total=sum(status_map.values()),
            active=status_map.get("ACTIVE", 0),
            mitigating=status_map.get("MITIGATING", 0),
            resolved=status_map.get("RESOLVED", 0),
            critical=critical_count or 0,
        ),
        sectors=_latest_crowd_metrics(db),
        parking=_latest_parking(db),
        transport=_latest_transport(db),
        energy=_latest_energy(db),
        carbon=_carbon_summary(db),
        unread_notifications=unread or 0,
    )


@router.websocket("/ws")
async def dashboard_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates.
    Streams events from the global EventBus to the client.
    """
    await websocket.accept()
    client_id = f"ws_dash_{uuid.uuid4().hex}"
    queue = asyncio.Queue()

    async def event_handler(event: BusEvent):
        try:
            await queue.put(event.to_dict())
        except Exception as e:
            logger.warning(f"[WS] Failed to queue event for {client_id}: {e}")

    from app.bus.core import bus
    bus.subscribe("*", event_handler, name=client_id)
    logger.info(f"[WS] Client connected: {client_id}")

    try:
        while True:
            event_data = await queue.get()
            await websocket.send_json(event_data)
            queue.task_done()
    except WebSocketDisconnect:
        logger.info(f"[WS] Client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"[WS] Error on connection {client_id}: {e}")
    finally:
        bus.unsubscribe(client_id)
