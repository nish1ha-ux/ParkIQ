import pytest
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base
from app.services.seed_data import seed_database
from app.core.qr_crypto import qr_crypto_engine

# Initialize Database Schema for Testing
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
seed_database()

client = TestClient(app)

def get_driver_auth_header():
    res = client.post("/api/v1/auth/login", json={
        "email": "driver@parkiq.com",
        "password": "driver123"
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_start_parking_session():
    headers = get_driver_auth_header()

    unique_plate = f"KA-55-PK-{int(time.time() * 100) % 10000:04d}"
    # 1. Register new vehicle
    v_res = client.post("/api/v1/vehicles",
        json={"license_plate": unique_plate, "vehicle_type": "SUV"},
        headers=headers
    )
    assert v_res.status_code == 201
    vehicle_data = v_res.json()
    qr_token = vehicle_data["qr_token"]

    # 2. Get vacant slot ID
    lots_res = client.get("/api/v1/sessions/lots")
    lot_id = lots_res.json()[0]["id"]
    slots_res = client.get(f"/api/v1/sessions/lots/{lot_id}/slots")
    vacant_slot = [s for s in slots_res.json() if s["status"] == "VACANT"][0]

    # 3. Start parking session for 90 minutes
    start_res = client.post("/api/v1/sessions/start",
        json={
            "qr_token": qr_token,
            "slot_id": vacant_slot["id"],
            "expected_duration_minutes": 90
        },
        headers=headers
    )
    assert start_res.status_code == 201
    s_data = start_res.json()
    assert s_data["status"] == "ACTIVE"
    assert s_data["remaining_minutes"] >= 88 and s_data["remaining_minutes"] <= 90
    assert s_data["is_expiring_soon"] == False

def test_extend_parking_session():
    headers = get_driver_auth_header()

    # Fetch active session
    active_res = client.get("/api/v1/sessions/active", headers=headers)
    assert active_res.status_code == 200
    active_sessions = active_res.json()
    assert len(active_sessions) > 0

    session_id = active_sessions[0]["id"]
    initial_remaining = active_sessions[0]["remaining_minutes"]

    # Extend by 45 minutes
    ext_res = client.post(f"/api/v1/sessions/{session_id}/extend",
        json={"additional_minutes": 45},
        headers=headers
    )
    assert ext_res.status_code == 200
    ext_data = ext_res.json()
    assert ext_data["remaining_minutes"] >= initial_remaining + 44

def test_end_parking_session():
    headers = get_driver_auth_header()

    # Get active session vehicle QR token
    active_res = client.get("/api/v1/sessions/active", headers=headers)
    active_sessions = active_res.json()
    assert len(active_sessions) > 0
    vehicle_id = active_sessions[0]["vehicle_id"]

    # Get vehicle details
    v_list = client.get("/api/v1/vehicles", headers=headers).json()
    target_v = [v for v in v_list if v["id"] == vehicle_id][0]

    # End parking session
    end_res = client.post("/api/v1/sessions/end",
        json={"qr_token": target_v["qr_token"]},
        headers=headers
    )
    assert end_res.status_code == 200
    end_data = end_res.json()
    assert end_data["status"] == "CLOSED"
    assert end_data["remaining_minutes"] == 0

def test_parking_history():
    headers = get_driver_auth_header()

    history_res = client.get("/api/v1/sessions/history", headers=headers)
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert len(history_data) >= 1
    assert history_data[0]["status"] != "ACTIVE"
