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
from typing import Any, Dict, List, Optional

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
            sector = p.get("sector") or "Unknown"
            priority = p.get("priority") or "MEDIUM"
            inc_type = (p.get("incident_type") or "").upper()
            title_raw = p.get("title") or "Critical Alert"
            title = title_raw.lower()
            desc = (p.get("description") or "").lower()
            density = p.get("density", 0.0)

            db: Session = SessionLocal()
            try:
                # Deterministic Mitigation Matrix
                decision_text = ""
                reason = ""
                impact = ""
                responsible_team = ""
                eta = ""
                action_type = ""

                # 1. Security Incidents
                if (
                    inc_type == "SECURITY"
                    or any(k in title or k in desc for k in ["security", "perimeter", "unauthorized", "disruptive", "breach", "altercation", "intruder", "lockdown", "fight", "weapon"])
                ):
                    action_type = "CLOSE_GATES"
                    responsible_team = "SECURITY"
                    decision_text = f"Emergency lockdown: immediately close and lock all turnstile scanners and access gates in {sector}."
                    reason = f"Security incident '{title_raw}' reported in {sector}."
                    impact = "Prevent unauthorized access, contain perimeter zone, and secure the zone."
                    eta = "1 minute"

                # 2. Medical Incidents
                elif (
                    inc_type == "MEDICAL"
                    or any(k in title or k in desc for k in ["medical", "cardiac", "heat", "exhaustion", "fainting", "collapse", "injured", "injury", "ambulance", "heat exhaustion"])
                ):
                    action_type = "MEDICAL_ESCALATION"
                    responsible_team = "MEDICAL"
                    decision_text = f"Deploy emergency medical responders with trauma kits and triage equipment to {sector}."
                    reason = f"Medical emergency '{title_raw}' reported in {sector}."
                    impact = "Provide rapid first-aid stabilization and coordinate emergency medical transport."
                    eta = "2 minutes"

                # 3. Gate Malfunction / Turnstile Delay
                elif (
                    any(k in title or k in desc for k in ["gate", "turnstile", "scanner", "malfunction", "turnstile failure"])
                ):
                    action_type = "OPEN_GATES"
                    responsible_team = "OPERATIONS"
                    decision_text = f"Unlock and open auxiliary manual check-in lanes and backup scanners at {sector}."
                    reason = f"Equipment malfunction or turnstile failure '{title_raw}' reported at {sector}."
                    impact = "Divert ingress/egress flow to operational check-in channels and lower wait times."
                    eta = "3 minutes"

                # 4. Crowd Congestion / Density
                elif (
                    inc_type == "CROWD"
                    or any(k in title or k in desc for k in ["congestion", "density", "crowd", "crush", "accumulation"])
                ):
                    action_type = "DISPATCH_VOLUNTEERS"
                    responsible_team = "VOLUNTEER"
                    decision_text = f"Deploy 3 crowd-management volunteers to {sector} to direct ingress/egress flow."
                    reason = f"Crowd congestion incident '{title_raw}' reported in {sector}."
                    impact = "Disperse density hotspots, lower local density index, and guide fans."
                    eta = "3 minutes"

                # 5. Default Fallbacks
                else:
                    if priority in ("CRITICAL", "HIGH"):
                        action_type = "DISPATCH_VOLUNTEERS"
                        responsible_team = "VOLUNTEER"
                        decision_text = f"Deploy emergency volunteer taskforce to {sector} to assist security and operations."
                        reason = f"High priority incident '{title_raw}' reported in {sector}."
                        impact = "On-site assessment, crowd guidance, and coordination support."
                        eta = "5 minutes"
                    else:
                        action_type = "BROADCAST_MESSAGES"
                        responsible_team = "OPERATIONS"
                        decision_text = f"Broadcast status alert and request operational report from staff at {sector}."
                        reason = f"Incident '{title_raw}' reported in {sector}."
                        impact = "Maintain operational situational awareness and monitor condition."
                        eta = "3 minutes"

                # Cache check to avoid duplicate decisions within 45s
                cache_key = f"inc_{action_type}_{sector}"
                now_ts = asyncio.get_event_loop().time()
                if cache_key in self._decision_cache and (now_ts - self._decision_cache[cache_key]) < 45.0:
                    return

                self._decision_cache[cache_key] = now_ts

                # Create Decision
                db_decision = Decision(
                    id=str(uuid.uuid4()),
                    prediction_id=None,
                    incident_id=inc_id,
                    decision=decision_text,
                    reason=reason,
                    expected_impact=impact,
                    responsible_team=responsible_team,
                    eta=eta,
                    action_type=action_type
                )
                db.add(db_decision)

                # Send Notification to Operations
                ops_user = db.query(User).join(User.role).filter(User.role.has(name="OPERATIONS")).first()
                ops_id = str(ops_user.id) if ops_user else None
                if ops_id:
                    db.add(Notification(
                        id=str(uuid.uuid4()),
                        recipient_id=ops_id,
                        title=f"Incident Decision: {action_type}",
                        message=f"Mitigation plan initiated: {decision_text}",
                        read=False,
                        priority="HIGH" if priority in ("CRITICAL", "HIGH") else "MEDIUM",
                        type="SYSTEM",
                        created_at=datetime.now(timezone.utc)
                    ))

                db.commit()

                # Publish decision to Event Bus
                try:
                    from app.bus.core import bus
                    await bus.publish(BusEvent(
                        topic="decision.created",
                        source="engine.decision",
                        payload={
                            "id": db_decision.id,
                            "decision": db_decision.decision,
                            "reason": db_decision.reason,
                            "expected_impact": db_decision.expected_impact,
                            "responsible_team": db_decision.responsible_team,
                            "eta": db_decision.eta,
                            "action_type": db_decision.action_type,
                            "created_at": datetime.now(timezone.utc).isoformat()
                        }
                    ))
                except Exception as e_bus:
                    logger.warning(f"[DECISION] Failed to publish decision.created: {e_bus}")

                logger.warning(
                    f"[DECISION] 🚨 MITIGATION ACTIVATED [{action_type}] | Team={responsible_team} | "
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
            
            # Publish decision to Event Bus
            try:
                from app.bus.core import bus
                await bus.publish(BusEvent(
                    topic="decision.created",
                    source="engine.decision",
                    payload={
                        "id": decision_to_save.id,
                        "decision": decision_to_save.decision,
                        "reason": decision_to_save.reason,
                        "expected_impact": decision_to_save.expected_impact,
                        "responsible_team": decision_to_save.responsible_team,
                        "eta": decision_to_save.eta,
                        "action_type": decision_to_save.action_type,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                ))
            except Exception as e_bus:
                logger.warning(f"[DECISION] Failed to publish decision.created: {e_bus}")
            
            logger.info(
                f"[DECISION] Deterministic mitigation activated [{decision_to_save.action_type}] | "
                f"Team={decision_to_save.responsible_team} | Decision={decision_to_save.decision}"
            )


# Global Singleton Instance
decision_engine = DecisionEngine()
