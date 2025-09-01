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
from app.utils.logger import setup_logging

# Global instances
socketio = SocketIO()

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
    
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('transcriptions', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Register socketio events
    from app.routes.socketio_events import register_socketio_events
    register_socketio_events(socketio)
    
    return app

def create_socketio_app(app):
    """Create SocketIO app instance"""
    return socketio
