"""
ArenaMind AI — Decision Engine (Milestone 7 — Rule Engine & Mitigation Matrix)
=============================================================================

This engine runs asynchronously in the background. It:
1. Subscribes to the Event Bus to process predictions and critical incidents.
2. Evaluates the Mitigation Matrix rules to compute deterministic actions.
3. Automatically triggers:
   - Dispatch Volunteers (DISPATCH_VOLUNTEERS)
   - Open Gates (OPEN_GATES)
   - Close Gates (CLOSE_GATES)
   - Broadcast Messages (BROADCAST_MESSAGES)
   - Medical Escalation (MEDICAL_ESCALATION)
   - Transport Diversion (TRANSPORT_DIVERSION)
   - Parking Redirection (PARKING_REDIRECTION)
4. Exposes and formats Decisions with Decision, Reason, Expected Impact, Team, and ETA.
5. Persists Decision records to the database.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.bus.schemas import BusEvent
from app.models import Prediction, Incident, Decision, Task, Notification, User

logger = logging.getLogger("arenamind.decision")


class DecisionEngine:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        # Deduplication cache: key -> timestamp of last decision to prevent command spam
        self._decision_cache: Dict[str, float] = {}

    def register_listeners(self, bus) -> None:
        """Subscribe to relevant Event Bus topics."""
        # Listen to custom prediction completion event
        bus.subscribe("predictions.updated", self.handle_predictions_updated, "decision_predictions_listener")
        # Listen to critical incident alerts
        bus.subscribe("incident.raised", self.handle_incident_raised, "decision_incident_listener")
        logger.info("[DECISION] Listeners registered on Event Bus.")

    async def handle_predictions_updated(self, event: BusEvent) -> None:
        """Triggered when new predictions are saved by the Prediction Engine."""
        async with self._lock:
            logger.info("[DECISION] Live predictions update received. Evaluating Mitigation Matrix...")
            db: Session = SessionLocal()
            try:
                predictions = (
                    db.query(Prediction)
                    .order_by(Prediction.created_at.desc())
                    .limit(20)
                    .all()
                )
                
                for pred in predictions:
                    await self._evaluate_prediction_rules(db, pred)
            except Exception as e:
                logger.error(f"[DECISION] Evaluation failed: {e}", exc_info=True)
            finally:
                db.close()

    async def handle_incident_raised(self, event: BusEvent) -> None:
        """Triggered when a critical security or safety incident is raised."""
        async with self._lock:
            p = event.payload
            inc_id = p.get("incident_id")
            sector = p.get("sector")
            priority = p.get("priority")
            density = p.get("density", 0.0)
            
            db: Session = SessionLocal()
            try:
                # Rule: Security incident raised in a gate/sector -> CLOSE_GATES
                if event.topic == "incident.raised" and priority in ("CRITICAL", "HIGH"):
                    # Check cache to avoid duplicate closing commands
                    cache_key = f"close_gate_{sector}"
                    now_ts = asyncio.get_event_loop().time()
                    if cache_key in self._decision_cache and (now_ts - self._decision_cache[cache_key]) < 60.0:
                        return
                    
                    self._decision_cache[cache_key] = now_ts
                    
                    # Create Decision
                    decision_text = f"Emergency lockdown: immediately close and lock all turnstile scanners at {sector}."
                    reason = f"Critical security alert raised: incident {inc_id[:8]} reported at {sector}."
                    impact = "Prevent unauthorized access and isolate perimeter zone containment."
                    
                    db_decision = Decision(
                        id=str(uuid.uuid4()),
                        prediction_id=None,
                        incident_id=inc_id,
                        decision=decision_text,
                        reason=reason,
                        expected_impact=impact,
                        responsible_team="SECURITY",
                        eta="1 minute",
                        action_type="CLOSE_GATES"
                    )
                    db.add(db_decision)
                    db.commit()
                    
                    logger.warning(
                        f"[DECISION] 🚨 MITIGATION ACTIVATED [CLOSE_GATES] | Team=SECURITY | "
                        f"Decision: {decision_text} | Reason: {reason}"
                    )
            except Exception as e:
                db.rollback()
                logger.error(f"[DECISION] Incident handler failed: {e}", exc_info=True)
            finally:
                db.close()

    # -----------------------------------------------------------------------
    # Mitigation Matrix Rules
    # -----------------------------------------------------------------------

    async def _evaluate_prediction_rules(self, db: Session, pred: Prediction) -> None:
        now_ts = asyncio.get_event_loop().time()
        cache_key = f"rule_{pred.type}_{pred.target_sector}"

        # Throttle: don't generate duplicate decisions for the same prediction type & sector within 45s
        if cache_key in self._decision_cache and (now_ts - self._decision_cache[cache_key]) < 45.0:
            return

        decision_to_save: Optional[Decision] = None

        # Helper to find operations/staff user ID to notify
        ops_user = db.query(User).join(User.role).filter(User.role.has(name="OPERATIONS")).first()
        ops_id = str(ops_user.id) if ops_user else None

        # Rule 1: Crowd Congestion -> Dispatch Volunteers & Open Gates
        if pred.type == "CROWD_CONGESTION" and pred.probability >= 0.70:
            self._decision_cache[cache_key] = now_ts
            decision_to_save = Decision(
                id=str(uuid.uuid4()),
                prediction_id=pred.id,
                incident_id=pred.incident_id,
                decision=f"Deploy 3 crowd-management volunteers to {pred.target_sector} and open reserve exit lanes.",
                reason=pred.reasoning,
                expected_impact="Disperse density hotspots and lower local density index by 15%.",
                responsible_team="VOLUNTEER",
                eta="3 minutes",
                action_type="DISPATCH_VOLUNTEERS"
            )

        # Rule 2: Gate Queue Growth -> Open Gates
        elif pred.type == "GATE_QUEUE_GROWTH" and pred.probability >= 0.70:
            self._decision_cache[cache_key] = now_ts
            decision_to_save = Decision(
                id=str(uuid.uuid4()),
                prediction_id=pred.id,
                incident_id=pred.incident_id,
                decision=f"Open backup scanners and check-in turnstiles at {pred.target_sector}.",
                reason=pred.reasoning,
                expected_impact="Increase throughput to 80 fans/min, lowering wait time below 10 minutes.",
                responsible_team="OPERATIONS",
                eta="4 minutes",
                action_type="OPEN_GATES"
            )

        # Rule 3: Parking Forecast -> Parking Redirection & Broadcast Messages
        elif pred.type == "PARKING_FORECAST" and pred.probability >= 0.70:
            self._decision_cache[cache_key] = now_ts
            decision_to_save = Decision(
                id=str(uuid.uuid4()),
                prediction_id=pred.id,
                incident_id=pred.incident_id,
                decision="Activate highway VMS boards and redirect inbound vehicles to South Lot B.",
                reason=pred.reasoning,
                expected_impact="Prevent complete parking gridlock at the entrance lanes.",
                responsible_team="TRANSPORT",
                eta="2 minutes",
                action_type="PARKING_REDIRECTION"
            )

        # Rule 4: Transport Delay -> Transport Diversion
        elif pred.type == "TRANSPORT_DELAY" and pred.probability >= 0.70:
            self._decision_cache[cache_key] = now_ts
            decision_to_save = Decision(
                id=str(uuid.uuid4()),
                prediction_id=pred.id,
                incident_id=pred.incident_id,
                decision="Divert Express shuttle fleet from West Link to Stadium Express bypass lanes.",
                reason=pred.reasoning,
                expected_impact="Bypass localized traffic delays to maintain a 5-minute passenger headway.",
                responsible_team="TRANSPORT",
                eta="5 minutes",
                action_type="TRANSPORT_DIVERSION"
            )

        # Rule 5: Volunteer Demand -> Dispatch Volunteers
        elif pred.type == "VOLUNTEER_DEMAND" and pred.probability >= 0.65:
            self._decision_cache[cache_key] = now_ts
            decision_to_save = Decision(
                id=str(uuid.uuid4()),
                prediction_id=pred.id,
                incident_id=pred.incident_id,
                decision=f"Redeploy 2 wayfinding staff members from concession stands to {pred.target_sector}.",
                reason=pred.reasoning,
                expected_impact="Resolve wayfinding questions and assist crowd control protocols.",
                responsible_team="VOLUNTEER",
                eta="5 minutes",
                action_type="DISPATCH_VOLUNTEERS"
            )

        # Rule 6: Medical Load -> Medical Escalation
        elif pred.type == "MEDICAL_LOAD" and pred.probability >= 0.65:
            self._decision_cache[cache_key] = now_ts
            decision_to_save = Decision(
                id=str(uuid.uuid4()),
                prediction_id=pred.id,
                incident_id=pred.incident_id,
                decision="Deploy roaming medical responders and establish hydration station at Stadium Bowl.",
                reason=pred.reasoning,
                expected_impact="Respond to patient heat exhaustion cases within 3 minutes of report.",
                responsible_team="MEDICAL",
                eta="2 minutes",
                action_type="MEDICAL_ESCALATION"
            )

        # Rule 7: Energy Forecast -> Broadcast Messages (Load Shedding)
        elif pred.type == "ENERGY_FORECAST" and pred.probability >= 0.75:
            self._decision_cache[cache_key] = now_ts
            decision_to_save = Decision(
                id=str(uuid.uuid4()),
                prediction_id=pred.id,
                incident_id=pred.incident_id,
                decision=f"Initiate energy conservation load-shedding protocol in {pred.target_sector}.",
                reason=pred.reasoning,
                expected_impact="Decrease peak load in the sector by 75 kW to prevent local grid trip.",
                responsible_team="OPERATIONS",
                eta="3 minutes",
                action_type="BROADCAST_MESSAGES"
            )

        # Rule 8: Carbon Projection -> Transport Diversion (Renewables Offset)
        elif pred.type == "CARBON_PROJECTION" and pred.probability >= 0.80:
            self._decision_cache[cache_key] = now_ts
            decision_to_save = Decision(
                id=str(uuid.uuid4()),
                prediction_id=pred.id,
                incident_id=pred.incident_id,
                decision="Increase green energy offset targets: activate standby clean energy solar reserves.",
                reason=pred.reasoning,
                expected_impact="Decrease net match operations carbon emissions rate by 10%.",
                responsible_team="OPERATIONS",
                eta="1 minute",
                action_type="TRANSPORT_DIVERSION"
            )

        if decision_to_save:
            db.add(decision_to_save)
            
            # Auto-generate a corresponding system task/notification to operations
            if ops_id:
                db.add(Notification(
                    id=str(uuid.uuid4()),
                    recipient_id=ops_id,
                    title=f"Decision Generated: {decision_to_save.action_type}",
                    message=f"Mitigation plan proposed: {decision_to_save.decision}",
                    read=False,
                    priority="HIGH" if pred.probability >= 0.80 else "MEDIUM",
                    type="SYSTEM",
                    created_at=datetime.now(timezone.utc)
                ))
            
            db.commit()
            
            logger.info(
                f"[DECISION] Deterministic mitigation activated [{decision_to_save.action_type}] | "
                f"Team={decision_to_save.responsible_team} | Decision={decision_to_save.decision}"
            )


# Global Singleton Instance
decision_engine = DecisionEngine()
