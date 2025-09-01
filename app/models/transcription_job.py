"""
Transcription job model
"""

from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class TranscriptionJob:
    """Represents a transcription job"""
    
    job_id: str
    status: str = 'starting'
    progress: int = 0
    filename: str = ''
    original_filename: str = ''
    model_size: str = 'base'
    enable_speaker_diarization: bool = True
    language: str = 'auto'
    start_time: str = ''
    end_time: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    file_size_mb: float = 0.0
    
    def __post_init__(self):
        if not self.start_time:
            self.start_time = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def update_status(self, status: str, progress: int = None, message: str = None):
        """Update job status"""
        self.status = status
        if progress is not None:
            self.progress = progress
        if status == 'completed' or status == 'error':
            self.end_time = datetime.now().isoformat()
    
    def set_result(self, result: Dict[str, Any]):
        """Set transcription result"""
        self.result = result
        self.status = 'completed'
        self.progress = 100
        self.end_time = datetime.now().isoformat()
    
    def set_error(self, error: str):
        """Set error message"""
        self.error = error
        self.status = 'error'
        self.progress = 0
        self.end_time = datetime.now().isoformat()
    
    @property
    def is_completed(self) -> bool:
        """Check if job is completed"""
        return self.status in ['completed', 'error']
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get job duration in seconds"""
        if not self.start_time or not self.end_time:
            return None
        
        start = datetime.fromisoformat(self.start_time)
        end = datetime.fromisoformat(self.end_time)
        return (end - start).total_seconds()
