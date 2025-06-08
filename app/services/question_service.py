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
            'message': question_data['question'],
            'field': question_data['field'],
            'context': context
        }
    
    async def process_conversational_input(self, user_message: str, profile: UserProfile) -> Dict[str, Any]:
        """Process conversational input from chat UI and extract profile information"""
        
        # Get missing fields to focus on
        missing_fields = self._get_missing_fields(profile)
        
        if not missing_fields:
            return {
                'message': "Your profile is complete! Thanks for chatting with me.",
                'profile_updates': {},
                'extracted_fields': []
            }
        
        # Try to extract information for the first missing field only
        # This makes the conversation more natural and focused
        primary_field = missing_fields[0]
        extracted_value = self._extract_value_from_answer(user_message, primary_field)
        
        profile_updates = {}
        if extracted_value is not None:
            profile_updates[primary_field] = extracted_value
        
        # Generate appropriate response
        if profile_updates:
            field_name = list(profile_updates.keys())[0]
            acknowledgment = f"Great! I've noted your {field_name.replace('_', ' ')}."
            
            # Get next missing field for follow-up question
            remaining_fields = [f for f in missing_fields if f not in profile_updates]
            if remaining_fields:
                next_question = self._generate_simple_question(remaining_fields[0])
                response_message = f"{acknowledgment} {next_question}"
            else:
                response_message = f"{acknowledgment} Your profile is now complete!"
        else:
            # No information extracted, handle appropriately
            if user_message.lower().strip() in ['hi', 'hello', 'hey']:
                # Greeting - respond naturally
                response_message = f"Hello! Nice to meet you. {self._generate_simple_question(primary_field)}"
            elif user_message.lower().strip() in ['ok', 'okay', 'yes']:
                # Acknowledgment - continue with next question
                response_message = self._generate_simple_question(primary_field)
            else:
                # Unclear response - ask for clarification
                response_message = f"I didn't quite catch that. {self._generate_simple_question(primary_field)}"
        
        return {
            'message': response_message,
            'profile_updates': profile_updates,
            'extracted_fields': list(profile_updates.keys())
        }
    
    def _generate_simple_question(self, field: str) -> str:
        """Generate a simple question for a specific field (fallback when LLM is not available)"""
        
        questions = {
            'age': "What's your age?",
            'gender': "How do you identify in terms of gender?",
            'activity_level': "How would you describe your current activity level? (sedentary, moderate, or active)",
            'dietary_preference': "Do you have any dietary preferences? (e.g., vegan, vegetarian, or no preference)",
            'sleep_quality': "How would you rate your sleep quality? (poor, average, or good)",
            'stress_level': "What's your current stress level? (low, medium, or high)",
            'health_goals': "What are your main health and wellness goals?"
        }
        
        return questions.get(field, "Could you tell me more about yourself?")
    
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
        
        # Don't extract from very short or casual responses
        if len(answer.strip()) < 2 or answer_lower in ['hi', 'hello', 'hey', 'ok', 'okay', 'yes', 'no']:
            return None
        
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
            elif any(word in answer_lower for word in ['moderate', 'medium', 'some', 'occasionally']):
                return 'moderate'
            return None
        
        elif field == 'dietary_preference':
            if any(word in answer_lower for word in ['vegan']):
                return 'vegan'
            elif any(word in answer_lower for word in ['vegetarian']):
                return 'vegetarian'
            elif any(word in answer_lower for word in ['no preference', 'omnivore', 'everything', 'anything']):
                return 'no_preference'
            return None
        
        elif field == 'sleep_quality':
            if any(word in answer_lower for word in ['poor', 'bad', 'terrible', 'awful']):
                return 'poor'
            elif any(word in answer_lower for word in ['good', 'great', 'excellent', 'well']):
                return 'good'
            elif any(word in answer_lower for word in ['average', 'okay', 'fair', 'decent']):
                return 'average'
            return None
        
        elif field == 'stress_level':
            if any(word in answer_lower for word in ['high', 'stressed', 'overwhelmed', 'anxious']):
                return 'high'
            elif any(word in answer_lower for word in ['low', 'calm', 'relaxed', 'peaceful']):
                return 'low'
            elif any(word in answer_lower for word in ['medium', 'moderate', 'normal', 'average']):
                return 'medium'
            return None
        
        elif field == 'gender':
            # Only extract if the answer looks like a gender response
            if any(word in answer_lower for word in ['male', 'female', 'man', 'woman', 'non-binary', 'other', 'prefer not to say']):
                return answer.strip()
            return None
        
        elif field == 'health_goals':
            # Only extract if the answer is substantial and looks like health goals
            if len(answer.strip()) >= 3 and any(word in answer_lower for word in ['lose', 'gain', 'weight', 'fitness', 'health', 'muscle', 'exercise', 'diet', 'wellness', 'goal', 'fit', 'strong', 'slim', 'tone', 'build', 'cardio', 'strength']):
                return answer.strip()
            return None
        
        else:
            return None 