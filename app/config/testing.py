from app.config.base import BaseConfig, DatabaseConfig
from typing import List

class TestingConfig(BaseConfig):
    """Testing environment configuration"""
    
    # Debug and Logging
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # CORS (permissive for testing)
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # LLM Configuration (disabled for testing)
    OPENAI_API_KEY: str = ""  # Empty for testing
    LLM_TIMEOUT: int = 5
    
    # Redis Configuration (use fake Redis for testing)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: str = ""
    USE_REDIS: bool = False  # Disable Redis for tests
    
    # MongoDB Configuration (use in-memory for testing)
    MONGODB_URL: str = "mongodb://localhost:27017/healf_test"
    MONGODB_PASSWORD: str = ""
    USE_IN_MEMORY_DB: bool = True  # Use in-memory database for tests
    
    # Testing-specific settings
    TESTING: bool = True
    USE_MOCK_SERVICES: bool = True
    
    # Docker Configuration for Testing
    DOCKER_CONFIG = {
        "api_port": 8000,
        "python_version": "3.11",
        "workers": 1,
        "memory_limit": "256m",
        "cpu_limit": "0.25",
        "use_redis": False,  # Disable Redis for testing
        "redis_version": "7",
        "redis_password": "",
        "mongo_version": "7",
        "mongo_password": "",
        "include_frontend": False
    }

class TestingDatabaseConfig(DatabaseConfig):
    """Testing database configuration"""
    
    def get_connection_string(self) -> str:
        return "sqlite:///:memory:"  # Use in-memory SQLite for testing 