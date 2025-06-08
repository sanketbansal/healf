"""
WebSocket Data Access Object (DAO) using generic Redis DAO
"""

from typing import Dict, Any, Optional, Set, List
from datetime import datetime, timezone, timedelta
from fastapi import WebSocket
from app.dao.redis_dao import get_redis_dao

class WebSocketDAO:
    """WebSocket DAO using generic Redis DAO for session and state management"""
    
    def __init__(self):
        self.redis_dao = get_redis_dao()
        # In-memory connections (these can't be stored in Redis)
        self.active_connections: Dict[str, WebSocket] = {}
        
    def _get_session_key(self, user_id: str) -> str:
        """Generate session key for user"""
        return f"session:{user_id}"
    
    def _get_context_key(self, user_id: str) -> str:
        """Generate context key for user"""
        return f"context:{user_id}"
    
    def _get_stats_key(self) -> str:
        """Generate key for WebSocket statistics"""
        return "websocket_stats"
    
    async def connect_user(self, user_id: str, websocket: WebSocket) -> None:
        """Handle new WebSocket connection"""
        # Store connection in memory
        self.active_connections[user_id] = websocket
        
        # Create session in Redis using generic DAO
        session_data = {
            "user_id": user_id,
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "message_count": 0,
            "session_state": "active"
        }
        
        await self.redis_dao.session_create(user_id, session_data, ttl=3600)
        
        # Update global stats
        await self._update_connection_stats(1)
    
    async def disconnect_user(self, user_id: str) -> None:
        """Handle WebSocket disconnection"""
        # Remove from active connections
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # Update session in Redis using generic DAO
        session_data = await self.redis_dao.session_get(user_id)
        if session_data:
            session_data["disconnected_at"] = datetime.now(timezone.utc).isoformat()
            session_data["session_state"] = "disconnected"
            
            # Store disconnected session for 24 hours for analytics
            await self.redis_dao.set(
                self._get_session_key(user_id), 
                session_data, 
                ttl=86400
            )
        
        # Update global stats
        await self._update_connection_stats(-1)
    
    async def is_user_connected(self, user_id: str) -> bool:
        """Check if user is currently connected"""
        return user_id in self.active_connections
    
    async def get_user_websocket(self, user_id: str) -> Optional[WebSocket]:
        """Get WebSocket connection for user"""
        return self.active_connections.get(user_id)
    
    async def get_session_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Redis using generic DAO"""
        return await self.redis_dao.session_get(user_id)
    
    async def update_session_activity(self, user_id: str, message_type: str = None) -> None:
        """Update session activity and message count"""
        session_data = await self.redis_dao.session_get(user_id)
        if session_data:
            # Update activity and message count
            update_data = {
                "last_activity": datetime.now(timezone.utc).isoformat(),
                "message_count": session_data.get("message_count", 0) + 1
            }
            
            # Track message types
            if message_type:
                message_types = session_data.get("message_types", {})
                message_types[message_type] = message_types.get(message_type, 0) + 1
                update_data["message_types"] = message_types
            
            await self.redis_dao.session_update(user_id, update_data, extend_ttl=True)
    
    async def store_conversation_context(self, user_id: str, context: Dict[str, Any]) -> None:
        """Store conversation context in Redis using generic DAO"""
        await self.redis_dao.set(
            self._get_context_key(user_id), 
            context, 
            ttl=3600  # 1 hour TTL
        )
    
    async def get_conversation_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation context from Redis using generic DAO"""
        return await self.redis_dao.get(self._get_context_key(user_id))
    
    async def _update_connection_stats(self, delta: int) -> None:
        """Update global connection statistics using generic DAO"""
        stats_key = self._get_stats_key()
        
        # Get current stats
        stats = await self.redis_dao.get(stats_key)
        if not stats:
            stats = {
                "active_connections": 0,
                "total_connections": 0,
                "peak_connections": 0,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        
        # Update stats
        stats["active_connections"] = max(0, stats["active_connections"] + delta)
        if delta > 0:
            stats["total_connections"] += 1
            stats["peak_connections"] = max(stats["peak_connections"], stats["active_connections"])
        stats["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        # Store updated stats (no expiration for persistent stats)
        await self.redis_dao.set(stats_key, stats)
    
    async def get_connection_statistics(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics using generic DAO"""
        stats_key = self._get_stats_key()
        stats = await self.redis_dao.get(stats_key)
        
        if stats:
            # Add current in-memory count for accuracy
            stats["current_in_memory"] = len(self.active_connections)
            return stats
        
        return {
            "active_connections": len(self.active_connections),
            "current_in_memory": len(self.active_connections),
            "total_connections": 0,
            "peak_connections": 0,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_active_user_ids(self) -> Set[str]:
        """Get set of currently active user IDs"""
        return set(self.active_connections.keys())
    
    async def get_user_activity_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user activity summary"""
        session_data = await self.get_session_data(user_id)
        context_data = await self.get_conversation_context(user_id)
        
        return {
            "session": session_data,
            "context": context_data,
            "is_connected": self.is_user_connected(user_id),
            "connection_count": len(self.active_connections)
        }
    
    async def store_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Store user preferences using generic DAO"""
        pref_key = f"user_prefs:{user_id}"
        return await self.redis_dao.set(pref_key, preferences, ttl=2592000)  # 30 days TTL
    
    async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences using generic DAO"""
        pref_key = f"user_prefs:{user_id}"
        return await self.redis_dao.get(pref_key)
    
    async def track_user_event(self, user_id: str, event_type: str, event_data: Dict[str, Any] = None) -> bool:
        """Track user events for analytics using Redis lists"""
        event_key = f"events:{user_id}"
        
        event = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": event_data or {}
        }
        
        # Use Redis list to store events (latest first)
        await self.redis_dao.lpush(event_key, event)
        
        # Keep only latest 100 events per user
        list_length = await self.redis_dao.llen(event_key)
        if list_length > 100:
            # Trim list to keep only latest 100 events
            await self.redis_dao.get_client().ltrim(event_key, 0, 99)
        
        # Set TTL on events key
        await self.redis_dao.expire(event_key, 86400)  # 24 hours
        
        return True
    
    async def get_user_events(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user events using Redis lists"""
        event_key = f"events:{user_id}"
        return await self.redis_dao.lrange(event_key, 0, limit - 1)
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions using generic DAO"""
        # Get all session keys
        session_keys = await self.redis_dao.keys("session:*")
        cleaned_count = 0
        
        for key in session_keys:
            session_data = await self.redis_dao.get(key)
            if session_data and session_data.get("session_state") == "disconnected":
                disconnected_at_str = session_data.get("disconnected_at")
                if disconnected_at_str:
                    try:
                        disconnected_at = datetime.fromisoformat(disconnected_at_str)
                        if datetime.now(timezone.utc) - disconnected_at > timedelta(hours=24):
                            await self.redis_dao.delete(key)
                            cleaned_count += 1
                    except ValueError:
                        # Invalid date format, clean it up
                        await self.redis_dao.delete(key)
                        cleaned_count += 1
        
        return cleaned_count
    
    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive WebSocket analytics"""
        connection_stats = await self.get_connection_statistics()
        
        # Get session statistics
        session_keys = await self.redis_dao.keys("session:*")
        active_sessions = 0
        disconnected_sessions = 0
        
        for key in session_keys:
            session_data = await self.redis_dao.get(key)
            if session_data:
                if session_data.get("session_state") == "active":
                    active_sessions += 1
                else:
                    disconnected_sessions += 1
        
        return {
            "connections": connection_stats,
            "sessions": {
                "active": active_sessions,
                "disconnected": disconnected_sessions,
                "total": active_sessions + disconnected_sessions
            },
            "memory": {
                "active_connections": len(self.active_connections),
                "connection_ids": list(self.active_connections.keys())
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of Redis connection and WebSocket state"""
        redis_healthy = await self.redis_dao.ping()
        
        return {
            "redis": redis_healthy,
            "active_connections": len(self.active_connections),
            "memory_usage": {
                "connections": len(self.active_connections)
            }
        }
    
    async def close_connections(self):
        """Close Redis connections using generic DAO"""
        await self.redis_dao.close()

# Singleton instance
_websocket_dao_instance = None

def get_websocket_dao() -> WebSocketDAO:
    """Get singleton WebSocketDAO instance"""
    global _websocket_dao_instance
    if _websocket_dao_instance is None:
        _websocket_dao_instance = WebSocketDAO()
    return _websocket_dao_instance 