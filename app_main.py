#!/usr/bin/env python3
"""
Voice Transcriber Web Application - Main Entry Point
Refactored with proper structure and organization
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app, create_socketio_app
from app.config import config

def main():
    """Main application entry point"""
    
    # Get configuration from environment
    config_name = os.environ.get('FLASK_ENV', 'development')
    app_config = config.get(config_name, config['default'])
    
    # Create Flask application
    app = create_app(app_config)
    
    # Create SocketIO app
    socketio = create_socketio_app(app)
    
    # Get configuration
    host = app.config.get('HOST', '0.0.0.0')
    port = app.config.get('PORT', 5001)
    debug = app.config.get('DEBUG', False)
    
    print(f"🚀 Starting Voice Transcriber Web App")
    print(f"📍 Environment: {config_name}")
    print(f"🌐 URL: http://{host}:{port}")
    print(f"🔧 Debug: {debug}")
    print("=" * 50)
    
    # Run the application
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True
    )

if __name__ == '__main__':
    main()
