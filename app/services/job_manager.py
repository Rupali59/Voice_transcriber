"""
Job management service for handling transcription jobs
"""

import threading
import time
from typing import Dict, Optional
from datetime import datetime, timedelta

from app.models.transcription_job import TranscriptionJob

class JobManager:
    """Manages transcription jobs"""
    
    def __init__(self, max_concurrent_jobs: int = 5, cleanup_hours: int = 1):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.cleanup_hours = cleanup_hours
        self.jobs: Dict[str, TranscriptionJob] = {}
        self.lock = threading.Lock()
        self._start_cleanup_thread()
    
    def create_job(self, job_id: str, filename: str, original_filename: str, 
                   model_size: str, enable_speaker_diarization: bool, 
                   language: str, file_size_mb: float) -> TranscriptionJob:
        """Create a new transcription job"""
        with self.lock:
            if len(self.jobs) >= self.max_concurrent_jobs:
                raise Exception(f"Too many transcription jobs running. Maximum: {self.max_concurrent_jobs}")
            
            job = TranscriptionJob(
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
    
    def get_job(self, job_id: str) -> Optional[TranscriptionJob]:
        """Get a job by ID"""
        with self.lock:
            return self.jobs.get(job_id)
    
    def update_job_status(self, job_id: str, status: str, progress: int = None, message: str = None):
        """Update job status"""
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                job.update_status(status, progress, message)
    
    def set_job_result(self, job_id: str, result: dict):
        """Set job result"""
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                job.set_result(result)
    
    def set_job_error(self, job_id: str, error: str):
        """Set job error"""
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                job.set_error(error)
    
    def remove_job(self, job_id: str):
        """Remove a job"""
        with self.lock:
            self.jobs.pop(job_id, None)
    
    def get_active_jobs_count(self) -> int:
        """Get count of active jobs"""
        with self.lock:
            return len([job for job in self.jobs.values() if not job.is_completed])
    
    def get_all_jobs(self) -> Dict[str, TranscriptionJob]:
        """Get all jobs"""
        with self.lock:
            return self.jobs.copy()
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_loop():
            while True:
                try:
                    self._cleanup_old_jobs()
                    time.sleep(3600)  # Run cleanup every hour
                except Exception as e:
                    print(f"Job cleanup error: {e}")
                    time.sleep(3600)
        
        cleanup_thread = threading.Thread(target=cleanup_loop)
        cleanup_thread.daemon = True
        cleanup_thread.start()
    
    def _cleanup_old_jobs(self):
        """Clean up old completed jobs"""
        cutoff_time = datetime.now() - timedelta(hours=self.cleanup_hours)
        
        with self.lock:
            jobs_to_remove = []
            for job_id, job in self.jobs.items():
                if job.is_completed and job.end_time:
                    end_time = datetime.fromisoformat(job.end_time)
                    if end_time < cutoff_time:
                        jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self.jobs[job_id]
