from openai import AsyncOpenAI
from typing import Dict, Any, List, Optional
import json
import asyncio
from datetime import datetime
from app.config import settings

class LLMProvider:
    """Abstract base for LLM providers"""
    async def generate_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        raise NotImplementedError

class OpenAIProvider(LLMProvider):
    """OpenAI API provider implementation"""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
    
    async def generate_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.client:
            raise Exception("OpenAI API key not provided")
        
        try:
            response = await self.client.chat.completions.create(
                model=kwargs.get('model', settings.LLM_MODEL),
                messages=messages,
                temperature=kwargs.get('temperature', settings.LLM_TEMPERATURE),
                max_tokens=kwargs.get('max_tokens', settings.LLM_MAX_TOKENS)
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

class LLMDao:
    """Data Access Object for LLM operations"""
    
    def __init__(self, provider: LLMProvider = None):
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        self.provider = provider or OpenAIProvider(api_key)
        self.request_history: List[Dict[str, Any]] = []
        self.system_prompts = {
            'wellness_coach': self._get_wellness_coach_prompt(),
            'question_generator': self._get_question_generator_prompt(),
            'profile_analyzer': self._get_profile_analyzer_prompt()
        }
    
    async def generate_wellness_question(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a wellness-related question based on context"""
        
        # First try LLM if available
        if hasattr(self.provider, 'client') and self.provider.client:
            messages = [
                {"role": "system", "content": self.system_prompts['wellness_coach']},
                {"role": "user", "content": self._build_question_context(context)}
            ]
            
            try:
                response = await self.provider.generate_completion(messages)
                question_data = self._parse_question_response(response)
                
                # Log the request
                self._log_request('generate_wellness_question', context, question_data)
                
                return question_data
                
            except Exception as e:
                # Fall through to fallback logic
                self._log_request('generate_wellness_question_failed', context, None, error=str(e))
        
        # Use intelligent fallback that progresses through fields
        missing_field = context.get('missing_field')
        if not missing_field:
            # If no specific missing field provided, determine the next logical field
            missing_fields = context.get('missing_fields', [])
            if missing_fields:
                missing_field = missing_fields[0]  # Use first missing field from list
            else:
                # Last resort: use age as it's the most logical starting point
                missing_field = 'age'
        
        fallback = self._get_intelligent_fallback_question(missing_field, context)
        self._log_request('generate_wellness_question_fallback', context, fallback)
        return fallback
    
    def _get_intelligent_fallback_question(self, field: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get intelligent fallback questions that provide better user experience"""
        
        # Enhanced fallback questions with more context
        enhanced_questions = {
            'age': {
                'question': 'To get started, could you tell me your age? This helps us tailor recommendations for your life stage.',
                'field': 'age'
            },
            'gender': {
                'question': 'What gender do you identify as? This helps us provide more personalized wellness advice.',
                'field': 'gender'
            },
            'activity_level': {
                'question': 'How would you describe your current activity level? Are you more sedentary, moderately active, or very active?',
                'field': 'activity_level'
            },
            'dietary_preference': {
                'question': 'Do you follow any specific dietary preferences? For example, are you vegan, vegetarian, or have no specific preference?',
                'field': 'dietary_preference'
            },
            'sleep_quality': {
                'question': 'How would you rate your sleep quality overall? Would you say it\'s poor, average, or good?',
                'field': 'sleep_quality'
            },
            'stress_level': {
                'question': 'What\'s your current stress level like? Would you describe it as low, medium, or high?',
                'field': 'stress_level'
            },
            'health_goals': {
                'question': 'What are your main health and wellness goals? What would you like to achieve or improve?',
                'field': 'health_goals'
            }
        }
        
        return enhanced_questions.get(field, {
            'question': f'Could you tell me about your {field.replace("_", " ")}?',
            'field': field
        })
    
    def _get_wellness_coach_prompt(self) -> str:
        return """You are an experienced wellness coach creating personalized health profiles. 
        Your goal is to ask thoughtful, engaging questions that feel conversational and supportive.
        
        Guidelines:
        - Ask one question at a time
        - Make questions feel personal and relevant
        - Be encouraging and non-judgmental
        - Focus on understanding the person's lifestyle and goals
        - Always return valid JSON with 'question' and 'field' keys
        
        Example response: {"question": "What does your typical day look like in terms of physical activity?", "field": "activity_level"}"""
    
    def _get_question_generator_prompt(self) -> str:
        return """You are a wellness expert generating follow-up questions based on user responses.
        Create questions that dive deeper into their wellness journey.
        
        Always return a JSON array of question objects with 'question' and 'field' keys."""
    
    def _get_profile_analyzer_prompt(self) -> str:
        return """You are analyzing user responses to wellness questions.
        Extract the key information and return structured data.
        
        Return JSON with: 'field' (the profile field being updated), 'value' (extracted value), 'confidence' (0-1 score)"""
    
    def _build_question_context(self, context: Dict[str, Any]) -> str:
        missing_fields = context.get('missing_fields', [])
        current_profile = context.get('profile', {})
        
        context_str = f"Current profile completion: {context.get('completion_percentage', 0)}%\n"
        context_str += f"Missing information: {', '.join(missing_fields)}\n"
        context_str += f"Current profile data: {json.dumps(current_profile, indent=2)}\n"
        context_str += f"Focus on the '{context.get('missing_field', missing_fields[0] if missing_fields else 'general')}' field."
        
        return context_str
    
    def _parse_question_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response for question generation"""
        try:
            # Try to parse as JSON first
            data = json.loads(response)
            if 'question' in data and 'field' in data:
                return data
        except json.JSONDecodeError:
            pass
        
        # Fallback parsing
        return {
            'question': response.strip(),
            'field': 'general'
        }
    
    def _get_fallback_question(self, field: str) -> Dict[str, Any]:
        """Get fallback question when LLM fails - kept for backward compatibility"""
        return self._get_intelligent_fallback_question(field, {})
    
    def _log_request(self, operation: str, input_data: Dict[str, Any], output_data: Any, error: str = None):
        """Log LLM request for monitoring and debugging"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'input': input_data,
            'output': output_data,
            'error': error,
            'success': error is None
        }
        
        self.request_history.append(log_entry)
        
        # Keep only last 100 requests to prevent memory issues
        if len(self.request_history) > 100:
            self.request_history = self.request_history[-100:]

# Singleton instance
_llm_dao_instance = None

def get_llm_dao() -> LLMDao:
    """Get singleton LLMDao instance"""
    global _llm_dao_instance
    if _llm_dao_instance is None:
        _llm_dao_instance = LLMDao()
    return _llm_dao_instance 