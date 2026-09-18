from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, Vehicle, ParkingSession
from app.schemas.schemas import QRVerifyRequest, PublicQRStatusResponse
from app.routers.auth import get_current_user
from app.core.qr_crypto import qr_crypto_engine
from app.services.notification_service import notification_service
from app.services.websocket_service import websocket_manager

router = APIRouter(prefix="/qr", tags=["AES-256 QR Identity Engine"])

@router.post("/verify")
async def staff_verify_qr(
    req: QRVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Authenticated Staff & Admin endpoint to decrypt and verify full vehicle QR identity.
    """
    if current_user.role not in ["STAFF", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Only Parking Staff or Admins can verify QR identities")

    try:
        decrypted_payload = qr_crypto_engine.decrypt_vehicle_token(req.qr_token)
    except ValueError as e:
        # Trigger suspicious activity alert
        admin = db.query(User).filter(User.role == "ADMIN").first()
        admin_id = admin.id if admin else current_user.id
        
        try:
            notification_service.send_suspicious_qr_activity(
                db=db,
                user_id=admin_id,
                details=f"Tampered or corrupted QR token verify attempt at facility gate: {str(e)}"
            )
        except Exception as ex:
            print(f"[Notifications] Suspicious QR alert failed: {ex}")
            
        try:
            await websocket_manager.broadcast({
                "event": "suspicious_qr_scan",
                "message": "Suspicious QR scan detected! Forged, corrupted, or tampered QR code scanned at gate."
            })
        except Exception as ex:
            print(f"[Notifications] Suspicious QR broadcast failed: {ex}")
            
        raise HTTPException(status_code=400, detail=str(e))

    vehicle_id = decrypted_payload.get("v_id")
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle identity not found in ParkIQ database")

    # Fetch active session if any
    active_session = db.query(ParkingSession).filter(
        ParkingSession.vehicle_id == vehicle.id,
        ParkingSession.status == "ACTIVE"
    ).first()

    return {
        "status": "VERIFIED_VALID",
        "decrypted_identity": decrypted_payload,
        "owner_name": vehicle.owner.full_name,
        "vehicle_type": vehicle.vehicle_type,
        "license_plate": vehicle.license_plate,
        "active_session": {
            "session_id": active_session.id,
            "slot_number": active_session.slot.slot_number,
            "entry_time": active_session.entry_time,
            "predicted_departure": active_session.predicted_departure
        } if active_session else None
    }

@router.get("/public-status/{static_token}", response_model=PublicQRStatusResponse)
async def get_public_qr_status(static_token: str, db: Session = Depends(get_db)):
    """
    Public unauthenticated endpoint to scan a ParkIQ vehicle QR code using the static opaque token.
    Returns only non-sensitive status, concealing personal data.
    """
    # Lookup vehicle by static token
    vehicle = db.query(Vehicle).filter(Vehicle.static_qr_token == static_token).first()
    if not vehicle:
        return PublicQRStatusResponse(
            status="INVALID_OR_EXPIRED",
            masked_vehicle_id="N/A",
            masked_license_plate="N/A",
            session_active=False,
            message="Invalid or unknown QR token."
        )
    # Build minimal payload for mask_public_status
    decrypted_payload = {
        "v_id": vehicle.id,
        "plate": vehicle.license_plate
    }
    # Determine active session if any
    active_session = db.query(ParkingSession).filter(
        ParkingSession.vehicle_id == vehicle.id,
        ParkingSession.status == "ACTIVE"
    ).first()
    session_info = None
    if active_session:
        session_info = {
            "is_active": True,
            "slot_number": active_session.slot.slot_number if active_session.slot else "Assigned",
            "predicted_departure": active_session.predicted_departure.strftime("%Y-%m-%d %H:%M UTC") if active_session.predicted_departure else "20 minutes"
        }
    status_data = qr_crypto_engine.mask_public_status(decrypted_payload, session_info)
    return PublicQRStatusResponse(**status_data)
