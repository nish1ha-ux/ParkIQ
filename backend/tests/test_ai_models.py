import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base
from app.services.seed_data import seed_database
from app.ml.train_pipeline import train_and_save_all_models

# Initialize Database Schema & Models for Testing
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
seed_database()

client = TestClient(app)

def test_ai_training_pipeline():
    """Verify machine learning model training pipeline executes without errors."""
    train_and_save_all_models()

def test_ai_departure_prediction_api():
    """Verify Model 1: Departure Prediction API."""
    res = client.post("/api/v1/ai/predict/departure", json={
        "entry_time": datetime.utcnow().isoformat(),
        "vehicle_type": "EV",
        "floor_level": 1
    })
    assert res.status_code == 200
    data = res.json()
    assert "predicted_duration_minutes" in data
    assert "predicted_departure_time" in data
    assert data["predicted_duration_minutes"] > 0

def test_ai_occupancy_and_congestion_api():
    """Verify Model 2 & 3: Occupancy & Congestion Prediction API."""
    res = client.post("/api/v1/ai/predict/occupancy", json={
        "lot_id": "c0000000-0000-0000-0000-000000000001",
        "current_occupancy_pct": 75.0,
        "time_offset_hours": 2
    })
    assert res.status_code == 200
    data = res.json()
    assert "predicted_occupancy_pct" in data
    assert data["predicted_congestion_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]

def test_ai_slot_recommendation_api():
    """Verify Model 4: Parking Space Recommendation API."""
    lots_res = client.get("/api/v1/sessions/lots")
    lot_id = lots_res.json()[0]["id"]

    res = client.post("/api/v1/ai/recommend-slot", json={
        "lot_id": lot_id,
        "vehicle_type": "EV"
    })
    assert res.status_code == 200
    data = res.json()
    assert "recommended_slots" in data
    assert len(data["recommended_slots"]) > 0
    top_slot = data["recommended_slots"][0]
    assert "recommendation_score" in top_slot

def test_ai_fraud_detection_api():
    """Verify Model 5: QR Fraud & Velocity Anomaly Detection API."""
    # Login to get token
    login_res = client.post("/api/v1/auth/login", json={
        "email": "driver@parkiq.com",
        "password": "driver123"
    })
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Normal scan (5 km in 1 hour = 5 km/h)
    res_normal = client.post("/api/v1/ai/detect-fraud", json={
        "time_delta_sec": 3600.0,
        "distance_km": 5.0
    }, headers=headers)
    assert res_normal.status_code == 200
    assert res_normal.json()["is_fraudulent"] == False

    # Fraudulent scan (50 km in 10 seconds = 18,000 km/h impossible velocity)
    res_fraud = client.post("/api/v1/ai/detect-fraud", json={
        "time_delta_sec": 10.0,
        "distance_km": 50.0
    }, headers=headers)
    assert res_fraud.status_code == 200
    assert res_fraud.json()["is_fraudulent"] == True
    assert res_fraud.json()["risk_level"] == "HIGH"
