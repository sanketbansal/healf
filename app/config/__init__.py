import os
from app.config.development import DevelopmentConfig
from app.config.production import ProductionConfig
from app.config.testing import TestingConfig

def get_config():
    """Factory function to get configuration based on environment"""
    env = os.getenv("ENVIRONMENT", "testing").lower()
    
    config_mapping = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig
    }
    
    config_class = config_mapping.get(env, DevelopmentConfig)
    return config_class()

# Global config instance
settings = get_config()
