"""
WebSocket routes for real-time event streaming.

Provides endpoints for establishing WebSocket connections and
streaming real-time events to connected clients.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
import logging

from app.core.security import get_current_user_id
from app.websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/ws/events")
async def websocket_events(
    websocket: WebSocket,
    user_id: str = Query(None),
):
    """
    WebSocket endpoint for real-time event streaming.
    
    Query Parameters:
        user_id: Optional user ID for filtering events
    
    Broadcast Message Format:
        {
            "type": "event",
            "data": { ... event data ... },
            "timestamp": "2024-01-01T12:00:00"
        }
    """
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "disconnect":
                await websocket.close()
                break
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket disconnected for user: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)


@router.post("/events/broadcast")
async def broadcast_event(
    event_data: dict,
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Broadcast an event to all connected WebSocket clients.
    
    This endpoint is for testing and for the backend to push events
    to all connected frontend clients.
    
    Args:
        event_data: The event data to broadcast
        current_user_id: Current user (requires authentication)
    
    Returns:
        Success confirmation
    """
    await manager.broadcast({
        "type": "event",
        "user": current_user_id,
        **event_data,
    })
    
    return {
        "status": "broadcast_sent",
        "connections": manager.get_connection_count(),
    }
