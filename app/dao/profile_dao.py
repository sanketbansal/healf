"""
Profile Data Access Object (DAO) using generic Redis and MongoDB DAOs
"""

import os
from typing import Dict, Optional, List
from datetime import datetime, timezone
from app.models.user_profile import UserProfile
from app.config import settings

# For testing, we'll use in-memory storage
if getattr(settings, 'TESTING', False):
    # Simple in-memory storage for testing
    _test_profiles: Dict[str, Dict] = {}
    _test_cache: Dict[str, Dict] = {}

class ProfileDAO:
    """Profile DAO using generic Redis and MongoDB DAOs"""
    
    COLLECTION_NAME = "profiles"
    
    def __init__(self):
        # Check if we're in testing mode
        self.is_testing = getattr(settings, 'TESTING', False)
        
        if not self.is_testing:
            from app.dao.redis_dao import get_redis_dao
            from app.dao.mongo_dao import get_mongo_dao
            self.redis_dao = get_redis_dao()
            self.mongo_dao = get_mongo_dao()
        
    def _get_cache_key(self, user_id: str) -> str:
        """Generate cache key for user profile"""
        return f"profile:{user_id}"
    
    def _calculate_completion(self, profile_data: Dict) -> float:
        """Calculate profile completion percentage"""
        total_fields = 7  # age, gender, activity_level, dietary_preference, sleep_quality, stress_level, health_goals
        completed_fields = 0
        
        profile_fields = ['age', 'gender', 'activity_level', 'dietary_preference', 'sleep_quality', 'stress_level', 'health_goals']
        
        for field in profile_fields:
            if profile_data.get(field) is not None:
                completed_fields += 1
        
        return (completed_fields / total_fields) * 100.0
    
    async def create_profile(self, user_id: str) -> UserProfile:
        """Create a new user profile"""
        profile = UserProfile(user_id=user_id)
        profile_data = profile.model_dump()
        
        if self.is_testing:
            # Use in-memory storage for testing
            global _test_profiles, _test_cache
            profile_data['created_at'] = datetime.now(timezone.utc)
            profile_data['updated_at'] = datetime.now(timezone.utc)
            _test_profiles[user_id] = profile_data
            _test_cache[self._get_cache_key(user_id)] = profile_data
        else:
            # Save to MongoDB using generic DAO
            document_id = await self.mongo_dao.insert_one(self.COLLECTION_NAME, profile_data)
            
            if document_id:
                # Cache in Redis using generic DAO
                await self.redis_dao.cache_set(
                    self._get_cache_key(user_id), 
                    profile_data, 
                    ttl=3600  # 1 hour TTL
                )
        
        return profile
    
    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile from cache first, then MongoDB"""
        if self.is_testing:
            # Use in-memory storage for testing
            global _test_profiles, _test_cache
            cache_key = self._get_cache_key(user_id)
            
            # Try cache first
            if cache_key in _test_cache:
                try:
                    return UserProfile(**_test_cache[cache_key])
                except Exception as e:
                    print(f"Error creating profile from cache for {user_id}: {e}")
            
            # Fallback to profiles storage
            if user_id in _test_profiles:
                profile_data = _test_profiles[user_id]
                try:
                    profile = UserProfile(**profile_data)
                    _test_cache[cache_key] = profile_data
                    return profile
                except Exception as e:
                    print(f"Error creating profile from storage for {user_id}: {e}")
            
            return None
        
        else:
            cache_key = self._get_cache_key(user_id)
            
            # Try cache first using generic Redis DAO
            cached_data = await self.redis_dao.cache_get(cache_key)
            if cached_data:
                try:
                    return UserProfile(**cached_data)
                except Exception as e:
                    print(f"Error creating profile from cache for {user_id}: {e}")
            
            # Fallback to MongoDB using generic DAO
            profile_data = await self.mongo_dao.find_one(
                self.COLLECTION_NAME, 
                {"user_id": user_id}
            )
            
            if profile_data:
                # Remove MongoDB _id field
                profile_data.pop('_id', None)
                
                try:
                    profile = UserProfile(**profile_data)
                    
                    # Update cache using generic Redis DAO
                    await self.redis_dao.cache_set(cache_key, profile_data, ttl=3600)
                    
                    return profile
                except Exception as e:
                    print(f"Error creating profile from MongoDB data for {user_id}: {e}")
            
            return None
    
    async def update_profile(self, user_id: str, profile_data: Dict) -> Optional[UserProfile]:
        """Update user profile in both MongoDB and cache"""
        # Get current profile
        current_profile = await self.get_profile(user_id)
        if not current_profile:
            return None
        
        # Update profile data
        updated_data = current_profile.model_dump()
        updated_data.update(profile_data)
        
        # Recalculate completion percentage
        updated_data['completion_percentage'] = self._calculate_completion(updated_data)
        
        try:
            profile = UserProfile(**updated_data)
            
            if self.is_testing:
                # Use in-memory storage for testing
                global _test_profiles, _test_cache
                updated_data['updated_at'] = datetime.now(timezone.utc)
                _test_profiles[user_id] = updated_data
                _test_cache[self._get_cache_key(user_id)] = updated_data
                return profile
            else:
                # Update MongoDB using generic DAO
                success = await self.mongo_dao.update_one(
                    self.COLLECTION_NAME,
                    {"user_id": user_id},
                    updated_data
                )
                
                if success:
                    # Update cache using generic Redis DAO
                    cache_key = self._get_cache_key(user_id)
                    await self.redis_dao.cache_set(cache_key, updated_data, ttl=3600)
                    
                    return profile
            
        except Exception as e:
            print(f"Error updating profile for {user_id}: {e}")
        
        return None
    
    async def delete_profile(self, user_id: str) -> bool:
        """Delete user profile from both MongoDB and cache"""
        if self.is_testing:
            # Use in-memory storage for testing
            global _test_profiles, _test_cache
            cache_key = self._get_cache_key(user_id)
            
            deleted = False
            if user_id in _test_profiles:
                del _test_profiles[user_id]
                deleted = True
            if cache_key in _test_cache:
                del _test_cache[cache_key]
                
            return deleted
        else:
            # Delete from MongoDB using generic DAO
            mongo_deleted = await self.mongo_dao.delete_one(
                self.COLLECTION_NAME,
                {"user_id": user_id}
            )
            
            # Delete from cache using generic Redis DAO
            cache_key = self._get_cache_key(user_id)
            cache_deleted = await self.redis_dao.cache_delete(cache_key)
            
            return mongo_deleted
    
    async def get_all_profiles(self) -> List[UserProfile]:
        """Get all profiles (for admin/analytics)"""
        if self.is_testing:
            # Use in-memory storage for testing
            global _test_profiles
            profiles = []
            for profile_data in _test_profiles.values():
                try:
                    profiles.append(UserProfile(**profile_data))
                except Exception as e:
                    print(f"Error creating profile from data: {e}")
            return profiles
        else:
            profiles_data = await self.mongo_dao.find_many(self.COLLECTION_NAME)
            
            profiles = []
            for profile_data in profiles_data:
                profile_data.pop('_id', None)
                try:
                    profiles.append(UserProfile(**profile_data))
                except Exception as e:
                    print(f"Error creating profile from data: {e}")
            
            return profiles
    
    async def get_profiles_by_completion(self, min_completion: float = 100.0) -> List[UserProfile]:
        """Get profiles by completion percentage"""
        if self.is_testing:
            # Use in-memory storage for testing
            global _test_profiles
            profiles = []
            for profile_data in _test_profiles.values():
                if profile_data.get('completion_percentage', 0) >= min_completion:
                    try:
                        profiles.append(UserProfile(**profile_data))
                    except Exception as e:
                        print(f"Error creating profile from data: {e}")
            return profiles
        else:
            profiles_data = await self.mongo_dao.find_many(
                self.COLLECTION_NAME,
                {"completion_percentage": {"$gte": min_completion}}
            )
            
            profiles = []
            for profile_data in profiles_data:
                profile_data.pop('_id', None)
                try:
                    profiles.append(UserProfile(**profile_data))
                except Exception as e:
                    print(f"Error creating profile from data: {e}")
            
            return profiles
    
    async def get_profiles_by_field(self, field: str, value: str) -> List[UserProfile]:
        """Get profiles by specific field value"""
        profiles_data = await self.mongo_dao.find_many(
            self.COLLECTION_NAME,
            {field: value}
        )
        
        profiles = []
        for profile_data in profiles_data:
            profile_data.pop('_id', None)
            try:
                profiles.append(UserProfile(**profile_data))
            except Exception as e:
                print(f"Error creating profile from data: {e}")
        
        return profiles
    
    async def get_profile_statistics(self) -> Dict[str, int]:
        """Get profile statistics using MongoDB aggregation"""
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_profiles": {"$sum": 1},
                    "completed_profiles": {
                        "$sum": {"$cond": [{"$eq": ["$completion_percentage", 100]}, 1, 0]}
                    },
                    "avg_completion": {"$avg": "$completion_percentage"}
                }
            }
        ]
        
        results = await self.mongo_dao.aggregate(self.COLLECTION_NAME, pipeline)
        
        if results:
            stats = results[0]
            return {
                "total_profiles": stats.get("total_profiles", 0),
                "completed_profiles": stats.get("completed_profiles", 0),
                "incomplete_profiles": stats.get("total_profiles", 0) - stats.get("completed_profiles", 0),
                "average_completion": round(stats.get("avg_completion", 0), 2)
            }
        
        return {
            "total_profiles": 0,
            "completed_profiles": 0,
            "incomplete_profiles": 0,
            "average_completion": 0
        }
    
    async def cache_profile_analytics(self, analytics_data: Dict) -> bool:
        """Cache profile analytics data"""
        return await self.redis_dao.cache_set("profile_analytics", analytics_data, ttl=1800)  # 30 minutes
    
    async def get_cached_analytics(self) -> Optional[Dict]:
        """Get cached profile analytics data"""
        return await self.redis_dao.cache_get("profile_analytics")
    
    async def create_indexes(self) -> bool:
        """Create MongoDB indexes for better performance"""
        indexes_created = []
        
        # Create index on user_id (should be unique)
        indexes_created.append(
            await self.mongo_dao.create_index(self.COLLECTION_NAME, "user_id", unique=True)
        )
        
        # Create index on completion_percentage for filtering
        indexes_created.append(
            await self.mongo_dao.create_index(self.COLLECTION_NAME, "completion_percentage")
        )
        
        # Create compound index on common query fields
        indexes_created.append(
            await self.mongo_dao.create_index(
                self.COLLECTION_NAME, 
                [("gender", 1), ("age", 1), ("activity_level", 1)]
            )
        )
        
        return all(indexes_created)
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of Redis and MongoDB connections"""
        if self.is_testing:
            return {"redis": True, "mongodb": True}
        else:
            return {
                "redis": await self.redis_dao.ping(),
                "mongodb": await self.mongo_dao.ping()
            }
    
    async def close_connections(self):
        """Close database and cache connections"""
        if not self.is_testing:
            await self.redis_dao.close()
            await self.mongo_dao.close()

# Singleton instance
_profile_dao_instance = None

def get_profile_dao() -> ProfileDAO:
    """Get singleton ProfileDAO instance"""
    global _profile_dao_instance
    if _profile_dao_instance is None:
        _profile_dao_instance = ProfileDAO()
    return _profile_dao_instance 