from app.dao.llm_dao import LLMDao
from app.models.user_profile import UserProfile
from typing import Dict, Any, List

class QuestionService:
    """Business logic for question generation and processing"""
    
    def __init__(self, llm_dao: LLMDao):
        self.llm_dao = llm_dao
        self.max_questions_per_session = 5
    
    async def generate_next_question(self, profile: UserProfile) -> Dict[str, Any]:
        """Generate the next question based on current profile state"""
        
        # Check if profile is complete
        if profile.completion_percentage >= 100:
            return {
                'type': 'completion',
                'message': 'Congratulations! Your wellness profile is complete. You\'re ready to start your personalized wellness journey!',
                'profile': profile.model_dump()
            }
        
        # Determine missing fields
        missing_fields = self._get_missing_fields(profile)
        if not missing_fields:
            return {
                'type': 'completion',
                'message': 'Your profile is complete!',
                'profile': profile.model_dump()
            }
        
        # Build context for question generation
        context = {
            'profile': profile.model_dump(),
            'missing_fields': missing_fields,
            'missing_field': missing_fields[0],  # Focus on first missing field
            'completion_percentage': profile.completion_percentage
        }
        
        # Generate question using LLM DAO
        question_data = await self.llm_dao.generate_wellness_question(context)
        
        return {
            'type': 'question',
            'question': question_data['question'],
            'field': question_data['field'],
            'context': context
        }
    
    def process_user_answer(self, user_answer: str, question_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process user answer and extract structured data"""
        
        field = question_context.get('field', 'general')
        
        # Simple rule-based processing for now
        # In a more advanced version, this could use the LLM for analysis
        processed_value = self._extract_value_from_answer(user_answer, field)
        
        return {
            'field': field,
            'value': processed_value,
            'confidence': 1.0,
            'raw_answer': user_answer
        }
    
    def _get_missing_fields(self, profile: UserProfile) -> List[str]:
        """Identify missing profile fields"""
        missing = []
        
        if profile.age is None:
            missing.append("age")
        if profile.gender is None:
            missing.append("gender") 
        if profile.activity_level is None:
            missing.append("activity_level")
        if profile.dietary_preference is None:
            missing.append("dietary_preference")
        if profile.sleep_quality is None:
            missing.append("sleep_quality")
        if profile.stress_level is None:
            missing.append("stress_level")
        if profile.health_goals is None:
            missing.append("health_goals")
            
        return missing
    
    def _extract_value_from_answer(self, answer: str, field: str) -> Any:
        """Extract structured value from user answer based on field type"""
        answer_lower = answer.lower().strip()
        
        if field == 'age':
            # Extract age from answer
            import re
            age_match = re.search(r'\b(\d{1,3})\b', answer)
            if age_match:
                age = int(age_match.group(1))
                if 13 <= age <= 120:
                    return age
            return None
        
        elif field == 'activity_level':
            if any(word in answer_lower for word in ['sedentary', 'sit', 'desk', 'inactive', 'low']):
                return 'sedentary'
            elif any(word in answer_lower for word in ['active', 'exercise', 'gym', 'sport', 'run', 'high']):
                return 'active'
            else:
                return 'moderate'
        
        elif field == 'dietary_preference':
            if any(word in answer_lower for word in ['vegan']):
                return 'vegan'
            elif any(word in answer_lower for word in ['vegetarian']):
                return 'vegetarian'
            else:
                return 'no_preference'
        
        elif field == 'sleep_quality':
            if any(word in answer_lower for word in ['poor', 'bad', 'terrible', 'awful']):
                return 'poor'
            elif any(word in answer_lower for word in ['good', 'great', 'excellent', 'well']):
                return 'good'
            else:
                return 'average'
        
        elif field == 'stress_level':
            if any(word in answer_lower for word in ['high', 'stressed', 'overwhelmed', 'anxious']):
                return 'high'
            elif any(word in answer_lower for word in ['low', 'calm', 'relaxed', 'peaceful']):
                return 'low'
            else:
                return 'medium'
        
        elif field == 'gender':
            return answer.strip()
        
        elif field == 'health_goals':
            return answer.strip()
        
        else:
            return answer.strip() 