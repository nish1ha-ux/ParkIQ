import logging
from fastapi import WebSocket
from typing import List

logger = logging.getLogger("parkiq.websockets")

class ConnectionManager:
    """
    Manages active WebSocket connections for live notifications.
    Supports connection tracking, single-client messaging, and broadcasts.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send direct WebSocket message: {e}")

    async def broadcast(self, message: dict):
        logger.info(f"Broadcasting WebSocket event '{message.get('event')}' to {len(self.active_connections)} clients.")
        # Create a copy of connections to prevent mutation during iteration
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send broadcast to connection. Removing dead connection: {e}")
                self.disconnect(connection)

websocket_manager = ConnectionManager()
