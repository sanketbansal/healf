import os
from app.config.base import BaseConfig, DatabaseConfig
from typing import List

class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""
    
    # Debug and Logging
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # Development-specific CORS (more permissive)
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:8080",
        "http://127.0.0.1:3000"
    ]
    
    # LLM Configuration for development
    OPENAI_API_KEY: str = ""  # Empty for demo - will use fallback logic
    LLM_TIMEOUT: int = 30
    
    # Redis Configuration (use environment variable if available, otherwise localhost)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_PASSWORD: str = ""  # No password for development
    
    # MongoDB Configuration (use environment variable if available, otherwise localhost)
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017/healf_development")
    MONGODB_PASSWORD: str = ""  # No password for development
    USE_IN_MEMORY_DB: bool = False  # Use real MongoDB
    
    # Docker Configuration for Development
    DOCKER_CONFIG = {
        "api_port": 8000,
        "python_version": "3.11",
        "workers": 1,  # Single worker for dev
        "memory_limit": "512m",
        "cpu_limit": "0.5",
        "use_redis": True,  # Enable Redis
        "redis_version": "7",
        "redis_password": "",
        "mongo_version": "7",  # Add MongoDB
        "mongo_password": "",
        "include_frontend": False
    }

class DevelopmentDatabaseConfig(DatabaseConfig):
    """Development database configuration"""
    
    def get_connection_string(self) -> str:
        return os.getenv("MONGODB_URL", "mongodb://localhost:27017/healf_development") 