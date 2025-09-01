"""
API routes for the Voice Transcriber application
"""

import os
import uuid
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.exceptions import RequestEntityTooLarge

from app.models.file_upload import FileUpload

api_bp = Blueprint('api', __name__)

@api_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get file service from app context
        from app.services.file_service import FileService
        file_service = FileService(
            current_app.config['UPLOAD_FOLDER'],
            current_app.config['ALLOWED_EXTENSIONS']
        )
        
        # Save uploaded file
        file_upload = file_service.save_uploaded_file(
            file, 
            current_app.config['MAX_CONTENT_LENGTH']
        )
        
        return jsonify({
            'success': True,
            'filename': file_upload.filename,
            'original_name': file_upload.original_name,
            'size_mb': round(file_upload.size_mb, 2),
            'filepath': file_upload.filepath
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except RequestEntityTooLarge:
        return jsonify({'error': 'File too large'}), 413
    except Exception as e:
        current_app.logger.error(f"Upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500

@api_bp.route('/transcribe', methods=['POST'])
def start_transcription():
    """Start transcription process"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        model_size = data.get('model_size', 'base')
        enable_speaker_diarization = data.get('enable_speaker_diarization', True)
        language = data.get('language', 'auto')
        temperature = data.get('temperature', 0.2)
        beam_size = data.get('beam_size', 5)
        best_of = data.get('best_of', 1)
        patience = data.get('patience', 1.0)
        length_penalty = data.get('length_penalty', 1.0)
        
        if not filename:
            return jsonify({'error': 'No filename provided'}), 400
        
        # Create FileUpload object from filename
        from app.models.file_upload import FileUpload
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        file_upload = FileUpload(
            filename=filename,
            original_name=filename,  # This would be stored in a real app
            filepath=filepath,
            size_bytes=os.path.getsize(filepath)
        )
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Get transcription service from app context
        from app.services.transcription_service import TranscriptionService
        transcription_service = TranscriptionService()
        transcription_service.init_app(current_app)
        
        # Start transcription
        job = transcription_service.start_transcription(
            job_id=job_id,
            file_upload=file_upload,
            model_size=model_size,
            enable_speaker_diarization=enable_speaker_diarization,
            language=language,
            temperature=temperature,
            beam_size=beam_size,
            best_of=best_of,
            patience=patience,
            length_penalty=length_penalty
        )
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Transcription started'
        })
        
    except Exception as e:
        current_app.logger.error(f"Transcription start error: {e}")
        return jsonify({'error': 'Failed to start transcription'}), 500

@api_bp.route('/job/<job_id>')
def get_job_status(job_id):
    """Get job status"""
    from app.services.transcription_service import TranscriptionService
    transcription_service = TranscriptionService()
    transcription_service.init_app(current_app)
    
    job = transcription_service.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job.to_dict())

@api_bp.route('/download/<filename>')
def download_file(filename):
    """Download transcription file"""
    try:
        filepath = os.path.join('transcriptions', filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(filepath, as_attachment=True)
        
    except Exception as e:
        current_app.logger.error(f"Download error: {e}")
        return jsonify({'error': 'Download failed'}), 500

@api_bp.route('/models')
def get_available_models():
    """Get available Whisper models"""
    return jsonify({
        'models': [
            {'id': 'tiny', 'name': 'Tiny', 'description': 'Fastest, lowest accuracy'},
            {'id': 'base', 'name': 'Base', 'description': 'Good balance of speed and accuracy'},
            {'id': 'small', 'name': 'Small', 'description': 'Better accuracy, slower'},
            {'id': 'medium', 'name': 'Medium', 'description': 'High accuracy, slower'},
            {'id': 'large', 'name': 'Large', 'description': 'Best accuracy, slowest'}
        ]
    })
