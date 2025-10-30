"""
Application configuration classes.

Provides environment-specific settings and centralizes all hardcoded values.
"""
import os
from typing import List, Optional


class Config:
    """Base configuration class with default values."""
    
    # Flask Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    # File Upload Settings
    UPLOAD_FOLDER = os.path.abspath("./battlescribe")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Supported File Extensions
    SUPPORTED_EXTENSIONS = {'.ros', '.rosz'}
    
    # Wahapedia API Configuration
    WAHAPEDIA_BASE_URL = "https://wahapedia.ru/wh40k10ed/"
    WAHAPEDIA_CSV_FILES = [
        "Datasheets.csv",
        "Datasheets_stratagems.csv", 
        "Detachment_abilities.csv",
        "Factions.csv",
        "Stratagems.csv",
        "Last_update.csv"
    ]
    WAHAPEDIA_DATA_DIR = os.path.abspath("./wahapedia")
    WAHAPEDIA_DATA_PATH = os.path.abspath("./wahapedia")  # Keep for backward compatibility
    WAHAPEDIA_FILE_LIST = "_file_list.json"
    
    # Request Settings
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 5
    RETRY_DELAY = 3
    RATE_LIMIT_DELAY = 5
    WAHAPEDIA_MAX_RETRIES = 5
    WAHAPEDIA_RETRY_DELAY = 3
    WAHAPEDIA_RATE_LIMIT_DELAY = 5
    MIN_FILE_SIZE = 2048  # Minimum file size to avoid rate limit responses
    
    # File Cleanup
    FILE_RETENTION_HOURS = 24
    
    # Application Behavior
    MOBILE_USER_AGENTS = ['mobile', 'android']
    
    @staticmethod
    def init_app(app):
        """Initialize app-specific configuration."""
        # Ensure upload directories exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.WAHAPEDIA_DATA_PATH, exist_ok=True)


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    
    # More verbose logging in development
    REQUEST_TIMEOUT = 60  # Longer timeout for debugging
    

class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    
    # Use environment variables in production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-key-must-be-set'
    
    # Production optimizations
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 15
    

class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    DEBUG = True
    
    # Use temporary directories for testing
    UPLOAD_FOLDER = "/tmp/test_battlescribe"
    WAHAPEDIA_DATA_PATH = "/tmp/test_wahapedia"
    
    # Faster timeouts for tests
    REQUEST_TIMEOUT = 5
    MAX_RETRIES = 1
    FILE_RETENTION_HOURS = 1


# Configuration dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: Optional[str] = None) -> Config:
    """Get configuration class by name or from environment."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config.get(config_name, DevelopmentConfig)