import logging
from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import (
    Role, User, Event, Incident, Prediction, Recommendation, Task,
    Notification, CrowdMetric, Transport, Parking, Energy, Carbon,
    ReplayLog, Telemetry
)

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("arenamind-seed")

def seed_database():
    db: Session = SessionLocal()
    try:
        logger.info("Starting database seeding...")

        # 1. Clear existing data in reverse order of foreign keys
        logger.info("Clearing existing tables...")
        db.query(Telemetry).delete()
        db.query(ReplayLog).delete()
        db.query(Carbon).delete()
        db.query(Energy).delete()
        db.query(Parking).delete()
        db.query(Transport).delete()
        db.query(CrowdMetric).delete()
        db.query(Notification).delete()
        db.query(Task).delete()
        db.query(Recommendation).delete()
        db.query(Prediction).delete()
        db.query(Incident).delete()
        db.query(Event).delete()
        db.query(User).delete()
        db.query(Role).delete()
        db.commit()

        # 2. Seed Roles
        logger.info("Seeding roles...")
        roles = {
            "ADMIN": Role(id=1, name="ADMIN", description="System administrator with root control"),
            "OPERATIONS": Role(id=2, name="OPERATIONS", description="Stadium Operations Manager"),
            "VOLUNTEER": Role(id=3, name="VOLUNTEER", description="On-field volunteer staff"),
            "MEDICAL": Role(id=4, name="MEDICAL", description="First responder and medical staff"),
            "SECURITY": Role(id=5, name="SECURITY", description="Stadium safety and security personnel"),
            "FAN": Role(id=6, name="FAN", description="Tournament ticket holder / spectator")
        }
        for role in roles.values():
            db.add(role)
        db.commit()

        # 3. Seed Users
        logger.info("Seeding users...")
        user_ops = User(
            id="11111111-1111-1111-1111-111111111111",
            email="manager@fifa.com",
            display_name="Sarah Jenkins (Ops Chief)",
            role_id=roles["OPERATIONS"].id
        )
        user_vol1 = User(
            id="22222222-2222-2222-2222-222222222222",
            email="volunteer1@fifa.com",
            display_name="Juan Alvarez",
            role_id=roles["VOLUNTEER"].id
        )
        user_vol2 = User(
            id="33333333-3333-3333-3333-333333333333",
            email="volunteer2@fifa.com",
            display_name="Amina Sow",
            role_id=roles["VOLUNTEER"].id
        )
        user_med = User(
            id="44444444-4444-4444-4444-444444444444",
            email="medical1@fifa.com",
            display_name="Dr. Kenji Sato",
            role_id=roles["MEDICAL"].id
        )
        user_sec = User(
            id="55555555-5555-5555-5555-555555555555",
            email="security1@fifa.com",
            display_name="Officer Marcus Vance",
            role_id=roles["SECURITY"].id
        )
        user_fan = User(
            id="66666666-6666-6666-6666-666666666666",
            email="fan1@gmail.com",
            display_name="Diego Rossi",
            role_id=roles["FAN"].id
        )
        
        db.add_all([user_ops, user_vol1, user_vol2, user_med, user_sec, user_fan])
        db.commit()

        # 4. Seed Telemetry (Crowd Metrics)
        logger.info("Seeding crowd metrics...")
        now = datetime.now(timezone.utc)
        sectors = ["Sector A", "Sector B", "Sector C", "Sector D", "Sector E", "Sector F"]
        for sector in sectors:
            count = 6800 if sector == "Sector D" else 4200
            capacity = 8000
            metric = CrowdMetric(
                id=str(uuid.uuid4()),
                timestamp=now,
                sector=sector,
                count=count,
                capacity=capacity,
                density=count / capacity,
                velocity=1.2 if sector != "Sector D" else 0.4, # Slowed speed in Sector D
                wait_time_seconds=120 if sector != "Sector D" else 960, # High wait time in Sector D
                created_at=now
            )
            db.add(metric)
        db.commit()

        # 5. Seed Telemetry (Parking & Transit)
        logger.info("Seeding parking & transport...")
        parking_lots = [
            ("North Lot A", 1500, 1420, "CLOSED"),
            ("South Lot B", 2500, 1850, "OPEN"),
            ("East Lot C", 2000, 800, "OPEN")
        ]
        for name, cap, occupied, status in parking_lots:
            park = Parking(
                id=str(uuid.uuid4()),
                timestamp=now,
                lot_name=name,
                total_spots=cap,
                occupied_spots=occupied,
                occupancy_percentage=int((occupied / cap) * 100),
                status=status,
                created_at=now
            )
            db.add(park)

        shuttles = [
            ("Express A", "SH-012", "SHUTTLE", "DELAYED", "Concourse West", 90, 25.7749, -80.1917),
            ("Transit Metro 1", "TR-004", "TRAIN", "ON_TIME", "Stadium North Link", 45, 25.7801, -80.1850),
            ("Park & Ride Bus", "B-882", "BUS", "ON_TIME", "South Lot Gate", 75, 25.7690, -80.2010)
        ]
        for route, vid, type_, status, stop, occ, lat, lon in shuttles:
            tran = Transport(
                id=str(uuid.uuid4()),
                timestamp=now,
                route_name=route,
                vehicle_id=vid,
                type=type_,
                status=status,
                current_stop=stop,
                occupancy_percentage=occ,
                latitude=lat,
                longitude=lon,
                created_at=now
            )
            db.add(tran)
        db.commit()

        # 6. Seed Telemetry (Energy & Carbon)
        logger.info("Seeding energy & carbon offsets...")
        zones = ["Stadium Bowl", "West Concourse", "East Concourse", "Media Center"]
        for zone in zones:
            load = 88.5 if zone == "Stadium Bowl" else 62.0
            energy = Energy(
                id=str(uuid.uuid4()),
                timestamp=now,
                grid_zone=zone,
                active_power_kw=1240.5 if zone == "Stadium Bowl" else 480.0,
                reactive_power_kvar=150.0,
                voltage=480.0,
                load_percentage=load,
                carbon_offset_kg=24.5,
                created_at=now
            )
            db.add(energy)

        emissions = [
            ("Grid Electricity", 3450.2, "ENERGY"),
            ("Diesel Shuttle Fleet", 1820.5, "TRANSPORT"),
            ("Concession Operations", 850.0, "FOOD_WASTE")
        ]
        for source, val, category in emissions:
            carb = Carbon(
                id=str(uuid.uuid4()),
                timestamp=now,
                emission_source=source,
                amount_kg=val,
                category=category,
                created_at=now
            )
            db.add(carb)
        db.commit()

        # 7. Seed Incidents, Predictions, Recommendations, and Tasks (Congestion Scenario)
        logger.info("Seeding congestion incident and AI layers...")
        
        # Incident
        incident = Incident(
            id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            title="Gate 2 Ingress Congestion",
            description="Turnstile check speed dropped, Sector D capacity exceeding 85%. Crowd accumulation warning.",
            status="MITIGATING",
            priority="HIGH",
            sector="Sector D",
            reporter_id=user_ops.id,
            assignee_id=user_vol1.id,
            created_at=now - timedelta(minutes=15)
        )
        db.add(incident)
        db.commit()

        # Prediction
        prediction = Prediction(
            id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            incident_id=incident.id,
            type="CROWD_CONGESTION",
            probability=0.92,
            confidence=0.95,
            reasoning="Ingress velocity at Gate 2 is 85 fans/min while processing rate is restricted to 40 fans/min due to turnstile errors.",
            suggested_actions={"open_adjacent_gates": True, "reroute_signage": True, "volunteer_dispatch": 3},
            target_sector="Sector D",
            created_at=now - timedelta(minutes=14)
        )
        db.add(prediction)
        db.commit()

        # Recommendation
        recs = [
            Recommendation(
                id=str(uuid.uuid4()),
                prediction_id=prediction.id,
                title="Reroute Overflow to Gate 3",
                description="Gate 3 has 15% occupancy. Route incoming traffic from South Shuttle drop point to Gate 3.",
                confidence=0.91,
                status="ACCEPTED",
                created_at=now - timedelta(minutes=14)
            ),
            Recommendation(
                id=str(uuid.uuid4()),
                prediction_id=prediction.id,
                title="Deploy Crowd Control Volunteers",
                description="Send 3 volunteers to Gate 2 entrance corridor to direct fans physically.",
                confidence=0.88,
                status="ACCEPTED",
                created_at=now - timedelta(minutes=14)
            )
        ]
        db.add_all(recs)

        # Tasks
        task1 = Task(
            id="cccccccc-cccc-cccc-cccc-cccccccccccc",
            title="Manual Redirection at Gate 2 Corridor",
            description="Position yourself at Sector D corridor intersection. Wave fans toward Gate 3 entrance.",
            status="ACCEPTED",
            priority="HIGH",
            incident_id=incident.id,
            volunteer_id=user_vol1.id,
            created_at=now - timedelta(minutes=12),
            eta_minutes=5
        )
        task2 = Task(
            id="dddddddd-dddd-dddd-dddd-dddddddddddd",
            title="Open Turnstile 3B Auxiliary Gate",
            description="Unlock and engage the auxiliary manual pass gate at turnstile row 3B.",
            status="PENDING",
            priority="MEDIUM",
            incident_id=incident.id,
            volunteer_id=user_vol2.id,
            created_at=now - timedelta(minutes=12),
            eta_minutes=10
        )
        db.add_all([task1, task2])

        # Notifications
        notif1 = Notification(
            id=str(uuid.uuid4()),
            recipient_id=user_vol1.id,
            title="Urgent Crowd Dispatch",
            message="You have been assigned to: Manual Redirection at Gate 2 Corridor. ETA target is 5 mins.",
            read=False,
            priority="HIGH",
            type="TASK_ASSIGNMENT",
            created_at=now - timedelta(minutes=12)
        )
        notif2 = Notification(
            id=str(uuid.uuid4()),
            recipient_id=user_ops.id,
            title="AI Alert: Ingress Congestion Warning",
            message="Crowd congestion predicted at Gate 2 (92% probability). Mitigation plan initiated.",
            read=True,
            priority="HIGH",
            type="INCIDENT_ALERT",
            created_at=now - timedelta(minutes=14)
        )
        db.add_all([notif1, notif2])
        db.commit()

        # 8. Seed Events & Replay Logs (for scenario logs history)
        logger.info("Seeding event bus stream and replay logs...")
        events_to_seed = [
            ("2026-07-07T15:45:00Z", "CROWD_SPIKE", "sensor_turnstile_2", {"sector": "Sector D", "value": 0.82, "details": {"count": 6560}}),
            ("2026-07-07T15:46:00Z", "QUEUE_ALERT", "sensor_gate_2_queue", {"sector": "Sector D", "value": 960, "details": {"wait_time_seconds": 960}}),
            ("2026-07-07T15:47:00Z", "DECISION_MITIGATION", "engine_decision", {"sector": "Sector D", "value": 1.0, "details": {"incident_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "action": "VOLUNTEER_DISPATCH"}}),
            ("2026-07-07T15:48:00Z", "TASK_STATUS", "volunteer_app_juan", {"sector": "Sector D", "value": 1.0, "details": {"task_id": "cccccccc-cccc-cccc-cccc-cccccccccccc", "status": "ACCEPTED"}})
        ]
        
        session_id = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
        for ts_str, ev_type, source, payload in events_to_seed:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            ev = Event(
                id=str(uuid.uuid4()),
                timestamp=ts,
                type=ev_type,
                source=source,
                payload=payload
            )
            db.add(ev)
            
            # Log to Replay logs for replay scenario
            rep = ReplayLog(
                id=str(uuid.uuid4()),
                replay_session_id=session_id,
                timestamp=ts,
                event_type=ev_type,
                payload=payload,
                created_at=now
            )
            db.add(rep)
        db.commit()

        logger.info("Database seeding completed successfully.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error during seeding: {str(e)}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    # Create tables if not exists, then seed
    Base.metadata.create_all(bind=engine)
    seed_database()
