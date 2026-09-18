import pytest
import time
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

def test_unique_encrypted_qr_generation():
    """Verify each vehicle receives a unique AES-256 encrypted QR token."""
    v1_token = qr_crypto_engine.encrypt_vehicle_token("veh_001", "owner_111", "KA-01-AA-1000")
    v2_token = qr_crypto_engine.encrypt_vehicle_token("veh_002", "owner_222", "MH-12-BB-2000")

    assert v1_token != v2_token
    assert len(v1_token) > 30
    assert len(v2_token) > 30

def test_zero_pii_exposure_in_raw_qr_token():
    """Verify raw QR token string contains ZERO plaintext owner info."""
    owner_name = "Secret Owner John Doe"
    phone_number = "+15559998877"
    email = "secret_john@parkiq.com"

    token = qr_crypto_engine.encrypt_vehicle_token("veh_999", owner_name, "DL-01-CC-3000")

    # Raw token string must NOT contain any plaintext PII
    assert owner_name not in token
    assert phone_number not in token
    assert email not in token
    assert "DL-01-CC-3000" not in token

def test_public_unauthenticated_scan_privacy():
    """Verify public scan API returns non-sensitive status and conceals all PII.
    This test registers a vehicle, obtains its static QR token, and queries the public status endpoint.
    """
    # Login driver to register vehicle
    driver_res = client.post("/api/v1/auth/login", json={
        "email": "driver@parkiq.com",
        "password": "driver123"
    })
    assert driver_res.status_code == 200
    driver_jwt = driver_res.json()["access_token"]

    unique_plate = f"KA-{int(time.time()) % 10000:04d}-QR"
    v_res = client.post("/api/v1/vehicles",
        json={"license_plate": unique_plate, "vehicle_type": "SEDAN"},
        headers={"Authorization": f"Bearer {driver_jwt}"}
    )
    assert v_res.status_code == 201
    static_token = v_res.json()["static_qr_token"]

    # Query public status using static token
    res = client.get(f"/api/v1/qr/public-status/{static_token}")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "VALID_PARKIQ_VEHICLE"
    # Verify masked license plate format
    expected_mask = unique_plate[:2] + "****" + unique_plate[-2:]
    assert data["masked_license_plate"] == expected_mask
    # Ensure no PII exposed
    assert "driver" not in str(data)
    assert "owner" not in str(data)


def test_staff_authenticated_qr_decryption():
    """Verify authenticated staff scanner can decrypt token for gate access."""
    # 1. Login driver to register vehicle
    driver_res = client.post("/api/v1/auth/login", json={
        "email": "driver@parkiq.com",
        "password": "driver123"
    })
    assert driver_res.status_code == 200
    driver_jwt = driver_res.json()["access_token"]

    unique_plate = f"DL-{int(time.time()) % 10000:04d}-QR"
    # Register new vehicle
    v_res = client.post("/api/v1/vehicles",
        json={"license_plate": unique_plate, "vehicle_type": "SEDAN"},
        headers={"Authorization": f"Bearer {driver_jwt}"}
    )
    assert v_res.status_code == 201
    dev_token = v_res.json()["qr_token"]

    # 2. Login staff
    staff_res = client.post("/api/v1/auth/login", json={
        "email": "staff@parkiq.com",
        "password": "staff123"
    })
    assert staff_res.status_code == 200
    staff_token = staff_res.json()["access_token"]

    # 3. Staff verifies QR code
    verify_res = client.post("/api/v1/qr/verify", 
        json={"qr_token": dev_token},
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    assert verify_res.status_code == 200
    vdata = verify_res.json()
    assert vdata["status"] == "VERIFIED_VALID"
    assert vdata["license_plate"] == unique_plate

def test_tampered_qr_rejection():
    """Verify forged or corrupted QR tokens are rejected."""
    valid_token = qr_crypto_engine.encrypt_vehicle_token("v100", "u200", "KA-01-AA-1000")
    forged_token = valid_token[:-6] + "BADTOK"

    with pytest.raises(ValueError):
        qr_crypto_engine.decrypt_vehicle_token(forged_token)

    res = client.get(f"/api/v1/qr/public-status/{forged_token}")
    assert res.status_code == 200
    assert res.json()["status"] == "INVALID_OR_EXPIRED"
