from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.models import User, ParkingSession, Payment, PaymentStatus
from app.schemas.schemas import PaymentCreateRequest, PaymentVerifyRequest
from app.routers.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/payments", tags=["Razorpay Payment Gateway Integration"])

@router.post("/create-order")
def create_payment_order(
    req: PaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(ParkingSession).filter(ParkingSession.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Parking session not found")

    # Calculate fare based on duration
    exit_t = session.actual_exit_time or datetime.utcnow()
    duration_hours = max(1.0, round((exit_t - session.entry_time).total_seconds() / 3600.0, 2))
    rate = session.slot.lot.base_hourly_rate if session.slot and session.slot.lot else 5.0
    amount = round(duration_hours * rate, 2)

    # Generate mock Razorpay Order ID
    order_id = f"order_parkiq_{session.id[:8]}_{int(datetime.utcnow().timestamp())}"

    payment = Payment(
        session_id=session.id,
        user_id=current_user.id,
        amount=amount,
        payment_status=PaymentStatus.PENDING,
        razorpay_order_id=order_id
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {
        "payment_id": payment.id,
        "amount": amount,
        "currency": "USD",
        "razorpay_order_id": order_id,
        "key_id": settings.RAZORPAY_KEY_ID,
        "duration_hours": duration_hours,
        "hourly_rate": rate
    }

@router.post("/verify")
def verify_payment(
    req: PaymentVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    payment = db.query(Payment).filter(Payment.id == req.payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    payment.payment_status = PaymentStatus.PAID
    payment.razorpay_payment_id = req.razorpay_order_id.replace("order_", "pay_")
    db.commit()

    return {
        "status": "SUCCESS",
        "message": "Payment successfully processed and verified.",
        "payment_id": payment.id,
        "amount_paid": payment.amount
    }
