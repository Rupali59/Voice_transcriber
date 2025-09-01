"""
Request tracking service for monitoring transcription requests
"""

import uuid
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class RequestInfo:
    """Information about a transcription request"""
    request_id: str
    job_id: str
    client_ip: str
    user_agent: str
    filename: str
    file_size_mb: float
    model_size: str
    language: str
    temperature: float
    enable_speaker_diarization: bool
    start_time: str
    end_time: Optional[str] = None
    status: str = 'pending'
    progress: int = 0
    error: Optional[str] = None
    result_file: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None

class RequestTracker:
    """Tracks and monitors transcription requests"""
    
    def __init__(self, log_file: str = "logs/request_tracking.json"):
        self.requests: Dict[str, RequestInfo] = {}
        self.lock = threading.Lock()
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        self._load_requests()
    
    def start_request(self, job_id: str, client_ip: str, user_agent: str, 
                     filename: str, file_size_mb: float, model_size: str,
                     language: str, temperature: float, 
                     enable_speaker_diarization: bool) -> str:
        """Start tracking a new request"""
        request_id = str(uuid.uuid4())
        
        request_info = RequestInfo(
            request_id=request_id,
            job_id=job_id,
            client_ip=client_ip,
            user_agent=user_agent,
            filename=filename,
            file_size_mb=file_size_mb,
            model_size=model_size,
            language=language,
            temperature=temperature,
            enable_speaker_diarization=enable_speaker_diarization,
            start_time=datetime.now().isoformat(),
            status='started'
        )
        
        with self.lock:
            self.requests[request_id] = request_info
            self._save_requests()
        
        return request_id
    
    def update_request_status(self, request_id: str, status: str, 
                            progress: int = None, error: str = None):
        """Update request status"""
        with self.lock:
            if request_id in self.requests:
                request = self.requests[request_id]
                request.status = status
                if progress is not None:
                    request.progress = progress
                if error:
                    request.error = error
                if status in ['completed', 'error', 'cancelled']:
                    request.end_time = datetime.now().isoformat()
                    if request.start_time:
                        start = datetime.fromisoformat(request.start_time)
                        end = datetime.fromisoformat(request.end_time)
                        request.processing_time_seconds = (end - start).total_seconds()
                self._save_requests()
    
    def complete_request(self, request_id: str, result_file: str = None):
        """Mark request as completed"""
        with self.lock:
            if request_id in self.requests:
                request = self.requests[request_id]
                request.status = 'completed'
                request.end_time = datetime.now().isoformat()
                request.result_file = result_file
                if request.start_time:
                    start = datetime.fromisoformat(request.start_time)
                    end = datetime.fromisoformat(request.end_time)
                    request.processing_time_seconds = (end - start).total_seconds()
                self._save_requests()
    
    def get_request(self, request_id: str) -> Optional[RequestInfo]:
        """Get request by ID"""
        with self.lock:
            return self.requests.get(request_id)
    
    def get_requests_by_job_id(self, job_id: str) -> List[RequestInfo]:
        """Get all requests for a specific job"""
        with self.lock:
            return [req for req in self.requests.values() if req.job_id == job_id]
    
    def get_all_requests(self, limit: int = 100, status_filter: str = None) -> List[RequestInfo]:
        """Get all requests with optional filtering"""
        with self.lock:
            requests = list(self.requests.values())
            
            if status_filter:
                requests = [req for req in requests if req.status == status_filter]
            
            # Sort by start time (newest first)
            requests.sort(key=lambda x: x.start_time, reverse=True)
            
            return requests[:limit]
    
    def get_requests_by_client(self, client_ip: str, limit: int = 50) -> List[RequestInfo]:
        """Get requests from a specific client"""
        with self.lock:
            requests = [req for req in self.requests.values() if req.client_ip == client_ip]
            requests.sort(key=lambda x: x.start_time, reverse=True)
            return requests[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get request statistics"""
        with self.lock:
            total_requests = len(self.requests)
            if total_requests == 0:
                return {
                    'total_requests': 0,
                    'active_requests': 0,
                    'completed_requests': 0,
                    'failed_requests': 0,
                    'average_processing_time': 0,
                    'total_processing_time': 0,
                    'requests_by_status': {},
                    'requests_by_model': {},
                    'requests_by_language': {}
                }
            
            active_requests = len([r for r in self.requests.values() if r.status in ['started', 'processing']])
            completed_requests = len([r for r in self.requests.values() if r.status == 'completed'])
            failed_requests = len([r for r in self.requests.values() if r.status == 'error'])
            
            # Calculate processing times
            processing_times = [r.processing_time_seconds for r in self.requests.values() 
                              if r.processing_time_seconds is not None]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            total_processing_time = sum(processing_times)
            
            # Status breakdown
            status_counts = {}
            for request in self.requests.values():
                status_counts[request.status] = status_counts.get(request.status, 0) + 1
            
            # Model breakdown
            model_counts = {}
            for request in self.requests.values():
                model_counts[request.model_size] = model_counts.get(request.model_size, 0) + 1
            
            # Language breakdown
            language_counts = {}
            for request in self.requests.values():
                language_counts[request.language] = language_counts.get(request.language, 0) + 1
            
            return {
                'total_requests': total_requests,
                'active_requests': active_requests,
                'completed_requests': completed_requests,
                'failed_requests': failed_requests,
                'average_processing_time': round(avg_processing_time, 2),
                'total_processing_time': round(total_processing_time, 2),
                'requests_by_status': status_counts,
                'requests_by_model': model_counts,
                'requests_by_language': language_counts
            }
    
    def cleanup_old_requests(self, days: int = 7):
        """Remove requests older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self.lock:
            requests_to_remove = []
            for request_id, request in self.requests.items():
                if request.start_time:
                    start_date = datetime.fromisoformat(request.start_time)
                    if start_date < cutoff_date:
                        requests_to_remove.append(request_id)
            
            for request_id in requests_to_remove:
                del self.requests[request_id]
            
            if requests_to_remove:
                self._save_requests()
                print(f"Cleaned up {len(requests_to_remove)} old requests")
    
    def _save_requests(self):
        """Save requests to file"""
        try:
            requests_data = {
                'requests': {req_id: asdict(req) for req_id, req in self.requests.items()},
                'last_updated': datetime.now().isoformat()
            }
            with open(self.log_file, 'w') as f:
                json.dump(requests_data, f, indent=2)
        except Exception as e:
            print(f"Error saving requests: {e}")
    
    def _load_requests(self):
        """Load requests from file"""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    requests_data = data.get('requests', {})
                    for req_id, req_dict in requests_data.items():
                        self.requests[req_id] = RequestInfo(**req_dict)
                print(f"Loaded {len(self.requests)} requests from file")
        except Exception as e:
            print(f"Error loading requests: {e}")
    
    def export_requests(self, format: str = 'json') -> str:
        """Export requests in specified format"""
        with self.lock:
            if format == 'json':
                return json.dumps({
                    'requests': [asdict(req) for req in self.requests.values()],
                    'exported_at': datetime.now().isoformat(),
                    'total_count': len(self.requests)
                }, indent=2)
            elif format == 'csv':
                import csv
                import io
                output = io.StringIO()
                if self.requests:
                    writer = csv.DictWriter(output, fieldnames=asdict(list(self.requests.values())[0]).keys())
                    writer.writeheader()
                    for req in self.requests.values():
                        writer.writerow(asdict(req))
                return output.getvalue()
            else:
                raise ValueError(f"Unsupported format: {format}")
