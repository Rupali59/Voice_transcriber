"""
Voice Transcriber Web Application
Flask application factory with proper structure
"""

import os
import logging
from flask import Flask
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import Config
from app.routes import main_bp, api_bp
from app.routes.admin import admin_bp
from app.routes.ip_admin import ip_admin_bp
from app.utils.logger import setup_logging

# Global instances
socketio = SocketIO()

# Global service instances (singletons)
transcription_service = None
file_service = None
ip_file_service = None
storage_manager = None
job_manager = None
request_tracker = None

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Setup logging
    setup_logging(app)
    
    # Use ProxyFix for proper handling behind reverse proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Initialize extensions
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp)
    app.register_blueprint(ip_admin_bp)
    
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('transcriptions', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Register socketio events
    from app.routes.socketio_events import register_socketio_events
    register_socketio_events(socketio)
    
    # Initialize global services
    _initialize_services(app)
    
    return app

def _initialize_services(app):
    """Initialize global service instances"""
    global transcription_service, file_service, ip_file_service, storage_manager, job_manager, request_tracker
    
    from app.services.transcription_service import TranscriptionService
    from app.services.file_service import FileService
    from app.services.ip_file_service import IPFileService
    from app.services.storage_manager import StorageManager, CleanupPolicy
    from app.services.job_manager import JobManager
    from app.services.request_tracker import RequestTracker
    
    # Create shared instances
    job_manager = JobManager(
        max_concurrent_jobs=app.config.get('MAX_CONCURRENT_JOBS', 5),
        cleanup_hours=app.config.get('JOB_CLEANUP_HOURS', 1)
    )
    
    file_service = FileService(
        upload_folder=app.config['UPLOAD_FOLDER'],
        allowed_extensions=app.config['ALLOWED_EXTENSIONS']
    )
    
    # Initialize IP-based file service with DoS protection
    ip_file_service = IPFileService(
        base_upload_folder=app.config['UPLOAD_FOLDER'],
        allowed_extensions=app.config['ALLOWED_EXTENSIONS']
    )
    
    # Initialize storage manager with cleanup policies
    cleanup_policy = CleanupPolicy(
        max_age_hours=app.config.get('IP_FILE_RETENTION_HOURS', 72),
        max_total_size_mb=app.config.get('MAX_TOTAL_STORAGE_MB', 10000),  # 10GB
        max_disk_usage_percent=app.config.get('MAX_DISK_USAGE_PERCENT', 80.0),
        cleanup_interval_hours=app.config.get('STORAGE_CLEANUP_INTERVAL_HOURS', 6),
        emergency_cleanup_threshold=app.config.get('EMERGENCY_CLEANUP_THRESHOLD', 90.0),
        priority_cleanup_age_hours=app.config.get('PRIORITY_CLEANUP_AGE_HOURS', 24)
    )
    
    global storage_manager
    storage_manager = StorageManager(
        base_path=app.config['UPLOAD_FOLDER'],
        policy=cleanup_policy
    )
    
    request_tracker = RequestTracker()
    
    transcription_service = TranscriptionService()
    transcription_service.job_manager = job_manager
    transcription_service.file_service = file_service
    transcription_service.app = app

def get_transcription_service():
    """Get the global transcription service instance"""
    return transcription_service

def get_file_service():
    """Get the global file service instance"""
    return file_service

def get_job_manager():
    """Get the global job manager instance"""
    return job_manager

def get_request_tracker():
    """Get the global request tracker instance"""
    return request_tracker

def get_ip_file_service():
    """Get the global IP file service instance"""
    return ip_file_service

def get_storage_manager():
    """Get the global storage manager instance"""
    return storage_manager

def create_socketio_app(app):
    """Create SocketIO app instance"""
    return socketio
