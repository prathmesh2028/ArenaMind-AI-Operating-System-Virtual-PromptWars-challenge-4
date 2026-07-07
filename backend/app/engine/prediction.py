"""
ArenaMind AI — Prediction Engine (Milestone 6 — Deterministic & Heuristic)
=============================================================================

This engine runs asynchronously in the background. It:
1. Subscribes to the Event Bus (*.tick topics) to capture real-time telemetry.
2. Maintains a sliding history window (last 6 ticks) of all stadium metrics.
3. Performs mathematical extrapolation and heuristic projections.
4. Generates predictions for the 8 mandated categories:
   - Crowd Risk (CROWD_CONGESTION)
   - Queue Growth (GATE_QUEUE_GROWTH)
   - Parking Forecast (PARKING_FORECAST)
   - Transport Delay (TRANSPORT_DELAY)
   - Volunteer Demand (VOLUNTEER_DEMAND)
   - Medical Load (MEDICAL_LOAD)
   - Energy Forecast (ENERGY_FORECAST)
   - Carbon Projection (CARBON_PROJECTION)
5. Generates concrete mitigation recommendations for operations personnel.
6. Persists the predictions and recommendations to the database.
"""

import asyncio
import logging
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.bus.schemas import BusEvent
from app.models import Prediction, Recommendation

logger = logging.getLogger("arenamind.prediction")


class PredictionEngine:
    def __init__(self, history_maxlen: int = 10) -> None:
        self.is_running: bool = False
        self.history_maxlen: int = history_maxlen

        # Telemetry history deques
        self.crowd_history: Dict[str, deque] = {}      # sector -> deque(count)
        self.gate_history: Dict[str, deque] = {}       # gate -> deque(queue_depth)
        self.parking_history: Dict[str, deque] = {}    # lot -> deque(occupied)
        self.transport_history: Dict[str, deque] = {}  # route -> deque(occupancy_pct)
        self.energy_history: Dict[str, deque] = {}     # zone -> deque(active_power_kw)
        self.weather_history: deque = deque(maxlen=history_maxlen)
        self.volunteer_counts: Dict[str, int] = {}     # sector -> count of volunteers
        
        # Carbon footprint accumulation tracker
        self.latest_carbon_footprint: float = 3450.0 + 1820.0 + 850.0

        # Lock to ensure thread-safe/async-safe updates
        self._lock = asyncio.Lock()
        
        # Tick counter to throttle DB writes (every 3 tick sets we write predictions)
        self._tick_counter: int = 0

    def register_listeners(self, bus) -> None:
        """Register listeners on the global Event Bus."""
        bus.subscribe("crowd.tick", self.handle_crowd_tick, "pred_crowd_listener")
        bus.subscribe("gate.queue.tick", self.handle_gate_tick, "pred_gate_listener")
        bus.subscribe("parking.tick", self.handle_parking_tick, "pred_parking_listener")
        bus.subscribe("transport.tick", self.handle_transport_tick, "pred_transport_listener")
        bus.subscribe("energy.tick", self.handle_energy_tick, "pred_energy_listener")
        bus.subscribe("weather.tick", self.handle_weather_tick, "pred_weather_listener")
        bus.subscribe("volunteer.position", self.handle_volunteer_tick, "pred_volunteer_listener")
        logger.info("[PREDICTION] Listeners registered on Event Bus.")

    # -----------------------------------------------------------------------
    # Event Handlers (Telemetry Ingestion)
    # -----------------------------------------------------------------------

    async def handle_crowd_tick(self, event: BusEvent) -> None:
        async with self._lock:
            p = event.payload
            sector = p.get("sector")
            count = p.get("count", 0)
            if sector:
                self.crowd_history.setdefault(sector, deque(maxlen=self.history_maxlen)).append(count)

    async def handle_gate_tick(self, event: BusEvent) -> None:
        async with self._lock:
            p = event.payload
            gate = p.get("gate")
            depth = p.get("queue_depth", 0)
            if gate:
                self.gate_history.setdefault(gate, deque(maxlen=self.history_maxlen)).append(depth)

    async def handle_parking_tick(self, event: BusEvent) -> None:
        async with self._lock:
            p = event.payload
            lot = p.get("lot")
            occupied = p.get("occupied", 0)
            if lot:
                self.parking_history.setdefault(lot, deque(maxlen=self.history_maxlen)).append(occupied)

    async def handle_transport_tick(self, event: BusEvent) -> None:
        async with self._lock:
            p = event.payload
            route = p.get("route")
            occ_pct = p.get("occupancy_pct", 0)
            if route:
                self.transport_history.setdefault(route, deque(maxlen=self.history_maxlen)).append(occ_pct)

    async def handle_energy_tick(self, event: BusEvent) -> None:
        async with self._lock:
            p = event.payload
            zone = p.get("zone")
            power = p.get("active_power_kw", 0.0)
            carbon_rate = p.get("carbon_rate_kg_per_tick", 0.0)
            self.latest_carbon_footprint += carbon_rate
            if zone:
                self.energy_history.setdefault(zone, deque(maxlen=self.history_maxlen)).append(power)

    async def handle_weather_tick(self, event: BusEvent) -> None:
        async with self._lock:
            p = event.payload
            self.weather_history.append(p)
            
            # Use weather ticks as a logical pulse to evaluate predictions
            self._tick_counter += 1
            if self._tick_counter >= 3:
                self._tick_counter = 0
                # Dispatch prediction task in background
                asyncio.create_task(self.evaluate_and_save_predictions())

    async def handle_volunteer_tick(self, event: BusEvent) -> None:
        async with self._lock:
            p = event.payload
            vid = p.get("volunteer_id")
            sector = p.get("sector")
            # We resolve volunteer count by checking current positions dynamically
            # Since this is an event stream, we just track current mapping
            if sector:
                self.volunteer_counts[sector] = self.volunteer_counts.get(sector, 0) + 1

    # -----------------------------------------------------------------------
    # Prediction Calculations
    # -----------------------------------------------------------------------

    def _calculate_trend(self, history: deque) -> float:
        """Returns the average rate of change per tick. Positive is increasing."""
        if len(history) < 2:
            return 0.0
        diffs = [history[i] - history[i-1] for i in range(1, len(history))]
        return sum(diffs) / len(diffs)

    def predict_crowd_risk(self) -> List[Dict[str, Any]]:
        predictions = []
        for sector, history in self.crowd_history.items():
            if not history:
                continue
            current = history[-1]
            trend = self._calculate_trend(history)
            capacity = 8000
            
            # Predict density in 5 ticks (25 seconds)
            predicted_count = current + (trend * 5)
            predicted_density = min(1.0, predicted_count / capacity)
            
            probability = 0.1
            if predicted_density >= 0.90:
                probability = 0.92
            elif predicted_density >= 0.80:
                probability = 0.75
            elif predicted_density >= 0.60:
                probability = 0.40
                
            severity = "LOW"
            priority = "LOW"
            if predicted_density >= 0.90:
                severity = "CRITICAL"
                priority = "CRITICAL"
            elif predicted_density >= 0.80:
                severity = "HIGH"
                priority = "HIGH"
            elif predicted_density >= 0.65:
                severity = "MEDIUM"
                priority = "MEDIUM"

            reason = f"Density in {sector} is currently {current/capacity:.1%} with a growth velocity of {trend:.1f} fans/tick."
            predicted_outcome = f"Crowd density in {sector} will reach {predicted_density:.1%} within the next 30 seconds."

            predictions.append({
                "type": "CROWD_CONGESTION",
                "probability": probability,
                "confidence": 0.85,
                "severity": severity,
                "priority": priority,
                "reasoning": reason,
                "predicted_outcome": predicted_outcome,
                "target_sector": sector,
                "suggested_actions": {
                    "action": "Divert crowd signage",
                    "target_sector": sector,
                    "reroute_path": "Sector A/F corridor"
                },
                "recommendation_title": f"Divert ingress flow from {sector}",
                "recommendation_desc": "Congestion predicted. Update external digital boards to guide fans to alternative gates."
            })
        return predictions

    def predict_queue_growth(self) -> List[Dict[str, Any]]:
        predictions = []
        for gate, history in self.gate_history.items():
            if not history:
                continue
            current = history[-1]
            trend = self._calculate_trend(history)
            
            # Predict queue depth in 6 ticks
            predicted_depth = max(0, current + int(trend * 6))
            
            probability = 0.2
            if predicted_depth > 180:
                probability = 0.88
            elif predicted_depth > 100:
                probability = 0.65
            elif predicted_depth > 50:
                probability = 0.45

            severity = "LOW"
            priority = "LOW"
            if predicted_depth > 180:
                severity = "HIGH"
                priority = "HIGH"
            elif predicted_depth > 100:
                severity = "MEDIUM"
                priority = "MEDIUM"

            reason = f"Queue depth at {gate} is at {current} persons. Trend is {'rising' if trend > 0 else 'falling'} at {trend:.1f} people/tick."
            predicted_outcome = f"Queue depth at {gate} will grow to {predicted_depth} people, causing processing delay."

            predictions.append({
                "type": "GATE_QUEUE_GROWTH",
                "probability": probability,
                "confidence": 0.80,
                "severity": severity,
                "priority": priority,
                "reasoning": reason,
                "predicted_outcome": predicted_outcome,
                "target_sector": gate,
                "suggested_actions": {
                    "action": "Open reserve lanes",
                    "reserve_lanes_count": 2
                },
                "recommendation_title": f"Divert ingress at {gate}",
                "recommendation_desc": f"Open backup scanner lanes at {gate} to decrease queue processing time."
            })
        return predictions

    def predict_parking_forecast(self) -> List[Dict[str, Any]]:
        predictions = []
        for lot, history in self.parking_history.items():
            if not history:
                continue
            current = history[-1]
            trend = self._calculate_trend(history)
            capacity = 1500 if "North" in lot else 2000 if "East" in lot else 2500 if "South" in lot else 500
            
            # Predict fill rate
            ticks_to_fill = (capacity - current) / trend if trend > 0 else 999
            minutes_to_fill = max(1.0, (ticks_to_fill * 5.0) / 60.0)
            
            probability = 0.1
            if current / capacity > 0.95:
                probability = 0.99
            elif ticks_to_fill < 12:  # less than 1 minute
                probability = 0.90
            elif ticks_to_fill < 36:  # less than 3 minutes
                probability = 0.70
                
            severity = "LOW"
            priority = "LOW"
            if probability > 0.90:
                severity = "HIGH"
                priority = "HIGH"
            elif probability > 0.60:
                severity = "MEDIUM"
                priority = "MEDIUM"

            reason = f"Parking lot {lot} is at {current}/{capacity} spaces occupied. Trend is +{trend:.1f} cars/tick."
            predicted_outcome = f"Parking lot {lot} will reach 100% capacity in approximately {minutes_to_fill:.1f} minutes."

            predictions.append({
                "type": "PARKING_FORECAST",
                "probability": probability,
                "confidence": 0.90,
                "severity": severity,
                "priority": priority,
                "reasoning": reason,
                "predicted_outcome": predicted_outcome,
                "target_sector": "Parking Lot",
                "suggested_actions": {
                    "action": "Redirect to alternative lot",
                    "primary_lot": lot,
                    "target_alternative": "South Lot B"
                },
                "recommendation_title": f"Redirect parking from {lot}",
                "recommendation_desc": f"Lot {lot} approaching capacity. Redirect inbound cars to open parking structures."
            })
        return predictions

    def predict_transport_delay(self) -> List[Dict[str, Any]]:
        predictions = []
        for route, history in self.transport_history.items():
            if not history:
                continue
            current = history[-1]
            trend = self._calculate_trend(history)
            
            probability = 0.15
            if current > 95:
                probability = 0.85
            elif current > 85:
                probability = 0.60
                
            severity = "LOW"
            priority = "LOW"
            if current > 95:
                severity = "HIGH"
                priority = "HIGH"
            elif current > 80:
                severity = "MEDIUM"
                priority = "MEDIUM"

            reason = f"Route {route} vehicle occupancy is at {current}%. Trend is +{trend:.1f}% occupancy/tick."
            predicted_outcome = f"Route {route} will experience traffic delays of 10-15 minutes due to shuttle congestion."

            predictions.append({
                "type": "TRANSPORT_DELAY",
                "probability": probability,
                "confidence": 0.78,
                "severity": severity,
                "priority": priority,
                "reasoning": reason,
                "predicted_outcome": predicted_outcome,
                "target_sector": "Transit Hub",
                "suggested_actions": {
                    "action": "Inject reserve buses",
                    "count": 2
                },
                "recommendation_title": f"Dispatch standby buses for {route}",
                "recommendation_desc": "High shuttle occupancy detected. Inject backup buses into rotation to clear queue."
            })
        return predictions

    def predict_volunteer_demand(self) -> List[Dict[str, Any]]:
        predictions = []
        # Correlate volunteer density with sector crowd load
        for sector, count_history in self.crowd_history.items():
            if not count_history:
                continue
            crowd_count = count_history[-1]
            vol_count = self.volunteer_counts.get(sector, 0)
            
            # Expected ratio: 1 volunteer per 500 fans
            expected_vols = max(1, crowd_count // 500)
            shortage = max(0, expected_vols - vol_count)
            
            probability = 0.1
            if shortage > 4:
                probability = 0.85
            elif shortage > 2:
                probability = 0.60
                
            severity = "LOW"
            priority = "LOW"
            if shortage > 4:
                severity = "HIGH"
                priority = "HIGH"
            elif shortage > 1:
                severity = "MEDIUM"
                priority = "MEDIUM"

            reason = f"Sector {sector} volunteer support is {vol_count} against an optimal count of {expected_vols} for {crowd_count} fans."
            predicted_outcome = f"Sector {sector} will experience crowd management strain due to a shortage of {shortage} volunteers."

            predictions.append({
                "type": "VOLUNTEER_DEMAND",
                "probability": probability,
                "confidence": 0.82,
                "severity": severity,
                "priority": priority,
                "reasoning": reason,
                "predicted_outcome": predicted_outcome,
                "target_sector": sector,
                "suggested_actions": {
                    "action": "Redeploy volunteers",
                    "source_sector": "Sector F",
                    "destination_sector": sector,
                    "redeploy_count": shortage
                },
                "recommendation_title": f"Redeploy volunteers to {sector}",
                "recommendation_desc": f"Dispatch {shortage} staff members from lower-density zones to Sector {sector[-1]}."
            })
        return predictions

    def predict_medical_load(self) -> List[Dict[str, Any]]:
        # Depends on Weather Heat Index
        if not self.weather_history:
            return []
        
        w = self.weather_history[-1]
        hi = w.get("heat_index_c", 32.0)
        
        # Calculate base crowd total
        total_crowd = sum(h[-1] for h in self.crowd_history.values() if h)
        
        # Risk factors
        probability = 0.10
        if hi > 40.0:
            probability = 0.90
        elif hi > 36.0:
            probability = 0.65
        elif hi > 32.0:
            probability = 0.35
            
        severity = "LOW"
        priority = "LOW"
        if hi > 40.0:
            severity = "CRITICAL"
            priority = "CRITICAL"
        elif hi > 36.0:
            severity = "HIGH"
            priority = "HIGH"
        elif hi > 33.0:
            severity = "MEDIUM"
            priority = "MEDIUM"

        reason = f"Extreme heat index of {hi:.1f}°C combined with {total_crowd} active fans inside the bowl."
        projected_cases = int((total_crowd / 10000) * (1.2 if hi < 33 else 2.5 if hi < 38 else 6.0))
        predicted_outcome = f"Medical stations will receive approximately {projected_cases} heat exhaustion cases within the hour."

        return [{
            "type": "MEDICAL_LOAD",
            "probability": probability,
            "confidence": 0.75,
            "severity": severity,
            "priority": priority,
            "reasoning": reason,
            "predicted_outcome": predicted_outcome,
            "target_sector": "Stadium Bowl",
            "suggested_actions": {
                "action": "Issue hydration alerts",
                "hydration_booths": "ACTIVATE"
            },
            "recommendation_title": "Activate extra hydration zones",
            "recommendation_desc": "High heat index predicted. Deploy auxiliary hydration tents and trigger PA/screen hydration notices."
        }]

    def predict_energy_forecast(self) -> List[Dict[str, Any]]:
        predictions = []
        for zone, history in self.energy_history.items():
            if not history:
                continue
            current = history[-1]
            trend = self._calculate_trend(history)
            
            # Predict load in 5 ticks
            predicted_kw = current + (trend * 5)
            
            probability = 0.1
            if predicted_kw > 1100:
                probability = 0.88
            elif predicted_kw > 800:
                probability = 0.55
                
            severity = "LOW"
            priority = "LOW"
            if predicted_kw > 1100:
                severity = "HIGH"
                priority = "HIGH"
            elif predicted_kw > 800:
                severity = "MEDIUM"
                priority = "MEDIUM"

            reason = f"Grid load in {zone} is {current:.1f} kW. Trend is {trend:+.2f} kW/tick."
            predicted_outcome = f"{zone} active load will reach {predicted_kw:.1f} kW, pushing grid constraints."

            predictions.append({
                "type": "ENERGY_FORECAST",
                "probability": probability,
                "confidence": 0.80,
                "severity": severity,
                "priority": priority,
                "reasoning": reason,
                "predicted_outcome": predicted_outcome,
                "target_sector": zone,
                "suggested_actions": {
                    "action": "HVAC setpoint load shed",
                    "load_shed_kw": 80.0
                },
                "recommendation_title": f"Initiate energy load-shedding for {zone}",
                "recommendation_desc": f"Shed non-critical load in {zone} by adjusting HVAC setpoints up 1.5°C."
            })
        return predictions

    def predict_carbon_projection(self) -> List[Dict[str, Any]]:
        # Compute projection based on latest accumulated value
        current_co2 = self.latest_carbon_footprint
        
        # Extrapolate to 2 hour match duration (120 ticks * rate)
        projected_total = round(current_co2 * 1.5, 2)
        
        reason = f"Current accumulated event footprint is {current_co2:.1f} kg CO2. Average emission rate is constant."
        predicted_outcome = f"Total event operations footprint will reach {projected_total:.1f} kg CO2 by match conclusion."

        return [{
            "type": "CARBON_PROJECTION",
            "probability": 0.95,
            "confidence": 0.88,
            "severity": "LOW",
            "priority": "LOW",
            "reasoning": reason,
            "predicted_outcome": predicted_outcome,
            "target_sector": "Stadium Infrastructure",
            "suggested_actions": {
                "action": "Increase solar output utilization",
                "offset_percentage_target": 15
            },
            "recommendation_title": "Increase renewable grid offset",
            "recommendation_desc": "Extrapolated carbon footprint is rising. Engage solar reserves to offset fossil electricity draw."
        }]

    # -----------------------------------------------------------------------
    # Database Persistence & Run Execution
    # -----------------------------------------------------------------------

    async def evaluate_and_save_predictions(self) -> None:
        """Run all prediction heuristic tasks and save results to the database."""
        logger.info("[PREDICTION] Evaluating live telemetry metrics...")
        
        all_projections = []
        async with self._lock:
            all_projections += self.predict_crowd_risk()
            all_projections += self.predict_queue_growth()
            all_projections += self.predict_parking_forecast()
            all_projections += self.predict_transport_delay()
            all_projections += self.predict_volunteer_demand()
            all_projections += self.predict_medical_load()
            all_projections += self.predict_energy_forecast()
            all_projections += self.predict_carbon_projection()

        if not all_projections:
            logger.info("[PREDICTION] History still warming up. Skipping evaluation.")
            return

        db: Session = SessionLocal()
        try:
            # We overwrite previous predictions of the same types to keep db clean
            # but provide historical insights. For the demo, we keep only the latest 40 predictions.
            db.query(Prediction).filter(Prediction.incident_id == None).delete(synchronize_session=False)

            for proj in all_projections:
                pred_id = str(uuid.uuid4())
                pred = Prediction(
                    id=pred_id,
                    incident_id=None,
                    type=proj["type"],
                    probability=proj["probability"],
                    confidence=proj["confidence"],
                    severity=proj["severity"],
                    priority=proj["priority"],
                    reasoning=proj["reasoning"],
                    predicted_outcome=proj["predicted_outcome"],
                    suggested_actions=proj["suggested_actions"],
                    target_sector=proj["target_sector"]
                )
                db.add(pred)

                # Add a corresponding recommendation
                rec = Recommendation(
                    id=str(uuid.uuid4()),
                    prediction_id=pred_id,
                    title=proj["recommendation_title"],
                    description=proj["recommendation_desc"],
                    confidence=proj["confidence"],
                    status="PENDING"
                )
                db.add(rec)
                
            db.commit()
            logger.info(f"[PREDICTION] Successfully persisted {len(all_projections)} new projections & recommendations.")
            try:
                from app.bus.core import bus
                from app.bus.schemas import BusEvent
                bus.publish_sync(BusEvent(
                    topic="predictions.updated",
                    source="engine.prediction",
                    payload={"count": len(all_projections)}
                ))
            except Exception as e_bus:
                logger.warning(f"[PREDICTION] Failed to publish predictions.updated: {e_bus}")
        except Exception as e:
            db.rollback()
            logger.error(f"[PREDICTION] Failed to save evaluations to DB: {e}", exc_info=True)
        finally:
            db.close()


# Global Singleton Instance
prediction_engine = PredictionEngine()
