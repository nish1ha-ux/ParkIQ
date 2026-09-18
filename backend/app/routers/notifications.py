import logging
from typing import Optional
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, UserDeviceToken
from app.schemas.schemas import DeviceTokenRegisterRequest
from app.routers.auth import get_current_user
from app.core.security import decode_access_token
from app.services.websocket_service import websocket_manager

logger = logging.getLogger("parkiq.notifications")

router = APIRouter(prefix="/notifications", tags=["Notifications & Live Feeds"])

@router.post("/register-token", status_code=status.HTTP_201_CREATED)
def register_device_token(
    req: DeviceTokenRegisterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Registers a Firebase Cloud Messaging device token for push notifications.
    """
    # Check if this token is already registered for the user
    existing = db.query(UserDeviceToken).filter(
        UserDeviceToken.user_id == current_user.id,
        UserDeviceToken.token == req.token
    ).first()

    if not existing:
        new_token = UserDeviceToken(
            user_id=current_user.id,
            token=req.token
        )
        db.add(new_token)
        db.commit()
        logger.info(f"Registered new device token for user {current_user.id}.")
        return {"status": "REGISTERED", "message": "Device token successfully associated."}
        
    return {"status": "EXISTS", "message": "Device token already registered."}

@router.websocket("/ws")
async def websocket_notifications_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time dashboard events and notifications.
    Requires a valid JWT token passed as a query parameter (?token=...) or WS header/subprotocol.
    """
    # Extract token from query params if not injected
    ws_token = token or websocket.query_params.get("token")
    
    # Validate the token and associated user
    valid = False
    reason = "Authentication token is missing"
    
    if ws_token:
        payload = decode_access_token(ws_token)
        if payload:
            user_id = payload.get("sub")
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                valid = True
            else:
                reason = "Associated user does not exist"
        else:
            reason = "Invalid or expired authentication token"

    if not valid:
        # Accept then close immediately to return the policy violation code
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=reason)
        return

    # If valid, ConnectionManager.connect will call accept()
    await websocket_manager.connect(websocket)
    try:
        while True:
            # We listen for messages to keep connection active and catch client disconnects
            data = await websocket.receive_text()
            # Echo back or log if needed, otherwise ignore client commands
            await websocket_manager.send_personal_message({"status": "ACK", "echo": data}, websocket)
    except WebSocketDisconnect:
        logger.info("WebSocket connection disconnected by client.")
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        websocket_manager.disconnect(websocket)
