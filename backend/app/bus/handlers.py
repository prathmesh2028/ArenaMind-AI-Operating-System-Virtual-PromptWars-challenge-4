"""
Event Bus — Built-in Handlers
================================
These handlers are registered on startup and respond to events flowing
through the bus. Each is a pure async function that receives a BusEvent.

Handlers included:
  1. CrowdDensityHandler   — crowd.density.warning / .critical → logs + triggers alerts
  2. MedicalEventHandler   — medical.* → escalates CRITICAL events, logs all
  3. SecurityEventHandler  — security.* → logs, escalates HIGH/CRITICAL
  4. EnergyHandler         — energy.high_load → logs warning
  5. TransportHandler      — transport.delay → logs, annotates telemetry
  6. GateMalfunctionHandler— gate.malfunction → logs, recommends action
  7. WeatherHeatHandler    — weather.heat_stress → fan hydration advisory
  8. AuditHandler          — * → comprehensive audit log of all bus events
"""

import logging
from datetime import datetime, timezone

from app.bus.schemas import BusEvent

logger = logging.getLogger("arenamind.bus.handlers")


# ---------------------------------------------------------------------------
# 1. Crowd Density Handler
# ---------------------------------------------------------------------------

async def crowd_density_handler(event: BusEvent) -> None:
    """Respond to crowd density threshold crossings."""
    p = event.payload
    sector = p.get("sector") or event.sector or "Unknown"
    density = p.get("density", 0.0)

    if event.topic == "crowd.density.critical":
        logger.critical(
            f"[HANDLER:crowd] 🚨 CRITICAL density in {sector}: "
            f"{density:.1%} | count={p.get('count')}"
        )
    elif event.topic == "crowd.density.warning":
        logger.warning(
            f"[HANDLER:crowd] ⚠️  WARNING density in {sector}: "
            f"{density:.1%} | count={p.get('count')}"
        )


# ---------------------------------------------------------------------------
# 2. Medical Event Handler
# ---------------------------------------------------------------------------

async def medical_event_handler(event: BusEvent) -> None:
    """Process medical events — log all, escalate CRITICAL."""
    p = event.payload
    etype = p.get("event_type", "UNKNOWN")
    severity = p.get("severity", "LOW")
    sector = p.get("sector") or event.sector or "Unknown"
    description = p.get("description", "No description")
    aid_station = p.get("nearest_aid_station", "Nearest Aid Station")

    if severity == "CRITICAL":
        logger.critical(
            f"[HANDLER:medical] 🚑 CRITICAL MEDICAL EVENT — {etype} in {sector}: "
            f"{description} → Dispatch to {aid_station}"
        )
    elif severity == "HIGH":
        logger.error(
            f"[HANDLER:medical] 🚑 HIGH Medical Event — {etype} in {sector}: {description}"
        )
    else:
        logger.info(
            f"[HANDLER:medical] Medical event — {etype} in {sector}: {description}"
        )

    # Log the day's total for situational awareness
    total = p.get("medical_events_today", "?")
    logger.info(f"[HANDLER:medical] Medical events today: {total}")


# ---------------------------------------------------------------------------
# 3. Security Event Handler
# ---------------------------------------------------------------------------

async def security_event_handler(event: BusEvent) -> None:
    """Process security incidents — log and escalate HIGH/CRITICAL."""
    p = event.payload
    etype = p.get("event_type", "UNKNOWN")
    severity = p.get("severity", "LOW")
    sector = p.get("sector") or event.sector or "Unknown"
    description = p.get("description", "No description")

    if severity == "CRITICAL":
        logger.critical(
            f"[HANDLER:security] 🔴 CRITICAL SECURITY — {etype} at {sector}: {description}"
        )
    elif severity == "HIGH":
        logger.error(
            f"[HANDLER:security] 🟠 HIGH Security — {etype} at {sector}: {description}"
        )
    else:
        logger.info(
            f"[HANDLER:security] Security event — {etype} at {sector}: {description}"
        )

    total = p.get("security_events_today", "?")
    logger.info(f"[HANDLER:security] Security events today: {total}")


# ---------------------------------------------------------------------------
# 4. Energy High Load Handler
# ---------------------------------------------------------------------------

async def energy_handler(event: BusEvent) -> None:
    """Respond to grid zone high load warnings."""
    p = event.payload
    zone = p.get("zone", "Unknown Zone")
    load = p.get("load_pct", 0.0)

    logger.warning(
        f"[HANDLER:energy] ⚡ High grid load in {zone}: {load:.1f}% "
        f"| active_kw={p.get('active_power_kw', '?')}"
    )


# ---------------------------------------------------------------------------
# 5. Transport Delay Handler
# ---------------------------------------------------------------------------

async def transport_handler(event: BusEvent) -> None:
    """Process transport delays and re-routing advisories."""
    p = event.payload
    route = p.get("route", "Unknown Route")
    vehicle_id = p.get("vehicle_id", "?")
    delay = p.get("delay_minutes", 0)
    occ = p.get("occupancy_pct", "?")
    message = p.get("message", "")

    logger.warning(
        f"[HANDLER:transport] 🚌 DELAY — {route} ({vehicle_id}): "
        f"+{delay} min | occupancy={occ}% | {message}"
    )


# ---------------------------------------------------------------------------
# 6. Gate Malfunction Handler
# ---------------------------------------------------------------------------

async def gate_malfunction_handler(event: BusEvent) -> None:
    """Handle gate malfunction events."""
    p = event.payload
    gate = p.get("gate", event.sector or "Unknown Gate")

    if event.topic == "gate.malfunction":
        logger.error(
            f"[HANDLER:gate] 🔧 MALFUNCTION at {gate} — "
            "Recommend diverting fans to adjacent gate immediately."
        )
    elif event.topic == "gate.restored":
        logger.info(f"[HANDLER:gate] ✅ {gate} restored to service.")


# ---------------------------------------------------------------------------
# 7. Weather Heat Stress Handler
# ---------------------------------------------------------------------------

async def weather_heat_handler(event: BusEvent) -> None:
    """Issue fan hydration advisories on extreme heat stress conditions."""
    p = event.payload
    heat_index = p.get("heat_index_c", "?")
    message = p.get("message", "")

    logger.warning(
        f"[HANDLER:weather] 🌡️ HEAT STRESS — Heat index: {heat_index}°C | {message}"
    )


# ---------------------------------------------------------------------------
# 8. Incident Lifecycle Handler
# ---------------------------------------------------------------------------

async def incident_lifecycle_handler(event: BusEvent) -> None:
    """Log incident raised/resolved lifecycle events."""
    p = event.payload
    inc_id = p.get("incident_id", "?")
    sector = p.get("sector") or event.sector or "?"
    priority = p.get("priority", "?")

    if event.topic == "incident.raised":
        logger.error(
            f"[HANDLER:incident] 🚨 INCIDENT RAISED — id={inc_id[:8]} "
            f"sector={sector} priority={priority}"
        )
    elif event.topic == "incident.resolved":
        logger.info(
            f"[HANDLER:incident] ✅ INCIDENT RESOLVED — id={inc_id[:8]} sector={sector}"
        )


# ---------------------------------------------------------------------------
# 9. Audit Handler (catches ALL events)
# ---------------------------------------------------------------------------

async def audit_handler(event: BusEvent) -> None:
    """
    Universal audit log — receives every event on the bus.
    Writes a concise one-liner audit trail at DEBUG level.
    """
    logger.debug(
        f"[AUDIT] id={event.id[:8]} topic={event.topic} "
        f"source={event.source} sector={event.sector or '-'} "
        f"attempt={event.attempt} ts={event.timestamp.isoformat()}"
    )


# ---------------------------------------------------------------------------
# Registration Helper
# ---------------------------------------------------------------------------

def register_all_handlers(bus_instance) -> None:
    """
    Register all built-in handlers with a given EventBus instance.
    Called once on application startup.
    """
    from app.bus.core import EventBus

    handlers = [
        # Crowd
        ("crowd.density.*",  crowd_density_handler,      "crowd_density_handler"),
        # Medical (all subtopics)
        ("medical.*",        medical_event_handler,      "medical_event_handler"),
        # Security (all subtopics)
        ("security.*",       security_event_handler,     "security_event_handler"),
        # Energy
        ("energy.high_load", energy_handler,             "energy_handler"),
        # Transport
        ("transport.delay",  transport_handler,          "transport_handler"),
        # Gates
        ("gate.malfunction", gate_malfunction_handler,   "gate_malfunction_handler"),
        ("gate.restored",    gate_malfunction_handler,   "gate_restored_handler"),
        # Weather
        ("weather.heat_stress", weather_heat_handler,   "weather_heat_handler"),
        # Incident lifecycle
        ("incident.*",       incident_lifecycle_handler, "incident_lifecycle_handler"),
        # Audit (all events)
        ("*",                audit_handler,              "audit_handler"),
    ]

    for pattern, fn, name in handlers:
        bus_instance.subscribe(pattern, fn, name=name)

    logger.info(f"[BUS] {len(handlers)} built-in handlers registered.")
