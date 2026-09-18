from fastapi import FastAPI, BackgroundTasks, HTTPException, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from app.config import settings
from app.ml.inference import ai_inference_engine
from app.ml.train_pipeline import train_and_save_all_models

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Dedicated AI Prediction Service for ParkIQ"
)

# Initialize DB connection engine once globally to prevent connection exhaustion/leak
db_engine = create_engine(settings.final_database_url)

# CORS Configuration
origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True if "*" not in origins else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix=settings.API_V1_STR)

# Request & Response Pydantic Schemas
class AIDepartureRequest(BaseModel):
    entry_time: Optional[datetime] = None
    vehicle_type: Optional[str] = "SEDAN"
    floor_level: Optional[int] = 1

class AIOccupancyRequest(BaseModel):
    lot_id: str
    current_occupancy_pct: float = Field(ge=0.0, le=100.0)
    time_offset_hours: Optional[int] = Field(default=2, ge=1, le=24)

class AISlotRecommendRequest(BaseModel):
    lot_id: str
    vehicle_type: Optional[str] = "SEDAN"
    vacant_slots: Optional[List[Dict[str, Any]]] = None

class AIFraudDetectRequest(BaseModel):
    time_delta_sec: float = Field(ge=0.0)
    distance_km: float = Field(ge=0.0)

class AIUnifiedPredictRequest(BaseModel):
    lot_id: str
    time_offset_hours: Optional[int] = Field(default=2, ge=1, le=24)

@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "service": settings.PROJECT_NAME, "version": settings.VERSION}

@router.post("/predict/departure")
def predict_departure_time(req: AIDepartureRequest):
    """
    Predicts expected departure timestamp and total duration.
    """
    entry_t = req.entry_time or datetime.now(timezone.utc).replace(tzinfo=None)
    # Ensure entry_t is naive datetime (without timezone) for duration calculations
    if entry_t.tzinfo is not None:
        entry_t = entry_t.replace(tzinfo=None)
        
    result = ai_inference_engine.predict_departure_duration(
        entry_time=entry_t,
        vehicle_type=req.vehicle_type or "SEDAN",
        floor_level=req.floor_level or 1
    )
    return result

@router.post("/predict/occupancy")
def forecast_occupancy_and_congestion(req: AIOccupancyRequest):
    """
    Forecasts garage fill-rate % and congestion level after N hours.
    """
    result = ai_inference_engine.forecast_occupancy_and_congestion(
        current_occupancy_pct=req.current_occupancy_pct,
        offset_hours=req.time_offset_hours or 2
    )
    result["lot_id"] = req.lot_id
    return result

@router.post("/recommend-slot")
def recommend_best_parking_slots(req: AISlotRecommendRequest):
    """
    Scores and recommends optimal vacant parking slots.
    """
    vacant_list = req.vacant_slots
    if vacant_list is None:
        # Fetch from database if vacant_slots is not passed
        try:
            with db_engine.connect() as conn:
                query = text("""
                    SELECT id, slot_number, floor_level, slot_type 
                    FROM parking_slots 
                    WHERE lot_id = :lot_id AND status = 'VACANT'
                """)
                res = conn.execute(query, {"lot_id": req.lot_id})
                vacant_list = [dict(row._mapping) for row in res]
        except Exception as e:
            print(f"[AI Service] Recommend slots DB error: {e}")
            vacant_list = []

    scored = ai_inference_engine.recommend_best_parking_slots(vacant_list, req.vehicle_type or "SEDAN")
    return {
        "lot_id": req.lot_id,
        "recommended_slots": scored[:3],
        "total_vacant_slots": len(vacant_list)
    }

@router.post("/detect-fraud")
def detect_qr_fraud_anomaly(req: AIFraudDetectRequest):
    """
    Detects QR code cloning, impossible velocity, or duplicate scan fraud.
    """
    result = ai_inference_engine.detect_qr_cloning_fraud(
        time_delta_sec=req.time_delta_sec,
        distance_km=req.distance_km
    )
    return result

@router.post("/predict")
def unified_predict(req: AIUnifiedPredictRequest):
    """
    Unified API endpoint specifically designed to power the frontend dashboard metrics.
    Combines:
    1. Database-queried occupancy rate.
    2. Model 2 & 3: Projected occupancy rate + Congestion level.
    3. Model 1: Average predicted duration of a new session.
    """
    current_occupancy_pct = 50.0  # Safe default if db is empty
    
    try:
        with db_engine.connect() as conn:
            # Get total slots
            total_slots = conn.execute(
                text("SELECT COUNT(*) FROM parking_slots WHERE lot_id = :lot_id"),
                {"lot_id": req.lot_id}
            ).scalar() or 0
            
            # Get occupied slots
            occupied_slots = conn.execute(
                text("SELECT COUNT(*) FROM parking_slots WHERE lot_id = :lot_id AND status = 'OCCUPIED'"),
                {"lot_id": req.lot_id}
            ).scalar() or 0
            
            if total_slots > 0:
                current_occupancy_pct = round((occupied_slots / total_slots) * 100.0, 1)
    except Exception as e:
        print(f"[AI Service] Unified predict DB error: {e}")

    # Forecast occupancy using Model 2
    offset = req.time_offset_hours or 2
    forecast_result = ai_inference_engine.forecast_occupancy_and_congestion(
        current_occupancy_pct=current_occupancy_pct,
        offset_hours=offset
    )

    # Calculate average predicted duration using Model 1
    # Average across common vehicle types to get a representative average stay duration
    durations = []
    now = datetime.now()
    for vt in ["SEDAN", "SUV", "EV"]:
        dep_pred = ai_inference_engine.predict_departure_duration(
            entry_time=now,
            vehicle_type=vt,
            floor_level=1
        )
        durations.append(dep_pred["predicted_duration_minutes"])
    
    avg_duration = int(sum(durations) / len(durations)) if durations else 120

    return {
        "current_occupancy_pct": current_occupancy_pct,
        "predicted_occupancy_pct": forecast_result["predicted_occupancy_pct"],
        "predicted_congestion_level": forecast_result["predicted_congestion_level"],
        "average_predicted_duration_minutes": avg_duration,
        "lot_id": req.lot_id,
        "time_offset_hours": offset,
        "model_used": forecast_result["model_used"]
    }

@router.post("/train", status_code=status.HTTP_202_ACCEPTED)
def trigger_model_training(background_tasks: BackgroundTasks):
    """
    Triggers machine learning model re-training pipeline in the background.
    """
    background_tasks.add_task(train_and_save_all_models)
    return {
        "status": "TRAINING_INITIATED",
        "message": "AI model training pipeline executed in background."
    }

app.include_router(router)

