"""
Advanced Storage Management Service
Handles disk space monitoring, cleanup policies, and storage optimization
"""

import os
import shutil
import time
import threading
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

@dataclass
class StorageStats:
    """Storage statistics for monitoring"""
    total_size_mb: float
    total_files: int
    oldest_file_age_hours: float
    newest_file_age_hours: float
    average_file_size_mb: float
    disk_usage_percent: float
    available_space_mb: float

@dataclass
class CleanupPolicy:
    """File cleanup policy configuration"""
    max_age_hours: int = 72  # 3 days
    max_total_size_mb: float = 10000  # 10GB
    max_disk_usage_percent: float = 80.0  # 80%
    cleanup_interval_hours: int = 6  # Every 6 hours
    emergency_cleanup_threshold: float = 90.0  # 90% disk usage
    priority_cleanup_age_hours: int = 24  # Clean files older than 24h first

class StorageManager:
    """Advanced storage management with multiple cleanup policies"""
    
    def __init__(self, base_path: str, policy: Optional[CleanupPolicy] = None):
        self.base_path = Path(base_path)
        self.policy = policy or CleanupPolicy()
        self.stats_file = self.base_path / '.storage_stats.json'
        self.cleanup_log_file = self.base_path / '.cleanup_log.json'
        
        # Ensure base path exists
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Load previous stats
        self.last_stats = self._load_stats()
        
        # Start monitoring thread
        self._start_monitoring_thread()
    
    def _load_stats(self) -> Optional[StorageStats]:
        """Load previous storage statistics"""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    return StorageStats(**data)
        except Exception as e:
            print(f"Warning: Could not load storage stats: {e}")
        return None
    
    def _save_stats(self, stats: StorageStats):
        """Save storage statistics"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump({
                    'total_size_mb': stats.total_size_mb,
                    'total_files': stats.total_files,
                    'oldest_file_age_hours': stats.oldest_file_age_hours,
                    'newest_file_age_hours': stats.newest_file_age_hours,
                    'average_file_size_mb': stats.average_file_size_mb,
                    'disk_usage_percent': stats.disk_usage_percent,
                    'available_space_mb': stats.available_space_mb
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save storage stats: {e}")
    
    def _log_cleanup(self, action: str, details: Dict):
        """Log cleanup actions"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'details': details
            }
            
            # Load existing log
            log_data = []
            if self.cleanup_log_file.exists():
                with open(self.cleanup_log_file, 'r') as f:
                    log_data = json.load(f)
            
            # Add new entry
            log_data.append(log_entry)
            
            # Keep only last 100 entries
            if len(log_data) > 100:
                log_data = log_data[-100:]
            
            # Save log
            with open(self.cleanup_log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not log cleanup action: {e}")
    
    def get_storage_stats(self) -> StorageStats:
        """Get current storage statistics"""
        total_size = 0
        total_files = 0
        file_ages = []
        
        # Walk through all files
        for root, dirs, files in os.walk(self.base_path):
            # Skip hidden files and directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = Path(root) / file
                try:
                    stat = file_path.stat()
                    total_size += stat.st_size
                    total_files += 1
                    
                    # Calculate file age
                    file_age = (time.time() - stat.st_mtime) / 3600  # hours
                    file_ages.append(file_age)
                except OSError:
                    continue
        
        # Calculate statistics
        total_size_mb = total_size / (1024 * 1024)
        oldest_age = max(file_ages) if file_ages else 0
        newest_age = min(file_ages) if file_ages else 0
        average_size = total_size_mb / total_files if total_files > 0 else 0
        
        # Get disk usage
        disk_usage = shutil.disk_usage(self.base_path)
        disk_usage_percent = (disk_usage.used / disk_usage.total) * 100
        available_space_mb = disk_usage.free / (1024 * 1024)
        
        stats = StorageStats(
            total_size_mb=total_size_mb,
            total_files=total_files,
            oldest_file_age_hours=oldest_age,
            newest_file_age_hours=newest_age,
            average_file_size_mb=average_size,
            disk_usage_percent=disk_usage_percent,
            available_space_mb=available_space_mb
        )
        
        # Save stats
        self._save_stats(stats)
        self.last_stats = stats
        
        return stats
    
    def cleanup_by_age(self, max_age_hours: Optional[int] = None) -> Tuple[int, float]:
        """Clean up files older than specified age"""
        max_age = max_age_hours or self.policy.max_age_hours
        cutoff_time = time.time() - (max_age * 3600)
        
        deleted_files = 0
        freed_space_mb = 0
        
        for root, dirs, files in os.walk(self.base_path):
            # Skip hidden files and directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = Path(root) / file
                try:
                    if file_path.stat().st_mtime < cutoff_time:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        deleted_files += 1
                        freed_space_mb += file_size / (1024 * 1024)
                except OSError:
                    continue
        
        if deleted_files > 0:
            self._log_cleanup('age_cleanup', {
                'max_age_hours': max_age,
                'deleted_files': deleted_files,
                'freed_space_mb': freed_space_mb
            })
        
        return deleted_files, freed_space_mb
    
    def cleanup_by_size(self, target_size_mb: float) -> Tuple[int, float]:
        """Clean up files to reduce total size to target"""
        current_stats = self.get_storage_stats()
        
        if current_stats.total_size_mb <= target_size_mb:
            return 0, 0
        
        # Get all files sorted by age (oldest first)
        files_with_age = []
        for root, dirs, files in os.walk(self.base_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file.startswith('.'):
                    continue
                file_path = Path(root) / file
                try:
                    stat = file_path.stat()
                    files_with_age.append((file_path, stat.st_mtime, stat.st_size))
                except OSError:
                    continue
        
        # Sort by age (oldest first)
        files_with_age.sort(key=lambda x: x[1])
        
        deleted_files = 0
        freed_space_mb = 0
        current_size = current_stats.total_size_mb
        
        for file_path, _, file_size in files_with_age:
            if current_size - (file_size / (1024 * 1024)) <= target_size_mb:
                break
            
            try:
                file_path.unlink()
                deleted_files += 1
                freed_space_mb += file_size / (1024 * 1024)
                current_size -= file_size / (1024 * 1024)
            except OSError:
                continue
        
        if deleted_files > 0:
            self._log_cleanup('size_cleanup', {
                'target_size_mb': target_size_mb,
                'deleted_files': deleted_files,
                'freed_space_mb': freed_space_mb
            })
        
        return deleted_files, freed_space_mb
    
    def emergency_cleanup(self) -> Tuple[int, float]:
        """Emergency cleanup when disk usage is too high"""
        current_stats = self.get_storage_stats()
        
        if current_stats.disk_usage_percent < self.policy.emergency_cleanup_threshold:
            return 0, 0
        
        # Aggressive cleanup: remove files older than 24 hours first
        deleted_files, freed_space = self.cleanup_by_age(self.policy.priority_cleanup_age_hours)
        
        # If still over threshold, remove more files
        current_stats = self.get_storage_stats()
        if current_stats.disk_usage_percent >= self.policy.emergency_cleanup_threshold:
            # Remove files older than 6 hours
            more_deleted, more_freed = self.cleanup_by_age(6)
            deleted_files += more_deleted
            freed_space += more_freed
        
        if deleted_files > 0:
            self._log_cleanup('emergency_cleanup', {
                'disk_usage_percent': current_stats.disk_usage_percent,
                'deleted_files': deleted_files,
                'freed_space_mb': freed_space
            })
        
        return deleted_files, freed_space
    
    def smart_cleanup(self) -> Dict[str, any]:
        """Intelligent cleanup based on multiple factors"""
        current_stats = self.get_storage_stats()
        cleanup_results = {
            'age_cleanup': {'deleted_files': 0, 'freed_space_mb': 0},
            'size_cleanup': {'deleted_files': 0, 'freed_space_mb': 0},
            'emergency_cleanup': {'deleted_files': 0, 'freed_space_mb': 0}
        }
        
        # 1. Emergency cleanup if disk usage is too high
        if current_stats.disk_usage_percent >= self.policy.emergency_cleanup_threshold:
            deleted, freed = self.emergency_cleanup()
            cleanup_results['emergency_cleanup'] = {
                'deleted_files': deleted,
                'freed_space_mb': freed
            }
            current_stats = self.get_storage_stats()
        
        # 2. Size-based cleanup if total size exceeds limit
        if current_stats.total_size_mb > self.policy.max_total_size_mb:
            deleted, freed = self.cleanup_by_size(self.policy.max_total_size_mb)
            cleanup_results['size_cleanup'] = {
                'deleted_files': deleted,
                'freed_space_mb': freed
            }
            current_stats = self.get_storage_stats()
        
        # 3. Age-based cleanup for files older than max age
        if current_stats.oldest_file_age_hours > self.policy.max_age_hours:
            deleted, freed = self.cleanup_by_age()
            cleanup_results['age_cleanup'] = {
                'deleted_files': deleted,
                'freed_space_mb': freed
            }
        
        # 4. Disk usage cleanup if still over threshold
        current_stats = self.get_storage_stats()
        if current_stats.disk_usage_percent > self.policy.max_disk_usage_percent:
            deleted, freed = self.cleanup_by_size(
                current_stats.total_size_mb * (self.policy.max_disk_usage_percent / 100)
            )
            cleanup_results['size_cleanup']['deleted_files'] += deleted
            cleanup_results['size_cleanup']['freed_space_mb'] += freed
        
        return cleanup_results
    
    def _start_monitoring_thread(self):
        """Start background monitoring thread"""
        def monitoring_worker():
            while True:
                try:
                    time.sleep(self.policy.cleanup_interval_hours * 3600)
                    self.smart_cleanup()
                except Exception as e:
                    print(f"Storage monitoring error: {e}")
        
        monitoring_thread = threading.Thread(target=monitoring_worker, daemon=True)
        monitoring_thread.start()
    
    def get_cleanup_log(self, limit: int = 50) -> List[Dict]:
        """Get recent cleanup log entries"""
        try:
            if not self.cleanup_log_file.exists():
                return []
            
            with open(self.cleanup_log_file, 'r') as f:
                log_data = json.load(f)
            
            return log_data[-limit:] if limit else log_data
        except Exception as e:
            print(f"Warning: Could not load cleanup log: {e}")
            return []
    
    def get_storage_health(self) -> Dict[str, any]:
        """Get comprehensive storage health information"""
        current_stats = self.get_storage_stats()
        cleanup_log = self.get_cleanup_log(10)
        
        # Determine health status
        health_status = "healthy"
        if current_stats.disk_usage_percent >= self.policy.emergency_cleanup_threshold:
            health_status = "critical"
        elif current_stats.disk_usage_percent >= self.policy.max_disk_usage_percent:
            health_status = "warning"
        elif current_stats.total_size_mb > self.policy.max_total_size_mb:
            health_status = "warning"
        
        return {
            'status': health_status,
            'stats': {
                'total_size_mb': round(current_stats.total_size_mb, 2),
                'total_files': current_stats.total_files,
                'disk_usage_percent': round(current_stats.disk_usage_percent, 2),
                'available_space_mb': round(current_stats.available_space_mb, 2),
                'oldest_file_age_hours': round(current_stats.oldest_file_age_hours, 2),
                'average_file_size_mb': round(current_stats.average_file_size_mb, 2)
            },
            'policy': {
                'max_age_hours': self.policy.max_age_hours,
                'max_total_size_mb': self.policy.max_total_size_mb,
                'max_disk_usage_percent': self.policy.max_disk_usage_percent,
                'emergency_threshold': self.policy.emergency_cleanup_threshold
            },
            'recent_cleanups': cleanup_log
        }
