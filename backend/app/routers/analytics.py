from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import User, ParkingLot, ParkingSlot, ParkingSession, Payment, FraudAlert, SlotStatus, UserRole
from app.routers.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Facility Manager Analytics & Reports"])

@router.get("/dashboard-summary")
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
        raise HTTPException(status_code=403, detail="Only Managers and Staff can access dashboard analytics")

    total_lots = db.query(ParkingLot).count()
    total_slots = db.query(ParkingSlot).count()
    occupied_slots = db.query(ParkingSlot).filter(ParkingSlot.status == SlotStatus.OCCUPIED).count()
    vacant_slots = db.query(ParkingSlot).filter(ParkingSlot.status == SlotStatus.VACANT).count()
    reserved_slots = db.query(ParkingSlot).filter(ParkingSlot.status == SlotStatus.RESERVED).count()

    total_revenue = db.query(func.sum(Payment.amount)).filter(Payment.payment_status == "PAID").scalar() or 0.0
    active_sessions = db.query(ParkingSession).filter(ParkingSession.status == "ACTIVE").count()
    unresolved_alerts = db.query(FraudAlert).filter(FraudAlert.resolved == False).count()

    occupancy_pct = round((occupied_slots / total_slots * 100), 1) if total_slots > 0 else 0.0

    return {
        "total_lots": total_lots,
        "total_slots": total_slots,
        "occupied_slots": occupied_slots,
        "vacant_slots": vacant_slots,
        "reserved_slots": reserved_slots,
        "occupancy_rate_pct": occupancy_pct,
        "total_revenue_usd": round(total_revenue, 2),
        "active_sessions_count": active_sessions,
        "fraud_alerts_count": unresolved_alerts,
        "system_health": "OPTIMAL",
        "timestamp": datetime.utcnow()
    }

@router.get("/fraud-alerts")
def get_fraud_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
        raise HTTPException(status_code=403, detail="Access denied")

    alerts = db.query(FraudAlert).order_by(FraudAlert.created_at.desc()).all()
    return alerts
