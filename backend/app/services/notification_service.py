import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from app.config import settings
from app.models.models import UserDeviceToken, NotificationLog

logger = logging.getLogger("parkiq.notifications")

# Dynamically import Firebase SDK to ensure tests run even if packages are missing or during fallback.
firebase_available = False
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    firebase_available = True
except ImportError:
    logger.warning("firebase-admin package not installed. NotificationService will run in MOCK mode.")

class NotificationService:
    """
    Intelligent Notification Service for ParkIQ.
    Integrates with Firebase Cloud Messaging (FCM) for push notifications.
    Supports a transparent Mock Mode for development and testing.
    """
    def __init__(self):
        self.initialized = False
        if firebase_available and settings.FIREBASE_CREDENTIALS_PATH and not settings.FCM_MOCK_MODE:
            try:
                # Initialize Firebase App if not already initialized
                try:
                    firebase_admin.get_app()
                except ValueError:
                    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                    firebase_admin.initialize_app(cred)
                self.initialized = True
                logger.info("Firebase Admin SDK initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Firebase Admin SDK: {e}. Falling back to MOCK mode.")

    def send_push_notification(
        self,
        db: Session,
        user_id: str,
        event_type: str,
        title: str,
        body: str,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Sends a push notification to all registered devices of a user.
        Logs every dispatch to the Database for audit.
        """
        # Fetch registered device tokens for the user
        device_tokens = db.query(UserDeviceToken).filter(UserDeviceToken.user_id == user_id).all()
        tokens = [t.token for t in device_tokens]

        status = "SENT"
        if not tokens:
            logger.info(f"No FCM tokens registered for user {user_id}. Logged only.")
            status = "NO_DEVICE"

        # If real Firebase is initialized and we have tokens, dispatch them
        if self.initialized and tokens and not settings.FCM_MOCK_MODE:
            try:
                for token in tokens:
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title=title,
                            body=body
                        ),
                        data={
                            "event_type": event_type,
                            "session_id": session_id or ""
                        },
                        token=token
                    )
                    messaging.send(message)
                logger.info(f"Push notification of type {event_type} sent successfully to user {user_id}.")
            except Exception as e:
                logger.error(f"FCM send failed for user {user_id}: {e}")
                status = "FAILED"
        else:
            # FCM Mock / Log fallback
            mock_prefix = "[FCM MOCK]"
            if settings.FCM_MOCK_MODE:
                mock_prefix = "[FCM MOCK (Enabled)]"
            elif not self.initialized:
                mock_prefix = "[FCM MOCK (Firebase Uninitialized)]"
            logger.info(f"{mock_prefix} User: {user_id} | Type: {event_type} | Title: {title} | Body: {body}")

        # Persist notification log
        log_entry = NotificationLog(
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            title=title,
            body=body,
            status=status
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return status in ("SENT", "NO_DEVICE")

    # Helper methods for specific Phase 7 notification events:

    def send_session_started(self, db: Session, user_id: str, session_id: str, slot_number: str) -> bool:
        return self.send_push_notification(
            db=db,
            user_id=user_id,
            session_id=session_id,
            event_type="SESSION_STARTED",
            title="Parking Session Started",
            body=f"Your parking session has started in slot {slot_number}."
        )

    def send_session_expiring_soon(self, db: Session, user_id: str, session_id: str, slot_number: str, remaining_minutes: int) -> bool:
        return self.send_push_notification(
            db=db,
            user_id=user_id,
            session_id=session_id,
            event_type=f"EXPIRES_IN_{remaining_minutes}",
            title="Parking Session Expiring Soon",
            body=f"Your parking session in slot {slot_number} expires in {remaining_minutes} minutes."
        )

    def send_session_expired(self, db: Session, user_id: str, session_id: str, slot_number: str) -> bool:
        return self.send_push_notification(
            db=db,
            user_id=user_id,
            session_id=session_id,
            event_type="SESSION_EXPIRED",
            title="Parking Session Expired",
            body=f"Your parking session in slot {slot_number} has expired. Please vacate or extend immediately."
        )

    def send_session_extended(self, db: Session, user_id: str, session_id: str, slot_number: str, extended_minutes: int) -> bool:
        return self.send_push_notification(
            db=db,
            user_id=user_id,
            session_id=session_id,
            event_type="SESSION_EXTENDED",
            title="Parking Session Extended",
            body=f"Your parking session in slot {slot_number} was successfully extended by {extended_minutes} minutes."
        )

    def send_slot_available(self, db: Session, user_id: str, slot_number: str) -> bool:
        return self.send_push_notification(
            db=db,
            user_id=user_id,
            event_type="SLOT_AVAILABLE",
            title="Reserved Slot Available",
            body=f"Your reserved parking slot {slot_number} is now vacant and ready for check-in."
        )

    def send_reservation_confirmation(self, db: Session, user_id: str, reservation_id: str, slot_number: str, start_time: datetime) -> bool:
        formatted_time = start_time.strftime("%I:%M %p")
        return self.send_push_notification(
            db=db,
            user_id=user_id,
            event_type="RESERVATION_CONFIRMED",
            title="Reservation Confirmed",
            body=f"Reservation {reservation_id[:8]} confirmed for slot {slot_number} starting at {formatted_time}."
        )

    def send_security_alert(self, db: Session, user_id: str, session_id: str, alert_type: str, details: str) -> bool:
        return self.send_push_notification(
            db=db,
            user_id=user_id,
            session_id=session_id,
            event_type="SECURITY_ALERT",
            title=f"Security Alert: {alert_type}",
            body=details
        )

    def send_suspicious_qr_activity(self, db: Session, user_id: str, details: str) -> bool:
        return self.send_push_notification(
            db=db,
            user_id=user_id,
            event_type="SUSPICIOUS_QR_ACTIVITY",
            title="Suspicious QR Activity Detected",
            body=details
        )

notification_service = NotificationService()
