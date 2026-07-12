import pytest
from app.models import User

def test_login_successful_ops(client):
    res = client.post("/auth/login", json={"email": "manager@fifa.com"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_login_unauthorized_email(client):
    res = client.post("/auth/login", json={"email": "notexist@fifa.com"})
    assert res.status_code == 401
    assert "No account found" in res.json()["detail"]

def test_get_profile_me(client):
    # Authenticate first
    login_res = client.post("/auth/login", json={"email": "manager@fifa.com"})
    token = login_res.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/auth/me", headers=headers)
    assert res.status_code == 200
    profile = res.json()
    assert profile["email"] == "manager@fifa.com"
    assert profile["role"] == "OPERATIONS"

def test_refresh_jwt_token(client):
    login_res = client.post("/auth/login", json={"email": "volunteer1@fifa.com"})
    refresh_token = login_res.json()["refresh_token"]

    res = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
