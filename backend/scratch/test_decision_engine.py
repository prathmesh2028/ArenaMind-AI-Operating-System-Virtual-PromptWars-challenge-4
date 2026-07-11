import asyncio
import sys
import os

# Adjust path to import app package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, Base, engine
from app.models import Decision, Prediction, Incident, User, Role, Notification
from app.bus.schemas import BusEvent
from app.engine.decision import decision_engine

async def test_decision_engine():
    print("Starting Decision Engine test...")
    db = SessionLocal()
    try:
        # Create an operations user if not exists
        ops_role = db.query(Role).filter(Role.name == "OPERATIONS").first()
        if not ops_role:
            ops_role = Role(id=2, name="OPERATIONS", description="Stadium Operations Manager")
            db.add(ops_role)
            db.commit()
            
        ops_user = db.query(User).filter(User.email == "manager@fifa.com").first()
        if not ops_user:
            ops_user = User(
                id="11111111-1111-1111-1111-111111111111",
                email="manager@fifa.com",
                display_name="Sarah Jenkins (Ops Chief)",
                role_id=ops_role.id
            )
            db.add(ops_user)
            db.commit()

        # Clear decisions for a clean run
        db.query(Decision).delete()
        db.commit()

        # Test Case 1: Incident raised -> SECURITY (Unauthorized Entry) -> CLOSE_GATES
        event_sec = BusEvent(
            topic="incident.raised",
            source="test",
            payload={
                "incident_id": "11111111-2222-3333-4444-555555555555",
                "sector": "Sector A",
                "priority": "HIGH",
                "incident_type": "SECURITY",
                "title": "Unauthorized Entry at Gate 1",
                "description": "Intruder climbed fence near Gate 1"
            }
        )
        print("Handling Security Incident...")
        await decision_engine.handle_incident_raised(event_sec)

        # Test Case 2: Incident raised -> MEDICAL (Heat Exhaustion) -> MEDICAL_ESCALATION
        event_med = BusEvent(
            topic="incident.raised",
            source="test",
            payload={
                "incident_id": "22222222-3333-4444-5555-666666666666",
                "sector": "Sector B",
                "priority": "HIGH",
                "incident_type": "MEDICAL",
                "title": "Heat Exhaustion case",
                "description": "Spectator collapsed in Sector B seating area"
            }
        )
        print("Handling Medical Incident...")
        await decision_engine.handle_incident_raised(event_med)

        # Test Case 3: Incident raised -> CROWD -> DISPATCH_VOLUNTEERS
        event_crowd = BusEvent(
            topic="incident.raised",
            source="test",
            payload={
                "incident_id": "33333333-4444-5555-6666-777777777777",
                "sector": "Sector C",
                "priority": "HIGH",
                "incident_type": "CROWD",
                "title": "Crowd Congestion",
                "description": "Stairwell ingress queue exceeding capacity limit"
            }
        )
        print("Handling Crowd Incident...")
        await decision_engine.handle_incident_raised(event_crowd)

        # Test Case 4: Incident raised -> GATE MALFUNCTION -> OPEN_GATES
        event_gate = BusEvent(
            topic="incident.raised",
            source="test",
            payload={
                "incident_id": "44444444-5555-6666-7777-888888888888",
                "sector": "Gate 2",
                "priority": "HIGH",
                "incident_type": "MANUAL",
                "title": "Turnstile malfunction at Gate 2",
                "description": "Scanner lanes failed to read barcode tickets"
            }
        )
        print("Handling Gate Malfunction...")
        await decision_engine.handle_incident_raised(event_gate)

        # Query and assert results
        decisions = db.query(Decision).all()
        print(f"Decisions saved in DB: {len(decisions)}")
        assert len(decisions) >= 4, f"Expected at least 4 decisions, got {len(decisions)}"
        
        actions = set(d.action_type for d in decisions)
        print("Action types recorded:", actions)
        
        expected_actions = {"CLOSE_GATES", "MEDICAL_ESCALATION", "DISPATCH_VOLUNTEERS", "OPEN_GATES"}
        for action in expected_actions:
            assert action in actions, f"Missing expected action {action}"

        for d in decisions:
            print("-" * 50)
            print(f"Action Type: {d.action_type}")
            print(f"Decision: {d.decision}")
            print(f"Reason: {d.reason}")
            print(f"Expected Impact: {d.expected_impact}")
            print(f"Responsible Team: {d.responsible_team}")
            print(f"ETA: {d.eta}")
            
            assert d.decision, "Decision field is empty"
            assert d.reason, "Reason field is empty"
            assert d.expected_impact, "Expected impact field is empty"
            assert d.responsible_team, "Responsible team field is empty"
            assert d.eta, "ETA field is empty"

        print("All tests passed successfully!")
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_decision_engine())
