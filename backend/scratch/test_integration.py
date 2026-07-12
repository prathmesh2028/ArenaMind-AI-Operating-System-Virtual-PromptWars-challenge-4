import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

def test_system_integration():
    print("====================================================")
    print("      ARENAMIND INTEGRATION & VALIDATION HARNESS      ")
    print("====================================================\n")

    # 1. Test Authentication Roles
    print("1. Validating Authentication and Roles...")
    tokens = {}
    emails = {
        "operations": "manager@fifa.com",
        "fan": "fan1@gmail.com",
        "volunteer": "volunteer1@fifa.com"
    }

    for role, email in emails.items():
        try:
            res = requests.post(f"{API_BASE_URL}/auth/login", json={"email": email})
            if res.status_code == 200:
                data = res.json()
                tokens[role] = data["access_token"]
                print(f"  [PASS] Authenticated {role} role using {email}")
            else:
                print(f"  [FAIL] Failed to authenticate {role} role (status: {res.status_code})")
        except Exception as e:
            print(f"  [ERROR] Connection error during auth for {role}: {str(e)}")
            return

    if len(tokens) < 3:
        print("\n[CRITICAL] Missing required authentication credentials. Aborting remaining tests.")
        return

    headers_ops = {"Authorization": f"Bearer {tokens['operations']}"}
    headers_fan = {"Authorization": f"Bearer {tokens['fan']}"}
    headers_vol = {"Authorization": f"Bearer {tokens['volunteer']}"}

    # 2. Validate Fan Portal Endpoints
    print("\n2. Validating Fan Portal Logistics REST APIs...")
    fan_endpoints = [
        ("crowd-status", "/fan/crowd-status"),
        ("transport", "/fan/transport"),
        ("parking", "/fan/parking"),
        ("notifications", "/fan/notifications")
    ]
    for name, path in fan_endpoints:
        res = requests.get(f"{API_BASE_URL}{path}", headers=headers_fan)
        if res.status_code == 200:
            print(f"  [PASS] Fan GET {path} returned 200 OK")
        else:
            print(f"  [FAIL] Fan GET {path} returned {res.status_code}")

    # 3. Validate Volunteer Portal Endpoints
    print("\n3. Validating Volunteer Portal Task Management APIs...")
    vol_endpoints = [
        ("tasks", "/volunteer/tasks"),
        ("notifications", "/volunteer/notifications")
    ]
    for name, path in vol_endpoints:
        res = requests.get(f"{API_BASE_URL}{path}", headers=headers_vol)
        if res.status_code == 200:
            print(f"  [PASS] Volunteer GET {path} returned 200 OK")
        else:
            print(f"  [FAIL] Volunteer GET {path} returned {res.status_code}")

    # 4. Validate Incident Creation (SOS Panic reporting)
    print("\n4. Validating SOS Distress reporting to Operations DB...")
    mock_incident = {
        "title": "Integration Test Panic Event",
        "description": "Triggered by automated test suit to verify end-to-end telemetry propagation.",
        "priority": "CRITICAL",
        "sector": "Sector D"
    }
    res_inc = requests.post(f"{API_BASE_URL}/incidents", headers=headers_fan, json=mock_incident)
    incident_id = None
    if res_inc.status_code == 201:
        incident_id = res_inc.json()["id"]
        print(f"  [PASS] Created SOS incident (ID: {incident_id}) successfully")
    else:
        print(f"  [FAIL] Failed to create SOS incident (status: {res_inc.status_code})")

    # 5. Validate Decisions Logging
    print("\n5. Validating Decision Matrix logs...")
    res_dec = requests.get(f"{API_BASE_URL}/decisions?page_size=5", headers=headers_ops)
    if res_dec.status_code == 200:
        print(f"  [PASS] Operations GET /decisions returned 200 OK")
    else:
        print(f"  [FAIL] Operations GET /decisions returned {res_dec.status_code}")

    # 6. Validate Scenario Replay sessions listing
    print("\n6. Validating Scenario Replay Session listings...")
    res_repl = requests.get(f"{API_BASE_URL}/replay/sessions", headers=headers_ops)
    if res_repl.status_code == 200:
        print(f"  [PASS] Operations GET /replay/sessions returned 200 OK")
        sessions = res_repl.json()
        if len(sessions) > 0:
            sess_id = sessions[0]["replay_session_id"]
            res_events = requests.get(f"{API_BASE_URL}/replay/sessions/{sess_id}/events", headers=headers_ops)
            if res_events.status_code == 200:
                print(f"  [PASS] Operations GET /replay/sessions/{sess_id}/events returned 200 OK")
            else:
                print(f"  [FAIL] Failed to load event logs for session {sess_id}")
    else:
        print(f"  [FAIL] Operations GET /replay/sessions returned {res_repl.status_code}")

    # 7. Clean up mock incident
    if incident_id:
        print("\n7. Resolving mock integration incident...")
        res_resolve = requests.patch(
            f"{API_BASE_URL}/incidents/{incident_id}",
            headers=headers_ops,
            json={"status": "RESOLVED"}
        )
        if res_resolve.status_code == 200:
            print("  [PASS] Mock incident marked as RESOLVED")
        else:
            print("  [FAIL] Failed to resolve mock incident")

    print("\n====================================================")
    print("             INTEGRATION TESTS COMPLETE             ")
    print("====================================================")

if __name__ == "__main__":
    test_system_integration()
