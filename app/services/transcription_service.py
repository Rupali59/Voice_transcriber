"""
Transcription service for handling AI transcription
"""

import os
import sys
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from app.models.transcription_job import TranscriptionJob
from app.services.job_manager import JobManager
from app.services.file_service import FileService

try:
    from unified_voice_transcriber import UnifiedVoiceTranscriber
except ImportError:
    print("Warning: unified_voice_transcriber not found. Transcription will not work.")
    UnifiedVoiceTranscriber = None

class TranscriptionService:
    """Handles transcription operations"""
    
    def __init__(self):
        self.job_manager: Optional[JobManager] = None
        self.file_service: Optional[FileService] = None
        self.app = None
    
    def init_app(self, app):
        """Initialize service with Flask app"""
        self.app = app
        self.job_manager = JobManager(
            max_concurrent_jobs=app.config.get('MAX_CONCURRENT_JOBS', 5),
            cleanup_hours=app.config.get('JOB_CLEANUP_HOURS', 1)
        )
        self.file_service = FileService(
            upload_folder=app.config['UPLOAD_FOLDER'],
            allowed_extensions=app.config['ALLOWED_EXTENSIONS']
        )
    
    def start_transcription(self, job_id: str, file_upload, model_size: str, 
                          enable_speaker_diarization: bool, language: str) -> TranscriptionJob:
        """Start transcription process"""
        if not self.job_manager or not self.file_service:
            raise RuntimeError("Service not initialized")
        
        # Create job
        job = self.job_manager.create_job(
            job_id=job_id,
            filename=file_upload.filename,
            original_filename=file_upload.original_name,
            model_size=model_size,
            enable_speaker_diarization=enable_speaker_diarization,
            language=language,
            file_size_mb=file_upload.size_mb
        )
        
        # Start background transcription
        thread = threading.Thread(
            target=self._transcribe_background,
            args=(job_id, file_upload.filepath, model_size, enable_speaker_diarization, language)
        )
        thread.daemon = True
        thread.start()
        
        return job
    
    def _transcribe_background(self, job_id: str, filepath: str, model_size: str, 
                             enable_speaker_diarization: bool, language: str):
        """Background transcription process"""
        try:
            # Update status
            self.job_manager.update_job_status(job_id, 'loading_model', 10)
            self._emit_progress_update(job_id, 'loading_model', 10, 'Loading Whisper model...')
            
            # Create transcriber
            if not UnifiedVoiceTranscriber:
                raise Exception("Transcription service not available")
            
            transcriber = UnifiedVoiceTranscriber(
                model_size=model_size,
                enable_speaker_diarization=enable_speaker_diarization
            )
            
            # Update status
            self.job_manager.update_job_status(job_id, 'transcribing', 30)
            self._emit_progress_update(job_id, 'transcribing', 30, 'Transcribing audio...')
            
            # Transcribe audio
            result = transcriber.transcribe_audio(filepath)
            
            if result:
                # Update status
                self.job_manager.update_job_status(job_id, 'processing', 80)
                self._emit_progress_update(job_id, 'processing', 80, 'Processing results...')
                
                # Save transcription
                output_filename = f"transcription_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                output_path = os.path.join('transcriptions', output_filename)
                
                # Generate markdown content
                content = self._generate_transcription_markdown(
                    filepath, result, model_size, 
                    self.job_manager.get_job(job_id).start_time
                )
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Update job with result
                result_data = {
                    'transcription': result,
                    'output_file': output_filename,
                    'output_path': output_path
                }
                
                self.job_manager.set_job_result(job_id, result_data)
                
                self._emit_progress_update(job_id, 'completed', 100, 'Transcription completed!', {
                    'output_file': output_filename,
                    'language': result.get('language', 'Unknown'),
                    'duration': result.get('duration', 'Unknown'),
                    'speakers': len(set([seg.get('speaker', 'Unknown') for seg in result.get('segments', [])]))
                })
                
            else:
                raise Exception("Transcription failed")
                
        except Exception as e:
            self.job_manager.set_job_error(job_id, str(e))
            self._emit_progress_update(job_id, 'error', 0, f'Error: {str(e)}')
    
    def _emit_progress_update(self, job_id: str, status: str, progress: int, message: str, result: dict = None):
        """Emit progress update via SocketIO"""
        if self.app:
            from flask_socketio import emit
            data = {
                'job_id': job_id,
                'status': status,
                'progress': progress,
                'message': message
            }
            if result:
                data['result'] = result
            
            emit('progress_update', data, namespace='/')
    
    def _generate_transcription_markdown(self, filepath: str, result: dict, model_size: str, start_time: str) -> str:
        """Generate markdown content for transcription"""
        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath) / (1024 * 1024)
        
        lines = [
            f"# {Path(filename).stem} - Transcription",
            "",
            f"**File:** {filename}",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**File Size:** {file_size:.1f} MB",
            f"**Language:** {result.get('language', 'Unknown')}",
            f"**Duration:** {result.get('duration', 'Unknown')}",
            f"**Model Used:** Whisper {model_size.upper()}",
            f"**Speaker Diarization:** {'Enabled' if result.get('speaker_segments') else 'Disabled'}",
            "",
            "## Transcription",
            "",
            result.get('text', 'No transcription available')
        ]
        
        # Add speaker analysis if available
        if result.get('speaker_segments'):
            lines.extend([
                "",
                "## Speaker Analysis",
                ""
            ])
            
            for i, segment in enumerate(result.get('speaker_segments', [])):
                lines.extend([
                    f"**Speaker {segment.get('speaker', i)}** "
                    f"({segment.get('start_time', 'Unknown')} - "
                    f"{segment.get('end_time', 'Unknown')})",
                    f"{segment.get('text', '')}",
                    ""
                ])
        
        return "\n".join(lines)
    
    def get_job(self, job_id: str) -> Optional[TranscriptionJob]:
        """Get job by ID"""
        if self.job_manager:
            return self.job_manager.get_job(job_id)
        return None
    
    def get_all_jobs(self) -> Dict[str, TranscriptionJob]:
        """Get all jobs"""
        if self.job_manager:
            return self.job_manager.get_all_jobs()
        return {}
