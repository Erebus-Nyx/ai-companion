# production_config.py
# Production configuration for AI Companion deployment

import os
from typing import Dict, Any

class ProductionConfig:
    """Production configuration for AI Companion"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
    DEBUG = False
    TESTING = False
    
    # Server Configuration
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 19443))
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///ai_companion.db')
    
    # AI Model Configuration
    LLM_MODEL_PATH = os.environ.get('LLM_MODEL_PATH', 'models/llm/')
    TTS_MODEL_PATH = os.environ.get('TTS_MODEL_PATH', 'models/tts/')
    LIVE2D_MODELS_PATH = os.environ.get('LIVE2D_MODELS_PATH', 'models/live2d/')
    
    # Live2D Specific Configuration
    LIVE2D_CACHE_SIZE = int(os.environ.get('LIVE2D_CACHE_SIZE', 5))
    LIVE2D_MAX_MODELS = int(os.environ.get('LIVE2D_MAX_MODELS', 10))
    
    # Audio Configuration
    AUDIO_SAMPLE_RATE = int(os.environ.get('AUDIO_SAMPLE_RATE', 16000))
    AUDIO_CHUNK_SIZE = int(os.environ.get('AUDIO_CHUNK_SIZE', 1024))
    VAD_ENABLED = os.environ.get('VAD_ENABLED', 'true').lower() == 'true'
    TTS_ENABLED = os.environ.get('TTS_ENABLED', 'true').lower() == 'true'
    
    # LLM Configuration
    LLM_MAX_TOKENS = int(os.environ.get('LLM_MAX_TOKENS', 2048))
    LLM_TEMPERATURE = float(os.environ.get('LLM_TEMPERATURE', 0.7))
    
    # Security Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Performance Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    SOCKETIO_ASYNC_MODE = 'threading'
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'ai_companion.log')
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            'SECRET_KEY': cls.SECRET_KEY,
            'DEBUG': cls.DEBUG,
            'TESTING': cls.TESTING,
            'HOST': cls.HOST,
            'PORT': cls.PORT,
            'DATABASE_URL': cls.DATABASE_URL,
            'LLM_MODEL_PATH': cls.LLM_MODEL_PATH,
            'TTS_MODEL_PATH': cls.TTS_MODEL_PATH,
            'LIVE2D_MODELS_PATH': cls.LIVE2D_MODELS_PATH,
            'CORS_ORIGINS': cls.CORS_ORIGINS,
            'MAX_CONTENT_LENGTH': cls.MAX_CONTENT_LENGTH,
            'SOCKETIO_ASYNC_MODE': cls.SOCKETIO_ASYNC_MODE,
            'LOG_LEVEL': cls.LOG_LEVEL,
            'LOG_FILE': cls.LOG_FILE,
        }


class DevelopmentConfig(ProductionConfig):
    """Development configuration"""
    DEBUG = True
    HOST = '127.0.0.1'
    LOG_LEVEL = 'DEBUG'


class CloudflareConfig(ProductionConfig):
    """Configuration optimized for Cloudflare deployment"""
    # Cloudflare typically expects apps on standard ports
    PORT = int(os.environ.get('PORT', 8080))
    
    # Trust Cloudflare proxy headers
    PROXY_FIX = True
    
    # Cloudflare-specific CORS settings
    CORS_ORIGINS = [
        'https://*.your-domain.com',
        'https://your-domain.com'
    ]


def get_config(environment: str = 'production') -> ProductionConfig:
    """Get configuration based on environment"""
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'cloudflare': CloudflareConfig,
    }
    
    config_class = configs.get(environment, ProductionConfig)
    return config_class()


def create_env_file_template():
    """Create a template .env file for production"""
    template = """# AI Companion Production Environment Configuration
# Copy this file to .env and update the values

# Server Configuration
HOST=0.0.0.0
PORT=19443

# Security (CHANGE THESE!)
SECRET_KEY=your-super-secret-key-change-this-immediately

# Database
DATABASE_URL=sqlite:///ai_companion_production.db

# Model Paths
LLM_MODEL_PATH=models/llm/
TTS_MODEL_PATH=models/tts/
LIVE2D_MODELS_PATH=models/live2d/

# CORS Origins (comma-separated)
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=ai_companion.log

# Optional: For Cloudflare deployment
# PORT=8080
# HOST=0.0.0.0
"""
    
    with open('.env.template', 'w') as f:
        f.write(template)
    
    print("📄 Created .env.template file")
    print("📝 Copy to .env and update values for production")


if __name__ == '__main__':
    # Create environment template
    create_env_file_template()
    
    # Print configuration examples
    print("\n🔧 Configuration Examples:")
    print("=" * 40)
    
    print("\n📦 Development:")
    dev_config = get_config('development')
    print(f"Host: {dev_config.HOST}:{dev_config.PORT}")
    print(f"Debug: {dev_config.DEBUG}")
    
    print("\n🚀 Production:")
    prod_config = get_config('production')
    print(f"Host: {prod_config.HOST}:{prod_config.PORT}")
    print(f"Debug: {prod_config.DEBUG}")
    
    print("\n☁️  Cloudflare:")
    cf_config = get_config('cloudflare')
    print(f"Host: {cf_config.HOST}:{cf_config.PORT}")
    print(f"CORS: {cf_config.CORS_ORIGINS}")
