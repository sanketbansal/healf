from app.dao.profile_dao import ProfileDAO
from app.models.user_profile import UserProfile
from typing import Optional, Dict, Any

class ProfileService:
    """Business logic for profile management"""
    
    def __init__(self, profile_dao: ProfileDAO):
        self.profile_dao = profile_dao
    
    async def get_or_create_profile(self, user_id: str) -> UserProfile:
        """Get existing profile or create new one"""
        profile = await self.profile_dao.get_profile(user_id)
        if not profile:
            profile = await self.profile_dao.create_profile(user_id)
        return profile
    
    async def update_profile(self, user_id: str, updates: Dict[str, Any]) -> UserProfile:
        """Update user profile with validation"""
        # Validate updates before applying
        validated_updates = self._validate_updates(updates)
        
        profile = await self.profile_dao.update_profile(user_id, validated_updates)
        if not profile:
            # Profile doesn't exist, create it first
            profile = await self.profile_dao.create_profile(user_id)
            profile = await self.profile_dao.update_profile(user_id, validated_updates)
        
        return profile
    
    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile"""
        return await self.profile_dao.get_profile(user_id)
    
    async def delete_profile(self, user_id: str) -> bool:
        """Delete user profile"""
        return await self.profile_dao.delete_profile(user_id)
    
    def get_profile_completion_status(self, profile: UserProfile) -> Dict[str, Any]:
        """Get detailed completion status"""
        missing_fields = []
        completed_fields = []
        
        field_mapping = {
            'age': profile.age,
            'gender': profile.gender,
            'activity_level': profile.activity_level,
            'dietary_preference': profile.dietary_preference,
            'sleep_quality': profile.sleep_quality,
            'stress_level': profile.stress_level,
            'health_goals': profile.health_goals
        }
        
        for field, value in field_mapping.items():
            if value is None:
                missing_fields.append(field)
            else:
                completed_fields.append(field)
        
        return {
            'completion_percentage': profile.completion_percentage,
            'missing_fields': missing_fields,
            'completed_fields': completed_fields,
            'is_complete': len(missing_fields) == 0
        }
    
    def _validate_updates(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Validate profile updates"""
        validated = {}
        
        for field, value in updates.items():
            if field == 'age':
                if isinstance(value, (int, str)):
                    try:
                        age_val = int(value)
                        if 13 <= age_val <= 120:
                            validated[field] = age_val
                    except (ValueError, TypeError):
                        pass
            
            elif field == 'activity_level':
                if value in ['sedentary', 'moderate', 'active']:
                    validated[field] = value
            
            elif field == 'dietary_preference':
                if value in ['vegan', 'vegetarian', 'no_preference']:
                    validated[field] = value
            
            elif field == 'sleep_quality':
                if value in ['poor', 'average', 'good']:
                    validated[field] = value
            
            elif field == 'stress_level':
                if value in ['low', 'medium', 'high']:
                    validated[field] = value
            
            elif field in ['gender', 'health_goals']:
                if isinstance(value, str) and value.strip():
                    validated[field] = value.strip()
        
        return validated 