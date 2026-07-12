import pytest
from app.models import Incident, Task, Role, User
import uuid

def get_auth_headers(client, email: str):
    res = client.post("/auth/login", json={"email": email})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_incidents_crud(client):
    headers_fan = get_auth_headers(client, "fan1@gmail.com")
    headers_ops = get_auth_headers(client, "manager@fifa.com")

    # 1. Post new SOS incident
    mock_incident = {
        "title": "Medical distress Sector D",
        "description": "Fan reported heat exhaust symptoms near Gate 3.",
        "priority": "HIGH",
        "sector": "Sector D"
    }
    res_post = client.post("/incidents", headers=headers_fan, json=mock_incident)
    assert res_post.status_code == 201
    data = res_post.json()
    assert data["title"] == "Medical distress Sector D"
    incident_id = data["id"]

    # 2. Get list of incidents
    res_get = client.get("/incidents", headers=headers_ops)
    assert res_get.status_code == 200
    assert len(res_get.json()) >= 1

    # 3. Patch status to MITIGATING
    res_patch = client.patch(f"/incidents/{incident_id}", headers=headers_ops, json={"status": "MITIGATING"})
    assert res_patch.status_code == 200
    assert res_patch.json()["status"] == "MITIGATING"


def test_volunteer_tasks_workflow(client, db):
    headers_ops = get_auth_headers(client, "manager@fifa.com")
    headers_vol = get_auth_headers(client, "volunteer1@fifa.com")

    # Seed an incident first
    incident = Incident(
        id=str(uuid.uuid4()),
        title="Test Incident for Task",
        description="Verification",
        status="ACTIVE",
        priority="HIGH",
        sector="Sector E"
    )
    db.add(incident)
    db.commit()

    # Seed a task
    task_id = str(uuid.uuid4())
    task = Task(
        id=task_id,
        title="Escort paramedic to Sector E",
        status="PENDING",
        priority="HIGH",
        incident_id=incident.id,
        volunteer_id="22222222-2222-2222-2222-222222222222" # volunteer1 ID
    )
    db.add(task)
    db.commit()

    # 1. Get volunteer tasks
    res_tasks = client.get("/volunteer/tasks", headers=headers_vol)
    assert res_tasks.status_code == 200
    assert len(res_tasks.json()) >= 1

    # 2. Accept task
    res_accept = client.patch(f"/volunteer/tasks/{task_id}/accept", headers=headers_vol)
    assert res_accept.status_code == 200
    assert res_accept.json()["status"] == "ACCEPTED"

    # 3. Complete task
    res_comp = client.patch(f"/volunteer/tasks/{task_id}/complete", headers=headers_vol)
    assert res_comp.status_code == 200
    assert res_comp.json()["status"] == "COMPLETED"


def test_fan_logistics_endpoints(client):
    headers_fan = get_auth_headers(client, "fan1@gmail.com")

    # 1. Test crowd status
    res = client.get("/fan/crowd-status", headers=headers_fan)
    assert res.status_code == 200
    assert "sectors" in res.json()

    # 2. Test transport schedules
    res = client.get("/fan/transport", headers=headers_fan)
    assert res.status_code == 200
    assert "vehicles" in res.json()

    # 3. Test parking occupancy
    res = client.get("/fan/parking", headers=headers_fan)
    assert res.status_code == 200
    assert "parking_lots" in res.json()

    # 4. Test notifications
    res = client.get("/fan/notifications", headers=headers_fan)
    assert res.status_code == 200
    assert "notifications" in res.json()


def test_predictions_and_decisions_endpoints(client):
    headers_ops = get_auth_headers(client, "manager@fifa.com")

    # 1. Get predictions list
    res_pred = client.get("/predictions", headers=headers_ops)
    assert res_pred.status_code == 200

    # 2. Get decisions logs
    res_dec = client.get("/decisions", headers=headers_ops)
    assert res_dec.status_code == 200


def test_replay_endpoints(client):
    headers_ops = get_auth_headers(client, "manager@fifa.com")

    # 1. Get replay sessions list
    res = client.get("/replay/sessions", headers=headers_ops)
    assert res.status_code == 200

    # 2. Get events from specific session ID (using mock guid)
    session_id = str(uuid.uuid4())
    res_events = client.get(f"/replay/sessions/{session_id}/events", headers=headers_ops)
    assert res_events.status_code == 200
