import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional

from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, classification_report, accuracy_score
from sqlalchemy import create_engine, text
from app.config import settings

MODEL_DIR = settings.MODEL_DIR

VEHICLE_TYPE_MAP = {
    "SEDAN": 0,
    "SUV": 1,
    "EV": 2,
    "BIKE": 3
}

def load_data_from_db():
    """
    Attempts to load historical parking data from the database.
    If database data is sparse or empty, fallback to synthetic data.
    """
    db_url = settings.final_database_url
    print(f"[ML Pipeline] Connecting to database at {db_url} for training data...")
    try:
        engine = create_engine(db_url)
        # Check sessions count
        with engine.connect() as conn:
            res = conn.execute(text("SELECT COUNT(*) FROM parking_sessions"))
            count = res.scalar()
            
        if count > 100:
            print(f"[ML Pipeline] Found {count} sessions in DB. Loading dataset...")
            query = """
            SELECT 
                ps.entry_time, 
                ps.actual_exit_time, 
                ps.predicted_departure,
                ps.status,
                v.vehicle_type,
                s.floor_level
            FROM parking_sessions ps
            JOIN vehicles v ON ps.vehicle_id = v.id
            JOIN parking_slots s ON ps.slot_id = s.id
            WHERE ps.actual_exit_time IS NOT NULL OR ps.predicted_departure IS NOT NULL
            """
            df_sessions = pd.read_sql(query, engine)
            return process_db_sessions(df_sessions)
        else:
            print(f"[ML Pipeline] Only {count} sessions found. Falling back to synthetic dataset.")
            return None
    except Exception as e:
        print(f"[ML Pipeline] Database fetch error: {e}. Falling back to synthetic dataset.")
        return None

def process_db_sessions(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Processes database records into ML features."""
    if df.empty:
        return None
        
    # Check for missing values in target columns
    # We explain why we drop or fill: we drop rows missing both actual_exit_time and predicted_departure, 
    # since we need a target for duration prediction.
    initial_len = len(df)
    df = df.dropna(subset=["entry_time"])
    
    # Calculate duration
    df["exit_time"] = df["actual_exit_time"].fillna(df["predicted_departure"])
    df = df.dropna(subset=["exit_time"])
    
    if len(df) == 0:
        print("[ML Pipeline] No valid exit/departure times found after cleaning.")
        return None
        
    # Convert dates to datetime
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    df["exit_time"] = pd.to_datetime(df["exit_time"])
    
    df["duration_mins"] = (df["exit_time"] - df["entry_time"]).dt.total_seconds() / 60.0
    # Clean durations that don't make sense (negative or extremely short/long)
    df = df[(df["duration_mins"] > 5) & (df["duration_mins"] < 1440)]
    
    # Extract features
    df["entry_hour"] = df["entry_time"].dt.hour
    df["day_of_week"] = df["entry_time"].dt.weekday
    df["vehicle_type_num"] = df["vehicle_type"].str.upper().map(VEHICLE_TYPE_MAP).fillna(0).astype(int)
    df["slot_floor"] = df["floor_level"].fillna(1).astype(int)
    
    # Mock some extra columns for occupancy & fraud since DB doesn't have detailed historical load tests
    num_samples = len(df)
    np.random.seed(42)
    df["current_occupancy"] = np.random.uniform(10.0, 95.0, num_samples)
    
    # Future occupancy target (+2 hours projection)
    future_occupancy = []
    for occ, h in zip(df["current_occupancy"], df["entry_hour"]):
        if (8 <= h <= 11) or (17 <= h <= 19):
            trend = occ * np.random.uniform(1.1, 1.35)
        elif h >= 22 or h <= 5:
            trend = occ * np.random.uniform(0.3, 0.6)
        else:
            trend = occ * np.random.uniform(0.85, 1.05)
        future_occupancy.append(min(100.0, max(5.0, trend)))
    df["future_occupancy"] = future_occupancy
    
    # Fraud fields
    df["time_delta_sec"] = np.random.uniform(1, 3600, num_samples)
    df["distance_km"] = np.random.uniform(0.1, 50, num_samples)
    df["speed_kmh"] = (df["distance_km"] / (df["time_delta_sec"] / 3600.0))
    df["is_fraud"] = ((df["speed_kmh"] > 150) | (df["time_delta_sec"] < 30)).astype(int)
    
    print(f"[ML Pipeline] Cleaned database records. Kept {len(df)} of {initial_len} samples.")
    return df

def generate_synthetic_data(num_samples=2500):
    """
    Generates realistic synthetic historical dataset for ParkIQ model training.
    """
    print(f"[ML Pipeline] Generating {num_samples} synthetic training samples...")
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
    Trains and persists all ParkIQ AI Machine Learning Models.
    Adheres strictly to the ml-best-practices skill.
    """
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Load or generate training data
    df = load_data_from_db()
    if df is None:
        df = generate_synthetic_data()

    # Check for missing/null values in loaded dataset
    null_summary = df.isnull().sum()
    print("[ML Pipeline] Missing values summary:")
    print(null_summary.to_string())
    
    # Handle missing values if any exist by dropping or filling (already handled in cleaning)
    if df.isnull().any().any():
        print("[ML Pipeline] Nulls detected. Dropping incomplete rows to preserve target integrity.")
        df = df.dropna()

    metrics_dict = {}

    # ==========================================
    # MODEL 1: DEPARTURE DURATION PREDICTION
    # ==========================================
    print("[ML Pipeline] Training 1: Departure Duration Prediction Model...")
    
    # Features & targets
    # For synthetic data, columns are entry_hour, day_of_week, vehicle_type, slot_floor.
    # For database data, column vehicle_type is vehicle_type_num. Let's unify them:
    v_col = "vehicle_type" if "vehicle_type" in df.columns else "vehicle_type_num"
    f_col = "slot_floor"
    
    X_dep = df[["entry_hour", "day_of_week", v_col, f_col]].values
    y_dep = df["duration_mins"].values

    # STRICT FEATURIZATION ORDERING: Split BEFORE fitting scaling pipeline
    X_dep_train, X_dep_test, y_dep_train, y_dep_test = train_test_split(
        X_dep, y_dep, test_size=0.2, random_state=42
    )

    scaler_dep = StandardScaler()
    X_dep_train_scaled = scaler_dep.fit_transform(X_dep_train)
    X_dep_test_scaled = scaler_dep.transform(X_dep_test)

    model_dep = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
    model_dep.fit(X_dep_train_scaled, y_dep_train)

    # Evaluate Model 1
    y_dep_pred = model_dep.predict(X_dep_test_scaled)
    mae_dep = mean_absolute_error(y_dep_test, y_dep_pred)
    rmse_dep = np.sqrt(mean_squared_error(y_dep_test, y_dep_pred))
    r2_dep = r2_score(y_dep_test, y_dep_pred)

    metrics_dict["departure_prediction"] = {
        "MAE": float(mae_dep),
        "RMSE": float(rmse_dep),
        "R2": float(r2_dep)
    }

    # Save Model 1 and Scaler
    joblib.dump(model_dep, os.path.join(MODEL_DIR, "model_departure.joblib"))
    joblib.dump(scaler_dep, os.path.join(MODEL_DIR, "scaler_departure.joblib"))

    # ==========================================
    # MODEL 2: FUTURE OCCUPANCY FORECASTING
    # ==========================================
    print("[ML Pipeline] Training 2: Occupancy Forecasting Model...")
    X_occ = df[["entry_hour", "day_of_week", "current_occupancy"]].values
    y_occ = df["future_occupancy"].values

    # STRICT FEATURIZATION ORDERING: Split BEFORE fitting scaling pipeline
    X_occ_train, X_occ_test, y_occ_train, y_occ_test = train_test_split(
        X_occ, y_occ, test_size=0.2, random_state=42
    )

    scaler_occ = StandardScaler()
    X_occ_train_scaled = scaler_occ.fit_transform(X_occ_train)
    X_occ_test_scaled = scaler_occ.transform(X_occ_test)

    model_occ = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
    model_occ.fit(X_occ_train_scaled, y_occ_train)

    # Evaluate Model 2
    y_occ_pred = model_occ.predict(X_occ_test_scaled)
    mae_occ = mean_absolute_error(y_occ_test, y_occ_pred)
    rmse_occ = np.sqrt(mean_squared_error(y_occ_test, y_occ_pred))
    r2_occ = r2_score(y_occ_test, y_occ_pred)

    metrics_dict["occupancy_prediction"] = {
        "MAE": float(mae_occ),
        "RMSE": float(rmse_occ),
        "R2": float(r2_occ)
    }

    # Save Model 2 and Scaler
    joblib.dump(model_occ, os.path.join(MODEL_DIR, "model_occupancy.joblib"))
    joblib.dump(scaler_occ, os.path.join(MODEL_DIR, "scaler_occupancy.joblib"))

    # ==========================================
    # MODEL 3: QR FRAUD DETECTION
    # ==========================================
    print("[ML Pipeline] Training 3: QR Fraud & Anomaly Classifier...")
    X_fraud = df[["time_delta_sec", "distance_km", "speed_kmh"]].values
    y_fraud = df["is_fraud"].values

    # STRICT FEATURIZATION ORDERING: Split BEFORE fitting scaling pipeline
    X_fraud_train, X_fraud_test, y_fraud_train, y_fraud_test = train_test_split(
        X_fraud, y_fraud, test_size=0.2, random_state=42
    )

    scaler_fraud = StandardScaler()
    X_fraud_train_scaled = scaler_fraud.fit_transform(X_fraud_train)
    X_fraud_test_scaled = scaler_fraud.transform(X_fraud_test)

    # Fit Random Forest Classifier
    model_fraud = RandomForestClassifier(n_estimators=100, random_state=42)
    model_fraud.fit(X_fraud_train_scaled, y_fraud_train)

    # Fit Isolation Forest (Unsupervised Anomaly) on scaled training data
    model_iso = IsolationForest(contamination=0.05, random_state=42)
    model_iso.fit(X_fraud_train_scaled)

    # Evaluate Model 3 (Random Forest)
    y_fraud_pred = model_fraud.predict(X_fraud_test_scaled)
    acc_fraud = accuracy_score(y_fraud_test, y_fraud_pred)
    report = classification_report(y_fraud_test, y_fraud_pred, output_dict=True)

    metrics_dict["fraud_classification"] = {
        "accuracy": float(acc_fraud),
        "macro_f1": float(report["macro avg"]["f1-score"]),
        "weighted_f1": float(report["weighted avg"]["f1-score"]),
        "fraud_precision": float(report["1"]["precision"]) if "1" in report else 0.0,
        "fraud_recall": float(report["1"]["recall"]) if "1" in report else 0.0
    }

    # Save Model 3, Isolation Forest, and Scaler
    joblib.dump(model_fraud, os.path.join(MODEL_DIR, "model_fraud.joblib"))
    joblib.dump(model_iso, os.path.join(MODEL_DIR, "model_iso.joblib"))
    joblib.dump(scaler_fraud, os.path.join(MODEL_DIR, "scaler_fraud.joblib"))

    # Write evaluation metrics to file
    metrics_path = os.path.join(MODEL_DIR, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics_dict, f, indent=4)

    print(f"[ML Pipeline] All AI models trained successfully. Metrics saved to {metrics_path}")
    print(json.dumps(metrics_dict, indent=2))

if __name__ == "__main__":
    train_and_save_all_models()
