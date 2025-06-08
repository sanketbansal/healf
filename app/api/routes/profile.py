from fastapi import APIRouter, HTTPException, Depends
from app.models.user_profile import UserProfile, QuestionResponse
from app.services.profile_service import ProfileService
from app.dao.profile_dao import ProfileDAO
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])

# Singleton instances for dependencies
_profile_dao = ProfileDAO()
_profile_service = ProfileService(_profile_dao)

# Dependency injection
def get_profile_service():
    return _profile_service

@router.post("/init/{user_id}")
async def initiate_profile(user_id: str, profile_service: ProfileService = Depends(get_profile_service)):
    """Initialize user profiling session"""
    try:
        profile = await profile_service.get_or_create_profile(user_id)
        return {"status": "success", "profile": profile.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}")
async def get_profile(user_id: str, profile_service: ProfileService = Depends(get_profile_service)):
    """Get current user profile"""
    profile = await profile_service.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile.model_dump()

@router.put("/{user_id}")
async def update_profile(user_id: str, updates: Dict[str, Any], profile_service: ProfileService = Depends(get_profile_service)):
    """Update user profile"""
    try:
        profile = await profile_service.update_profile(user_id, updates)
        return {"status": "success", "profile": profile.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}")
async def delete_profile(user_id: str, profile_service: ProfileService = Depends(get_profile_service)):
    """Delete user profile"""
    try:
        success = await profile_service.delete_profile(user_id)
        if success:
            return {"status": "success", "message": "Profile deleted"}
        else:
            raise HTTPException(status_code=404, detail="Profile not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/completion")
async def get_profile_completion(user_id: str, profile_service: ProfileService = Depends(get_profile_service)):
    """Get profile completion status"""
    profile = await profile_service.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    completion_status = profile_service.get_profile_completion_status(profile)
    return completion_status 