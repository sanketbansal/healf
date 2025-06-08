"""
Pytest configuration and fixtures for testing
"""

import pytest
import asyncio
import os
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.user_profile import UserProfile
from datetime import datetime, timezone

# Set testing environment before any imports
os.environ["ENVIRONMENT"] = "testing"

class MockRedisDAO:
    """Mock Redis DAO for testing"""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._sessions: Dict[str, Dict[str, Any]] = {}
    
    async def get_client(self):
        return self
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        self._data[key] = value
        return True
    
    async def get(self, key: str) -> Optional[Any]:
        return self._data.get(key)
    
    async def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False
    
    async def cache_set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        return await self.set(f"cache:{key}", value, ttl)
    
    async def cache_get(self, key: str) -> Optional[Any]:
        return await self.get(f"cache:{key}")
    
    async def cache_delete(self, key: str) -> bool:
        return await self.delete(f"cache:{key}")
    
    async def session_create(self, session_id: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        session_data = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
            **data
        }
        self._sessions[session_id] = session_data
        return True
    
    async def session_get(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._sessions.get(session_id)
    
    async def session_update(self, session_id: str, data: Dict[str, Any], extend_ttl: bool = True) -> bool:
        if session_id in self._sessions:
            self._sessions[session_id].update(data)
            self._sessions[session_id]["last_activity"] = datetime.now(timezone.utc).isoformat()
            return True
        return False
    
    async def session_delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    async def ping(self) -> bool:
        return True
    
    async def close(self):
        pass

class MockMongoDAO:
    """Mock MongoDB DAO for testing"""
    
    def __init__(self):
        self._collections: Dict[str, List[Dict[str, Any]]] = {}
    
    async def get_client(self):
        return self
    
    async def get_database(self):
        return self
    
    async def get_collection(self, collection_name: str):
        return self
    
    async def insert_one(self, collection_name: str, document: Dict[str, Any]) -> Optional[str]:
        if collection_name not in self._collections:
            self._collections[collection_name] = []
        
        document['_id'] = f"test_id_{len(self._collections[collection_name])}"
        document['created_at'] = datetime.now(timezone.utc)
        document['updated_at'] = datetime.now(timezone.utc)
        
        self._collections[collection_name].append(document.copy())
        return document['_id']
    
    async def find_one(self, collection_name: str, filter_dict: Dict[str, Any], 
                      projection: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if collection_name not in self._collections:
            return None
        
        for doc in self._collections[collection_name]:
            match = True
            for key, value in filter_dict.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                return doc.copy()
        return None
    
    async def find_many(self, collection_name: str, filter_dict: Dict[str, Any] = None,
                       projection: Optional[Dict[str, Any]] = None, 
                       sort: Optional[List[tuple]] = None,
                       limit: Optional[int] = None, 
                       skip: Optional[int] = None) -> List[Dict[str, Any]]:
        if collection_name not in self._collections:
            return []
        
        results = []
        for doc in self._collections[collection_name]:
            if filter_dict is None:
                results.append(doc.copy())
            else:
                match = True
                for key, value in filter_dict.items():
                    if doc.get(key) != value:
                        match = False
                        break
                if match:
                    results.append(doc.copy())
        
        return results
    
    async def update_one(self, collection_name: str, filter_dict: Dict[str, Any], 
                        update_dict: Dict[str, Any], upsert: bool = False) -> bool:
        if collection_name not in self._collections:
            self._collections[collection_name] = []
        
        # Handle $set operation
        if '$set' in update_dict:
            update_data = update_dict['$set']
        else:
            update_data = update_dict
        
        for doc in self._collections[collection_name]:
            match = True
            for key, value in filter_dict.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                doc.update(update_data)
                doc['updated_at'] = datetime.now(timezone.utc)
                return True
        
        return False
    
    async def delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> bool:
        if collection_name not in self._collections:
            return False
        
        for i, doc in enumerate(self._collections[collection_name]):
            match = True
            for key, value in filter_dict.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                del self._collections[collection_name][i]
                return True
        
        return False
    
    async def ping(self) -> bool:
        return True
    
    async def close(self):
        pass

@pytest.fixture
def mock_redis_dao():
    """Fixture providing mock Redis DAO"""
    return MockRedisDAO()

@pytest.fixture
def mock_mongo_dao():
    """Fixture providing mock MongoDB DAO"""
    return MockMongoDAO()

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically setup test environment"""
    # Clear test data before each test
    try:
        from app.dao.profile_dao import _test_profiles, _test_cache
        _test_profiles.clear()
        _test_cache.clear()
    except ImportError:
        # Test data not available yet, that's fine
        pass
    
    yield
    
    # Clean up after test
    try:
        from app.dao.profile_dao import _test_profiles, _test_cache
        _test_profiles.clear() 
        _test_cache.clear()
    except ImportError:
        pass 