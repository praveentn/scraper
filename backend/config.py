# backend/config.py
import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///scraper.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_timeout': 20,
        'pool_recycle': -1,
        'pool_pre_ping': True
    }
    
    # Server configuration with new default ports
    FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.environ.get('FLASK_PORT', 5232))
    REACT_PORT = int(os.environ.get('REACT_PORT', 3232))
    
    # JWT Configuration - Fixed to use consistent secret key
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'
    
    # File upload configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json', 'txt', 'pdf'}
    
    # CORS Configuration with new ports
    CORS_ORIGINS = [
        f"http://localhost:{os.environ.get('REACT_PORT', 3232)}",
        f"http://127.0.0.1:{os.environ.get('REACT_PORT', 3232)}",
        "http://localhost:3232",
        "http://127.0.0.1:3232",
        "http://localhost:3000",  # Default React port fallback
        "http://127.0.0.1:3000"   # Default React port fallback
    ]
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT', 'https://prave-mcngte2t-eastus2.cognitiveservices.azure.com/openai/deployments/gpt-4.1-nano/chat/completions?api-version=2025-01-01-preview')
    AZURE_OPENAI_API_KEY = os.environ.get('AZURE_OPENAI_API_KEY', 'openai-key-placeholder')
    AZURE_OPENAI_API_VERSION = os.environ.get('AZURE_OPENAI_API_VERSION', '2025-01-01-preview')
    AZURE_OPENAI_DEPLOYMENT = os.environ.get('AZURE_OPENAI_DEPLOYMENT', 'gpt-4.1-nano')
    AZURE_OPENAI_MODEL = os.environ.get('AZURE_OPENAI_MODEL', 'gpt-4.1-nano')
    AZURE_OPENAI_MAX_TOKENS = int(os.environ.get('AZURE_OPENAI_MAX_TOKENS', 4000))
    AZURE_OPENAI_TEMPERATURE = float(os.environ.get('AZURE_OPENAI_TEMPERATURE', 0.7))
    
    # Rate Limiting Configuration
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    RATELIMIT_DEFAULT = "1000 per hour"
    RATELIMIT_HEADERS_ENABLED = True
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'true').lower() == 'true'
    
    # Security Configuration
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_ENABLED = False  # Disable CSRF for API
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Application Configuration
    APP_NAME = 'Blitz'
    APP_VERSION = '1.0.0'
    DEBUG = False
    TESTING = False
    
    # Database Configuration
    SQLALCHEMY_ECHO = False
    
    # Scraping Configuration
    SCRAPING_CONFIG = {
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'request_timeout': 30,
        'max_retries': 3,
        'request_delay': 1.0,
        'max_concurrent_requests': 10,
        'allowed_domains': []
    }
    
    # Search Configuration
    SEARCH_CONFIG = {
        'use_selenium': True,
        'selenium_headless': True,
        'search_timeout': 30,
        'bing_api_key': os.environ.get('BING_API_KEY'),
        'google_api_key': os.environ.get('GOOGLE_API_KEY'),
        'google_cse_id': os.environ.get('GOOGLE_CSE_ID'),
        'serpapi_key': os.environ.get('SERPAPI_KEY')
    }
    
    # Cache Configuration
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False
    LOG_LEVEL = 'DEBUG'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = False  # Keep disabled for API
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    LOG_LEVEL = 'INFO'
    LOG_TO_STDOUT = True
    RATELIMIT_DEFAULT = "500 per hour"


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


def get_config():
    """Get configuration class based on environment"""
    env = os.environ.get('FLASK_ENV', 'development').lower()
    
    if env == 'production':
        return ProductionConfig
    elif env == 'testing':
        return TestingConfig
    else:
        return DevelopmentConfig


def validate_azure_openai_config(config):
    """Validate Azure OpenAI configuration"""
    required_fields = ['AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_API_KEY']
    missing_fields = []
    
    for field in required_fields:
        value = getattr(config, field, None)
        if not value or value.endswith('placeholder'):
            missing_fields.append(field)
    
    return {
        'valid': len(missing_fields) == 0,
        'missing_fields': missing_fields
    }


def init_directories():
    """Initialize required directories"""
    directories = [
        'uploads',
        'logs',
        'exports',
        'temp'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


if __name__ == '__main__':
    config = get_config()()
    validation = validate_azure_openai_config(config)
    
    print(f"Configuration: {config.__class__.__name__}")
    print(f"Flask Port: {config.FLASK_PORT}")
    print(f"React Port: {config.REACT_PORT}")
    
    if validation['valid']:
        print("✅ Azure OpenAI configuration is valid")
    else:
        print(f"⚠️  Missing Azure OpenAI fields: {validation['missing_fields']}")
    
    init_directories()
    print("✅ Required directories created")