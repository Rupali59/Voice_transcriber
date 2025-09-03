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
    
    # Model Cache Configuration
    WHISPER_MODEL_CACHE_SIZE = int(os.environ.get('WHISPER_MODEL_CACHE_SIZE', 3))
    MODEL_IDLE_TIMEOUT = int(os.environ.get('MODEL_IDLE_TIMEOUT', 1800))  # 30 minutes
    MODEL_CLEANUP_INTERVAL = int(os.environ.get('MODEL_CLEANUP_INTERVAL', 300))  # 5 minutes
    ENABLE_GPU_ACCELERATION = os.environ.get('ENABLE_GPU_ACCELERATION', 'true').lower() == 'true'
    PRELOAD_MODELS = os.environ.get('PRELOAD_MODELS', 'base,small').split(',')
    
    # IP-based DoS Protection Configuration
    MAX_FILES_PER_IP = int(os.environ.get('MAX_FILES_PER_IP', 50))
    MAX_SIZE_MB_PER_IP = float(os.environ.get('MAX_SIZE_MB_PER_IP', 1000))  # 1GB
    MAX_FILES_24H_PER_IP = int(os.environ.get('MAX_FILES_24H_PER_IP', 20))
    MAX_SIZE_24H_MB_PER_IP = float(os.environ.get('MAX_SIZE_24H_MB_PER_IP', 500))  # 500MB
    RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get('RATE_LIMIT_WINDOW_SECONDS', 3600))  # 1 hour
    MAX_REQUESTS_PER_WINDOW = int(os.environ.get('MAX_REQUESTS_PER_WINDOW', 100))
    IP_CLEANUP_INTERVAL_HOURS = int(os.environ.get('IP_CLEANUP_INTERVAL_HOURS', 24))
    IP_FILE_RETENTION_HOURS = int(os.environ.get('IP_FILE_RETENTION_HOURS', 72))  # 3 days
    
    # Advanced Storage Management Configuration
    MAX_TOTAL_STORAGE_MB = float(os.environ.get('MAX_TOTAL_STORAGE_MB', 10000))  # 10GB
    MAX_DISK_USAGE_PERCENT = float(os.environ.get('MAX_DISK_USAGE_PERCENT', 80.0))  # 80%
    STORAGE_CLEANUP_INTERVAL_HOURS = int(os.environ.get('STORAGE_CLEANUP_INTERVAL_HOURS', 6))  # 6 hours
    EMERGENCY_CLEANUP_THRESHOLD = float(os.environ.get('EMERGENCY_CLEANUP_THRESHOLD', 90.0))  # 90%
    PRIORITY_CLEANUP_AGE_HOURS = int(os.environ.get('PRIORITY_CLEANUP_AGE_HOURS', 24))  # 24 hours
    
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
