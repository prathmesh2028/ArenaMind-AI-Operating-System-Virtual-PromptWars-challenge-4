"""
Event Bus — Structured Event Schema
=====================================
All events that flow through the ArenaMind Event Bus are wrapped in a
BusEvent envelope before being published. This ensures every consumer
receives a consistent, versioned, traceable structure.

Schema Design:
  - id:         UUID — globally unique event identity
  - topic:      Dot-path event type, e.g. "crowd.density.warning"
  - source:     Emitting subsystem, e.g. "simulator.crowd"
  - sector:     Optional stadium sector context
  - payload:    Arbitrary dict — subsystem-specific data
  - timestamp:  ISO UTC datetime of emission
  - attempt:    Delivery attempt counter (incremented on retry)
  - max_retries: Maximum delivery attempts before DLQ
  - session_id: Optional replay session grouping key
  - metadata:   Optional freeform key-value annotations
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class BusEvent:
    """
    The canonical event envelope for all ArenaMind Event Bus messages.
    All publishers must produce this structure; all subscribers receive it.
    """
    topic: str                                      # e.g. "crowd.density.warning"
    source: str                                     # subsystem that emitted it
    payload: dict[str, Any]                         # event-specific data

    # Auto-assigned
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Delivery tracking
    attempt: int = 0                                # incremented on each retry
    max_retries: int = 3

    # Optional context
    sector: Optional[str] = None
    session_id: Optional[str] = None               # set during replay
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "topic": self.topic,
            "source": self.source,
            "sector": self.sector,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "attempt": self.attempt,
            "max_retries": self.max_retries,
            "session_id": self.session_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BusEvent":
        ts = d.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return cls(
            id=d.get("id", str(uuid.uuid4())),
            topic=d["topic"],
            source=d["source"],
            payload=d.get("payload", {}),
            timestamp=ts or datetime.now(timezone.utc),
            attempt=d.get("attempt", 0),
            max_retries=d.get("max_retries", 3),
            sector=d.get("sector"),
            session_id=d.get("session_id"),
            metadata=d.get("metadata", {}),
        )

    def with_retry(self) -> "BusEvent":
        """Return a copy of this event with attempt incremented."""
        import copy
        clone = copy.copy(self)
        clone.attempt += 1
        return clone


@dataclass
class DeadLetterEntry:
    """
    An event that exceeded its max_retries and was moved to the Dead Letter Queue.
    """
    event: BusEvent
    last_error: str
    failed_handler: str
    failed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Allows manual retry from the API
    retried: bool = False
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event.to_dict(),
            "last_error": self.last_error,
            "failed_handler": self.failed_handler,
            "failed_at": self.failed_at.isoformat(),
            "retried": self.retried,
            "retry_count": self.retry_count,
        }


# ---------------------------------------------------------------------------
# Topic Naming Convention (reference — not enforced)
# ---------------------------------------------------------------------------
# Topics follow a dot-separated hierarchy:
#
#   crowd.tick            — periodic crowd telemetry
#   crowd.density.warning — density threshold breach
#   crowd.density.critical
#   gate.queue.tick
#   gate.malfunction
#   gate.restored
#   parking.tick
#   parking.full
#   transport.tick
#   transport.delay
#   energy.tick
#   energy.high_load
#   weather.tick
#   weather.heat_stress
#   volunteer.position
#   volunteer.redeployed
#   medical.event
#   security.event
#   incident.raised
#   incident.resolved
#   replay.event          — events replayed from history

TOPIC_ALIASES: dict[str, str] = {
    # Maps Digital Twin raw event_type → normalized bus topic
    "CROWD_TICK":               "crowd.tick",
    "CROWD_DENSITY_WARNING":    "crowd.density.warning",
    "CROWD_DENSITY_CRITICAL":   "crowd.density.critical",
    "GATE_QUEUE_TICK":          "gate.queue.tick",
    "GATE_MALFUNCTION":         "gate.malfunction",
    "GATE_RESTORED":            "gate.restored",
    "QUEUE_ALERT":              "gate.queue.alert",
    "PARKING_TICK":             "parking.tick",
    "PARKING_FULL":             "parking.full",
    "TRANSPORT_TICK":           "transport.tick",
    "TRANSPORT_DELAY":          "transport.delay",
    "ENERGY_TICK":              "energy.tick",
    "ENERGY_HIGH_LOAD":         "energy.high_load",
    "WEATHER_TICK":             "weather.tick",
    "HEAT_STRESS_WARNING":      "weather.heat_stress",
    "VOLUNTEER_POSITION_TICK":  "volunteer.position",
    "VOLUNTEER_REDEPLOYED":     "volunteer.redeployed",
    "INCIDENT_RAISED":          "incident.raised",
    "INCIDENT_RESOLVED":        "incident.resolved",
}

def normalize_topic(raw_type: str) -> str:
    """Convert a raw Digital Twin event type to a normalized bus topic."""
    return TOPIC_ALIASES.get(raw_type) or raw_type.lower().replace("_", ".")
