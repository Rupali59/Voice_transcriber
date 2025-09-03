"""
Mock services for Voice Transcriber tests
Provides mock implementations of various services for testing
"""

import os
import sys
from unittest.mock import Mock, MagicMock
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class MockFileUpload:
    """Mock file upload object"""
    
    def __init__(self, filename="test.wav", original_name="test.wav", 
                 size_mb=5.0, filepath="/uploads/test.wav"):
        self.filename = filename
        self.original_name = original_name
        self.size_mb = size_mb
        self.filepath = filepath
        self.upload_time = datetime.now()
        self.content_type = "audio/wav"


class MockTranscriptionJob:
    """Mock transcription job object"""
    
    def __init__(self, job_id="test-job-123", status="starting", progress=0):
        self.job_id = job_id
        self.status = status
        self.progress = progress
        self.filename = "test.wav"
        self.original_filename = "test.wav"
        self.model_size = "base"
        self.enable_speaker_diarization = True
        self.language = "en"
        self.start_time = datetime.now()
        self.end_time = None
        self.result = None
        self.error = None
        self.file_size_mb = 5.0


class MockTranscriptionResult:
    """Mock transcription result object"""
    
    def __init__(self, text="Test transcription", language="en", 
                 duration="0:05", segments=None, speaker_segments=None):
        self.text = text
        self.language = language
        self.duration = duration
        self.segments = segments or []
        self.speaker_segments = speaker_segments or []
        
        # Add get method for dictionary-like access
        self.get = lambda key, default=None: getattr(self, key, default)


class MockFileService:
    """Mock file service"""
    
    def __init__(self):
        self.uploaded_files = {}
        self.file_counter = 0
    
    def save_uploaded_file(self, file, max_size):
        """Mock save uploaded file"""
        self.file_counter += 1
        filename = f"uuid_{self.file_counter}_{file.filename}"
        file_upload = MockFileUpload(
            filename=filename,
            original_name=file.filename,
            size_mb=0.001,  # Small size for testing
            filepath=f"/uploads/{filename}"
        )
        self.uploaded_files[filename] = file_upload
        return file_upload
    
    def get_file_by_filename(self, filename):
        """Mock get file by filename"""
        return self.uploaded_files.get(filename)
    
    def delete_file(self, filename):
        """Mock delete file"""
        if filename in self.uploaded_files:
            del self.uploaded_files[filename]
            return True
        return False
    
    def get_all_files(self):
        """Mock get all files"""
        return list(self.uploaded_files.values())


class MockJobManager:
    """Mock job manager"""
    
    def __init__(self, max_concurrent_jobs=5, cleanup_hours=1):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.cleanup_hours = cleanup_hours
        self.jobs = {}
        self.job_counter = 0
    
    def create_job(self, job_id, filename, original_filename, model_size, 
                   enable_speaker_diarization, language, file_size_mb):
        """Mock create job"""
        job = MockTranscriptionJob(
            job_id=job_id,
            filename=filename,
            original_filename=original_filename,
            model_size=model_size,
            enable_speaker_diarization=enable_speaker_diarization,
            language=language,
            file_size_mb=file_size_mb
        )
        self.jobs[job_id] = job
        return job
    
    def get_job(self, job_id):
        """Mock get job"""
        return self.jobs.get(job_id)
    
    def get_all_jobs(self):
        """Mock get all jobs"""
        return self.jobs.copy()
    
    def update_job_status(self, job_id, status, progress):
        """Mock update job status"""
        if job_id in self.jobs:
            self.jobs[job_id].status = status
            self.jobs[job_id].progress = progress
    
    def set_job_result(self, job_id, result):
        """Mock set job result"""
        if job_id in self.jobs:
            self.jobs[job_id].result = result
            self.jobs[job_id].status = "completed"
            self.jobs[job_id].progress = 100
            self.jobs[job_id].end_time = datetime.now()
    
    def set_job_error(self, job_id, error):
        """Mock set job error"""
        if job_id in self.jobs:
            self.jobs[job_id].error = error
            self.jobs[job_id].status = "error"
            self.jobs[job_id].end_time = datetime.now()
    
    def cancel_job(self, job_id):
        """Mock cancel job"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            if job.status in ['starting', 'loading_model', 'transcribing', 'processing']:
                job.status = 'cancelled'
                return True
        return False
    
    def cleanup_old_jobs(self):
        """Mock cleanup old jobs"""
        # Remove jobs older than cleanup_hours
        cutoff_time = datetime.now().timestamp() - (self.cleanup_hours * 3600)
        jobs_to_remove = []
        
        for job_id, job in self.jobs.items():
            if job.start_time.timestamp() < cutoff_time:
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
        
        return len(jobs_to_remove)


class MockTranscriptionService:
    """Mock transcription service"""
    
    def __init__(self):
        self.job_manager = MockJobManager()
        self.file_service = MockFileService()
        self.app = None
    
    def init_app(self, app):
        """Mock init app"""
        self.app = app
        self.job_manager = MockJobManager(
            max_concurrent_jobs=app.config.get('MAX_CONCURRENT_JOBS', 5),
            cleanup_hours=app.config.get('JOB_CLEANUP_HOURS', 1)
        )
        self.file_service = MockFileService()
    
    def start_transcription(self, job_id, file_upload, model_size, 
                           enable_speaker_diarization, language, temperature=0.2, request_id=None):
        """Mock start transcription"""
        job = self.job_manager.create_job(
            job_id=job_id,
            filename=file_upload.filename,
            original_filename=file_upload.original_name,
            model_size=model_size,
            enable_speaker_diarization=enable_speaker_diarization,
            language=language,
            file_size_mb=file_upload.size_mb
        )
        
        # Simulate background processing
        import threading
        thread = threading.Thread(
            target=self._mock_transcribe_background,
            args=(job_id, file_upload.filepath, model_size, enable_speaker_diarization, language, temperature)
        )
        thread.daemon = True
        thread.start()
        
        return job
    
    def _mock_transcribe_background(self, job_id, filepath, model_size, 
                                   enable_speaker_diarization, language, temperature):
        """Mock background transcription"""
        import time
        
        try:
            # Simulate processing steps
            self.job_manager.update_job_status(job_id, 'loading_model', 10)
            time.sleep(0.1)  # Simulate model loading
            
            self.job_manager.update_job_status(job_id, 'transcribing', 30)
            time.sleep(0.2)  # Simulate transcription
            
            self.job_manager.update_job_status(job_id, 'processing', 80)
            time.sleep(0.1)  # Simulate processing
            
            # Create mock result
            result = {
                'transcription': MockTranscriptionResult(
                    text="Mock transcription result",
                    language=language,
                    duration="0:05",
                    segments=[],
                    speaker_segments=[]
                ),
                'output_file': f"transcription_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                'output_path': f"/transcriptions/transcription_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            }
            
            self.job_manager.set_job_result(job_id, result)
            
        except Exception as e:
            self.job_manager.set_job_error(job_id, str(e))
    
    def get_job(self, job_id):
        """Mock get job"""
        return self.job_manager.get_job(job_id)
    
    def get_all_jobs(self):
        """Mock get all jobs"""
        return self.job_manager.get_all_jobs()
    
    def cancel_job(self, job_id):
        """Mock cancel job"""
        return self.job_manager.cancel_job(job_id)


class MockModelCache:
    """Mock model cache"""
    
    def __init__(self):
        self.models = {}
        self.model_usage = {}
        self.cache_config = {
            'max_models': 3,
            'idle_timeout': 1800,
            'cleanup_interval': 300,
            'enable_gpu': False
        }
    
    def get_model(self, model_size):
        """Mock get model"""
        if model_size in self.models:
            self._update_usage(model_size)
            return self.models[model_size]
        
        # Mock model loading
        mock_model = Mock()
        self.models[model_size] = mock_model
        self._update_usage(model_size, is_new=True)
        return mock_model
    
    def _update_usage(self, model_size, is_new=False):
        """Mock update usage"""
        from datetime import datetime
        now = datetime.now()
        
        if is_new:
            self.model_usage[model_size] = {
                'first_used': now,
                'last_used': now,
                'access_count': 1
            }
        else:
            if model_size in self.model_usage:
                self.model_usage[model_size]['last_used'] = now
                self.model_usage[model_size]['access_count'] += 1
    
    def preload_models(self, model_sizes):
        """Mock preload models"""
        for model_size in model_sizes:
            if model_size not in self.models:
                self.get_model(model_size)
    
    def get_cache_stats(self):
        """Mock get cache stats"""
        return {
            'cached_models': list(self.models.keys()),
            'cache_size': len(self.models),
            'max_cache_size': self.cache_config['max_models'],
            'model_usage': self.model_usage.copy(),
            'memory_usage': {
                'rss_mb': 1024.0,
                'vms_mb': 2048.0,
                'percent': 25.0
            }
        }
    
    def clear_cache(self):
        """Mock clear cache"""
        self.models.clear()
        self.model_usage.clear()
    
    def optimize_memory(self):
        """Mock optimize memory"""
        pass


class MockRequestTracker:
    """Mock request tracker"""
    
    def __init__(self):
        self.requests = {}
        self.request_counter = 0
    
    def create_request(self, filename, model_size, enable_speaker_diarization, language):
        """Mock create request"""
        self.request_counter += 1
        request_id = f"req_{self.request_counter}"
        
        request = {
            'request_id': request_id,
            'filename': filename,
            'model_size': model_size,
            'enable_speaker_diarization': enable_speaker_diarization,
            'language': language,
            'status': 'pending',
            'timestamp': datetime.now(),
            'progress': 0
        }
        
        self.requests[request_id] = request
        return request_id
    
    def update_request_status(self, request_id, status, progress=None, error=None):
        """Mock update request status"""
        if request_id in self.requests:
            self.requests[request_id]['status'] = status
            if progress is not None:
                self.requests[request_id]['progress'] = progress
            if error is not None:
                self.requests[request_id]['error'] = error
    
    def complete_request(self, request_id, result_file):
        """Mock complete request"""
        if request_id in self.requests:
            self.requests[request_id]['status'] = 'completed'
            self.requests[request_id]['progress'] = 100
            self.requests[request_id]['result_file'] = result_file
            self.requests[request_id]['completed_at'] = datetime.now()
    
    def get_all_requests(self, status=None, limit=None):
        """Mock get all requests"""
        requests = list(self.requests.values())
        
        if status:
            requests = [req for req in requests if req['status'] == status]
        
        if limit:
            requests = requests[:limit]
        
        return requests
    
    def get_request(self, request_id):
        """Mock get request"""
        return self.requests.get(request_id)


class MockUnifiedVoiceTranscriber:
    """Mock unified voice transcriber"""
    
    def __init__(self, model_size="base", enable_speaker_diarization=True):
        self.model_size = model_size
        self.enable_speaker_diarization = enable_speaker_diarization
        self.model = Mock()
    
    def load_model(self):
        """Mock load model"""
        pass
    
    def transcribe_audio(self, audio_path, language="auto", temperature=0.2, output_dir="transcriptions"):
        """Mock transcribe audio"""
        return MockTranscriptionResult(
            text="Mock transcription result",
            language=language if language != "auto" else "en",
            duration="0:05",
            segments=[],
            speaker_segments=[]
        )


# Global mock instances
mock_file_service = MockFileService()
mock_job_manager = MockJobManager()
mock_transcription_service = MockTranscriptionService()
mock_model_cache = MockModelCache()
mock_request_tracker = MockRequestTracker()


def get_mock_file_service():
    """Get mock file service instance"""
    return mock_file_service


def get_mock_job_manager():
    """Get mock job manager instance"""
    return mock_job_manager


def get_mock_transcription_service():
    """Get mock transcription service instance"""
    return mock_transcription_service


def get_mock_model_cache():
    """Get mock model cache instance"""
    return mock_model_cache


def get_mock_request_tracker():
    """Get mock request tracker instance"""
    return mock_request_tracker


def reset_all_mocks():
    """Reset all mock instances"""
    global mock_file_service, mock_job_manager, mock_transcription_service
    global mock_model_cache, mock_request_tracker
    
    mock_file_service = MockFileService()
    mock_job_manager = MockJobManager()
    mock_transcription_service = MockTranscriptionService()
    mock_model_cache = MockModelCache()
    mock_request_tracker = MockRequestTracker()
