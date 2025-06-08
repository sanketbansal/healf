"""
Generic Redis Data Access Object (DAO)
Provides reusable Redis operations for caching, session management, and data storage
"""

import json
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone, timedelta
import redis.asyncio as redis
from app.config import settings

class RedisDAO:
    """Generic Redis DAO for all Redis operations"""
    
    def __init__(self):
        self._redis_client: Optional[redis.Redis] = None
        
    async def get_client(self) -> redis.Redis:
        """Get Redis client with connection pooling"""
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD if hasattr(settings, 'REDIS_PASSWORD') else None,
                decode_responses=True,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                max_connections=20
            )
        return self._redis_client
    
    # =================== Basic Operations ===================
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a key-value pair with optional TTL"""
        try:
            client = await self.get_client()
            serialized_value = json.dumps(value, default=str)
            
            if ttl:
                return await client.setex(key, ttl, serialized_value)
            else:
                return await client.set(key, serialized_value)
        except Exception as e:
            print(f"Redis SET error for key {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        try:
            client = await self.get_client()
            value = await client.get(key)
            
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis GET error for key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key"""
        try:
            client = await self.get_client()
            result = await client.delete(key)
            return result > 0
        except Exception as e:
            print(f"Redis DELETE error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            client = await self.get_client()
            return await client.exists(key) > 0
        except Exception as e:
            print(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key"""
        try:
            client = await self.get_client()
            return await client.expire(key, ttl)
        except Exception as e:
            print(f"Redis EXPIRE error for key {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get TTL for key"""
        try:
            client = await self.get_client()
            return await client.ttl(key)
        except Exception as e:
            print(f"Redis TTL error for key {key}: {e}")
            return -1
    
    # =================== Hash Operations ===================
    
    async def hset(self, key: str, field: str, value: Any) -> bool:
        """Set hash field"""
        try:
            client = await self.get_client()
            serialized_value = json.dumps(value, default=str)
            return await client.hset(key, field, serialized_value)
        except Exception as e:
            print(f"Redis HSET error for key {key}, field {field}: {e}")
            return False
    
    async def hget(self, key: str, field: str) -> Optional[Any]:
        """Get hash field"""
        try:
            client = await self.get_client()
            value = await client.hget(key, field)
            
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis HGET error for key {key}, field {field}: {e}")
            return None
    
    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all hash fields"""
        try:
            client = await self.get_client()
            hash_data = await client.hgetall(key)
            
            result = {}
            for field, value in hash_data.items():
                try:
                    result[field] = json.loads(value)
                except json.JSONDecodeError:
                    result[field] = value
            
            return result
        except Exception as e:
            print(f"Redis HGETALL error for key {key}: {e}")
            return {}
    
    async def hdel(self, key: str, field: str) -> bool:
        """Delete hash field"""
        try:
            client = await self.get_client()
            return await client.hdel(key, field) > 0
        except Exception as e:
            print(f"Redis HDEL error for key {key}, field {field}: {e}")
            return False
    
    # =================== List Operations ===================
    
    async def lpush(self, key: str, *values: Any) -> int:
        """Push values to left of list"""
        try:
            client = await self.get_client()
            serialized_values = [json.dumps(v, default=str) for v in values]
            return await client.lpush(key, *serialized_values)
        except Exception as e:
            print(f"Redis LPUSH error for key {key}: {e}")
            return 0
    
    async def rpush(self, key: str, *values: Any) -> int:
        """Push values to right of list"""
        try:
            client = await self.get_client()
            serialized_values = [json.dumps(v, default=str) for v in values]
            return await client.rpush(key, *serialized_values)
        except Exception as e:
            print(f"Redis RPUSH error for key {key}: {e}")
            return 0
    
    async def lrange(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get list range"""
        try:
            client = await self.get_client()
            values = await client.lrange(key, start, end)
            
            result = []
            for value in values:
                try:
                    result.append(json.loads(value))
                except json.JSONDecodeError:
                    result.append(value)
            
            return result
        except Exception as e:
            print(f"Redis LRANGE error for key {key}: {e}")
            return []
    
    async def llen(self, key: str) -> int:
        """Get list length"""
        try:
            client = await self.get_client()
            return await client.llen(key)
        except Exception as e:
            print(f"Redis LLEN error for key {key}: {e}")
            return 0
    
    # =================== Set Operations ===================
    
    async def sadd(self, key: str, *members: Any) -> int:
        """Add members to set"""
        try:
            client = await self.get_client()
            serialized_members = [json.dumps(m, default=str) for m in members]
            return await client.sadd(key, *serialized_members)
        except Exception as e:
            print(f"Redis SADD error for key {key}: {e}")
            return 0
    
    async def smembers(self, key: str) -> set:
        """Get all set members"""
        try:
            client = await self.get_client()
            members = await client.smembers(key)
            
            result = set()
            for member in members:
                try:
                    result.add(json.loads(member))
                except json.JSONDecodeError:
                    result.add(member)
            
            return result
        except Exception as e:
            print(f"Redis SMEMBERS error for key {key}: {e}")
            return set()
    
    async def srem(self, key: str, *members: Any) -> int:
        """Remove members from set"""
        try:
            client = await self.get_client()
            serialized_members = [json.dumps(m, default=str) for m in members]
            return await client.srem(key, *serialized_members)
        except Exception as e:
            print(f"Redis SREM error for key {key}: {e}")
            return 0
    
    # =================== Advanced Operations ===================
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        try:
            client = await self.get_client()
            return await client.keys(pattern)
        except Exception as e:
            print(f"Redis KEYS error for pattern {pattern}: {e}")
            return []
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment key by amount"""
        try:
            client = await self.get_client()
            return await client.incrby(key, amount)
        except Exception as e:
            print(f"Redis INCR error for key {key}: {e}")
            return 0
    
    async def decr(self, key: str, amount: int = 1) -> int:
        """Decrement key by amount"""
        try:
            client = await self.get_client()
            return await client.decrby(key, amount)
        except Exception as e:
            print(f"Redis DECR error for key {key}: {e}")
            return 0
    
    # =================== Cache-Specific Operations ===================
    
    async def cache_set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set cache with default 1 hour TTL"""
        return await self.set(f"cache:{key}", value, ttl)
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get from cache"""
        return await self.get(f"cache:{key}")
    
    async def cache_delete(self, key: str) -> bool:
        """Delete from cache"""
        return await self.delete(f"cache:{key}")
    
    # =================== Session Operations ===================
    
    async def session_create(self, session_id: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Create session with TTL"""
        session_data = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
            **data
        }
        return await self.set(f"session:{session_id}", session_data, ttl)
    
    async def session_get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        return await self.get(f"session:{session_id}")
    
    async def session_update(self, session_id: str, data: Dict[str, Any], extend_ttl: bool = True) -> bool:
        """Update session data"""
        current_data = await self.session_get(session_id)
        if not current_data:
            return False
        
        current_data.update(data)
        current_data["last_activity"] = datetime.now(timezone.utc).isoformat()
        
        ttl = 3600 if extend_ttl else None
        return await self.set(f"session:{session_id}", current_data, ttl)
    
    async def session_delete(self, session_id: str) -> bool:
        """Delete session"""
        return await self.delete(f"session:{session_id}")
    
    # =================== Analytics Operations ===================
    
    async def analytics_increment(self, metric: str, amount: int = 1) -> int:
        """Increment analytics metric"""
        return await self.incr(f"analytics:{metric}", amount)
    
    async def analytics_get(self, metric: str) -> int:
        """Get analytics metric"""
        try:
            value = await self.get(f"analytics:{metric}")
            return int(value) if value else 0
        except (ValueError, TypeError):
            return 0
    
    # =================== Connection Management ===================
    
    async def ping(self) -> bool:
        """Test Redis connection"""
        try:
            client = await self.get_client()
            return await client.ping()
        except Exception as e:
            print(f"Redis PING error: {e}")
            return False
    
    async def info(self) -> Dict[str, str]:
        """Get Redis server info"""
        try:
            client = await self.get_client()
            return await client.info()
        except Exception as e:
            print(f"Redis INFO error: {e}")
            return {}
    
    async def flushdb(self) -> bool:
        """Flush current database (use with caution)"""
        try:
            client = await self.get_client()
            return await client.flushdb()
        except Exception as e:
            print(f"Redis FLUSHDB error: {e}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self._redis_client:
            await self._redis_client.close()

# Singleton instance
_redis_dao_instance = None

def get_redis_dao() -> RedisDAO:
    """Get singleton RedisDAO instance"""
    global _redis_dao_instance
    if _redis_dao_instance is None:
        _redis_dao_instance = RedisDAO()
    return _redis_dao_instance 