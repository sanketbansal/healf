from openai import AsyncOpenAI
import google.generativeai as genai
from typing import Dict, Any, List, Optional
import json
import asyncio
from datetime import datetime
from app.config import settings

class LLMProvider:
    """Abstract base for LLM providers"""
    async def generate_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """Check if the provider is available (has valid credentials)"""
        raise NotImplementedError

class OpenAIProvider(LLMProvider):
    """OpenAI API provider implementation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
    
    def is_available(self) -> bool:
        return bool(self.api_key and self.client)
    
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

class GeminiProvider(LLMProvider):
    """Google Gemini API provider implementation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(
                model_name=getattr(settings, 'GEMINI_MODEL', 'gemini-pro')
            )
        else:
            self.model = None
    
    def is_available(self) -> bool:
        return bool(self.api_key and self.model)
    
    async def generate_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        if not self.model:
            raise Exception("Gemini API key not provided")
        
        try:
            # Convert OpenAI format messages to Gemini format
            prompt = self._convert_messages_to_prompt(messages)
            
            # Configure generation settings
            generation_config = genai.types.GenerationConfig(
                temperature=kwargs.get('temperature', settings.LLM_TEMPERATURE),
                max_output_tokens=kwargs.get('max_tokens', settings.LLM_MAX_TOKENS),
            )
            
            # Generate response
            response = await self.model.generate_content_async(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI-style messages to a single prompt for Gemini"""
        prompt_parts = []
        
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"Instructions: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)

class LLMDao:
    """Data Access Object for LLM operations with multi-provider support"""
    
    def __init__(self, providers: List[LLMProvider] = None):
        if providers:
            self.providers = providers
        else:
            # Initialize providers based on LLM_PROVIDER setting
            self.providers = []
            
            # Get preferred provider from config
            preferred_provider = getattr(settings, 'LLM_PROVIDER', 'openai').lower()
            
            # Initialize all available providers
            available_providers = {}
            
            openai_key = getattr(settings, 'OPENAI_API_KEY', '')
            if openai_key:
                available_providers['openai'] = OpenAIProvider(openai_key)
            
            gemini_key = getattr(settings, 'GEMINI_API_KEY', '')
            if gemini_key:
                available_providers['gemini'] = GeminiProvider(gemini_key)
            
            # Add preferred provider first if available
            if preferred_provider in available_providers:
                self.providers.append(available_providers[preferred_provider])
                # Remove from available to avoid duplicates
                del available_providers[preferred_provider]
            
            # Add remaining providers as fallbacks
            for provider in available_providers.values():
                self.providers.append(provider)
            
            # If no providers available, add empty ones for fallback mode
            if not self.providers:
                if preferred_provider == 'gemini':
                    self.providers = [GeminiProvider(''), OpenAIProvider('')]
                else:
                    self.providers = [OpenAIProvider(''), GeminiProvider('')]
        
        self.request_history: List[Dict[str, Any]] = []
        self.system_prompts = {
            'unified_wellness_assistant': self._get_unified_wellness_prompt()
        }
    
    async def generate_wellness_question(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a wellness-related question using available providers with fallback"""
        
        # Try each available provider
        for i, provider in enumerate(self.providers):
            if not provider.is_available():
                continue
                
            try:
                messages = [
                    {"role": "system", "content": self.system_prompts['unified_wellness_assistant']},
                    {"role": "user", "content": self._build_question_context(context)}
                ]
                
                response = await provider.generate_completion(messages)
                question_data = self._parse_question_response(response)
                
                # Log successful request
                provider_name = provider.__class__.__name__
                self._log_request('generate_wellness_question', context, question_data, 
                                provider=provider_name)
                
                return question_data
                
            except Exception as e:
                provider_name = provider.__class__.__name__
                self._log_request('generate_wellness_question_failed', context, None, 
                                error=str(e), provider=provider_name)
                
                # Continue to next provider or fallback
                continue
        
        # Use intelligent fallback if all providers fail
        missing_field = context.get('missing_field')
        if not missing_field:
            missing_fields = context.get('missing_fields', [])
            if missing_fields:
                missing_field = missing_fields[0]
            else:
                missing_field = 'age'
        
        fallback = self._get_intelligent_fallback_question(missing_field, context)
        self._log_request('generate_wellness_question_fallback', context, fallback)
        return fallback
    
    async def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all configured providers"""
        preferred_provider = getattr(settings, 'LLM_PROVIDER', 'openai').lower()
        
        status = {
            'providers': [],
            'available_count': 0,
            'total_count': len(self.providers),
            'preferred_provider': preferred_provider,
            'primary_provider': None
        }
        
        for i, provider in enumerate(self.providers):
            provider_name = provider.__class__.__name__.replace('Provider', '').lower()
            provider_info = {
                'name': provider.__class__.__name__,
                'type': provider_name,
                'available': provider.is_available(),
                'is_primary': i == 0,  # First provider is primary
                'order': i + 1
            }
            status['providers'].append(provider_info)
            
            if provider_info['available']:
                status['available_count'] += 1
                
            # Set primary provider if this is the first available one
            if provider_info['is_primary'] and provider_info['available']:
                status['primary_provider'] = provider_name
        
        status['fallback_only'] = status['available_count'] == 0
        return status
    
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
    
    def _get_unified_wellness_prompt(self) -> str:
        return """You are an intelligent wellness coach that can handle complete conversations about health and wellness profiling.

CAPABILITIES:
1. Generate personalized wellness questions based on missing profile information
2. Process and understand user responses to extract key information  
3. Decide what to ask next based on conversation flow
4. Maintain context throughout the entire wellness profiling journey
5. Handle greetings, clarifications, and conversational nuances

CONVERSATION STYLE:
- Be warm, encouraging, and non-judgmental
- Ask one focused question at a time
- Make questions feel personal and relevant to their lifestyle
- Acknowledge their responses before moving to the next topic
- Use natural, conversational language
- Adapt your tone based on context (greeting, clarification, follow-up)

RESPONSE FORMAT:
Always return valid JSON with these fields:
{
    "question": "Your next question for the user",
    "field": "profile_field_being_addressed",
    "reasoning": "Brief explanation of why this question is relevant"
}

CONTEXT HANDLING:
- If "is_greeting": true - Start with a warm welcome
- If "just_updated": provided - Acknowledge what was just learned
- If "needs_clarification": true - Gently ask for clarification
- If "unclear_response": provided - Reference their previous response
- If "previous_response": provided - Build on their last answer

PROFILING AREAS TO EXPLORE:
- Demographics: age, gender, location
- Physical Activity: exercise habits, activity level, fitness goals
- Nutrition: dietary preferences, eating patterns, restrictions
- Sleep: quality, duration, schedule consistency
- Stress: current levels, management techniques, stressors
- Health Goals: what they want to achieve or improve
- Lifestyle: work-life balance, social connections, hobbies

GUIDELINES:
- Focus on understanding their current state before asking about goals
- Be curious about their motivation and challenges
- Build on previous responses to create natural conversation flow
- If they mention specific issues, explore them with empathy
- Keep questions open-ended to encourage detailed responses
- For clarifications, be patient and provide examples

EXAMPLE INTERACTIONS:
Greeting Context: {"is_greeting": true, "missing_field": "age"}
Response: {"question": "Welcome! I'm excited to help you build your wellness profile. To get started, could you share your age with me?", "field": "age", "reasoning": "Starting with a basic demographic question after greeting"}

Clarification Context: {"needs_clarification": true, "unclear_response": "maybe", "missing_field": "dietary_preference"}
Response: {"question": "I want to make sure I understand your dietary preferences correctly. Do you follow any specific eating patterns like vegetarian, vegan, or do you eat everything?", "field": "dietary_preference", "reasoning": "Providing clear examples to help clarify dietary preferences"}

Follow-up Context: {"just_updated": "activity_level", "missing_field": "sleep_quality"}
Response: {"question": "That's great to know about your activity level! Now, how would you describe your sleep quality? Do you generally sleep well, or do you struggle with getting good rest?", "field": "sleep_quality", "reasoning": "Transitioning naturally from activity to sleep, acknowledging previous response"}
        
Remember: You're building a comprehensive wellness profile through natural conversation, adapting to each person's communication style and needs."""
    
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
                # Return the full response including reasoning if present
                return {
                    'question': data['question'],
                    'field': data['field'],
                    'reasoning': data.get('reasoning', '')
                }
        except json.JSONDecodeError:
            pass
        
        # Fallback parsing for non-JSON responses
        return {
            'question': response.strip(),
            'field': 'general',
            'reasoning': 'Fallback response - LLM did not return structured JSON'
        }
    
    def _log_request(self, operation: str, input_data: Dict[str, Any], output_data: Any, 
                    error: str = None, provider: str = None):
        """Log LLM request for monitoring and debugging"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'provider': provider,
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