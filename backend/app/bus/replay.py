"""
Event Bus — Replay Engine
==========================
Supports replaying historical event sessions through the live bus.

Replay modes:
  1. DB Replay   — load events from ReplayLog by session_id and re-publish
  2. Events Replay — load raw Event records by source/type/time range and re-publish
  3. Speed control — replay at real-time, 2x, 5x, or instant

All replayed events are tagged with:
  - session_id = the original session being replayed
  - metadata.replay = true
  - metadata.original_timestamp = original event timestamp
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.bus.schemas import BusEvent, normalize_topic

logger = logging.getLogger("arenamind.bus.replay")


async def replay_session(
    bus,
    session_id: str,
    speed_factor: float = 1.0,
    db=None,
) -> dict:
    """
    Replay all events in a ReplayLog session through the live bus.

    Args:
        bus:          EventBus instance.
        session_id:   The replay session ID to load.
        speed_factor: 1.0 = real-time, 2.0 = double speed, 0.0 = instant.
        db:           SQLAlchemy session (caller provides it).

    Returns:
        Summary dict with event count and duration.
    """
    from app.models import ReplayLog

    events = (
        db.query(ReplayLog)
        .filter(ReplayLog.replay_session_id == session_id)
        .order_by(ReplayLog.timestamp.asc())
        .all()
    )

    if not events:
        return {"replayed": 0, "session_id": session_id, "message": "No events found."}

    logger.info(
        f"[REPLAY] Starting replay of session {session_id!r} "
        f"({len(events)} events, speed={speed_factor}x)"
    )

    replayed = 0
    prev_ts: Optional[datetime] = None
    start_wall = asyncio.get_event_loop().time()

    for log_row in events:
        # Calculate inter-event delay for realistic timing
        if speed_factor > 0 and prev_ts is not None:
            gap_seconds = (log_row.timestamp - prev_ts).total_seconds()
            sleep_time = max(0.0, gap_seconds / speed_factor)
            if sleep_time > 0.001:
                await asyncio.sleep(sleep_time)

        # Build a BusEvent from the replay log entry
        original_payload = log_row.payload or {}
        replay_event = BusEvent(
            id=str(uuid.uuid4()),
            topic=normalize_topic(log_row.event_type),
            source=f"replay.{session_id}",
            payload=original_payload,
            timestamp=datetime.now(timezone.utc),
            sector=original_payload.get("sector"),
            session_id=session_id,
            metadata={
                "replay": True,
                "original_event_id": str(log_row.id),
                "original_timestamp": log_row.timestamp.isoformat(),
                "original_event_type": log_row.event_type,
            },
        )
        await bus.publish(replay_event)
        replayed += 1
        prev_ts = log_row.timestamp

    duration_s = round(asyncio.get_event_loop().time() - start_wall, 2)
    logger.info(
        f"[REPLAY] Session {session_id!r} complete — "
        f"{replayed} events replayed in {duration_s}s"
    )

    return {
        "session_id": session_id,
        "replayed": replayed,
        "duration_seconds": duration_s,
        "speed_factor": speed_factor,
    }


async def replay_event_range(
    bus,
    source: Optional[str] = None,
    event_type: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = 500,
    speed_factor: float = 0.0,
    db=None,
) -> dict:
    """
    Replay raw Event records from the events table through the live bus.
    Useful for replaying specific sensor streams or time ranges.

    Args:
        bus:          EventBus instance.
        source:       Filter by event source (e.g. 'simulator.crowd').
        event_type:   Filter by event type (e.g. 'CROWD_TICK').
        since/until:  Time range filters.
        limit:        Max events to replay.
        speed_factor: Replay speed (0.0 = instant).
        db:           SQLAlchemy session.

    Returns:
        Summary dict.
    """
    from app.models import Event as EventModel

    query = db.query(EventModel).order_by(EventModel.timestamp.asc())
    if source:
        query = query.filter(EventModel.source == source)
    if event_type:
        query = query.filter(EventModel.type == event_type)
    if since:
        query = query.filter(EventModel.timestamp >= since)
    if until:
        query = query.filter(EventModel.timestamp <= until)

    records = query.limit(limit).all()

    if not records:
        return {"replayed": 0, "message": "No events found matching criteria."}

    logger.info(f"[REPLAY] Replaying {len(records)} events from event table (speed={speed_factor}x)")

    session_id = f"range_replay_{uuid.uuid4().hex[:8]}"
    replayed = 0
    prev_ts: Optional[datetime] = None

    for row in records:
        if speed_factor > 0 and prev_ts is not None:
            gap = (row.timestamp - prev_ts).total_seconds()
            await asyncio.sleep(max(0.0, gap / speed_factor))

        payload = row.payload or {}
        replay_event = BusEvent(
            id=str(uuid.uuid4()),
            topic=normalize_topic(row.type),
            source=f"replay.range",
            payload=payload,
            timestamp=datetime.now(timezone.utc),
            sector=payload.get("sector"),
            session_id=session_id,
            metadata={
                "replay": True,
                "original_event_id": str(row.id),
                "original_timestamp": row.timestamp.isoformat(),
            },
        )
        await bus.publish(replay_event)
        replayed += 1
        prev_ts = row.timestamp

    return {
        "session_id": session_id,
        "replayed": replayed,
        "speed_factor": speed_factor,
    }
