import pytest
import time
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base
from app.services.seed_data import seed_database

# Initialize database schema for tests
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
seed_database()

client = TestClient(app)

def test_device_token_registration():
    """Verify endpoint to register FCM device tokens."""
    # 1. Login driver user
    login_res = client.post("/api/v1/auth/login", json={
        "email": "driver@parkiq.com",
        "password": "driver123"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # 2. Register token
    test_token = f"fcm_test_device_token_{int(time.time())}"
    res = client.post(
        "/api/v1/notifications/register-token",
        json={"token": test_token},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 201
    assert res.json()["status"] in ["REGISTERED", "EXISTS"]

def test_websocket_echo():
    """Verify WebSocket server connects and handles client messages."""
    # Login to get token
    login_res = client.post("/api/v1/auth/login", json={
        "email": "driver@parkiq.com",
        "password": "driver123"
    })
    token = login_res.json()["access_token"]
    
    with client.websocket_connect(f"/api/v1/notifications/ws?token={token}") as websocket:
        websocket.send_text("Ping ParkIQ")
        data = websocket.receive_json()
        assert data["status"] == "ACK"
        assert data["echo"] == "Ping ParkIQ"

def test_websocket_parking_started_broadcast():
    """Verify check-in event broadcasts live WebSocket alerts to connected monitors."""
    # 1. Login driver to register vehicle and start session
    login_res = client.post("/api/v1/auth/login", json={
        "email": "driver@parkiq.com",
        "password": "driver123"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    unique_plate = f"DL-WS-{int(time.time()) % 10000:04d}"
    v_res = client.post(
        "/api/v1/vehicles",
        json={"license_plate": unique_plate, "vehicle_type": "SEDAN"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert v_res.status_code == 201
    qr_token = v_res.json()["qr_token"]

    # Retrieve slot info
    lots_res = client.get("/api/v1/sessions/lots")
    lot_id = lots_res.json()[0]["id"]
    slots_res = client.get(f"/api/v1/sessions/lots/{lot_id}/slots")
    vacant_slots = [s for s in slots_res.json() if s["status"] == "VACANT"]
    assert len(vacant_slots) > 0
    slot = vacant_slots[0]

    # 2. Open WebSocket client
    with client.websocket_connect(f"/api/v1/notifications/ws?token={token}") as websocket:
        # 3. Trigger check-in
        start_res = client.post(
            "/api/v1/sessions/start",
            json={
                "qr_token": qr_token,
                "slot_id": slot["id"],
                "expected_duration_minutes": 60
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert start_res.status_code == 201
        session_id = start_res.json()["id"]

        # 4. Receive and verify broadcast message on WebSocket
        broadcast_data = websocket.receive_json()
        assert broadcast_data["event"] == "parking_started"
        assert broadcast_data["session_id"] == session_id
        assert broadcast_data["slot_number"] == slot["slot_number"]
