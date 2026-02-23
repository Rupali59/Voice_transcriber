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
    
    # Initialize and preload models
    try:
        from app.services.model_cache_manager import get_model_cache_manager
        cache_manager = get_model_cache_manager()
        
        # Get configuration
        preload_models = app.config.get('PRELOAD_MODELS', [])
        warmup_models = app.config.get('WARMUP_MODELS', [])
        priority_models = app.config.get('PRIORITY_MODELS', [])
        
        print(f"🔄 Initializing model cache system...")
        
        # Preload configured models
        if preload_models:
            print(f"🔄 Preloading models: {preload_models}")
            cache_manager.preload_models(preload_models)
        
        # Warm up priority models
        if priority_models:
            print(f"🔥 Warming up priority models: {priority_models}")
            cache_manager.warmup_priority_models()
        
        # Ensure all warmup models are loaded
        if warmup_models:
            print(f"⚡ Ensuring warmup models are loaded: {warmup_models}")
            cache_manager.ensure_models_loaded(warmup_models)
        
        # Display cache status
        stats = cache_manager.get_cache_stats()
        loaded_models = stats.get('cached_models', [])
        print(f"✅ Model cache initialized with {len(loaded_models)} models: {loaded_models}")
        
        # Display cache health
        health = cache_manager.get_cache_health()
        print(f"📊 Cache health: {health['status']} - {health.get('message', 'OK')}")
        
    except Exception as e:
        print(f"⚠️  Model cache initialization failed: {e}")
        import traceback
        traceback.print_exc()
    
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
