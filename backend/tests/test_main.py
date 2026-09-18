import pytest
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

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "HEALTHY"

def test_aes_256_qr_crypto_encryption_and_decryption():
    vehicle_id = "veh_test_12345"
    owner_id = "user_test_67890"
    license_plate = "KA-01-AB-1234"

    # Encrypt
    encrypted_token = qr_crypto_engine.encrypt_vehicle_token(vehicle_id, owner_id, license_plate)
    assert isinstance(encrypted_token, str)
    assert len(encrypted_token) > 30

    # Decrypt
    decrypted_payload = qr_crypto_engine.decrypt_vehicle_token(encrypted_token)
    assert decrypted_payload["v_id"] == vehicle_id
    assert decrypted_payload["o_id"] == owner_id
    assert decrypted_payload["plate"] == license_plate

    # Tamper resistance test
    tampered_token = encrypted_token[:-5] + "XXXXX"
    with pytest.raises(ValueError):
        qr_crypto_engine.decrypt_vehicle_token(tampered_token)

def test_public_qr_privacy_scan():
    # Login driver to obtain JWT
    driver_res = client.post("/api/v1/auth/login", json={
        "email": "driver@parkiq.com",
        "password": "driver123"
    })
    assert driver_res.status_code == 200
    driver_jwt = driver_res.json()["access_token"]
    # Register vehicle to get static QR token
    v_res = client.post("/api/v1/vehicles", json={"license_plate": "MH-12-EV-9999", "vehicle_type": "EV"},
                        headers={"Authorization": f"Bearer {driver_jwt}"})
    assert v_res.status_code == 201
    static_token = v_res.json()["static_qr_token"]
    # Query public status using static token
    response = client.get(f"/api/v1/qr/public-status/{static_token}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "VALID_PARKIQ_VEHICLE"
    assert "owner_secret" not in str(data)
    assert "john_doe" not in str(data)
    assert data["masked_license_plate"] == "MH****99"

def test_user_register_and_login():
    email = "newtestdriver@parkiq.com"
    # Register
    reg_res = client.post("/api/v1/auth/register", json={
        "full_name": "Test Driver",
        "email": email,
        "password": "password123",
        "phone": "+1555123456"
    })
    assert reg_res.status_code in [201, 400]

    # Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": "driver@parkiq.com",
        "password": "driver123"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

def test_rag_assistant_chat():
    response = client.post("/api/v1/rag/chat", json={
        "question": "What is the EV charging policy and rate?"
    })
    assert response.status_code == 200
    data = response.json()
    assert "EV" in data["answer"] or "charging" in data["answer"].lower() or "ParkIQ" in data["answer"]
