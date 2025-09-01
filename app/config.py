"""
Configuration management for the Voice Transcriber application
"""

import os
from pathlib import Path

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'voice-transcriber-secret-key-2024'
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024))  # 500MB
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a', 'flac', 'ogg', 'wma', 'aac', 'mp4'}
    
    # Transcription Configuration
    MAX_CONCURRENT_JOBS = int(os.environ.get('MAX_CONCURRENT_JOBS', 5))
    JOB_CLEANUP_HOURS = int(os.environ.get('JOB_CLEANUP_HOURS', 1))
    FILE_CLEANUP_HOURS = int(os.environ.get('FILE_CLEANUP_HOURS', 24))
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/web_app.log')
    
    # Server Configuration
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5001))
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    SRC_DIR = BASE_DIR / 'src'
    TRANSCRIPTIONS_DIR = BASE_DIR / 'transcriptions'
    LOGS_DIR = BASE_DIR / 'logs'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    UPLOAD_FOLDER = 'test_uploads'
    MAX_CONCURRENT_JOBS = 1

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
