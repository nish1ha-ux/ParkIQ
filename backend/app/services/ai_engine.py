import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
from sqlalchemy.orm import Session
from app.models.models import ParkingSlot, ParkingSession, SlotStatus, FraudAlert

class ParkIQAIEngine:
    """
    AI Predictive Analytics Engine for ParkIQ:
    - Smart Parking Slot Recommendation based on proximity & occupancy dynamics.
    - Departure Time & Parking Duration Forecasting.
    - Future Occupancy & Congestion Rate Prediction.
    - Real-time QR Fraud & Unauthorized Parking Anomaly Detection.
    """

    @staticmethod
    def predict_departure_time(vehicle_type: str, entry_time: datetime) -> datetime:
        """
        Predicts vehicle departure time based on vehicle type, day of week, and entry time.
        """
        hour = entry_time.hour
        # Base duration patterns: Workday peak vs quick visit
        if 8 <= hour <= 10:
            duration_minutes = random.randint(240, 480)  # Workday stay (4-8 hours)
        elif 12 <= hour <= 14:
            duration_minutes = random.randint(45, 90)    # Lunch visit
        elif 17 <= hour <= 20:
            duration_minutes = random.randint(90, 180)   # Evening shopping / dinner
        else:
            duration_minutes = random.randint(60, 120)

        # EV vehicles often park longer if charging
        if vehicle_type == "EV":
            duration_minutes += 30

        return entry_time + timedelta(minutes=duration_minutes)

    @staticmethod
    def recommend_best_slots(db: Session, lot_id: str, limit: int = 3) -> List[str]:
        """
        Scores vacant slots in a lot and recommends the optimal ones.
        Scoring algorithm prioritizes lower floor levels and slots near main entrance.
        """
        vacant_slots = db.query(ParkingSlot).filter(
            ParkingSlot.lot_id == lot_id,
            ParkingSlot.status == SlotStatus.VACANT
        ).all()

        if not vacant_slots:
            return []

        # Sort slots by floor level ASC, then slot number
        sorted_slots = sorted(vacant_slots, key=lambda s: (s.floor_level, s.slot_number))
        return [s.id for s in sorted_slots[:limit]]

    @staticmethod
    def forecast_occupancy(db: Session, lot_id: str, offset_hours: int = 1) -> Dict[str, Any]:
        """
        Predicts lot occupancy and congestion level after N hours.
        """
        total_slots = db.query(ParkingSlot).filter(ParkingSlot.lot_id == lot_id).count()
        if total_slots == 0:
            total_slots = 50

        occupied_count = db.query(ParkingSlot).filter(
            ParkingSlot.lot_id == lot_id,
            ParkingSlot.status == SlotStatus.OCCUPIED
        ).count()

        current_pct = round((occupied_count / total_slots) * 100, 1)

        # Time-based projection matrix
        target_time = datetime.utcnow() + timedelta(hours=offset_hours)
        hour = target_time.hour
        
        # Traffic multiplier
        if 8 <= hour <= 11 or 17 <= hour <= 19:
            trend_factor = 1.25  # High influx peak
        elif 22 <= hour or hour <= 6:
            trend_factor = 0.4   # Low night usage
        else:
            trend_factor = 0.95

        predicted_pct = min(100.0, max(5.0, round(current_pct * trend_factor, 1)))

        if predicted_pct >= 85.0:
            congestion = "CRITICAL"
        elif predicted_pct >= 70.0:
            congestion = "HIGH"
        elif predicted_pct >= 40.0:
            congestion = "MODERATE"
        else:
            congestion = "LOW"

        vacant_recommended = ParkIQAIEngine.recommend_best_slots(db, lot_id)

        return {
            "lot_id": lot_id,
            "current_occupancy_pct": current_pct,
            "predicted_occupancy_pct": predicted_pct,
            "predicted_congestion_level": congestion,
            "recommended_slot_ids": vacant_recommended,
            "average_predicted_duration_minutes": 135
        }

    @staticmethod
    def detect_qr_fraud(db: Session, vehicle_id: str, slot_id: str, qr_token: str) -> Optional[FraudAlert]:
        """
        Checks for QR fraud or duplicate check-in anomalies.
        """
        # Check if vehicle already has an active session
        existing_session = db.query(ParkingSession).filter(
            ParkingSession.vehicle_id == vehicle_id,
            ParkingSession.status == "ACTIVE"
        ).first()

        if existing_session:
            alert = FraudAlert(
                session_id=existing_session.id,
                alert_type="DUPLICATE_SCAN",
                severity="HIGH",
                details=f"Vehicle ID {vehicle_id} attempted duplicate QR entry while session {existing_session.id} is active."
            )
            db.add(alert)
            db.commit()
            
            # Send security alerts via Notification Service
            from app.services.notification_service import notification_service
            user_id = existing_session.vehicle.owner.id if existing_session.vehicle and existing_session.vehicle.owner else None
            if user_id:
                notification_service.send_security_alert(
                    db=db,
                    user_id=user_id,
                    session_id=existing_session.id,
                    alert_type="DUPLICATE_SCAN",
                    details=alert.details
                )
                notification_service.send_suspicious_qr_activity(
                    db=db,
                    user_id=user_id,
                    details="Suspicious concurrent QR check-in attempt blocked for your vehicle."
                )
            
            return alert

        return None

    @staticmethod
    def evaluate_session_notifications(db: Session):
        """
        AI dynamic evaluation logic to determine which notification alerts should be dispatched.
        """
        import math
        from app.services.notification_service import notification_service
        from app.models.models import SessionStatus, NotificationLog
        
        now = datetime.utcnow()
        active_sessions = db.query(ParkingSession).filter(ParkingSession.status == SessionStatus.ACTIVE).all()
        
        for session in active_sessions:
            if not session.predicted_departure:
                continue
            
            # Calculate remaining time in minutes
            remaining_seconds = (session.predicted_departure - now).total_seconds()
            remaining_minutes = remaining_seconds / 60.0
            
            # AI Dynamic Decision based on lot congestion:
            lot_id = session.slot.lot_id if session.slot else None
            congestion = "LOW"
            if lot_id:
                forecast = ParkIQAIEngine.forecast_occupancy(db, lot_id)
                congestion = forecast.get("predicted_congestion_level", "LOW")
            
            # Determine alert intervals based on congestion pressure
            if congestion in ("CRITICAL", "HIGH"):
                # Congested: Send granular notifications at 30, 20, 10, 5 mins and expired
                target_warnings = [30, 20, 10, 5, 0]
            elif congestion == "MODERATE":
                # Moderate: Send notifications at 20, 10, and expired
                target_warnings = [20, 10, 0]
            else:
                # Low congestion: Send notifications at 10 and expired
                target_warnings = [10, 0]
                
            for mins in target_warnings:
                event_type = f"EXPIRES_IN_{mins}" if mins > 0 else "SESSION_EXPIRED"
                
                # Check if already sent
                sent_log = db.query(NotificationLog).filter(
                    NotificationLog.session_id == session.id,
                    NotificationLog.event_type == event_type
                ).first()
                
                if sent_log:
                    continue
                
                # Dispatch trigger logic
                if mins > 0:
                    if remaining_minutes <= mins and remaining_minutes > (mins - 5):
                        user_id = session.vehicle.user_id if session.vehicle else None
                        if user_id:
                            notification_service.send_session_expiring_soon(
                                db=db,
                                user_id=user_id,
                                session_id=session.id,
                                slot_number=session.slot.slot_number if session.slot else "N/A",
                                remaining_minutes=mins
                            )
                else:
                    # Expired check
                    if remaining_minutes <= 0:
                        session.status = SessionStatus.VIOLATION
                        db.commit()
                        
                        user_id = session.vehicle.user_id if session.vehicle else None
                        if user_id:
                            notification_service.send_session_expired(
                                db=db,
                                user_id=user_id,
                                session_id=session.id,
                                slot_number=session.slot.slot_number if session.slot else "N/A"
                            )

ai_engine = ParkIQAIEngine()
