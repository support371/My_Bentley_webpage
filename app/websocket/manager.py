"""
WebSocket connection manager for real-time event streaming.

This module handles WebSocket connections from the frontend and
broadcasts real-time events to connected clients.
"""

import json
from typing import Set, Any
from datetime import datetime
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and event broadcasting."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.user_connections: dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str | None = None):
        """
        Accept and register a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            user_id: Optional user ID for user-specific connections
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
        
        logger.info(f"WebSocket connected: {len(self.active_connections)} total")
    
    def disconnect(self, websocket: WebSocket, user_id: str | None = None):
        """
        Unregister a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            user_id: Optional user ID
        """
        self.active_connections.discard(websocket)
        
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.info(f"WebSocket disconnected: {len(self.active_connections)} remaining")
    
    async def broadcast(self, data: dict[str, Any]):
        """
        Broadcast a message to all connected clients.
        
        Args:
            data: Dictionary to broadcast as JSON
        """
        if not self.active_connections:
            return
        
        message = json.dumps({
            **data,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Broadcast to all clients
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.active_connections.discard(connection)
    
    async def broadcast_to_user(
        self,
        user_id: str,
        data: dict[str, Any],
    ):
        """
        Broadcast a message to a specific user's connections.
        
        Args:
            user_id: The user ID
            data: Dictionary to broadcast as JSON
        """
        if user_id not in self.user_connections:
            return
        
        message = json.dumps({
            **data,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        disconnected = []
        for connection in self.user_connections[user_id]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending to user WebSocket: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            self.user_connections[user_id].discard(connection)
    
    def get_connection_count(self) -> int:
        """Get current number of active connections."""
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()
