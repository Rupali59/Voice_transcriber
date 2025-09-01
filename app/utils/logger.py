"""
Logging configuration
"""

import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    """Setup application logging"""
    
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            app.config.get('LOG_FILE', 'logs/web_app.log'),
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Voice Transcriber startup')
