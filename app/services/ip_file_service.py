"""
IP-based file management service with DoS protection
"""

import os
import time
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading
from collections import defaultdict

from app.models.file_upload import FileUpload
from app.config import Config

@dataclass
class IPQuota:
    """IP-based quota tracking"""
    ip_address: str
    total_files: int
    total_size_mb: float
    last_activity: datetime
    file_count_24h: int
    size_mb_24h: float
    is_blocked: bool
    block_reason: Optional[str] = None
    block_until: Optional[datetime] = None

@dataclass
class IPFileRecord:
    """Record of a file uploaded by an IP"""
    ip_address: str
    filename: str
    original_name: str
    filepath: str
    size_mb: float
    upload_time: datetime
    last_accessed: datetime
    access_count: int = 0

class IPFileService:
    """Manages files by IP address with DoS protection"""
    
    def __init__(self, base_upload_folder: str, allowed_extensions: set):
        self.base_upload_folder = base_upload_folder
        self.allowed_extensions = allowed_extensions
        self.quota_file = os.path.join(base_upload_folder, '.ip_quotas.json')
        self.files_file = os.path.join(base_upload_folder, '.ip_files.json')
        
        # DoS protection settings
        self.max_files_per_ip = int(os.environ.get('MAX_FILES_PER_IP', 50))
        self.max_size_mb_per_ip = float(os.environ.get('MAX_SIZE_MB_PER_IP', 1000))  # 1GB
        self.max_files_24h_per_ip = int(os.environ.get('MAX_FILES_24H_PER_IP', 20))
        self.max_size_24h_mb_per_ip = float(os.environ.get('MAX_SIZE_24H_MB_PER_IP', 500))  # 500MB
        self.rate_limit_window = int(os.environ.get('RATE_LIMIT_WINDOW_SECONDS', 3600))  # 1 hour
        self.max_requests_per_window = int(os.environ.get('MAX_REQUESTS_PER_WINDOW', 100))
        
        # Cleanup settings
        self.cleanup_interval_hours = int(os.environ.get('IP_CLEANUP_INTERVAL_HOURS', 24))
        self.file_retention_hours = int(os.environ.get('IP_FILE_RETENTION_HOURS', 72))  # 3 days
        
        # In-memory tracking for rate limiting
        self.request_counts = defaultdict(list)  # IP -> list of timestamps
        self.lock = threading.Lock()
        
        # Load existing data
        self.ip_quotas: Dict[str, IPQuota] = {}
        self.ip_files: Dict[str, List[IPFileRecord]] = defaultdict(list)
        self._load_data()
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def _load_data(self):
        """Load IP quotas and file records from disk"""
        try:
            # Load quotas
            if os.path.exists(self.quota_file):
                with open(self.quota_file, 'r') as f:
                    data = json.load(f)
                    for ip, quota_data in data.items():
                        quota_data['last_activity'] = datetime.fromisoformat(quota_data['last_activity'])
                        if quota_data.get('block_until'):
                            quota_data['block_until'] = datetime.fromisoformat(quota_data['block_until'])
                        self.ip_quotas[ip] = IPQuota(**quota_data)
            
            # Load file records
            if os.path.exists(self.files_file):
                with open(self.files_file, 'r') as f:
                    data = json.load(f)
                    for ip, files_data in data.items():
                        for file_data in files_data:
                            file_data['upload_time'] = datetime.fromisoformat(file_data['upload_time'])
                            file_data['last_accessed'] = datetime.fromisoformat(file_data['last_accessed'])
                            self.ip_files[ip].append(IPFileRecord(**file_data))
        except Exception as e:
            print(f"Warning: Could not load IP data: {e}")
    
    def _save_data(self):
        """Save IP quotas and file records to disk"""
        try:
            # Save quotas
            quota_data = {}
            for ip, quota in self.ip_quotas.items():
                quota_dict = asdict(quota)
                quota_dict['last_activity'] = quota.last_activity.isoformat()
                if quota.block_until:
                    quota_dict['block_until'] = quota.block_until.isoformat()
                quota_data[ip] = quota_dict
            
            with open(self.quota_file, 'w') as f:
                json.dump(quota_data, f, indent=2)
            
            # Save file records
            files_data = {}
            for ip, files in self.ip_files.items():
                files_list = []
                for file_record in files:
                    file_dict = asdict(file_record)
                    file_dict['upload_time'] = file_record.upload_time.isoformat()
                    file_dict['last_accessed'] = file_record.last_accessed.isoformat()
                    files_list.append(file_dict)
                files_data[ip] = files_list
            
            with open(self.files_file, 'w') as f:
                json.dump(files_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save IP data: {e}")
    
    def _get_ip_folder(self, ip_address: str) -> str:
        """Get the folder path for an IP address"""
        # Hash IP for security and folder structure
        ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:16]
        ip_folder = os.path.join(self.base_upload_folder, f"ip_{ip_hash}")
        os.makedirs(ip_folder, exist_ok=True)
        return ip_folder
    
    def _check_rate_limit(self, ip_address: str) -> Tuple[bool, str]:
        """Check if IP is within rate limits"""
        with self.lock:
            now = time.time()
            window_start = now - self.rate_limit_window
            
            # Clean old requests
            self.request_counts[ip_address] = [
                req_time for req_time in self.request_counts[ip_address]
                if req_time > window_start
            ]
            
            # Check if within limits
            if len(self.request_counts[ip_address]) >= self.max_requests_per_window:
                return False, f"Rate limit exceeded. Max {self.max_requests_per_window} requests per {self.rate_limit_window//3600} hours"
            
            # Add current request
            self.request_counts[ip_address].append(now)
            return True, ""
    
    def _check_quota(self, ip_address: str, file_size_mb: float) -> Tuple[bool, str]:
        """Check if IP is within quota limits"""
        now = datetime.now()
        quota = self.ip_quotas.get(ip_address)
        
        if not quota:
            # Create new quota
            quota = IPQuota(
                ip_address=ip_address,
                total_files=0,
                total_size_mb=0.0,
                last_activity=now,
                file_count_24h=0,
                size_mb_24h=0.0,
                is_blocked=False
            )
            self.ip_quotas[ip_address] = quota
        
        # Check if IP is blocked
        if quota.is_blocked:
            if quota.block_until and now < quota.block_until:
                return False, f"IP blocked until {quota.block_until}: {quota.block_reason}"
            else:
                # Unblock if time has passed
                quota.is_blocked = False
                quota.block_reason = None
                quota.block_until = None
        
        # Reset 24h counters if needed
        if now - quota.last_activity > timedelta(hours=24):
            quota.file_count_24h = 0
            quota.size_mb_24h = 0.0
        
        # Check limits
        if quota.total_files >= self.max_files_per_ip:
            return False, f"Maximum files per IP exceeded ({self.max_files_per_ip})"
        
        if quota.total_size_mb + file_size_mb > self.max_size_mb_per_ip:
            return False, f"Maximum storage per IP exceeded ({self.max_size_mb_per_ip}MB)"
        
        if quota.file_count_24h >= self.max_files_24h_per_ip:
            return False, f"Maximum files per 24h exceeded ({self.max_files_24h_per_ip})"
        
        if quota.size_mb_24h + file_size_mb > self.max_size_24h_mb_per_ip:
            return False, f"Maximum storage per 24h exceeded ({self.max_size_24h_mb_per_ip}MB)"
        
        return True, ""
    
    def _update_quota(self, ip_address: str, file_size_mb: float):
        """Update quota after successful file upload"""
        quota = self.ip_quotas[ip_address]
        quota.total_files += 1
        quota.total_size_mb += file_size_mb
        quota.file_count_24h += 1
        quota.size_mb_24h += file_size_mb
        quota.last_activity = datetime.now()
    
    def _block_ip(self, ip_address: str, reason: str, hours: int = 24):
        """Block an IP address"""
        quota = self.ip_quotas.get(ip_address)
        if quota:
            quota.is_blocked = True
            quota.block_reason = reason
            quota.block_until = datetime.now() + timedelta(hours=hours)
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def generate_unique_filename(self, original_filename: str, ip_address: str) -> str:
        """Generate unique filename for IP"""
        from werkzeug.utils import secure_filename
        filename = secure_filename(original_filename)
        timestamp = int(time.time())
        ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:8]
        return f"{timestamp}_{ip_hash}_{filename}"
    
    def save_uploaded_file(self, file, max_size_bytes: int, ip_address: str) -> FileUpload:
        """Save uploaded file with IP tracking and DoS protection"""
        # Check rate limiting
        rate_ok, rate_msg = self._check_rate_limit(ip_address)
        if not rate_ok:
            raise ValueError(f"Rate limit exceeded: {rate_msg}")
        
        if not file or file.filename == '':
            raise ValueError("No file provided")
        
        if not self.is_allowed_file(file.filename):
            raise ValueError(f"Invalid file type. Allowed: {', '.join(self.allowed_extensions)}")
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > max_size_bytes:
            raise ValueError(f"File too large. Maximum size: {max_size_bytes / (1024*1024):.0f}MB")
        
        file_size_mb = file_size / (1024 * 1024)
        
        # Check quota
        quota_ok, quota_msg = self._check_quota(ip_address, file_size_mb)
        if not quota_ok:
            # Block IP if they're trying to exceed limits
            if "exceeded" in quota_msg:
                self._block_ip(ip_address, f"Quota violation: {quota_msg}", hours=24)
            raise ValueError(f"Quota exceeded: {quota_msg}")
        
        # Get IP-specific folder
        ip_folder = self._get_ip_folder(ip_address)
        
        # Generate unique filename
        unique_filename = self.generate_unique_filename(file.filename, ip_address)
        filepath = os.path.join(ip_folder, unique_filename)
        
        # Save file
        file.save(filepath)
        
        # Create FileUpload object
        file_upload = FileUpload(
            filename=unique_filename,
            original_name=file.filename,
            filepath=filepath,
            size_bytes=file_size
        )
        
        # Update quota
        self._update_quota(ip_address, file_size_mb)
        
        # Record file
        file_record = IPFileRecord(
            ip_address=ip_address,
            filename=unique_filename,
            original_name=file.filename,
            filepath=filepath,
            size_mb=file_size_mb,
            upload_time=datetime.now(),
            last_accessed=datetime.now()
        )
        self.ip_files[ip_address].append(file_record)
        
        # Save data
        self._save_data()
        
        return file_upload
    
    def get_files_by_ip(self, ip_address: str) -> List[IPFileRecord]:
        """Get all files uploaded by an IP address"""
        files = self.ip_files.get(ip_address, [])
        # Update last accessed time
        for file_record in files:
            file_record.last_accessed = datetime.now()
            file_record.access_count += 1
        self._save_data()
        return files
    
    def get_file_by_ip_and_name(self, ip_address: str, filename: str) -> Optional[IPFileRecord]:
        """Get a specific file by IP and filename"""
        files = self.ip_files.get(ip_address, [])
        for file_record in files:
            if file_record.filename == filename:
                file_record.last_accessed = datetime.now()
                file_record.access_count += 1
                self._save_data()
                return file_record
        return None
    
    def delete_file_by_ip(self, ip_address: str, filename: str) -> bool:
        """Delete a file and update quota"""
        files = self.ip_files.get(ip_address, [])
        for i, file_record in enumerate(files):
            if file_record.filename == filename:
                # Delete physical file
                try:
                    if os.path.exists(file_record.filepath):
                        os.remove(file_record.filepath)
                except OSError:
                    pass
                
                # Update quota
                quota = self.ip_quotas.get(ip_address)
                if quota:
                    quota.total_files -= 1
                    quota.total_size_mb -= file_record.size_mb
                
                # Remove from records
                files.pop(i)
                self._save_data()
                return True
        return False
    
    def get_ip_quota(self, ip_address: str) -> Optional[IPQuota]:
        """Get quota information for an IP"""
        return self.ip_quotas.get(ip_address)
    
    def get_ip_stats(self, ip_address: str) -> Dict:
        """Get comprehensive stats for an IP"""
        quota = self.ip_quotas.get(ip_address)
        files = self.ip_files.get(ip_address, [])
        
        return {
            'ip_address': ip_address,
            'quota': asdict(quota) if quota else None,
            'file_count': len(files),
            'total_size_mb': sum(f.size_mb for f in files),
            'files': [asdict(f) for f in files],
            'limits': {
                'max_files_per_ip': self.max_files_per_ip,
                'max_size_mb_per_ip': self.max_size_mb_per_ip,
                'max_files_24h_per_ip': self.max_files_24h_per_ip,
                'max_size_24h_mb_per_ip': self.max_size_24h_mb_per_ip,
                'max_requests_per_window': self.max_requests_per_window,
                'rate_limit_window_hours': self.rate_limit_window // 3600
            }
        }
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(self.cleanup_interval_hours * 3600)
                    self._cleanup_old_files()
                except Exception as e:
                    print(f"Cleanup error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_old_files(self):
        """Clean up old files and reset quotas"""
        cutoff_time = datetime.now() - timedelta(hours=self.file_retention_hours)
        
        for ip_address in list(self.ip_files.keys()):
            files = self.ip_files[ip_address]
            files_to_remove = []
            
            for file_record in files:
                if file_record.upload_time < cutoff_time:
                    # Delete physical file
                    try:
                        if os.path.exists(file_record.filepath):
                            os.remove(file_record.filepath)
                    except OSError:
                        pass
                    files_to_remove.append(file_record)
            
            # Remove from records
            for file_record in files_to_remove:
                files.remove(file_record)
            
            # Update quota
            quota = self.ip_quotas.get(ip_address)
            if quota:
                quota.total_files = len(files)
                quota.total_size_mb = sum(f.size_mb for f in files)
        
        # Remove empty IP entries
        empty_ips = [ip for ip, files in self.ip_files.items() if not files]
        for ip in empty_ips:
            del self.ip_files[ip]
            if ip in self.ip_quotas:
                del self.ip_quotas[ip]
        
        self._save_data()
        print(f"Cleanup completed. Removed files older than {self.file_retention_hours} hours.")
    
    def cleanup_ip_files(self, ip_address: str) -> int:
        """Manually cleanup all files for an IP"""
        files = self.ip_files.get(ip_address, [])
        deleted_count = 0
        
        for file_record in files:
            try:
                if os.path.exists(file_record.filepath):
                    os.remove(file_record.filepath)
                    deleted_count += 1
            except OSError:
                pass
        
        # Clear records
        self.ip_files[ip_address] = []
        quota = self.ip_quotas.get(ip_address)
        if quota:
            quota.total_files = 0
            quota.total_size_mb = 0.0
        
        self._save_data()
        return deleted_count
