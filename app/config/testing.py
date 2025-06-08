from app.config.base import BaseConfig
from typing import List

class TestingConfig(BaseConfig):
    """Testing environment configuration - minimal and fast"""
    
    # Debug and Logging
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # CORS (permissive for testing)
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Disable external services for testing
    OPENAI_API_KEY: str = ""  # Empty - use fallback logic
    
    # Testing mode - automatically disables Redis, MongoDB, and other external services
    TESTING: bool = True 