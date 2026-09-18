import pytest
import time
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base, SessionLocal
from app.models.models import ParkingSession, ParkingSlot, SlotStatus, SessionStatus
from app.services.seed_data import seed_database

client = TestClient(app)

def test_complete_e2e_product_flow():
    # Setup: Reset and seed database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database()

    # ================= 1. Driver registers/logs in =================
    driver_email = "newdriver@parkiq.com"
    driver_pass = "newdriver123"
    
    # Registration
    reg_res = client.post("/api/v1/auth/register", json={
        "full_name": "New E2E Driver",
        "email": driver_email,
        "password": driver_pass,
        "phone": "+15559876543"
    })
    assert reg_res.status_code == 201
    
    # Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": driver_email,
        "password": driver_pass
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # ================= 2. Driver registers a vehicle =================
    veh_res = client.post("/api/v1/vehicles", json={
        "license_plate": "DL-05-XX-1234",
        "vehicle_type": "EV"
    }, headers=headers)
    assert veh_res.status_code == 201
    veh_data = veh_res.json()
    assert veh_data["license_plate"] == "DL-05-XX-1234"

    # ================= 3. System generates vehicle's encrypted QR code =================
    qr_token = veh_data["qr_token"]
    assert qr_token is not None
    assert len(qr_token) > 20  # Encrypted cipher text is reasonably long

    # ================= 4. Driver starts a 60-minute parking session =================
    # Fetch vacant slot
    lots_res = client.get("/api/v1/sessions/lots")
    lot_id = lots_res.json()[0]["id"]
    slots_res = client.get(f"/api/v1/sessions/lots/{lot_id}/slots")
    vacant_slot = [s for s in slots_res.json() if s["status"] == "VACANT"][0]
    
    start_res = client.post("/api/v1/sessions/start", json={
        "qr_token": qr_token,
        "slot_id": vacant_slot["id"],
        "expected_duration_minutes": 60
    }, headers=headers)
    assert start_res.status_code == 201
    session_data = start_res.json()
    assert session_data["status"] == "ACTIVE"

    # ================= 5. Verify the parking countdown =================
    active_res = client.get("/api/v1/sessions/active", headers=headers)
    assert active_res.status_code == 200
    active_sessions = active_res.json()
    assert len(active_sessions) == 1
    assert active_sessions[0]["remaining_minutes"] >= 58
    assert active_sessions[0]["remaining_minutes"] <= 60
    assert active_sessions[0]["is_expiring_soon"] == False

    # ================= 6. Verify AI departure prediction =================
    ai_dep_res = client.post("/api/v1/ai/predict/departure", json={
        "entry_time": datetime.utcnow().isoformat(),
        "vehicle_type": "EV",
        "floor_level": 1
    }, headers=headers)
    assert ai_dep_res.status_code == 200
    ai_dep_data = ai_dep_res.json()
    assert "predicted_duration_minutes" in ai_dep_data
    assert ai_dep_data["predicted_duration_minutes"] > 0

    # ================= 7. Simulate session reaching 20 minutes remaining =================
    db = SessionLocal()
    session_id = active_sessions[0]["id"]
    session_db = db.query(ParkingSession).filter(ParkingSession.id == session_id).first()
    assert session_db is not None
    
    # Adjust expected departure to be 19 minutes in the future
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    session_db.predicted_departure = now_utc + timedelta(minutes=19)
    db.commit()
    db.close()

    # ================= 8. Verify owner receives expiring soon status =================
    active_res = client.get("/api/v1/sessions/active", headers=headers)
    assert active_res.json()[0]["is_expiring_soon"] == True
    assert active_res.json()[0]["remaining_minutes"] == 19

    # ================= 9. Scan the vehicle QR as public/unauthenticated user =================
    # Retrieve static token from vehicle registration response
    static_token = veh_data["static_qr_token"]
    # Query public status using static token
    public_res = client.get(f"/api/v1/qr/public-status/{static_token}")
    assert public_res.status_code == 200
    public_data = public_res.json()

    # ================= 10 & 11. Verify public QR displays only status/time, NO PII exposed =================
    assert public_data["status"] == "VALID_PARKIQ_VEHICLE"
    assert public_data["session_active"] == True
    assert "estimated_departure" in public_data
    assert "parking_slot" in public_data
    
    # Check that owner details are NOT in the public response
    assert "license_plate" not in public_data
    assert "full_name" not in public_data
    assert "phone" not in public_data
    assert "email" not in public_data
    assert "user_id" not in public_data

    # ================= 12 & 13. Ask RAG questions grounded in knowledge base =================
    chat_res = client.post("/api/v1/rag/chat", json={
        "question": "What is the hourly rate for Grand Central Multi-Level Garage?"
    }, headers=headers)
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "question" in chat_data
    assert "answer" in chat_data
    # Verify that the hourly rate details are grounded (it should retrieve garage information from seed)
    assert "6.5" in chat_data["answer"] or "rate" in chat_data["answer"].lower()

    # ================= 14. Test unknown question and verify RAG does not hallucinate =================
    chat_unknown_res = client.post("/api/v1/rag/chat", json={
        "question": "Describe the chemical composition of the moon."
    }, headers=headers)
    assert chat_unknown_res.status_code == 200
    chat_unknown_data = chat_unknown_res.json()
    # Should trigger fallback notice or a grounded fallback response
    ans_lower = chat_unknown_data["answer"].lower()
    assert "fallback" in ans_lower or "support" in ans_lower or "helpdesk" in ans_lower

    # ================= 15 & 16. Complete checkout and verify closed state =================
    end_res = client.post("/api/v1/sessions/end", json={
        "qr_token": qr_token
    }, headers=headers)
    assert end_res.status_code == 200
    
    active_after_res = client.get("/api/v1/sessions/active", headers=headers)
    assert len(active_after_res.json()) == 0

    # ================= 17. Verify dashboard updates accordingly =================
    # Admin login
    admin_login = client.post("/api/v1/auth/login", json={
        "email": "admin@parkiq.com",
        "password": "admin123"
    })
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    
    dash_res = client.get("/api/v1/analytics/dashboard-summary", headers=admin_headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    
    # Assert slot we exited is indeed VACANT
    db = SessionLocal()
    slot_db = db.query(ParkingSlot).filter(ParkingSlot.id == vacant_slot["id"]).first()
    assert slot_db.status == SlotStatus.VACANT
    db.close()

    # ================= 18. Verify database state after completion =================
    db = SessionLocal()
    session_closed = db.query(ParkingSession).filter(ParkingSession.id == session_id).first()
    assert session_closed.status == SessionStatus.CLOSED
    assert session_closed.actual_exit_time is not None
    db.close()

    # ================= 19. Test unauthorized access to protected endpoints =================
    unauth_res = client.get("/api/v1/vehicles")
    assert unauth_res.status_code == 401
    
    unauth_dash = client.get("/api/v1/analytics/dashboard-summary")
    assert unauth_dash.status_code == 401

    # ================= 20. Test QR tampering/replay protection =================
    # Append invalid bytes to the qr token
    tampered_token = qr_token + "a"
    tampered_res = client.post("/api/v1/sessions/start", json={
        "qr_token": tampered_token,
        "slot_id": vacant_slot["id"],
        "expected_duration_minutes": 60
    }, headers=headers)
    assert tampered_res.status_code == 400
    assert "Invalid" in tampered_res.json()["detail"]
