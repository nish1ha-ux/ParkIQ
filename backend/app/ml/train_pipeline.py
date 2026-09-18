import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler

MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved_models")

def generate_synthetic_data(num_samples=2500):
    """
    Generates realistic synthetic historical dataset for ParkIQ model training:
    Features:
    - entry_hour (0-23)
    - day_of_week (0-6)
    - vehicle_type_num (0: SEDAN, 1: SUV, 2: EV, 3: BIKE)
    - slot_floor (1-5)
    - base_occupancy_pct (10-95)
    Target:
    - parking_duration_mins
    - future_occupancy_pct
    - is_fraudulent (0: Normal, 1: Fraud)
    """
    np.random.seed(42)

    entry_hour = np.random.randint(0, 24, num_samples)
    day_of_week = np.random.randint(0, 7, num_samples)
    vehicle_type = np.random.choice([0, 1, 2, 3], num_samples, p=[0.4, 0.35, 0.15, 0.1])
    slot_floor = np.random.randint(1, 6, num_samples)
    current_occupancy = np.random.uniform(10.0, 95.0, num_samples)

    # Calculate realistic parking duration based on peak work hours vs evening
    duration = []
    for h in entry_hour:
        if 8 <= h <= 10:
            dur = np.random.normal(360, 45)  # Workday stay (approx 6 hours)
        elif 12 <= h <= 14:
            dur = np.random.normal(60, 15)   # Lunch visit (approx 1 hour)
        elif 17 <= h <= 20:
            dur = np.random.normal(120, 30)  # Dinner/Shopping (approx 2 hours)
        else:
            dur = np.random.normal(90, 25)
        duration.append(max(15, dur))

    duration = np.array(duration)

    # Future occupancy target (+2 hours projection)
    future_occupancy = []
    for occ, h in zip(current_occupancy, entry_hour):
        if (8 <= h <= 11) or (17 <= h <= 19):
            trend = occ * np.random.uniform(1.1, 1.35)
        elif h >= 22 or h <= 5:
            trend = occ * np.random.uniform(0.3, 0.6)
        else:
            trend = occ * np.random.uniform(0.85, 1.05)
        future_occupancy.append(min(100.0, max(5.0, trend)))

    future_occupancy = np.array(future_occupancy)

    # Fraud status target (e.g. duplicate scan within 2 minutes or impossible entry speed)
    time_delta_sec = np.random.uniform(1, 3600, num_samples)
    distance_km = np.random.uniform(0.1, 50, num_samples)
    speed_kmh = (distance_km / (time_delta_sec / 3600.0))
    is_fraud = ((speed_kmh > 150) | (time_delta_sec < 30)).astype(int)

    df = pd.DataFrame({
        "entry_hour": entry_hour,
        "day_of_week": day_of_week,
        "vehicle_type": vehicle_type,
        "slot_floor": slot_floor,
        "current_occupancy": current_occupancy,
        "time_delta_sec": time_delta_sec,
        "distance_km": distance_km,
        "speed_kmh": speed_kmh,
        "duration_mins": duration,
        "future_occupancy": future_occupancy,
        "is_fraud": is_fraud
    })

    return df

def train_and_save_all_models():
    """
    Trains and persists all 5 ParkIQ AI Machine Learning Models.
    """
    os.makedirs(MODEL_DIR, exist_ok=True)
    df = generate_synthetic_data()

    print("[ML Pipeline] Training 1: Departure Duration Prediction Model (Gradient Boosting Regressor)...")
    X_dep = df[["entry_hour", "day_of_week", "vehicle_type", "slot_floor"]]
    y_dep = df["duration_mins"]

    scaler_dep = StandardScaler()
    X_dep_scaled = scaler_dep.fit_transform(X_dep)

    model_dep = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
    model_dep.fit(X_dep_scaled, y_dep)

    joblib.dump(model_dep, os.path.join(MODEL_DIR, "model_departure.joblib"))
    joblib.dump(scaler_dep, os.path.join(MODEL_DIR, "scaler_departure.joblib"))

    print("[ML Pipeline] Training 2: Occupancy & Congestion Forecasting Model...")
    X_occ = df[["entry_hour", "day_of_week", "current_occupancy"]]
    y_occ = df["future_occupancy"]

    scaler_occ = StandardScaler()
    X_occ_scaled = scaler_occ.fit_transform(X_occ)

    model_occ = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
    model_occ.fit(X_occ_scaled, y_occ)

    joblib.dump(model_occ, os.path.join(MODEL_DIR, "model_occupancy.joblib"))
    joblib.dump(scaler_occ, os.path.join(MODEL_DIR, "scaler_occupancy.joblib"))

    print("[ML Pipeline] Training 3: QR Fraud & Anomaly Classifier (Random Forest + Isolation Forest)...")
    X_fraud = df[["time_delta_sec", "distance_km", "speed_kmh"]]
    y_fraud = df["is_fraud"]

    scaler_fraud = StandardScaler()
    X_fraud_scaled = scaler_fraud.fit_transform(X_fraud)

    model_fraud = RandomForestClassifier(n_estimators=100, random_state=42)
    model_fraud.fit(X_fraud_scaled, y_fraud)

    model_iso = IsolationForest(contamination=0.05, random_state=42)
    model_iso.fit(X_fraud_scaled)

    joblib.dump(model_fraud, os.path.join(MODEL_DIR, "model_fraud.joblib"))
    joblib.dump(model_iso, os.path.join(MODEL_DIR, "model_iso.joblib"))
    joblib.dump(scaler_fraud, os.path.join(MODEL_DIR, "scaler_fraud.joblib"))

    print("[ML Pipeline] All AI models trained and persisted successfully in", MODEL_DIR)

if __name__ == "__main__":
    train_and_save_all_models()
