from app.config.base import BaseConfig, DatabaseConfig
from typing import List

class ProductionConfig(BaseConfig):
    """Production environment configuration"""
    
    # Debug and Logging
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Production CORS (restrictive)
    BACKEND_CORS_ORIGINS: List[str] = [
        "https://healf.app",
        "https://api.healf.app"
    ]
    
    # LLM Configuration for production
    OPENAI_API_KEY: str = ""  # Set your production key here or fetch from cloud provider key vault
    LLM_TIMEOUT: int = 10
    LLM_RETRY_ATTEMPTS: int = 3
    
    # Redis Configuration (same infrastructure as development)
    REDIS_URL: str = "redis://redis:6379"
    REDIS_PASSWORD: str = "your-secure-redis-password"
    
    # MongoDB Configuration (same infrastructure as development)
    MONGODB_URL: str = "mongodb://mongo:27017/healf_production"
    MONGODB_PASSWORD: str = "your-secure-mongo-password"
    USE_IN_MEMORY_DB: bool = False
    
    # Production database settings
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    
    # Docker Configuration for Production
    DOCKER_CONFIG = {
        "api_port": 8000,
        "python_version": "3.11",
        "workers": 4,  # Multiple workers for production
        "memory_limit": "2g",
        "cpu_limit": "2.0",
        "use_redis": True,
        "redis_version": "7",
        "redis_password": "your-secure-redis-password",
        "mongo_version": "7",  # Add MongoDB
        "mongo_password": "your-secure-mongo-password",
        "include_frontend": False
    }

class ProductionDatabaseConfig(DatabaseConfig):
    """Production database configuration"""
    
    def get_connection_string(self) -> str:
        return "mongodb://admin:your-secure-mongo-password@mongo:27017/healf_production" 