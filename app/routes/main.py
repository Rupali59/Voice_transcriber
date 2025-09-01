"""
Main routes for the Voice Transcriber application
"""

from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@main_bp.route('/health')
def health_check():
    """Health check endpoint"""
    from flask import jsonify, current_app
    from datetime import datetime
    
    from app.services.transcription_service import TranscriptionService
    transcription_service = TranscriptionService()
    transcription_service.init_app(current_app)
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_jobs': len(transcription_service.get_all_jobs())
    })
