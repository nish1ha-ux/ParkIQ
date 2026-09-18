import asyncio
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.services.seed_data import seed_database
from app.routers import auth, vehicles, qr, sessions, ai_predict, rag_chat, payments, analytics, notifications
from app.models.models import ParkingSession, SessionStatus, NotificationLog
from app.services.notification_service import notification_service
from app.services.websocket_service import websocket_manager

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise-grade AI-powered Smart Parking Intelligence Platform API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True if "*" not in origins else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def check_parking_sessions_loop():
    """
    Background loop that runs periodically to monitor active parking sessions.
    Dispatches notifications and WebSocket updates when parking is ending soon or expired.
    """
    print("[Session Checker] Background monitoring task started.")
    while True:
        # Check every 10 seconds for real-time responsiveness and test compatibility
        await asyncio.sleep(10)
        db = SessionLocal()
        try:
            now = datetime.utcnow()  # Matches DB naive datetime model timestamps
            # Fetch active sessions
            active_sessions = db.query(ParkingSession).filter(
                ParkingSession.status == SessionStatus.ACTIVE
            ).all()
            
            for session in active_sessions:
                exp_dep = session.predicted_departure
                if not exp_dep:
                    continue
                
                # Calculate remaining time in minutes
                diff_seconds = (exp_dep - now).total_seconds()
                rem_minutes = diff_seconds / 60.0
                
                # 1. Check if session has expired
                if rem_minutes <= 0:
                    # Check if already notified
                    sent = db.query(NotificationLog).filter(
                        NotificationLog.session_id == session.id,
                        NotificationLog.event_type == "SESSION_EXPIRED"
                    ).first()
                    if not sent:
                        # Send FCM notification
                        notification_service.send_session_expired(
                            db=db,
                            user_id=session.vehicle.user_id,
                            session_id=session.id,
                            slot_number=session.slot.slot_number
                        )
                        # Set status to VIOLATION
                        session.status = SessionStatus.VIOLATION
                        db.commit()
                        
                        # Broadcast WebSocket event
                        await websocket_manager.broadcast({
                            "event": "parking_expired",
                            "session_id": session.id,
                            "user_id": session.vehicle.user_id,
                            "slot_number": session.slot.slot_number,
                            "message": f"Parking session in slot {session.slot.slot_number} has expired. Status updated to VIOLATION."
                        })
                # 2. Check if session is expiring soon (<= 20 minutes remaining)
                elif rem_minutes <= 20:
                    # Check if already notified
                    sent = db.query(NotificationLog).filter(
                        NotificationLog.session_id == session.id,
                        NotificationLog.event_type == "EXPIRES_IN_20"
                    ).first()
                    if not sent:
                        # Send FCM notification
                        notification_service.send_session_expiring_soon(
                            db=db,
                            user_id=session.vehicle.user_id,
                            session_id=session.id,
                            slot_number=session.slot.slot_number,
                            remaining_minutes=20
                        )
                        # Broadcast WebSocket event
                        await websocket_manager.broadcast({
                            "event": "parking_ending",
                            "session_id": session.id,
                            "user_id": session.vehicle.user_id,
                            "slot_number": session.slot.slot_number,
                            "remaining_minutes": 20,
                            "message": f"Parking session in slot {session.slot.slot_number} is ending soon (under 20 minutes remaining)."
                        })
        except Exception as e:
            print(f"[Session Checker] Error: {e}")
        finally:
            db.close()

# Startup Event: Auto Seed DB & launch background tasks
@app.on_event("startup")
def on_startup():
    print("[ParkIQ] Starting ParkIQ backend service...")
    seed_database()
    # Start async session checker task in background
    asyncio.create_task(check_parking_sessions_loop())

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(vehicles.router, prefix=settings.API_V1_STR)
app.include_router(qr.router, prefix=settings.API_V1_STR)
app.include_router(sessions.router, prefix=settings.API_V1_STR)
app.include_router(ai_predict.router, prefix=settings.API_V1_STR)
app.include_router(rag_chat.router, prefix=settings.API_V1_STR)
app.include_router(payments.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ONLINE",
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "message": "Welcome to ParkIQ Smart Parking Intelligence Platform API"
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "HEALTHY", "database": "CONNECTED"}
