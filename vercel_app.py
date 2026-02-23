"""
Vercel-specific Flask application entry point
Optimized for serverless deployment on Vercel
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for Vercel
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('PYTHONPATH', str(project_root))

# Import the main app
from app_main import app

# Vercel expects the app to be available as 'application'
application = app

if __name__ == '__main__':
    # This won't be used in Vercel, but useful for local testing
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
