from typing import List, Optional
from abc import ABC, abstractmethod

class BaseConfig(ABC):
    """Base configuration class with common settings"""
    
    # Project Configuration
    PROJECT_NAME: str = "Healf Wellness Profiling Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # LLM Configuration
    LLM_MODEL: str = "gpt-4"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 150
    MAX_QUESTIONS: int = 5
    
    # WebSocket Configuration
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30
    MAX_CONNECTIONS_PER_USER: int = 1
    
    # Validation Rules
    MIN_AGE: int = 13
    MAX_AGE: int = 120

class DatabaseConfig(ABC):
    """Abstract database configuration"""
    
    @abstractmethod
    def get_connection_string(self) -> str:
        pass 