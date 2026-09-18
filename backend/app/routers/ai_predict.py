import httpx
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from app.database import get_db
from app.models.models import ParkingSlot, SlotStatus, User
from app.config import settings
from app.routers.auth import get_current_user
from app.services.notification_service import notification_service
from app.services.websocket_service import websocket_manager

# Keep local imports for local fallback execution
from app.ml.inference import ai_inference_engine
from app.ml.train_pipeline import train_and_save_all_models

router = APIRouter(prefix="/ai", tags=["AI Predictive Intelligence REST APIs"])

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

class AIFraudDetectRequest(BaseModel):
    time_delta_sec: float = Field(ge=0.0)
    distance_km: float = Field(ge=0.0)

class AIUnifiedPredictRequest(BaseModel):
    lot_id: str
    time_offset_hours: Optional[int] = Field(default=2, ge=1, le=24)

@router.post("/predict/departure")
async def predict_departure_time(req: AIDepartureRequest):
    """
    Model 1 Inference API: Predicts expected departure timestamp and total duration.
    Proxies to AI microservice with local fallback.
    """
    url = f"{settings.AI_SERVICE_URL}/api/v1/ai/predict/departure"
    # Ensure datetime serializes properly in JSON
    entry_t_str = req.entry_time.isoformat() if req.entry_time else None
    
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.post(url, json={
                "entry_time": entry_t_str,
                "vehicle_type": req.vehicle_type,
                "floor_level": req.floor_level
            })
            if res.status_code == 200:
                return res.json()
    except Exception as e:
        print(f"[AI Proxy] Service unreachable: {e}. Falling back to in-process model.")

    # Fallback to local execution
    entry_t = req.entry_time or datetime.now(timezone.utc).replace(tzinfo=None)
    if entry_t.tzinfo is not None:
        entry_t = entry_t.replace(tzinfo=None)
        
    return ai_inference_engine.predict_departure_duration(
        entry_time=entry_t,
        vehicle_type=req.vehicle_type or "SEDAN",
        floor_level=req.floor_level or 1
    )

@router.post("/predict/occupancy")
async def forecast_occupancy_and_congestion(req: AIOccupancyRequest):
    """
    Model 2 & 3 Inference API: Forecasts garage fill-rate % and congestion level after N hours.
    Proxies to AI microservice with local fallback.
    """
    url = f"{settings.AI_SERVICE_URL}/api/v1/ai/predict/occupancy"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.post(url, json={
                "lot_id": req.lot_id,
                "current_occupancy_pct": req.current_occupancy_pct,
                "time_offset_hours": req.time_offset_hours
            })
            if res.status_code == 200:
                return res.json()
    except Exception as e:
        print(f"[AI Proxy] Service unreachable: {e}. Falling back to in-process model.")

    # Fallback to local execution
    result = ai_inference_engine.forecast_occupancy_and_congestion(
        current_occupancy_pct=req.current_occupancy_pct,
        offset_hours=req.time_offset_hours or 2
    )
    result["lot_id"] = req.lot_id
    return result

@router.post("/recommend-slot")
async def recommend_best_parking_slots(req: AISlotRecommendRequest, db: Session = Depends(get_db)):
    """
    Model 4 Inference API: Scores and recommends optimal vacant parking slots.
    Proxies to AI microservice with local fallback.
    """
    slots = db.query(ParkingSlot).filter(
        ParkingSlot.lot_id == req.lot_id,
        ParkingSlot.status == SlotStatus.VACANT
    ).all()

    vacant_dicts = [
        {"id": str(s.id), "slot_number": s.slot_number, "floor_level": s.floor_level, "slot_type": s.slot_type}
        for s in slots
    ]

    url = f"{settings.AI_SERVICE_URL}/api/v1/ai/recommend-slot"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.post(url, json={
                "lot_id": req.lot_id,
                "vehicle_type": req.vehicle_type,
                "vacant_slots": vacant_dicts
            })
            if res.status_code == 200:
                return res.json()
    except Exception as e:
        print(f"[AI Proxy] Service unreachable: {e}. Falling back to in-process scoring.")

    # Fallback to local execution
    scored = ai_inference_engine.recommend_best_parking_slots(vacant_dicts, req.vehicle_type or "SEDAN")
    return {
        "lot_id": req.lot_id,
        "recommended_slots": scored[:3],
        "total_vacant_slots": len(vacant_dicts)
    }

@router.post("/detect-fraud")
async def detect_qr_fraud_anomaly(
    req: AIFraudDetectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Model 5 Inference API: Detects QR code cloning, impossible velocity, or duplicate scan fraud.
    Proxies to AI microservice with local fallback.
    """
    result = None
    url = f"{settings.AI_SERVICE_URL}/api/v1/ai/detect-fraud"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.post(url, json={
                "time_delta_sec": req.time_delta_sec,
                "distance_km": req.distance_km
            })
            if res.status_code == 200:
                result = res.json()
    except Exception as e:
        print(f"[AI Proxy] Service unreachable: {e}. Falling back to in-process model.")

    if result is None:
        # Fallback to local execution
        result = ai_inference_engine.detect_qr_cloning_fraud(
            time_delta_sec=req.time_delta_sec,
            distance_km=req.distance_km
        )

    # Trigger alerts if fraud was detected
    if result.get("is_fraudulent"):
        admin = db.query(User).filter(User.role == "ADMIN").first()
        admin_id = admin.id if admin else "system_admin"
        
        speed = result.get("travel_speed_kmh", 0.0)
        details = f"Suspicious QR scan clone detected! Impossible velocity: {speed} km/h (scanned {req.distance_km} km in {req.time_delta_sec} seconds)."
        
        try:
            notification_service.send_suspicious_qr_activity(
                db=db,
                user_id=admin_id,
                details=details
            )
        except Exception as ex:
            print(f"[Notifications] Fraud alert push failed: {ex}")
            
        try:
            await websocket_manager.broadcast({
                "event": "suspicious_qr_scan",
                "message": f"Suspicious QR activity: clone or impossible travel velocity of {speed} km/h detected."
            })
        except Exception as ex:
            print(f"[Notifications] Fraud alert broadcast failed: {ex}")

    return result

@router.post("/predict")
async def unified_predict(req: AIUnifiedPredictRequest, db: Session = Depends(get_db)):
    """
    Unified API endpoint designed to power the frontend dashboard metrics.
    Proxies to AI microservice with local fallback.
    """
    url = f"{settings.AI_SERVICE_URL}/api/v1/ai/predict"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.post(url, json={
                "lot_id": req.lot_id,
                "time_offset_hours": req.time_offset_hours
            })
            if res.status_code == 200:
                return res.json()
    except Exception as e:
        print(f"[AI Proxy] Service unreachable: {e}. Falling back to in-process unified prediction.")

    # Fallback to local database query & model execution
    total_slots = db.query(ParkingSlot).filter(ParkingSlot.lot_id == req.lot_id).count()
    occupied_slots = db.query(ParkingSlot).filter(
        ParkingSlot.lot_id == req.lot_id, 
        ParkingSlot.status == SlotStatus.OCCUPIED
    ).count()
    
    current_occupancy_pct = round((occupied_slots / total_slots * 100.0), 1) if total_slots > 0 else 50.0

    offset = req.time_offset_hours or 2
    forecast_result = ai_inference_engine.forecast_occupancy_and_congestion(
        current_occupancy_pct=current_occupancy_pct,
        offset_hours=offset
    )

    # Average prediction across vehicle types
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
async def trigger_model_training(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Triggers machine learning model re-training pipeline in the background.
    Proxies to AI microservice with local fallback.
    Restricted to STAFF and ADMIN roles.
    """
    if current_user.role not in ["STAFF", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Only Staff and Admins can trigger model training")
    url = f"{settings.AI_SERVICE_URL}/api/v1/ai/train"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.post(url)
            if res.status_code == 202:
                return res.json()
    except Exception as e:
        print(f"[AI Proxy] Service unreachable: {e}. Falling back to in-process background training.")

    background_tasks.add_task(train_and_save_all_models)
    return {
        "status": "TRAINING_INITIATED",
        "message": "AI model training pipeline executed in background locally."
    }
