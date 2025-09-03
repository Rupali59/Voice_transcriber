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
    """Handle file upload with IP-based tracking and DoS protection"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get client IP address
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        # Get IP file service from global instance
        from app import get_ip_file_service
        ip_file_service = get_ip_file_service()
        
        # Save uploaded file with IP tracking and DoS protection
        file_upload = ip_file_service.save_uploaded_file(
            file, 
            current_app.config['MAX_CONTENT_LENGTH'],
            client_ip
        )
        
        # Get quota info for response
        quota = ip_file_service.get_ip_quota(client_ip)
        
        return jsonify({
            'success': True,
            'filename': file_upload.filename,
            'original_name': file_upload.original_name,
            'size_mb': round(file_upload.size_mb, 2),
            'filepath': file_upload.filepath,
            'quota_info': {
                'total_files': quota.total_files if quota else 0,
                'total_size_mb': round(quota.total_size_mb, 2) if quota else 0.0,
                'files_24h': quota.file_count_24h if quota else 0,
                'size_24h_mb': round(quota.size_mb_24h, 2) if quota else 0.0
            }
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
        # Handle both form data and JSON data
        if request.content_type and 'application/json' in request.content_type:
            # Handle JSON data (legacy)
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
        else:
            # Handle form data (new design)
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Get client IP address
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
            if ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()
            
            # Get IP file service from global instance
            from app import get_ip_file_service
            ip_file_service = get_ip_file_service()
            
            # Save uploaded file with IP tracking and DoS protection
            file_upload = ip_file_service.save_uploaded_file(
                file, 
                current_app.config['MAX_CONTENT_LENGTH'],
                client_ip
            )
            
            # Get form parameters
            model_size = request.form.get('model', 'base')
            enable_speaker_diarization = request.form.get('diarization', 'false').lower() == 'true'
            language = request.form.get('language', 'auto')
            temperature = float(request.form.get('temperature', 0.2))
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Get services from global instances
        from app import get_transcription_service, get_request_tracker
        transcription_service = get_transcription_service()
        request_tracker = get_request_tracker()
        
        # Start tracking this request
        if 'client_ip' not in locals():
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
            if ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()
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
        # Try multiple possible locations for transcript files
        possible_paths = [
            os.path.join('transcriptions', filename),  # Project root transcriptions folder
            filename,  # Project root directly
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'transcriptions', filename)  # App relative path
        ]
        
        filepath = None
        for path in possible_paths:
            if os.path.exists(path):
                filepath = path
                break
        
        if not filepath:
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(filepath, as_attachment=True)
        
    except Exception as e:
        current_app.logger.error(f"Download error: {e}")
        return jsonify({'error': 'Download failed'}), 500

@api_bp.route('/transcript/<filename>')
def get_transcript(filename):
    """Get transcription content for viewing"""
    try:
        # Try multiple possible locations for transcript files
        possible_paths = [
            os.path.join('transcriptions', filename),  # Project root transcriptions folder
            filename,  # Project root directly
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'transcriptions', filename)  # App relative path
        ]
        
        filepath = None
        for path in possible_paths:
            if os.path.exists(path):
                filepath = path
                break
        
        if not filepath:
            return jsonify({'error': 'File not found'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'filename': filename,
            'content': content,
            'size': os.path.getsize(filepath)
        })
        
    except Exception as e:
        current_app.logger.error(f"Get transcript error: {e}")
        return jsonify({'error': 'Failed to read transcript'}), 500

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

@api_bp.route('/cache/stats', methods=['GET'])
def get_cache_stats():
    """Get model cache statistics"""
    try:
        from app.services.model_cache import get_model_cache
        cache = get_model_cache()
        stats = cache.get_cache_stats()
        return jsonify(stats)
    except Exception as e:
        current_app.logger.error(f"Cache stats error: {e}")
        return jsonify({'error': 'Failed to get cache stats'}), 500

@api_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear model cache"""
    try:
        from app.services.model_cache import get_model_cache
        cache = get_model_cache()
        cache.clear_cache()
        return jsonify({'success': True, 'message': 'Cache cleared'})
    except Exception as e:
        current_app.logger.error(f"Cache clear error: {e}")
        return jsonify({'error': 'Failed to clear cache'}), 500

@api_bp.route('/cache/optimize', methods=['POST'])
def optimize_memory():
    """Optimize memory usage"""
    try:
        from app.services.model_cache import get_model_cache
        cache = get_model_cache()
        cache.optimize_memory()
        return jsonify({'success': True, 'message': 'Memory optimized'})
    except Exception as e:
        current_app.logger.error(f"Memory optimization error: {e}")
        return jsonify({'error': 'Failed to optimize memory'}), 500

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

# IP-based file management endpoints

@api_bp.route('/my-files')
def get_my_files():
    """Get files uploaded by the current IP address"""
    try:
        # Get client IP address
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        from app import get_ip_file_service
        ip_file_service = get_ip_file_service()
        
        files = ip_file_service.get_files_by_ip(client_ip)
        
        return jsonify({
            'success': True,
            'ip_address': client_ip,
            'files': [asdict(f) for f in files],
            'file_count': len(files),
            'total_size_mb': round(sum(f.size_mb for f in files), 2)
        })
        
    except Exception as e:
        current_app.logger.error(f"Get my files error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get files'}), 500

@api_bp.route('/my-files/<filename>')
def get_my_file(filename):
    """Get a specific file uploaded by the current IP address"""
    try:
        # Get client IP address
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        from app import get_ip_file_service
        ip_file_service = get_ip_file_service()
        
        file_record = ip_file_service.get_file_by_ip_and_name(client_ip, filename)
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        return jsonify({
            'success': True,
            'file': asdict(file_record)
        })
        
    except Exception as e:
        current_app.logger.error(f"Get my file error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get file'}), 500

@api_bp.route('/my-files/<filename>', methods=['DELETE'])
def delete_my_file(filename):
    """Delete a file uploaded by the current IP address"""
    try:
        # Get client IP address
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        from app import get_ip_file_service
        ip_file_service = get_ip_file_service()
        
        success = ip_file_service.delete_file_by_ip(client_ip, filename)
        if not success:
            return jsonify({'error': 'File not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'File deleted successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Delete my file error: {e}")
        return jsonify({'success': False, 'error': 'Failed to delete file'}), 500

@api_bp.route('/my-quota')
def get_my_quota():
    """Get quota information for the current IP address"""
    try:
        # Get client IP address
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        from app import get_ip_file_service
        ip_file_service = get_ip_file_service()
        
        stats = ip_file_service.get_ip_stats(client_ip)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Get my quota error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get quota'}), 500

@api_bp.route('/my-files/cleanup', methods=['POST'])
def cleanup_my_files():
    """Clean up all files for the current IP address"""
    try:
        # Get client IP address
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        from app import get_ip_file_service
        ip_file_service = get_ip_file_service()
        
        deleted_count = ip_file_service.cleanup_ip_files(client_ip)
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {deleted_count} files',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        current_app.logger.error(f"Cleanup my files error: {e}")
        return jsonify({'success': False, 'error': 'Failed to cleanup files'}), 500

# Analytics Endpoints

@api_bp.route('/analytics/config')
def get_analytics_config():
    """Get analytics configuration for frontend"""
    try:
        from app.services.analytics_service import analytics_service
        config = analytics_service.get_analytics_config()
        return jsonify(config)
    except Exception as e:
        current_app.logger.error(f"Analytics config error: {e}")
        return jsonify({'error': 'Failed to get analytics config'}), 500

@api_bp.route('/analytics/track', methods=['POST'])
def track_analytics_event():
    """Track analytics event from frontend"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        from app.services.analytics_service import analytics_service
        
        event_name = data.get('event_name')
        if not event_name:
            return jsonify({'error': 'Event name required'}), 400
        
        # Track different event types
        if event_name == 'file_upload':
            analytics_service.track_file_upload(
                data.get('file_name', ''),
                data.get('file_size', 0),
                data.get('file_type', '')
            )
        elif event_name == 'transcription_start':
            analytics_service.track_transcription_start(
                data.get('model', ''),
                data.get('language', ''),
                data.get('speaker_diarization', False),
                data.get('temperature', 0.2),
                data.get('file_size', 0)
            )
        elif event_name == 'transcription_complete':
            analytics_service.track_transcription_complete(
                data.get('job_id', ''),
                data.get('model', ''),
                data.get('language', ''),
                data.get('processing_time', 0),
                data.get('file_size', 0),
                data.get('transcript_length', 0),
                data.get('success', True)
            )
        elif event_name == 'transcription_error':
            analytics_service.track_transcription_error(
                data.get('job_id', ''),
                data.get('error_type', ''),
                data.get('error_message', ''),
                data.get('model', ''),
                data.get('file_size', 0)
            )
        elif event_name == 'file_download':
            analytics_service.track_download(
                data.get('file_name', ''),
                data.get('file_type', ''),
                data.get('file_size', 0)
            )
        elif event_name == 'user_interaction':
            analytics_service.track_user_interaction(
                data.get('interaction_type', ''),
                data.get('element_id'),
                data.get('element_class'),
                data.get('additional_data')
            )
        elif event_name == 'performance_metric':
            analytics_service.track_performance_metric(
                data.get('metric_name', ''),
                data.get('metric_value', 0),
                data.get('unit'),
                data.get('context')
            )
        else:
            # Generic event tracking
            analytics_service.track_user_interaction(
                event_name,
                data.get('element_id'),
                data.get('element_class'),
                data
            )
        
        return jsonify({'success': True, 'message': 'Event tracked'})
        
    except Exception as e:
        current_app.logger.error(f"Analytics tracking error: {e}")
        return jsonify({'error': 'Failed to track event'}), 500

@api_bp.route('/analytics/summary')
def get_analytics_summary():
    """Get analytics summary for current session"""
    try:
        from app.services.analytics_service import analytics_service
        summary = analytics_service.get_analytics_summary()
        return jsonify(summary)
    except Exception as e:
        current_app.logger.error(f"Analytics summary error: {e}")
        return jsonify({'error': 'Failed to get analytics summary'}), 500

@api_bp.route('/analytics/user-properties', methods=['POST'])
def set_user_properties():
    """Set user properties for analytics"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        from app.services.analytics_service import analytics_service
        
        for property_name, property_value in data.items():
            analytics_service.set_user_property(property_name, property_value)
        
        return jsonify({'success': True, 'message': 'User properties set'})
        
    except Exception as e:
        current_app.logger.error(f"Set user properties error: {e}")
        return jsonify({'error': 'Failed to set user properties'}), 500

@api_bp.route('/transcripts', methods=['GET'])
def get_transcripts():
    """Get list of existing transcripts"""
    try:
        # Get client IP address
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        # Get IP file service from global instance
        from app import get_ip_file_service
        ip_file_service = get_ip_file_service()
        
        # Get files for this IP
        files = ip_file_service.get_files_by_ip(client_ip)
        
        # Filter for transcript files (files that have been transcribed)
        transcripts = []
        for file_record in files:
            # Check if this file has a corresponding transcript
            transcript_path = os.path.join(current_app.config['TRANSCRIPTION_FOLDER'], f"{file_record.filename}.txt")
            if os.path.exists(transcript_path):
                transcripts.append({
                    'filename': f"{file_record.filename}.txt",
                    'original_name': file_record.original_name,
                    'created_at': file_record.uploaded_at.isoformat(),
                    'size': os.path.getsize(transcript_path)
                })
        
        return jsonify({
            'success': True,
            'transcripts': transcripts
        })
        
    except Exception as e:
        current_app.logger.error(f"Get transcripts error: {e}")
        return jsonify({'error': 'Failed to get transcripts'}), 500

@api_bp.route('/transcripts/<filename>', methods=['GET'])
def download_transcript(filename):
    """Download a transcript file"""
    try:
        # Get client IP address
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        # Get IP file service from global instance
        from app import get_ip_file_service
        ip_file_service = get_ip_file_service()
        
        # Check if user has access to this file
        files = ip_file_service.get_files_by_ip(client_ip)
        file_names = [f.filename for f in files]
        
        # Remove .txt extension to match original filename
        original_filename = filename.replace('.txt', '')
        if original_filename not in file_names:
            return jsonify({'error': 'File not found or access denied'}), 404
        
        # Construct file path
        file_path = os.path.join(current_app.config['TRANSCRIPTION_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Transcript file not found'}), 404
        
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        current_app.logger.error(f"Download transcript error: {e}")
        return jsonify({'error': 'Failed to download transcript'}), 500
