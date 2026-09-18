from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import io
import base64
from app.database import get_db
from app.models.models import User, Vehicle
from app.schemas.schemas import VehicleCreate, VehicleResponse
from app.routers.auth import get_current_user
from app.core.qr_crypto import qr_crypto_engine
import uuid

router = APIRouter(prefix="/vehicles", tags=["Vehicles & AES-256 Dynamic QR Tokens"])

@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def register_vehicle(
    vehicle_in: VehicleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plate_clean = vehicle_in.license_plate.strip().upper()
    existing = db.query(Vehicle).filter(Vehicle.license_plate == plate_clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="Vehicle license plate already registered")
    # Create Vehicle instance
    vehicle = Vehicle(
        user_id=current_user.id,
        license_plate=plate_clean,
        vehicle_type=vehicle_in.vehicle_type or "SEDAN"
    )
    # Generate opaque static QR token for public scanning
    static_token = str(uuid.uuid4())
    vehicle.static_qr_token = static_token
    db.add(vehicle)
    db.flush()
    # Generate AES-256 Encrypted Digital QR Identity Token (Zero PII stored in raw token)
    qr_token = qr_crypto_engine.encrypt_vehicle_token(
        vehicle_id=vehicle.id,
        owner_id=current_user.id,
        license_plate=vehicle.license_plate
    )
    vehicle.qr_token = qr_token
    db.commit()
    db.refresh(vehicle)
    return vehicle

@router.get("", response_model=List[VehicleResponse])
def get_user_vehicles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    vehicles = db.query(Vehicle).filter(Vehicle.user_id == current_user.id).all()
    for v in vehicles:
        # Generate fresh rolling QR token on-the-fly for security
        v.qr_token = qr_crypto_engine.encrypt_vehicle_token(v.id, current_user.id, v.license_plate)
        db.commit()
    return vehicles

@router.post("/{vehicle_id}/qr/generate")
def generate_encrypted_qr_token(
    vehicle_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates a unique AES-256 encrypted QR token for a vehicle.
    Guarantees zero owner PII is exposed in the QR payload.
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id, Vehicle.user_id == current_user.id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found or access denied")

    # Refresh rolling AES-256-GCM token
    new_qr_token = qr_crypto_engine.encrypt_vehicle_token(
        vehicle_id=vehicle.id,
        owner_id=current_user.id,
        license_plate=vehicle.license_plate
    )
    vehicle.qr_token = new_qr_token
    db.commit()

    return {
        "vehicle_id": vehicle.id,
        "license_plate": vehicle.license_plate,
        "encrypted_qr_token": new_qr_token,
        "security_standard": "AES-256-GCM",
        "pii_exposed": False,
        "message": "Unique AES-256 encrypted QR token successfully generated. Payload contains zero owner personal details."
    }
