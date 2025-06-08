from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List
from enum import Enum

class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    MODERATE = "moderate" 
    ACTIVE = "active"

class DietaryPreference(str, Enum):
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    NO_PREFERENCE = "no_preference"

class SleepQuality(str, Enum):
    POOR = "poor"
    AVERAGE = "average"
    GOOD = "good"

class StressLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class UserProfile(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    
    user_id: str
    age: Optional[int] = Field(None, ge=13, le=120)
    gender: Optional[str] = None
    activity_level: Optional[ActivityLevel] = None
    dietary_preference: Optional[DietaryPreference] = None
    sleep_quality: Optional[SleepQuality] = None
    stress_level: Optional[StressLevel] = None
    health_goals: Optional[str] = None
    completion_percentage: float = Field(0.0, ge=0.0, le=100.0)
    
class QuestionResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    
    question_id: str
    question: str
    answer: str
    field_updated: str 