"""
Event Bus — FastAPI Router
===========================
Exposes Event Bus management and inspection endpoints.

GET  /bus/status              — queue depth, DLQ count, subscriber list, metrics
GET  /bus/topics              — all registered topic patterns and subscriber counts
GET  /bus/dlq                 — list all Dead Letter Queue entries
POST /bus/dlq/{event_id}/retry — manually retry a DLQ entry
DELETE /bus/dlq               — clear the entire DLQ
POST /bus/replay/session/{session_id}  — replay a ReplayLog session through the live bus
POST /bus/replay/range        — replay a filtered event range through the live bus
POST /bus/publish             — manually publish a test event to the bus
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.bus.core import bus
from app.bus.replay import replay_event_range, replay_session
from app.bus.schemas import BusEvent
from app.core.deps import CurrentUser, require_admin, require_operations
from app.database import get_db

logger = logging.getLogger("arenamind.bus.router")
router = APIRouter(prefix="/bus", tags=["Event Bus"])


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------

class ManualPublishRequest(BaseModel):
    topic: str
    source: str = "manual.api"
    payload: dict[str, Any] = {}
    sector: Optional[str] = None


class ReplayRangeRequest(BaseModel):
    source: Optional[str] = None
    event_type: Optional[str] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    limit: int = 500
    speed_factor: float = 0.0


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get(
    "/status",
    summary="Event Bus health and metrics",
    description=(
        "Returns live statistics: queue depth, DLQ depth, subscriber count, "
        "total events published/processed/failed, and per-subscriber metrics."
    ),
)
def bus_status(_: CurrentUser = Depends(require_operations)):
    return bus.get_stats()


@router.get(
    "/topics",
    summary="List all registered topic subscriptions",
)
def bus_topics(_: CurrentUser = Depends(require_operations)):
    subscribers = bus.list_subscribers()
    # Group by topic pattern
    by_topic: dict[str, list[str]] = {}
    for sub in subscribers:
        by_topic.setdefault(sub["topic_pattern"], []).append(sub["name"])

    return {
        "topic_count": len(by_topic),
        "topics": [
            {
                "pattern": pattern,
                "subscribers": names,
                "subscriber_count": len(names),
            }
            for pattern, names in sorted(by_topic.items())
        ],
    }


@router.get(
    "/subscribers",
    summary="List all subscribers with processing metrics",
)
def bus_subscribers(_: CurrentUser = Depends(require_operations)):
    return {
        "total": len(bus._subscribers),
        "subscribers": bus.list_subscribers(),
    }


@router.get(
    "/dlq",
    summary="List Dead Letter Queue entries",
    description="Returns all events that failed all retry attempts. Each entry includes the event, error, and failed handler name.",
)
def list_dlq(_: CurrentUser = Depends(require_operations)):
    entries = bus.get_dlq()
    return {
        "dlq_depth": len(entries),
        "entries": [e.to_dict() for e in entries],
    }


@router.post(
    "/dlq/{event_id}/retry",
    summary="Manually retry a Dead Letter Queue entry",
    description="Re-publishes the failed event back onto the bus. Resets the attempt counter for a fresh delivery.",
)
async def retry_dlq_entry(
    event_id: str,
    _: CurrentUser = Depends(require_operations),
):
    success = await bus.retry_dlq_entry(event_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No DLQ entry found with event_id={event_id}",
        )
    return {"message": f"Event {event_id[:8]} re-published from DLQ.", "success": True}


@router.delete(
    "/dlq",
    summary="Clear the entire Dead Letter Queue",
)
def clear_dlq(_: CurrentUser = Depends(require_admin)):
    count = bus.clear_dlq()
    return {"message": f"DLQ cleared. {count} entries removed.", "removed": count}


@router.post(
    "/replay/session/{session_id}",
    summary="Replay a historical ReplayLog session through the live bus",
    description=(
        "Loads all events from the specified ReplayLog session ID and re-publishes "
        "them through the live bus at the given speed factor. "
        "speed_factor=1.0 = real-time, speed_factor=0.0 = instant."
    ),
)
async def replay_session_endpoint(
    session_id: str,
    speed_factor: float = Query(default=0.0, ge=0.0, le=10.0),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_operations),
):
    result = await replay_session(bus, session_id, speed_factor=speed_factor, db=db)
    return result


@router.post(
    "/replay/range",
    summary="Replay a filtered range of events from the events table",
    description=(
        "Loads raw events matching the given filters and re-publishes them through "
        "the live bus. Useful for stress-testing specific subsystem streams."
    ),
)
async def replay_range_endpoint(
    body: ReplayRangeRequest,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_operations),
):
    result = await replay_event_range(
        bus=bus,
        source=body.source,
        event_type=body.event_type,
        since=body.since,
        until=body.until,
        limit=body.limit,
        speed_factor=body.speed_factor,
        db=db,
    )
    return result


@router.post(
    "/publish",
    summary="Manually publish a test event to the bus",
    description=(
        "Publishes a custom event directly to the Event Bus. "
        "Useful for testing handler behaviour without waiting for the Digital Twin."
    ),
)
async def manual_publish(
    body: ManualPublishRequest,
    _: CurrentUser = Depends(require_operations),
):
    event = BusEvent(
        topic=body.topic,
        source=body.source,
        payload=body.payload,
        sector=body.sector,
        metadata={"manual": True},
    )
    await bus.publish(event)
    logger.info(f"[BUS] Manual event published: topic={body.topic} id={event.id[:8]}")
    return {
        "message": "Event published successfully.",
        "event_id": event.id,
        "topic": event.topic,
    }
