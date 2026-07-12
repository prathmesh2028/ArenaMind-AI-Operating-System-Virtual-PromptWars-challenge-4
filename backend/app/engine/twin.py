"""
ArenaMind AI — Digital Twin Simulation Engine (Milestone 4 — Full Edition)
===========================================================================

This is a complete replacement of the basic twin.py implemented in Milestone 2.

Milestone 4 enhancements:
  - Configurable match scenarios (PRE_MATCH, KICK_OFF, HALF_TIME, FULL_TIME, POST_MATCH)
  - Synthetic crowd simulation with gate ingress/egress waves
  - Queue simulation at each gate with service rate modeling
  - Parking simulation with ingress/egress flows
  - Volunteer movement tracking
  - Bus/shuttle movement with realistic route simulation
  - Energy simulation with stadium lighting and HVAC load curves
  - Weather simulation with heat index and UV index
  - Medical event generation (realistic probabilistic)
  - Security incident generation (probabilistic)
  - Transportation delay events
  - Standardized event stream to internal Event Bus
  - All subsystems synchronized to the same match clock tick
"""

import asyncio
import logging
import math
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    Carbon, CrowdMetric, Energy, Event, Incident,
    Notification, Parking, Prediction, Recommendation,
    Task, Telemetry, Transport, User,
)

logger = logging.getLogger("arenamind.twin")


# ===========================================================================
# Match Scenario Definitions
# ===========================================================================

class MatchPhase(str, Enum):
    PRE_MATCH   = "PRE_MATCH"     # T-120 to T-0 min: fans arriving
    KICK_OFF    = "KICK_OFF"      # T+0 to T+45 min: first half
    HALF_TIME   = "HALF_TIME"     # T+45 to T+60 min: concourse surge
    SECOND_HALF = "SECOND_HALF"   # T+60 to T+105 min: second half
    FULL_TIME   = "FULL_TIME"     # T+105 to T+120 min: mass egress
    POST_MATCH  = "POST_MATCH"    # T+120+: stadium draining


@dataclass
class MatchScenario:
    """
    Defines a configurable match scenario that drives all simulation parameters.
    """
    name: str = "FIFA World Cup 2026 — Match Day"
    stadium: str = "Hard Rock Stadium"
    city: str = "Miami"
    total_capacity: int = 80000
    sectors: list[str] = field(default_factory=lambda: [
        "Sector A", "Sector B", "Sector C", "Sector D", "Sector E", "Sector F"
    ])
    sector_capacity: int = 8000          # per sector
    gates: list[str] = field(default_factory=lambda: [
        "Gate 1", "Gate 2", "Gate 3", "Gate 4", "Gate 5", "Gate 6"
    ])
    gate_service_rate: int = 40          # fans processed per minute per gate (normal)
    parking_lots: dict = field(default_factory=lambda: {
        "North Lot A": 1500,
        "South Lot B": 2500,
        "East Lot C":  2000,
        "VIP Lot D":   500,
    })
    volunteers: list[dict] = field(default_factory=lambda: [
        {"id": "V001", "name": "Juan Alvarez",    "sector": "Sector D", "role": "CROWD_CONTROL"},
        {"id": "V002", "name": "Amina Sow",       "sector": "Sector B", "role": "CROWD_CONTROL"},
        {"id": "V003", "name": "Kenji Sato",      "sector": "Sector A", "role": "MEDICAL"},
        {"id": "V004", "name": "Marcus Vance",    "sector": "Gate 2",   "role": "SECURITY"},
        {"id": "V005", "name": "Priya Sharma",    "sector": "Sector E", "role": "WAYFINDING"},
        {"id": "V006", "name": "Carlos Mendez",   "sector": "Sector F", "role": "CROWD_CONTROL"},
    ])
    transport_routes: list[dict] = field(default_factory=lambda: [
        {"id": "SH-012", "route": "Express A",        "type": "SHUTTLE", "capacity": 50,
         "stops": ["City Center", "Concourse West", "Stadium North"],
         "lat": 25.7749, "lon": -80.1917},
        {"id": "TR-004", "route": "Metro Line 1",     "type": "TRAIN",   "capacity": 200,
         "stops": ["Downtown Station", "Stadium North Link"],
         "lat": 25.7801, "lon": -80.1850},
        {"id": "B-882",  "route": "Park & Ride",      "type": "BUS",     "capacity": 80,
         "stops": ["South Lot Gate", "Main Entrance"],
         "lat": 25.7690, "lon": -80.2010},
        {"id": "SH-055", "route": "VIP Express",      "type": "SHUTTLE", "capacity": 30,
         "stops": ["VIP Lot D", "VIP Entrance"],
         "lat": 25.7760, "lon": -80.1895},
    ])
    # Probability (per tick) of spontaneous events
    medical_event_probability: float  = 0.04   # 4% chance per tick
    security_event_probability: float = 0.02   # 2% chance per tick
    # Weather baseline
    base_temperature_c: float = 32.0
    base_humidity_pct: float  = 78.0


# Default scenario
DEFAULT_SCENARIO = MatchScenario()


# ===========================================================================
# Event Bus Integration
# ===========================================================================
# Import the canonical BusEvent from the bus package so twin events flow
# directly through the real Event Bus with proper topic normalization.

from app.bus.schemas import BusEvent, normalize_topic


# ===========================================================================
# Twin State
# ===========================================================================

class TwinState:
    """
    Full mutable runtime state of the Digital Twin.
    All subsystems read and write from this single source of truth.
    """

    def __init__(self, scenario: MatchScenario) -> None:
        self.scenario = scenario
        self.tick: int = 0
        self.is_running: bool = False
        self.match_phase: MatchPhase = MatchPhase.PRE_MATCH
        self.match_elapsed_minutes: float = 0.0   # simulated match time

        # --- Crowd ---
        self.sector_counts: dict[str, int] = {s: 0 for s in scenario.sectors}
        self.sector_velocities: dict[str, float] = {s: 1.5 for s in scenario.sectors}

        # --- Gates / Queues ---
        self.gate_queues: dict[str, int] = {g: 0 for g in scenario.gates}
        self.gate_service_rates: dict[str, int] = {
            g: scenario.gate_service_rate for g in scenario.gates
        }
        self.gate_malfunction: dict[str, bool] = {g: False for g in scenario.gates}

        # --- Parking ---
        self.parking_state: dict[str, dict] = {
            lot: {"total": cap, "occupied": 0, "status": "OPEN"}
            for lot, cap in scenario.parking_lots.items()
        }

        # --- Volunteers ---
        self.volunteer_positions: dict[str, dict] = {
            v["id"]: {
                "name": v["name"],
                "sector": v["sector"],
                "role": v["role"],
                "lat": 25.7749 + random.uniform(-0.002, 0.002),
                "lon": -80.1917 + random.uniform(-0.002, 0.002),
                "status": "ON_DUTY",
                "assigned_task": None,
            }
            for v in scenario.volunteers
        }

        # --- Transport ---
        self.vehicles: dict[str, dict] = {
            v["id"]: {
                "route": v["route"],
                "type": v["type"],
                "capacity": v["capacity"],
                "stops": v["stops"],
                "lat": v["lat"],
                "lon": v["lon"],
                "current_stop_idx": 0,
                "occupancy": 0,
                "status": "ON_TIME",
                "delay_minutes": 0,
            }
            for v in scenario.transport_routes
        }

        # --- Energy ---
        self.grid_zones: dict[str, dict] = {
            "Stadium Bowl":   {"base_kw": 1240.0, "load_pct": 85.0, "solar_kw": 120.0},
            "West Concourse": {"base_kw": 480.0,  "load_pct": 60.0, "solar_kw": 40.0},
            "East Concourse": {"base_kw": 480.0,  "load_pct": 60.0, "solar_kw": 40.0},
            "Media Center":   {"base_kw": 320.0,  "load_pct": 45.0, "solar_kw": 15.0},
        }

        # --- Weather ---
        self.weather: dict = {
            "temperature_c": scenario.base_temperature_c,
            "humidity_pct": scenario.base_humidity_pct,
            "wind_speed_kmh": 12.0,
            "uv_index": 8.0,
            "heat_index_c": 38.0,
            "condition": "SUNNY",
        }

        # --- Carbon ---
        self.carbon_accumulators: dict[str, float] = {
            "Grid Electricity":      3450.0,
            "Diesel Shuttle Fleet":  1820.0,
            "Concession Operations": 850.0,
            "Generator Backup":      0.0,
        }

        # --- Incident tracking ---
        self.open_incidents: dict[str, str] = {}   # key → incident_id
        self.medical_events_today: int = 0
        self.security_events_today: int = 0

    def reset(self) -> None:
        self.__init__(self.scenario)


# Global singleton
_state: Optional[TwinState] = None


def _emit(event: BusEvent) -> None:
    """
    Forward a BusEvent to the global EventBus.
    Called from within the async tick — schedules publish as a coroutine.
    """
    try:
        from app.bus.core import bus
        # We are inside an async context (the tick coroutine), so use create_task
        asyncio.ensure_future(bus.publish(event))
    except Exception as exc:
        logger.warning(f"[TWIN] Event emit failed: {exc}")


# ===========================================================================
# Utility Helpers
# ===========================================================================

def _jitter(value: float, pct: float = 0.03) -> float:
    return value * (1 + random.uniform(-pct, pct))

def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))

def _phase_factor(state: TwinState) -> float:
    """Returns a 0.0→1.0 fan presence factor based on the current match phase."""
    phase_factors = {
        MatchPhase.PRE_MATCH:   min(1.0, state.match_elapsed_minutes / 90),  # ramp up
        MatchPhase.KICK_OFF:    0.98,
        MatchPhase.HALF_TIME:   0.95,
        MatchPhase.SECOND_HALF: 0.96,
        MatchPhase.FULL_TIME:   max(0.0, 1.0 - (state.match_elapsed_minutes - 105) / 30),
        MatchPhase.POST_MATCH:  max(0.0, 0.5 - (state.match_elapsed_minutes - 135) / 60),
    }
    return phase_factors.get(state.match_phase, 0.5)


def _advance_match_phase(state: TwinState, elapsed_delta: float) -> None:
    """Advance the simulated match clock and update the match phase."""
    state.match_elapsed_minutes += elapsed_delta

    t = state.match_elapsed_minutes
    if t < 0:
        state.match_phase = MatchPhase.PRE_MATCH
    elif t < 45:
        state.match_phase = MatchPhase.KICK_OFF
    elif t < 60:
        state.match_phase = MatchPhase.HALF_TIME
    elif t < 105:
        state.match_phase = MatchPhase.SECOND_HALF
    elif t < 120:
        state.match_phase = MatchPhase.FULL_TIME
    else:
        state.match_phase = MatchPhase.POST_MATCH


# ===========================================================================
# Subsystem Simulators
# ===========================================================================

def _simulate_crowd(state: TwinState) -> list[BusEvent]:
    """Simulate crowd movement across all sectors."""
    events = []
    factor = _phase_factor(state)
    scenario = state.scenario

    for sector in scenario.sectors:
        target = int(scenario.sector_capacity * factor * random.uniform(0.75, 1.0))

        # During half-time, Sector concourse areas surge; seating drains
        if state.match_phase == MatchPhase.HALF_TIME:
            target = int(target * random.uniform(0.6, 0.9))  # fans leave seats

        current = state.sector_counts[sector]
        # Smooth movement toward target
        delta = int((target - current) * 0.15 + random.randint(-80, 80))
        new_count = int(_clamp(current + delta, 0, scenario.sector_capacity))
        state.sector_counts[sector] = new_count

        density = new_count / scenario.sector_capacity
        velocity = _clamp(_jitter(1.5, 0.15) * (1.0 - density * 0.5), 0.2, 3.0)
        state.sector_velocities[sector] = round(velocity, 3)

        wait_time = max(30, int(density * 900))

        payload = {
            "sector": sector,
            "count": new_count,
            "capacity": scenario.sector_capacity,
            "density": round(density, 4),
            "velocity_ms": round(velocity, 3),
            "wait_time_seconds": wait_time,
            "match_phase": state.match_phase.value,
            "tick": state.tick,
        }

        events.append(BusEvent(topic="CROWD_TICK", source="simulator.crowd", sector=sector, payload=payload))

        # Emit HIGH density warning
        if density >= 0.90:
            events.append(BusEvent(
                topic="CROWD_DENSITY_CRITICAL", source="simulator.crowd", sector=sector,
                payload={"sector": sector, "density": round(density, 4), "count": new_count}
            ))
        elif density >= 0.80:
            events.append(BusEvent(
                topic="CROWD_DENSITY_WARNING", source="simulator.crowd", sector=sector,
                payload={"sector": sector, "density": round(density, 4), "count": new_count}
            ))

    return events


def _simulate_gates(state: TwinState) -> list[BusEvent]:
    """Simulate gate queues with service rate, random malfunctions, and ingress waves."""
    events = []
    factor = _phase_factor(state)

    for gate in state.scenario.gates:
        # Ingress rate: fans arriving from parking / transit
        if state.match_phase in (MatchPhase.PRE_MATCH, MatchPhase.KICK_OFF):
            arrival_rate = int(random.gauss(60, 15) * factor)
        elif state.match_phase == MatchPhase.HALF_TIME:
            arrival_rate = int(random.gauss(20, 10))  # re-entry after half time
        else:
            arrival_rate = int(random.gauss(5, 5))

        # Random gate malfunction (turnstile failure)
        if not state.gate_malfunction[gate] and random.random() < 0.008:
            state.gate_malfunction[gate] = True
            events.append(BusEvent(
                topic="GATE_MALFUNCTION", source="simulator.gates", sector=gate,
                payload={"gate": gate, "severity": "HIGH", "message": f"Turnstile failure at {gate}"}
            ))
        elif state.gate_malfunction[gate] and random.random() < 0.20:
            state.gate_malfunction[gate] = False
            events.append(BusEvent(
                topic="GATE_RESTORED", source="simulator.gates", sector=gate,
                payload={"gate": gate, "message": f"{gate} turnstile restored to service"}
            ))

        # Effective service rate drops to 15 if malfunctioning
        service_rate = 15 if state.gate_malfunction[gate] else state.gate_service_rates[gate]
        processed = min(state.gate_queues[gate] + arrival_rate, service_rate)
        queue_after = max(0, state.gate_queues[gate] + arrival_rate - processed)
        state.gate_queues[gate] = queue_after

        wait_time_est = (queue_after / service_rate * 60) if service_rate > 0 else 999

        events.append(BusEvent(
            topic="GATE_QUEUE_TICK", source="simulator.gates", sector=gate,
            payload={
                "gate": gate,
                "queue_depth": queue_after,
                "service_rate_per_min": service_rate,
                "wait_time_seconds": int(wait_time_est),
                "malfunctioning": state.gate_malfunction[gate],
                "tick": state.tick,
            }
        ))

        # High queue alert
        if queue_after > 200:
            events.append(BusEvent(
                topic="QUEUE_ALERT", source="simulator.gates", sector=gate,
                payload={"gate": gate, "queue_depth": queue_after, "severity": "HIGH"}
            ))

    return events


def _simulate_parking(state: TwinState) -> list[BusEvent]:
    """Simulate parking lot fill during ingress and drain during egress."""
    events = []
    phase = state.match_phase

    for lot_name, data in state.parking_state.items():
        total = data["total"]
        occupied = data["occupied"]

        if phase == MatchPhase.PRE_MATCH:
            delta = random.randint(10, 40)   # cars arriving
        elif phase in (MatchPhase.FULL_TIME, MatchPhase.POST_MATCH):
            delta = random.randint(-60, -20)  # cars leaving
        else:
            delta = random.randint(-5, 5)     # stable during match

        new_occupied = int(_clamp(occupied + delta, 0, total))
        pct = int((new_occupied / total) * 100)
        status = "FULL" if pct >= 99 else "AVAILABLE"

        state.parking_state[lot_name]["occupied"] = new_occupied
        state.parking_state[lot_name]["status"] = status

        events.append(BusEvent(
            topic="PARKING_TICK", source="simulator.parking", sector=None,
            payload={
                "lot": lot_name,
                "total": total,
                "occupied": new_occupied,
                "available": total - new_occupied,
                "pct_full": pct,
                "status": status,
                "tick": state.tick,
            }
        ))

        if pct >= 98:
            events.append(BusEvent(
                topic="PARKING_FULL", source="simulator.parking", sector=None,
                payload={"lot": lot_name, "message": f"{lot_name} is at full capacity"}
            ))

    return events


def _simulate_volunteers(state: TwinState) -> list[BusEvent]:
    """Simulate volunteer positions with realistic movement toward hotspots."""
    events = []

    for vid, vol in state.volunteer_positions.items():
        # Drift GPS position slightly
        vol["lat"] = round(vol["lat"] + random.uniform(-0.0003, 0.0003), 6)
        vol["lon"] = round(vol["lon"] + random.uniform(-0.0003, 0.0003), 6)

        # If sector has high density, volunteer "moves toward" it
        for sector, count in state.sector_counts.items():
            density = count / state.scenario.sector_capacity
            if density > 0.88 and vol["sector"] != sector and random.random() < 0.15:
                vol["sector"] = sector
                events.append(BusEvent(
                    topic="VOLUNTEER_REDEPLOYED", source="simulator.volunteers", sector=sector,
                    payload={
                        "volunteer_id": vid,
                        "name": vol["name"],
                        "new_sector": sector,
                        "reason": "HIGH_DENSITY_ALERT",
                    }
                ))

        events.append(BusEvent(
            topic="VOLUNTEER_POSITION_TICK", source="simulator.volunteers", sector=vol["sector"],
            payload={
                "volunteer_id": vid,
                "name": vol["name"],
                "role": vol["role"],
                "sector": vol["sector"],
                "lat": vol["lat"],
                "lon": vol["lon"],
                "status": vol["status"],
                "tick": state.tick,
            }
        ))

    return events


def _simulate_transport(state: TwinState) -> list[BusEvent]:
    """Simulate shuttle/bus/train GPS movement, occupancy, and delays."""
    events = []
    phase = state.match_phase

    for vid, vehicle in state.vehicles.items():
        # Occupancy logic
        if phase == MatchPhase.PRE_MATCH:
            occ_delta = random.randint(5, 20)
        elif phase in (MatchPhase.FULL_TIME, MatchPhase.POST_MATCH):
            occ_delta = random.randint(10, 30)  # packed during egress
        else:
            occ_delta = random.randint(-5, 5)

        vehicle["occupancy"] = int(_clamp(vehicle["occupancy"] + occ_delta, 0, vehicle["capacity"]))
        occ_pct = int((vehicle["occupancy"] / vehicle["capacity"]) * 100)

        # GPS drift along route
        vehicle["lat"] = round(vehicle["lat"] + random.uniform(-0.0006, 0.0006), 6)
        vehicle["lon"] = round(vehicle["lon"] + random.uniform(-0.0006, 0.0006), 6)

        # Delay logic
        if occ_pct >= 95 and random.random() < 0.3:
            vehicle["status"] = "DELAYED"
            vehicle["delay_minutes"] = random.randint(3, 15)
            events.append(BusEvent(
                topic="TRANSPORT_DELAY", source="simulator.transport", sector=None,
                payload={
                    "vehicle_id": vid,
                    "route": vehicle["route"],
                    "type": vehicle["type"],
                    "delay_minutes": vehicle["delay_minutes"],
                    "occupancy_pct": occ_pct,
                    "message": f"{vehicle['route']} is running {vehicle['delay_minutes']} min late due to overcrowding.",
                }
            ))
        elif vehicle["status"] == "DELAYED" and random.random() < 0.25:
            vehicle["status"] = "ON_TIME"
            vehicle["delay_minutes"] = 0

        # Advance to next stop
        if random.random() < 0.20:
            stops = vehicle["stops"]
            vehicle["current_stop_idx"] = (vehicle["current_stop_idx"] + 1) % len(stops)

        current_stop = vehicle["stops"][vehicle["current_stop_idx"]]

        events.append(BusEvent(
            topic="TRANSPORT_TICK", source="simulator.transport", sector=None,
            payload={
                "vehicle_id": vid,
                "route": vehicle["route"],
                "type": vehicle["type"],
                "status": vehicle["status"],
                "current_stop": current_stop,
                "occupancy": vehicle["occupancy"],
                "occupancy_pct": occ_pct,
                "lat": vehicle["lat"],
                "lon": vehicle["lon"],
                "delay_minutes": vehicle["delay_minutes"],
                "tick": state.tick,
            }
        ))

    return events


def _simulate_energy(state: TwinState) -> list[BusEvent]:
    """Simulate energy grid load with match-phase-aware load curves."""
    events = []
    phase = state.match_phase

    for zone, data in state.grid_zones.items():
        # Load is highest during kick-off (floodlights + scoreboards + concessions)
        if phase == MatchPhase.KICK_OFF:
            load_factor = random.uniform(0.90, 1.0)
        elif phase == MatchPhase.HALF_TIME:
            load_factor = random.uniform(0.95, 1.0)   # concession surge
        elif phase == MatchPhase.PRE_MATCH:
            load_factor = random.uniform(0.70, 0.85)
        elif phase in (MatchPhase.POST_MATCH, MatchPhase.FULL_TIME):
            load_factor = random.uniform(0.50, 0.75)
        else:
            load_factor = random.uniform(0.80, 0.95)

        kw = round(data["base_kw"] * load_factor * _jitter(1.0, 0.02), 2)
        load_pct = round(_clamp(data["load_pct"] * load_factor * _jitter(1.0, 0.03), 0, 100), 2)
        solar_offset = round(data["solar_kw"] * random.uniform(0.7, 1.0), 2)
        net_kw = round(kw - solar_offset, 2)
        carbon_rate = round(net_kw * 0.00197, 3)   # kg CO2 per kWh

        data["base_kw"]  = kw
        data["load_pct"] = load_pct

        events.append(BusEvent(
            topic="ENERGY_TICK", source="simulator.energy", sector=None,
            payload={
                "zone": zone,
                "active_power_kw": kw,
                "solar_offset_kw": solar_offset,
                "net_power_kw": net_kw,
                "load_pct": load_pct,
                "voltage": 480.0,
                "carbon_rate_kg_per_tick": carbon_rate,
                "tick": state.tick,
            }
        ))

        # High load warning
        if load_pct >= 95:
            events.append(BusEvent(
                topic="ENERGY_HIGH_LOAD", source="simulator.energy", sector=None,
                payload={"zone": zone, "load_pct": load_pct, "severity": "WARNING"}
            ))

    # Accumulate carbon
    total_new_carbon = sum(
        d["base_kw"] * 0.00197 for d in state.grid_zones.values()
    )
    state.carbon_accumulators["Grid Electricity"] = round(
        state.carbon_accumulators["Grid Electricity"] + total_new_carbon, 2
    )

    return events


def _simulate_weather(state: TwinState) -> list[BusEvent]:
    """Simulate weather changes over the course of the match."""
    w = state.weather

    # Temperature slightly increases during day match, drops in evening
    w["temperature_c"] = round(_clamp(_jitter(w["temperature_c"], 0.005), 20.0, 42.0), 1)
    w["humidity_pct"]   = round(_clamp(_jitter(w["humidity_pct"], 0.01), 40.0, 100.0), 1)
    w["wind_speed_kmh"] = round(_clamp(_jitter(w["wind_speed_kmh"], 0.05), 0.0, 60.0), 1)
    w["uv_index"]       = round(_clamp(_jitter(w["uv_index"], 0.02), 0.0, 11.0), 1)

    # Heat index calculation (simplified Steadman formula)
    T = w["temperature_c"]
    RH = w["humidity_pct"]
    HI = -8.78469475556 + 1.61139411 * T + 2.33854883889 * RH \
         - 0.14611605 * T * RH - 0.012308094 * T**2 \
         - 0.016424828 * RH**2 + 0.002211732 * T**2 * RH
    w["heat_index_c"] = round(_clamp(HI, T, 55.0), 1)

    # Random weather events
    if random.random() < 0.005:
        w["condition"] = random.choice(["PARTLY_CLOUDY", "OVERCAST", "LIGHT_RAIN"])
    elif random.random() < 0.002:
        w["condition"] = "THUNDERSTORM"

    event = BusEvent(
        topic="WEATHER_TICK", source="simulator.weather", sector=None,
        payload={
            "temperature_c": w["temperature_c"],
            "humidity_pct": w["humidity_pct"],
            "wind_speed_kmh": w["wind_speed_kmh"],
            "uv_index": w["uv_index"],
            "heat_index_c": w["heat_index_c"],
            "condition": w["condition"],
            "tick": state.tick,
        }
    )

    events = [event]

    # Heat stress warning
    if w["heat_index_c"] >= 40.0:
        events.append(BusEvent(
            topic="HEAT_STRESS_WARNING", source="simulator.weather", sector=None,
            payload={"heat_index_c": w["heat_index_c"], "message": "Extreme heat index. Fan hydration advisory issued."}
        ))

    return events


def _simulate_medical_events(state: TwinState) -> list[BusEvent]:
    """Probabilistically generate medical incidents."""
    events = []
    scenario = state.scenario

    # Probability increases with heat and crowd density
    base_prob = scenario.medical_event_probability
    heat_factor = 1.0 + max(0, (state.weather["heat_index_c"] - 35) * 0.05)
    density_factor = 1.0 + max(0, (sum(state.sector_counts.values()) / (scenario.sector_capacity * len(scenario.sectors)) - 0.7) * 2)
    adjusted_prob = min(0.25, base_prob * heat_factor * density_factor)

    if random.random() < adjusted_prob:
        state.medical_events_today += 1
        sector = random.choice(scenario.sectors)
        event_types = [
            ("HEAT_EXHAUSTION", "Fan collapsed due to heat exhaustion", "MEDIUM"),
            ("CARDIAC_EVENT",   "Fan reported chest pains", "CRITICAL"),
            ("FAINTING",        "Fan fainted near concession area", "HIGH"),
            ("CROWD_CRUSH_MINOR", "Minor crush injury near sector entry", "HIGH"),
            ("INJURY",          "Fan sustained a minor injury", "LOW"),
        ]
        etype, description, severity = random.choice(event_types)

        events.append(BusEvent(
            topic=f"MEDICAL_{etype}", source="simulator.medical", sector=sector,
            payload={
                "sector": sector,
                "event_type": etype,
                "description": description,
                "severity": severity,
                "medical_events_today": state.medical_events_today,
                "nearest_aid_station": f"Aid Station {sector[-1]}",
                "tick": state.tick,
            }
        ))

    return events


def _simulate_security_events(state: TwinState) -> list[BusEvent]:
    """Probabilistically generate security incidents."""
    events = []
    scenario = state.scenario

    # Security risk rises in high-density, late-match phases
    base_prob = scenario.security_event_probability
    if state.match_phase in (MatchPhase.FULL_TIME, MatchPhase.POST_MATCH):
        base_prob *= 2.0

    if random.random() < base_prob:
        state.security_events_today += 1
        sector = random.choice(scenario.sectors + scenario.gates)
        sec_types = [
            ("UNAUTHORIZED_ENTRY", "Individual attempted to bypass gate security", "HIGH"),
            ("DISRUPTIVE_FAN",     "Fan causing disturbance in stands", "MEDIUM"),
            ("PROHIBITED_ITEM",    "Prohibited item detected at gate scanner", "MEDIUM"),
            ("CROWD_DISTURBANCE",  "Minor crowd altercation in sector", "HIGH"),
            ("PERIMETER_BREACH",   "Uncleared individual near restricted zone", "CRITICAL"),
        ]
        etype, description, severity = random.choice(sec_types)

        events.append(BusEvent(
            topic=f"SECURITY_{etype}", source="simulator.security", sector=sector,
            payload={
                "sector": sector,
                "event_type": etype,
                "description": description,
                "severity": severity,
                "security_events_today": state.security_events_today,
                "tick": state.tick,
            }
        ))

    return events


# ===========================================================================
# Database Write Layer
# ===========================================================================

def _persist_events(db: Session, bus_events: list[BusEvent], now: datetime) -> None:
    """Write all bus events to the events table (twin-side persistence before bus routing)."""
    for be in bus_events:
        db.add(Event(
            id=be.id,
            timestamp=now,
            type=be.topic,
            source=be.source,
            payload=be.to_dict(),
        ))


def _persist_crowd_metrics(db: Session, state: TwinState, now: datetime) -> None:
    scenario = state.scenario
    for sector in scenario.sectors:
        count = state.sector_counts[sector]
        capacity = scenario.sector_capacity
        density = count / capacity
        velocity = state.sector_velocities.get(sector, 1.2)
        wait_time = max(30, int(density * 900))

        db.add(CrowdMetric(
            id=str(uuid.uuid4()),
            timestamp=now,
            sector=sector,
            count=count,
            capacity=capacity,
            density=round(density, 4),
            velocity=round(velocity, 3),
            wait_time_seconds=wait_time,
        ))

        db.add(Telemetry(
            id=str(uuid.uuid4()),
            timestamp=now,
            metric_name="CROWD_DENSITY",
            sector=sector,
            value={
                "count": count, "density": round(density, 4),
                "velocity": round(velocity, 3), "wait_time_s": wait_time,
                "phase": state.match_phase.value,
            },
        ))


def _persist_parking(db: Session, state: TwinState, now: datetime) -> None:
    for lot_name, data in state.parking_state.items():
        total = data["total"]
        occupied = data["occupied"]
        pct = int((occupied / total) * 100)
        db.add(Parking(
            id=str(uuid.uuid4()),
            timestamp=now,
            lot_name=lot_name,
            total_spots=total,
            occupied_spots=occupied,
            occupancy_percentage=pct,
            status="FULL" if pct >= 99 else "OPEN",
        ))


def _persist_transport(db: Session, state: TwinState, now: datetime) -> None:
    for vid, vehicle in state.vehicles.items():
        current_stop = vehicle["stops"][vehicle["current_stop_idx"]]
        occ_pct = int((vehicle["occupancy"] / vehicle["capacity"]) * 100)
        db.add(Transport(
            id=str(uuid.uuid4()),
            timestamp=now,
            route_name=vehicle["route"],
            vehicle_id=vid,
            type=vehicle["type"],
            status=vehicle["status"],
            current_stop=current_stop,
            occupancy_percentage=occ_pct,
            latitude=vehicle["lat"],
            longitude=vehicle["lon"],
        ))


def _persist_energy(db: Session, state: TwinState, now: datetime) -> None:
    for zone, data in state.grid_zones.items():
        kw = data["base_kw"]
        db.add(Energy(
            id=str(uuid.uuid4()),
            timestamp=now,
            grid_zone=zone,
            active_power_kw=kw,
            reactive_power_kvar=round(kw * 0.12, 2),
            voltage=480.0,
            load_percentage=data["load_pct"],
            carbon_offset_kg=round(data["solar_kw"] * 0.00197, 3),
        ))
    from app.models import Carbon
    for source, amount in state.carbon_accumulators.items():
        cat = "ENERGY" if "Electric" in source else "TRANSPORT" if "Shuttle" in source else "FOOD_WASTE"
        db.add(Carbon(
            id=str(uuid.uuid4()),
            timestamp=now,
            emission_source=source,
            amount_kg=amount,
            category=cat,
        ))


def _check_incidents(db: Session, state: TwinState, bus_events: list[BusEvent], now: datetime) -> None:
    """Check bus events and state for conditions that require incident creation."""
    ops_user = (
        db.query(User).join(User.role).filter(User.role.has(name="OPERATIONS")).first()
    )
    ops_id = str(ops_user.id) if ops_user else None

    # --- Crowd congestion incidents ---
    for sector in state.scenario.sectors:
        density = state.sector_counts[sector] / state.scenario.sector_capacity
        key = f"crowd_{sector}"

        if density >= 0.85 and key not in state.open_incidents:
            priority = "CRITICAL" if density >= 0.95 else "HIGH"
            inc_id = str(uuid.uuid4())
            pred_id = str(uuid.uuid4())

            db.add(Incident(
                id=inc_id,
                title=f"Crowd Congestion — {sector}",
                description=f"Digital Twin: density at {density:.1%} ({state.sector_counts[sector]} fans).",
                status="ACTIVE", priority=priority, sector=sector,
                reporter_id=None, assignee_id=ops_id, created_at=now,
                ai_summary=f"Auto-detected: {sector} at {density:.1%} capacity during {state.match_phase.value}.",
            ))
            db.add(Prediction(
                id=pred_id, incident_id=inc_id, type="CROWD_CONGESTION",
                probability=round(density, 3), confidence=0.93,
                reasoning=f"Sustained crowd density of {density:.1%} in {sector}.",
                suggested_actions={"reroute_signage": True, "volunteer_dispatch": 3, "open_adjacent_gates": True},
                target_sector=sector, created_at=now,
            ))
            db.add(Recommendation(
                id=str(uuid.uuid4()), prediction_id=pred_id,
                title=f"Redirect fans from {sector}", description="Activate digital signage and deploy crowd control volunteers.",
                confidence=0.88, status="PENDING", created_at=now,
            ))
            if ops_id:
                db.add(Notification(
                    id=str(uuid.uuid4()), recipient_id=ops_id,
                    title=f"{priority}: Congestion in {sector}",
                    message=f"Digital Twin detected {density:.1%} capacity in {sector}. Incident auto-raised.",
                    read=False, priority=priority, type="INCIDENT_ALERT", created_at=now,
                ))
            state.open_incidents[key] = inc_id

            _emit(BusEvent(
                topic="INCIDENT_RAISED",
                source="digital_twin",
                sector=sector,
                payload={
                    "incident_id": inc_id,
                    "sector": sector,
                    "priority": priority,
                    "density": density,
                    "incident_type": "CROWD",
                    "title": f"Crowd Congestion — {sector}",
                    "description": f"Digital Twin: density at {density:.1%} ({state.sector_counts[sector]} fans)."
                }
            ))

        elif density < 0.80 and key in state.open_incidents:
            inc_id = state.open_incidents.pop(key)
            inc = db.query(Incident).filter(Incident.id == inc_id).first()
            if inc and inc.status != "RESOLVED":
                inc.status = "RESOLVED"
                inc.resolved_at = now

    # --- Medical events → incidents ---
    for be in bus_events:
        if be.topic.startswith("MEDICAL_") and be.payload.get("severity") in ("CRITICAL", "HIGH"):
            key = f"medical_{state.tick}"
            if key not in state.open_incidents:
                inc_id = str(uuid.uuid4())
                sector = be.sector or "Unknown"
                title = f"Medical: {be.payload.get('event_type', 'UNKNOWN')} in {sector}"
                desc = be.payload.get("description", "")
                db.add(Incident(
                    id=inc_id, title=title,
                    description=desc,
                    status="ACTIVE", priority=be.payload["severity"],
                    sector=sector, reporter_id=None, assignee_id=ops_id, created_at=now,
                ))
                if ops_id:
                    db.add(Notification(
                        id=str(uuid.uuid4()), recipient_id=ops_id,
                        title=f"MEDICAL ALERT: {be.payload.get('event_type')} — {sector}",
                        message=desc,
                        read=False, priority=be.payload["severity"], type="INCIDENT_ALERT", created_at=now,
                    ))
                state.open_incidents[key] = inc_id
                
                _emit(BusEvent(
                    topic="INCIDENT_RAISED",
                    source="digital_twin",
                    sector=sector,
                    payload={
                        "incident_id": inc_id,
                        "sector": sector,
                        "priority": be.payload["severity"],
                        "incident_type": "MEDICAL",
                        "title": title,
                        "description": desc
                    }
                ))

    # --- Security events → incidents ---
    for be in bus_events:
        if be.topic.startswith("SECURITY_") and be.payload.get("severity") in ("CRITICAL", "HIGH"):
            key = f"security_{state.tick}"
            if key not in state.open_incidents:
                inc_id = str(uuid.uuid4())
                sector = be.sector or "Gate"
                title = f"Security: {be.payload.get('event_type')} at {sector}"
                desc = be.payload.get("description", "")
                db.add(Incident(
                    id=inc_id, title=title,
                    description=desc,
                    status="ACTIVE", priority=be.payload["severity"],
                    sector=sector, reporter_id=None, assignee_id=ops_id, created_at=now,
                ))
                state.open_incidents[key] = inc_id
                
                _emit(BusEvent(
                    topic="INCIDENT_RAISED",
                    source="digital_twin",
                    sector=sector,
                    payload={
                        "incident_id": inc_id,
                        "sector": sector,
                        "priority": be.payload["severity"],
                        "incident_type": "SECURITY",
                        "title": title,
                        "description": desc
                    }
                ))


# ===========================================================================
# Main Tick
# ===========================================================================

async def _run_tick(state: TwinState) -> None:
    """Execute one full simulation tick across all subsystems."""
    state.tick += 1
    now = datetime.now(timezone.utc)

    # Advance match clock: each tick = ~0.5 simulated minutes (configurable)
    _advance_match_phase(state, elapsed_delta=0.5)

    # Run all subsystem simulators
    bus_events: list[BusEvent] = []
    bus_events += _simulate_crowd(state)
    bus_events += _simulate_gates(state)
    bus_events += _simulate_parking(state)
    bus_events += _simulate_volunteers(state)
    bus_events += _simulate_transport(state)
    bus_events += _simulate_energy(state)
    bus_events += _simulate_weather(state)
    bus_events += _simulate_medical_events(state)
    bus_events += _simulate_security_events(state)

    # Emit all events to registered listeners
    for be in bus_events:
        _emit(be)

    # Persist to database
    db: Session = SessionLocal()
    try:
        # Event Bus handles event persistence asynchronously. Twin only persists state telemetry.
        # _persist_events(db, bus_events, now)
        _persist_crowd_metrics(db, state, now)
        _persist_parking(db, state, now)
        _persist_transport(db, state, now)
        _persist_energy(db, state, now)
        _check_incidents(db, state, bus_events, now)
        db.commit()

        logger.debug(
            f"[TWIN] Tick {state.tick} | Phase={state.match_phase.value} "
            f"| Events={len(bus_events)} "
            f"| Sectors={dict(state.sector_counts)}"
        )
    except Exception as exc:
        db.rollback()
        logger.error(f"[TWIN] Tick {state.tick} DB write failed: {exc}", exc_info=True)
    finally:
        db.close()


# ===========================================================================
# Public Lifecycle API
# ===========================================================================

async def start_twin(
    scenario: Optional[MatchScenario] = None,
    tick_interval_seconds: float = 5.0,
) -> None:
    """
    Start the Digital Twin simulation loop.

    Args:
        scenario: Match scenario configuration. Defaults to DEFAULT_SCENARIO.
        tick_interval_seconds: Real-world seconds between simulation ticks.
    """
    global _state

    if _state and _state.is_running:
        logger.warning("[TWIN] Already running — ignoring start request.")
        return

    _state = TwinState(scenario or DEFAULT_SCENARIO)
    _state.is_running = True

    logger.info(
        f"[TWIN] Starting — Scenario: {_state.scenario.name} | "
        f"Stadium: {_state.scenario.stadium} | "
        f"Tick interval: {tick_interval_seconds}s | "
        f"Sectors: {len(_state.scenario.sectors)} | "
        f"Vehicles: {len(_state.scenario.transport_routes)}"
    )

    try:
        while _state.is_running:
            await _run_tick(_state)
            await asyncio.sleep(tick_interval_seconds)
    except asyncio.CancelledError:
        logger.info("[TWIN] Simulation loop cancelled.")
    finally:
        _state.is_running = False
        logger.info(f"[TWIN] Stopped after {_state.tick} ticks.")


def stop_twin() -> None:
    global _state
    if _state:
        _state.is_running = False
    logger.info("[TWIN] Stop signal sent.")


def get_twin_status() -> dict[str, Any]:
    """Return a live snapshot of the current simulation state."""
    if not _state:
        return {"is_running": False, "tick": 0, "message": "Twin not initialized"}

    total_fans = sum(_state.sector_counts.values())
    total_cap = _state.scenario.sector_capacity * len(_state.scenario.sectors)

    return {
        "is_running": _state.is_running,
        "tick": _state.tick,
        "scenario": _state.scenario.name,
        "stadium": _state.scenario.stadium,
        "match_phase": _state.match_phase.value,
        "match_elapsed_minutes": round(_state.match_elapsed_minutes, 1),
        "total_fans": total_fans,
        "total_capacity": total_cap,
        "occupancy_pct": round(total_fans / total_cap * 100, 1) if total_cap else 0,
        "open_incidents": len(_state.open_incidents),
        "medical_events_today": _state.medical_events_today,
        "security_events_today": _state.security_events_today,
        "weather": _state.weather,
        "sectors": {
            s: {
                "count": c,
                "density_pct": round(c / _state.scenario.sector_capacity * 100, 1),
            }
            for s, c in _state.sector_counts.items()
        },
        "vehicles": [
            {
                "vehicle_id": vid,
                "route": v["route"],
                "status": v["status"],
                "occupancy_pct": int(v["occupancy"] / v["capacity"] * 100),
            }
            for vid, v in _state.vehicles.items()
        ],
        "parking": {
            lot: {
                "pct_full": int(d["occupied"] / d["total"] * 100),
                "status": d["status"],
            }
            for lot, d in _state.parking_state.items()
        },
    }
