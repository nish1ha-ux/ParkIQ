from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import math
from app.database import get_db
from app.models.models import User, Vehicle, ParkingLot, ParkingSlot, ParkingSession, SlotStatus, SessionStatus, UserRole
from app.schemas.schemas import (
    StartSessionRequest, EndSessionRequest, ExtendSessionRequest,
    SessionResponse, ParkingLotResponse, SlotResponse
)
from app.routers.auth import get_current_user
from app.core.qr_crypto import qr_crypto_engine
from app.services.notification_service import notification_service
from app.services.websocket_service import websocket_manager

router = APIRouter(prefix="/sessions", tags=["Parking Session Management"])

def calculate_session_metrics(session: ParkingSession) -> Dict[str, Any]:
    """Helper to compute expected departure, remaining time, and expiring soon status."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    exp_dep = session.predicted_departure or (session.entry_time + timedelta(hours=1))
    
    # Calculate remaining minutes
    if session.status == SessionStatus.ACTIVE:
        diff_seconds = (exp_dep - now).total_seconds()
        rem_minutes = max(0, math.ceil(diff_seconds / 60.0))
    else:
        rem_minutes = 0

    expiring_soon = (rem_minutes <= 20 and session.status == SessionStatus.ACTIVE)
    slot_num = session.slot.slot_number if session.slot else "N/A"

    return {
        "id": session.id,
        "vehicle_id": session.vehicle_id,
        "slot_id": session.slot_id,
        "slot_number": slot_num,
        "entry_time": session.entry_time,
        "expected_departure": exp_dep,
        "actual_exit_time": session.actual_exit_time,
        "remaining_minutes": rem_minutes,
        "is_expiring_soon": expiring_soon,
        "status": session.status
    }

@router.get("/lots", response_model=List[ParkingLotResponse])
def list_parking_lots(db: Session = Depends(get_db)):
    lots = db.query(ParkingLot).all()
    return lots

@router.get("/lots/{lot_id}/slots", response_model=List[SlotResponse])
def list_lot_slots(lot_id: str, db: Session = Depends(get_db)):
    slots = db.query(ParkingSlot).filter(ParkingSlot.lot_id == lot_id).all()
    return slots

@router.post("/start", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def start_parking_session(
    req: StartSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a new parking session.
    Calculates Expected Departure based on user's specified duration.
    """
    try:
        decrypted = qr_crypto_engine.decrypt_vehicle_token(req.qr_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid QR Token: {str(e)}")

    vehicle_id = decrypted.get("v_id")
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Check if vehicle already has an active session
    existing_session = db.query(ParkingSession).filter(
        ParkingSession.vehicle_id == vehicle.id,
        ParkingSession.status == SessionStatus.ACTIVE
    ).first()
    if existing_session:
        raise HTTPException(status_code=400, detail="Vehicle already has an active parking session")

    slot = db.query(ParkingSlot).filter(ParkingSlot.id == req.slot_id).first()
    if not slot or slot.status == SlotStatus.OCCUPIED:
        raise HTTPException(status_code=400, detail="Target slot is not available for parking")

    # Calculate expected departure timestamp deterministically
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    expected_dep = now_utc + timedelta(minutes=req.expected_duration_minutes)

    # Reserve & occupy slot
    slot.status = SlotStatus.OCCUPIED

    session = ParkingSession(
        vehicle_id=vehicle.id,
        slot_id=slot.id,
        entry_time=now_utc,
        predicted_departure=expected_dep,
        status=SessionStatus.ACTIVE,
        qr_token_entry=req.qr_token
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Dispatch FCM push notification
    try:
        notification_service.send_session_started(
            db=db,
            user_id=current_user.id,
            session_id=session.id,
            slot_number=slot.slot_number
        )
    except Exception as e:
        print(f"[Notifications] Started event push failed: {e}")

    # Broadcast via WebSocket
    try:
        await websocket_manager.broadcast({
            "event": "parking_started",
            "session_id": session.id,
            "user_id": current_user.id,
            "slot_number": slot.slot_number,
            "message": f"Parking session started in slot {slot.slot_number}."
        })
    except Exception as e:
        print(f"[Notifications] Started event broadcast failed: {e}")

    metrics = calculate_session_metrics(session)
    return SessionResponse(**metrics)

@router.post("/end", response_model=SessionResponse)
def end_parking_session(
    req: EndSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    End an active parking session and release the slot.
    """
    try:
        decrypted = qr_crypto_engine.decrypt_vehicle_token(req.qr_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid QR Token: {str(e)}")

    vehicle_id = decrypted.get("v_id")
    session = db.query(ParkingSession).filter(
        ParkingSession.vehicle_id == vehicle_id,
        ParkingSession.status == SessionStatus.ACTIVE
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="No active parking session found for this vehicle")

    # Release slot back to VACANT
    if session.slot:
        session.slot.status = SlotStatus.VACANT

    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    session.actual_exit_time = now_utc
    session.status = SessionStatus.CLOSED

    db.commit()
    db.refresh(session)

    metrics = calculate_session_metrics(session)
    return SessionResponse(**metrics)

@router.post("/{session_id}/extend", response_model=SessionResponse)
def extend_parking_session(
    session_id: str,
    req: ExtendSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extend the expected departure time of an active parking session.
    """
    session = db.query(ParkingSession).filter(
        ParkingSession.id == session_id,
        ParkingSession.status == SessionStatus.ACTIVE
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Active parking session not found")

    current_exp = session.predicted_departure or datetime.now(timezone.utc).replace(tzinfo=None)
    session.predicted_departure = current_exp + timedelta(minutes=req.additional_minutes)

    db.commit()
    db.refresh(session)

    metrics = calculate_session_metrics(session)
    return SessionResponse(**metrics)

@router.get("/active", response_model=List[SessionResponse])
def get_active_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch active parking sessions with real-time remaining minutes.
    """
    if current_user.role in [UserRole.STAFF, UserRole.ADMIN]:
        sessions = db.query(ParkingSession).filter(ParkingSession.status == SessionStatus.ACTIVE).all()
    else:
        user_vehicle_ids = [v.id for v in current_user.vehicles]
        sessions = db.query(ParkingSession).filter(
            ParkingSession.vehicle_id.in_(user_vehicle_ids),
            ParkingSession.status == SessionStatus.ACTIVE
        ).all()

    return [SessionResponse(**calculate_session_metrics(s)) for s in sessions]

@router.get("/history", response_model=List[SessionResponse])
def get_parking_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch full historical completed parking sessions for user's registered vehicles.
    """
    if current_user.role in [UserRole.STAFF, UserRole.ADMIN]:
        sessions = db.query(ParkingSession).filter(ParkingSession.status != SessionStatus.ACTIVE).order_by(ParkingSession.entry_time.desc()).all()
    else:
        user_vehicle_ids = [v.id for v in current_user.vehicles]
        sessions = db.query(ParkingSession).filter(
            ParkingSession.vehicle_id.in_(user_vehicle_ids),
            ParkingSession.status != SessionStatus.ACTIVE
        ).order_by(ParkingSession.entry_time.desc()).all()

    return [SessionResponse(**calculate_session_metrics(s)) for s in sessions]
