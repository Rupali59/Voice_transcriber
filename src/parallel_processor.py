"""
Parallel Processor for Voice Transcriber
Handles concurrent transcription of multiple audio files with optimized resource management
"""

import os
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from queue import Queue, Empty
import threading
from collections import defaultdict

from config_manager import ConfigManager
from unified_voice_transcriber import UnifiedVoiceTranscriber

logger = logging.getLogger(__name__)

@dataclass
class ProcessingJob:
    """Represents a single audio file processing job"""
    file_path: str
    priority: int = 0
    created_at: float = None
    estimated_duration: Optional[float] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
    
    def __lt__(self, other):
        """Priority queue ordering (higher priority first)"""
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.created_at < other.created_at

@dataclass
class ProcessingResult:
    """Result of a processing job"""
    file_path: str
    success: bool
    transcription: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0

class ParallelProcessor:
    """Parallel processor for multiple audio files with intelligent resource management"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.job_queue = Queue()
        self.results = {}
        self.stats = {
            'jobs_submitted': 0,
            'jobs_completed': 0,
            'jobs_failed': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0,
            'peak_cpu_usage': 0.0,
            'peak_memory_usage': 0.0
        }
        
        # Resource management
        self.max_concurrent = config.performance.max_concurrent_processes
        self.batch_size = config.performance.batch_size
        self.active_jobs = 0
        self.resource_lock = threading.Lock()
        
        # Performance tracking
        self.cpu_history = []
        self.memory_history = []
        self.throughput_history = []
        
        # Initialize transcriber pool
        self.transcriber_pool = self._create_transcriber_pool()
        
        # Start monitoring thread
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._resource_monitor, daemon=True)
        self.monitor_thread.start()
    
    def _create_transcriber_pool(self) -> List[UnifiedVoiceTranscriber]:
        """Create a pool of transcribers for parallel processing"""
        pool = []
        for i in range(self.max_concurrent):
            transcriber = UnifiedVoiceTranscriber(
                model_size=self.config.transcription.whisper_model_size,
                enable_speaker_diarization=self.config.transcription.enable_speaker_diarization
            )
            pool.append(transcriber)
            logger.info(f"Created transcriber {i+1}/{self.max_concurrent}")
        return pool
    
    def add_job(self, file_path: str, priority: int = 0) -> bool:
        """Add a new processing job to the queue"""
        try:
            job = ProcessingJob(file_path, priority)
            self.job_queue.put(job)
            self.stats['jobs_submitted'] += 1
            logger.info(f"Added job: {file_path} (priority: {priority})")
            return True
        except Exception as e:
            logger.error(f"Failed to add job {file_path}: {e}")
            return False
    
    def add_batch(self, file_paths: List[str], priority: int = 0) -> int:
        """Add multiple files as a batch"""
        added_count = 0
        for file_path in file_paths:
            if self.add_job(file_path, priority):
                added_count += 1
        logger.info(f"Added batch of {added_count}/{len(file_paths)} files")
        return added_count
    
    def process_jobs(self, max_jobs: Optional[int] = None) -> Dict[str, ProcessingResult]:
        """Process all jobs in the queue with parallel execution"""
        if self.job_queue.empty():
            logger.info("No jobs to process")
            return {}
        
        # Determine number of jobs to process
        if max_jobs is None:
            max_jobs = self.job_queue.qsize()
        
        jobs_to_process = []
        for _ in range(min(max_jobs, self.job_queue.qsize())):
            try:
                job = self.job_queue.get_nowait()
                jobs_to_process.append(job)
            except Empty:
                break
        
        if not jobs_to_process:
            return {}
        
        logger.info(f"Processing {len(jobs_to_process)} jobs with {self.max_concurrent} workers")
        
        # Process jobs in parallel
        results = {}
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            # Submit jobs
            future_to_job = {}
            for job in jobs_to_process:
                future = executor.submit(self._process_single_job, job)
                future_to_job[future] = job
            
            # Collect results
            for future in as_completed(future_to_job):
                job = future_to_job[future]
                try:
                    result = future.result()
                    results[job.file_path] = result
                    
                    # Update statistics
                    self._update_stats(result)
                    
                    if result.success:
                        logger.info(f"Completed: {job.file_path}")
                    else:
                        logger.error(f"Failed: {job.file_path} - {result.error}")
                        
                except Exception as e:
                    logger.error(f"Job {job.file_path} failed with exception: {e}")
                    results[job.file_path] = ProcessingResult(
                        file_path=job.file_path,
                        success=False,
                        error=str(e),
                        processing_time=0.0
                    )
        
        total_time = time.time() - start_time
        logger.info(f"Batch processing completed in {total_time:.2f}s")
        
        return results
    
    def _process_single_job(self, job: ProcessingJob) -> ProcessingResult:
        """Process a single job with resource tracking"""
        start_time = time.time()
        start_cpu = self._get_cpu_usage()
        start_memory = self._get_memory_usage()
        
        try:
            # Get available transcriber from pool
            transcriber = self._get_available_transcriber()
            
            # Process the file
            transcription = transcriber.transcribe_audio(job.file_path)
            
            processing_time = time.time() - start_time
            end_cpu = self._get_cpu_usage()
            end_memory = self._get_memory_usage()
            
            # Calculate resource usage
            cpu_usage = (start_cpu + end_cpu) / 2
            memory_usage = (start_memory + end_memory) / 2
            
            # Save transcription
            if transcription:
                self._save_transcription(job.file_path, transcription)
            
            return ProcessingResult(
                file_path=job.file_path,
                success=True,
                transcription=transcription,
                processing_time=processing_time,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing {job.file_path}: {e}")
            
            return ProcessingResult(
                file_path=job.file_path,
                success=False,
                error=str(e),
                processing_time=processing_time,
                cpu_usage=0.0,
                memory_usage=0.0
            )
    
    def _get_available_transcriber(self) -> UnifiedVoiceTranscriber:
        """Get an available transcriber from the pool"""
        # Simple round-robin for now, could be enhanced with load balancing
        return self.transcriber_pool[0]  # All transcribers are stateless
    
    def _save_transcription(self, file_path: str, transcription: Dict[str, Any]):
        """Save transcription to output directory"""
        try:
            input_file = Path(file_path)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_filename = f"{input_file.stem}_transcription_{timestamp}.md"
            output_path = Path(self.config.output.base_dir) / output_filename
            
            # Generate content
            content = self._generate_output_content(file_path, transcription)
            
            # Write file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Transcription saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving transcription: {e}")
    
    def _generate_output_content(self, file_path: str, transcription: Dict[str, Any]) -> str:
        """Generate markdown output content"""
        input_file = Path(file_path)
        
        lines = [
            f"# {input_file.stem} - Voice Memo Transcription",
            "",
            f"**File:** {input_file.name}",
            f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Language:** {transcription.get('language', 'Unknown')}",
            f"**Duration:** {transcription.get('duration', 'Unknown')}",
            f"**Model Used:** Whisper {self.config.transcription.whisper_model_size}",
            f"**Processing Mode:** Parallel (Batch)",
            "",
            "## Transcription",
            "",
            transcription.get('text', 'No transcription available')
        ]
        
        # Add speaker analysis if available
        if (self.config.output.include_speakers and
            transcription.get('speaker_segments')):
            lines.extend([
                "",
                "## Speaker Analysis",
                ""
            ])
            
            for i, segment in enumerate(transcription.get('speaker_segments', [])):
                lines.extend([
                    f"**Speaker {segment.get('speaker', i)}** "
                    f"({segment.get('start_time', 'Unknown')} - "
                    f"({segment.get('end_time', 'Unknown')})",
                    f"{segment.get('text', '')}",
                    ""
                ])
        
        return "\n".join(lines)
    
    def _update_stats(self, result: ProcessingResult):
        """Update processing statistics"""
        with self.resource_lock:
            if result.success:
                self.stats['jobs_completed'] += 1
                self.stats['total_processing_time'] += result.processing_time
                
                # Update averages
                if self.stats['jobs_completed'] > 0:
                    self.stats['average_processing_time'] = (
                        self.stats['total_processing_time'] / self.stats['jobs_completed']
                    )
                
                # Track peak resource usage
                self.stats['peak_cpu_usage'] = max(
                    self.stats['peak_cpu_usage'], 
                    result.cpu_usage
                )
                self.stats['peak_memory_usage'] = max(
                    self.stats['peak_memory_usage'], 
                    result.memory_usage
                )
            else:
                self.stats['jobs_failed'] += 1
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            return 0.0
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage"""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except ImportError:
            return 0.0
    
    def _resource_monitor(self):
        """Monitor system resources during processing"""
        while self.monitoring:
            try:
                cpu_usage = self._get_cpu_usage()
                memory_usage = self._get_memory_usage()
                
                self.cpu_history.append(cpu_usage)
                self.memory_history.append(memory_usage)
                
                # Keep only last 100 measurements
                if len(self.cpu_history) > 100:
                    self.cpu_history.pop(0)
                if len(self.memory_history) > 100:
                    self.memory_history.pop(0)
                
                time.sleep(5)  # Monitor every 5 seconds
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                time.sleep(10)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        with self.resource_lock:
            stats = self.stats.copy()
            
            # Add current queue status
            stats['queue_size'] = self.job_queue.qsize()
            stats['active_jobs'] = self.active_jobs
            
            # Add resource history
            if self.cpu_history:
                stats['current_cpu'] = self.cpu_history[-1]
                stats['average_cpu'] = sum(self.cpu_history) / len(self.cpu_history)
            if self.memory_history:
                stats['current_memory'] = self.memory_history[-1]
                stats['average_memory'] = sum(self.memory_history) / len(self.memory_history)
            
            return stats
    
    def print_stats(self):
        """Print current statistics in a human-readable format"""
        stats = self.get_stats()
        
        print("🚀 Parallel Processor Statistics")
        print("=" * 40)
        print(f"📊 Jobs: {stats['jobs_completed']}/{stats['jobs_submitted']} completed")
        print(f"❌ Failed: {stats['jobs_failed']}")
        print(f"📋 Queue: {stats['queue_size']} pending")
        print(f"⚡ Active: {stats['active_jobs']} running")
        print("")
        print(f"⏱️  Average Time: {stats['average_processing_time']:.2f}s")
        print(f"🔥 Peak CPU: {stats['peak_cpu_usage']:.1f}%")
        print(f"🧠 Peak Memory: {stats['peak_memory_usage']:.1f}%")
        print("")
        print(f"💻 Current CPU: {stats.get('current_cpu', 0):.1f}%")
        print(f"💾 Current Memory: {stats.get('current_memory', 0):.1f}%")
        print(f"📈 Average CPU: {stats.get('average_cpu', 0):.1f}%")
        print(f"📊 Average Memory: {stats.get('average_memory', 0):.1f}%")
    
    def stop(self):
        """Stop the parallel processor"""
        self.monitoring = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("Parallel processor stopped")
