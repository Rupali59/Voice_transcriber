"""
API routes for the Voice Transcriber application
"""

import os
import uuid
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.exceptions import RequestEntityTooLarge
from dataclasses import asdict

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
        
        # Get file service from global instance
        from app import get_file_service
        file_service = get_file_service()
        
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
        
        # Get services from global instances
        from app import get_transcription_service, get_request_tracker
        transcription_service = get_transcription_service()
        request_tracker = get_request_tracker()
        
        # Start tracking this request
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        user_agent = request.headers.get('User-Agent', 'unknown')
        request_id = request_tracker.start_request(
            job_id=job_id,
            client_ip=client_ip,
            user_agent=user_agent,
            filename=filename,
            file_size_mb=file_upload.size_mb,
            model_size=model_size,
            language=language,
            temperature=temperature,
            enable_speaker_diarization=enable_speaker_diarization
        )
        
        # Start transcription
        job = transcription_service.start_transcription(
            job_id=job_id,
            file_upload=file_upload,
            model_size=model_size,
            enable_speaker_diarization=enable_speaker_diarization,
            language=language,
            temperature=temperature,
            request_id=request_id
        )
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'request_id': request_id,
            'message': 'Transcription started'
        })
        
    except Exception as e:
        current_app.logger.error(f"Transcription start error: {e}")
        return jsonify({'error': 'Failed to start transcription'}), 500

@api_bp.route('/job/<job_id>')
def get_job_status(job_id):
    """Get job status"""
    from app import get_transcription_service
    transcription_service = get_transcription_service()
    
    job = transcription_service.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job.to_dict())

@api_bp.route('/job-status/<job_id>')
def get_job_status_api(job_id):
    """Get job status for API calls"""
    try:
        from app import get_transcription_service
        transcription_service = get_transcription_service()
        
        job = transcription_service.get_job(job_id)
        if not job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404
        
        # Get status message
        status_messages = {
            'starting': 'Starting transcription...',
            'loading_model': 'Loading AI model...',
            'transcribing': 'Transcribing audio...',
            'processing': 'Processing results...',
            'completed': 'Transcription completed',
            'error': 'Transcription failed',
            'cancelled': 'Transcription cancelled'
        }
        message = status_messages.get(job.status, 'Processing...')
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'status': job.status,
            'progress': job.progress,
            'message': message,
            'result': job.result,
            'start_time': job.start_time,
            'end_time': job.end_time,
            'error': job.error
        })
        
    except Exception as e:
        current_app.logger.error(f"Job status error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get job status'}), 500

@api_bp.route('/cancel-job/<job_id>', methods=['POST'])
def cancel_job(job_id):
    """Cancel a transcription job"""
    try:
        from app import get_transcription_service
        transcription_service = get_transcription_service()
        
        success = transcription_service.cancel_job(job_id)
        if success:
            return jsonify({
                'success': True,
                'message': 'Job cancelled successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Job not found or already completed'
            }), 404
            
    except Exception as e:
        current_app.logger.error(f"Cancel job error: {e}")
        return jsonify({'success': False, 'error': 'Failed to cancel job'}), 500

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

# Request Tracking Endpoints

@api_bp.route('/requests')
def get_all_requests():
    """Get all transcription requests with optional filtering"""
    try:
        from app import get_request_tracker
        request_tracker = get_request_tracker()
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        status_filter = request.args.get('status')
        client_ip = request.args.get('client_ip')
        
        if client_ip:
            requests = request_tracker.get_requests_by_client(client_ip, limit)
        else:
            requests = request_tracker.get_all_requests(limit, status_filter)
        
        return jsonify({
            'success': True,
            'requests': [asdict(req) for req in requests],
            'total_count': len(requests)
        })
        
    except Exception as e:
        current_app.logger.error(f"Get requests error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get requests'}), 500

@api_bp.route('/requests/<request_id>')
def get_request_details(request_id):
    """Get detailed information about a specific request"""
    try:
        from app import get_request_tracker
        request_tracker = get_request_tracker()
        
        request_info = request_tracker.get_request(request_id)
        if not request_info:
            return jsonify({'success': False, 'error': 'Request not found'}), 404
        
        return jsonify({
            'success': True,
            'request': asdict(request_info)
        })
        
    except Exception as e:
        current_app.logger.error(f"Get request details error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get request details'}), 500

@api_bp.route('/requests/job/<job_id>')
def get_requests_by_job(job_id):
    """Get all requests for a specific job"""
    try:
        from app import get_request_tracker
        request_tracker = get_request_tracker()
        
        requests = request_tracker.get_requests_by_job_id(job_id)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'requests': [asdict(req) for req in requests],
            'count': len(requests)
        })
        
    except Exception as e:
        current_app.logger.error(f"Get requests by job error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get requests by job'}), 500

@api_bp.route('/requests/statistics')
def get_request_statistics():
    """Get request statistics and analytics"""
    try:
        from app import get_request_tracker
        request_tracker = get_request_tracker()
        
        stats = request_tracker.get_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Get statistics error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get statistics'}), 500

@api_bp.route('/requests/export')
def export_requests():
    """Export requests in specified format"""
    try:
        from app import get_request_tracker
        request_tracker = get_request_tracker()
        
        format_type = request.args.get('format', 'json')
        
        if format_type not in ['json', 'csv']:
            return jsonify({'error': 'Invalid format. Use json or csv'}), 400
        
        export_data = request_tracker.export_requests(format_type)
        
        return jsonify({
            'success': True,
            'format': format_type,
            'data': export_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Export requests error: {e}")
        return jsonify({'success': False, 'error': 'Failed to export requests'}), 500

@api_bp.route('/requests/cleanup', methods=['POST'])
def cleanup_old_requests():
    """Clean up old requests"""
    try:
        from app import get_request_tracker
        request_tracker = get_request_tracker()
        
        days = request.json.get('days', 7) if request.is_json else 7
        
        request_tracker.cleanup_old_requests(days)
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up requests older than {days} days'
        })
        
    except Exception as e:
        current_app.logger.error(f"Cleanup requests error: {e}")
        return jsonify({'success': False, 'error': 'Failed to cleanup requests'}), 500
