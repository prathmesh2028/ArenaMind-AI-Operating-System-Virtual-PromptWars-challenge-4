import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime, timezone

import google.generativeai as genai
from app.config import settings
from app.database import SessionLocal
from app.models import CrowdMetric, Task, Incident, Transport, Energy, Carbon

logger = logging.getLogger("arenamind.services.gemini")

class GeminiMultiAgentService:
    def __init__(self) -> None:
        self.api_key = settings.GEMINI_API_KEY
        self.client_initialized = False
        # Do not fail on mock key - fallback mode handles it gracefully
        if self.api_key and self.api_key not in ("mock_gemini_key", "mock_key"):
            try:
                genai.configure(api_key=self.api_key)
                self.client_initialized = True
                logger.info("[GEMINI] Gemini SDK successfully configured.")
            except Exception as e:
                logger.warning(f"[GEMINI] Failed to configure Gemini SDK: {e}. Falling back to rule templates.")
        else:
            logger.info("[GEMINI] No valid API key provided. Using rule-based fallback mode.")

        # Agent prompts definitions
        self.agents_prompts: Dict[str, str] = {
            "crowd": (
                "You are the ArenaMind Crowd Intelligence Agent. Your job is to analyze crowd flow, "
                "density levels, gate queue processing rates, and concourse occupancy. Explain any anomalies "
                "and recommend mitigation steps such as digital signage redirection, volunteer dispatch, "
                "or opening reserve check-in lanes. Remember: you MUST NOT make operational decisions yourself. "
                "Always present explanations, insights, and recommendations clearly."
            ),
            "volunteer": (
                "You are the Volunteer Copilot Agent. Your role is to help coordinate volunteers, translate "
                "task instructions into clear guidance, prioritize open tasks, and optimize crew deployment. "
                "Provide direct, supportive, and encouraging feedback. Format task details with clear waypoints. "
                "Remember: you MUST NOT make operational decisions yourself."
            ),
            "medical": (
                "You are the Medical Response Agent. Your role is to monitor heat index stress levels, "
                "explain medical incidents, draft emergency triage descriptions, and suggest hydration tent activations "
                "or paramedic dispatch routes. Maintain a calm, professional, and clinical tone. "
                "Remember: you MUST NOT make operational decisions yourself."
            ),
            "security": (
                "You are the Security Agent. Your role is to explain security incident logs, outline perimeter breach "
                "threat vectors, recommend lockdown boundaries, and draft staff safety advisories. Use clear, "
                "tactical, and authoritative terminology. "
                "Remember: you MUST NOT make operational decisions yourself."
            ),
            "accessibility": (
                "You are the Accessibility Agent. Your role is to assist spectators and stadium crew with accessibility queries. "
                "Outline elevator locations, wheelchair ramps, companion seating, sensory rooms, and audio-described service desks. "
                "Be welcoming, inclusive, and highly descriptive. "
                "Remember: you MUST NOT make operational decisions yourself."
            ),
            "transportation": (
                "You are the Transportation Agent. Your role is to monitor shuttle occupancy, analyze route delays, "
                "suggest fleet injections, and translate transit updates for spectators. Focus on schedules, "
                "headways, and shuttle terminal logistics. "
                "Remember: you MUST NOT make operational decisions yourself."
            ),
            "sustainability": (
                "You are the Sustainability Agent. Your role is to analyze stadium grid active power consumption, "
                "track carbon emission categorizations, and recommend green operation offsets like standby solar "
                "integration or concession waste reductions. Be metric-focused and environmentally conscious. "
                "Remember: you MUST NOT make operational decisions yourself."
            ),
            "executive": (
                "You are the Executive Insights Agent. Your role is to generate strategic summaries of overall stadium operations, "
                "incident command briefs, and risk assessment dashboards. Keep insights clear, concise, and focused "
                "on overall stadium health indicators. "
                "Remember: you MUST NOT make operational decisions yourself."
            )
        }

    def _fetch_context(self, agent_id: str) -> str:
        """Query DB and format real-time context for the specified agent."""
        db = SessionLocal()
        try:
            if agent_id == "crowd":
                from sqlalchemy import func
                subq = db.query(CrowdMetric.sector, func.max(CrowdMetric.timestamp).label("max_ts")).group_by(CrowdMetric.sector).subquery()
                rows = db.query(CrowdMetric).join(subq, (CrowdMetric.sector == subq.c.sector) & (CrowdMetric.timestamp == subq.c.max_ts)).all()
                if not rows:
                    return "No crowd telemetry available yet."
                lines = []
                for r in rows:
                    lines.append(f"- {r.sector}: {r.count}/{r.capacity} fans (density {r.density:.1%}, wait time {r.wait_time_seconds}s, speed {r.velocity}m/s)")
                return "Current Stadium Sector Crowd Densities:\n" + "\n".join(lines)

            elif agent_id == "volunteer":
                tasks = db.query(Task).filter(Task.status.in_(["PENDING", "ACCEPTED"])).limit(10).all()
                if not tasks:
                    return "No active volunteer tasks pending deployment."
                lines = []
                for t in tasks:
                    volunteer_name = t.volunteer.display_name if t.volunteer else "Unassigned"
                    lines.append(f"- Task: {t.title} | Status: {t.status} | Priority: {t.priority} | Assignee: {volunteer_name} | ETA: {t.eta_minutes or '?'}m")
                return "Active Volunteer Tasks List:\n" + "\n".join(lines)

            elif agent_id == "medical":
                incidents = db.query(Incident).filter(Incident.status != "RESOLVED", Incident.title.like("%Medical%")).limit(5).all()
                lines = []
                for inc in incidents:
                    lines.append(f"- Incident: {inc.title} | Priority: {inc.priority} | Status: {inc.status} | Sector: {inc.sector}")
                medical_status = "Active Medical Incidents:\n" + "\n".join(lines) if lines else "No active medical alerts."
                return medical_status

            elif agent_id == "security":
                incidents = db.query(Incident).filter(Incident.status != "RESOLVED", Incident.title.like("%Security%")).limit(5).all()
                lines = []
                for inc in incidents:
                    lines.append(f"- Incident: {inc.title} | Priority: {inc.priority} | Status: {inc.status} | Sector: {inc.sector}")
                security_status = "Active Security Incidents:\n" + "\n".join(lines) if lines else "No active security alerts."
                return security_status

            elif agent_id == "accessibility":
                return (
                    "Stadium Accessibility Specifications:\n"
                    "- Wheelchair ramps located at North Gate A and South Gate B entrances.\n"
                    "- Concourse Elevators situated at Sector A, Sector C, and Sector E.\n"
                    "- Companion/accessible seating rows in upper/lower bowl sections 102, 114, and 205.\n"
                    "- Sensory Rooms open on West Concourse Level 2 for neurodivergent spectators.\n"
                    "- Assistive listening devices and audio-described headsets available at Customer Service Desk B."
                )

            elif agent_id == "transportation":
                from sqlalchemy import func
                subq = db.query(Transport.vehicle_id, func.max(Transport.timestamp).label("max_ts")).group_by(Transport.vehicle_id).subquery()
                rows = db.query(Transport).join(subq, (Transport.vehicle_id == subq.c.vehicle_id) & (Transport.timestamp == subq.c.max_ts)).all()
                if not rows:
                    return "No active transport routes reported."
                lines = []
                for r in rows:
                    lines.append(f"- {r.type} {r.route_name} ({r.vehicle_id}): Status {r.status} | Occupancy {r.occupancy_percentage}% | Next stop: {r.current_stop or 'N/A'}")
                return "Active Transportation Fleet Status:\n" + "\n".join(lines)

            elif agent_id == "sustainability":
                from sqlalchemy import func
                subq = db.query(Energy.grid_zone, func.max(Energy.timestamp).label("max_ts")).group_by(Energy.grid_zone).subquery()
                energy_rows = db.query(Energy).join(subq, (Energy.grid_zone == subq.c.grid_zone) & (Energy.timestamp == subq.c.max_ts)).all()
                
                carbon_rows = db.query(Carbon.category, func.sum(Carbon.amount_kg).label("total")).group_by(Carbon.category).all()
                
                lines = ["Stadium Active Power load per Grid Zone:"]
                for e in energy_rows:
                    lines.append(f"  * {e.grid_zone}: {e.active_power_kw} kW (Load {e.load_percentage:.1f}%)")
                lines.append("Cumulative Operations Carbon Footprint:")
                total_co2 = 0.0
                for c in carbon_rows:
                    lines.append(f"  * {c.category}: {c.total:.1f} kg CO2")
                    total_co2 += c.total
                lines.append(f"  * Total: {total_co2:.1f} kg CO2")
                return "\n".join(lines)

            elif agent_id == "executive":
                from sqlalchemy import func
                total_fans = db.query(func.sum(CrowdMetric.count)).scalar() or 0
                active_inc = db.query(func.count(Incident.id)).filter(Incident.status != "RESOLVED").scalar() or 0
                delayed_fleet = db.query(func.count(Transport.id)).filter(Transport.status == "DELAYED").scalar() or 0
                
                return (
                    "Stadium Operations Executive Snapshot:\n"
                    f"- Total active spectators inside seating bowls: {total_fans}\n"
                    f"- Active unresolved incidents: {active_inc}\n"
                    f"- Delayed transportation units: {delayed_fleet}\n"
                    "- Overall status: Operational with active monitoring protocols engaged."
                )

            else:
                return "No telemetry details available."
        except Exception as e:
            logger.error(f"[GEMINI] Context fetch failed: {e}", exc_info=True)
            return "Unable to retrieve database telemetry due to context error."
        finally:
            db.close()

    async def chat_stream(self, agent_id: str, message: str, context: Optional[dict] = None) -> AsyncGenerator[str, None]:
        """Streams responses for a given agent. Cascades to templates if Gemini fails or is mock."""
        system_prompt = self.agents_prompts.get(agent_id, "You are a stadium operations assistant.")
        realtime_context = self._fetch_context(agent_id)
        
        full_prompt = (
            f"SYSTEM PROMPT:\n{system_prompt}\n\n"
            f"REALTIME STADIUM DATA:\n{realtime_context}\n\n"
            f"ADDITIONAL CONTEXT:\n{context or 'None'}\n\n"
            f"USER QUERY: {message}\n"
        )

        use_gemini = self.client_initialized
        if use_gemini:
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Iterate and stream chunks
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: model.generate_content(full_prompt, stream=True)
                )
                
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
                        await asyncio.sleep(0.01)
                return
            except Exception as e:
                logger.error(f"[GEMINI] Streaming failed: {e}. Cascading to fallback...", exc_info=True)

        # Fallback Generator: Simulates streaming by splitting fallback text
        fallback_text = self._generate_fallback(agent_id, message, realtime_context)
        words = fallback_text.split(" ")
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i:i+3]) + " "
            yield chunk
            await asyncio.sleep(0.05)

    def _generate_fallback(self, agent_id: str, message: str, context: str) -> str:
        """Generate static detailed response summaries when Gemini is unavailable."""
        if agent_id == "crowd":
            return (
                "**[Crowd Intelligence Fallback Report]**\n\n"
                f"Based on real-time crowd telemetry:\n{context}\n\n"
                "**Operational Analysis & Recommendations:**\n"
                "1. If any sector density exceeds 85%, deploy crowd volunteers immediately to manage ingress check-in channels.\n"
                "2. Open backup turnstiles and update digital concourse signage to guide spectators to lower-congestion gate corridors.\n"
                "3. Operational decisions must be processed via the Rule Engine."
            )
        elif agent_id == "volunteer":
            return (
                "**[Volunteer Copilot Fallback Crew Brief]**\n\n"
                "Our current volunteer assignment roster displays:\n"
                f"{context}\n\n"
                "**Deployment Directives:**\n"
                "- High-priority tasks require immediate on-scene redirection at concourse junctions.\n"
                "- Keep wayfinding pathways clear and physically wave signs to guide stadium ingress waves.\n"
                "- Volunteers must log all completions through the Volunteer Portal."
            )
        elif agent_id == "medical":
            return (
                "**[Medical Response Fallback Triage Brief]**\n\n"
                "Current Medical Status Summary:\n"
                f"{context}\n\n"
                "**Standard Medical Protocol:**\n"
                "- For heat exhaustion or collapse, activate local hydration stations, distribute ice packs, and monitor signs.\n"
                "- For chest pain or cardiac alerts, immediately dispatch paramedics with AED to the target sector.\n"
                "- Triage incidents as high/critical until responders confirm status."
            )
        elif agent_id == "security":
            return (
                "**[Security Response Fallback Tactical Brief]**\n\n"
                "Current Security Incidents Summary:\n"
                f"{context}\n\n"
                "**Standard Security Procedures:**\n"
                "- In case of unauthorized entry or perimeter breach, trigger CLOSE_GATES lockdown protocol on turnstile lines.\n"
                "- For minor altercations, deploy security supervisors to disperse crowd tension.\n"
                "- Do not engage hostiles without tactical crew backup."
            )
        elif agent_id == "accessibility":
            return (
                "**[Accessibility Services Fallback Guide]**\n\n"
                f"{context}\n\n"
                "**Services Summary:**\n"
                "- Elevators: Concourse elevator lines in Sectors A, C, and E are fully operational.\n"
                "- Sensory rooms: Located in West Concourse Level 2 for neurodivergent fans.\n"
                "- Equipment: Headsets for audio-described commentary can be claimed at Information Desk B."
            )
        elif agent_id == "transportation":
            return (
                "**[Transportation Logistics Fallback Summary]**\n\n"
                f"{context}\n\n"
                "**Transit Directives:**\n"
                "- Shuttle Delay Mitigation: For delayed routes, inject standby backup buses from the transport depot.\n"
                "- Shuttle headways should be maintained under 10 minutes to avoid long queuing at terminal drops."
            )
        elif agent_id == "sustainability":
            return (
                "**[Sustainability Operations Fallback Summary]**\n\n"
                f"{context}\n\n"
                "**Energy Directives:**\n"
                "- When power load limits trip, initiate concession HVAC load shedding.\n"
                "- Ensure renewable offset solar grids are running at peak output to offset matching diesel emissions."
            )
        elif agent_id == "executive":
            return (
                "**[Executive Command Command-Center Snapshot]**\n\n"
                "Current System Health Indicators:\n"
                f"{context}\n\n"
                "**Strategic Directives:**\n"
                "- Overall stadium operations are stable. Priority risks are managed by the deterministic rule engine.\n"
                "- Maintain communication headways between on-field responders and central command center."
            )
        else:
            return (
                f"**[Operations Assistant Fallback]**\n\n"
                "Here is the real-time telemetry gathered:\n"
                f"{context}\n\n"
                "We are monitoring operations. Please submit specific queries to specialized agents."
            )

# Global Singleton Service
gemini_agent_service = GeminiMultiAgentService()
