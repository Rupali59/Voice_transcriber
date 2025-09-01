"""
Background Processor for Voice Transcriber
Handles file monitoring, queuing, and background transcription
"""

import time
import threading
import queue
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

from config_manager import ConfigManager
from unified_voice_transcriber import UnifiedVoiceTranscriber

logger = logging.getLogger(__name__)

class AudioFileHandler(FileSystemEventHandler):
    """Handles file system events for audio files"""
    
    def __init__(self, processor: 'BackgroundProcessor'):
        self.processor = processor
        self.processed_files = set()
    
    def on_created(self, event):
        if not event.is_directory and self._is_audio_file(event.src_path):
            self._handle_new_file(event.src_path)
    
    def on_moved(self, event):
        if not event.is_directory and self._is_audio_file(event.dest_path):
            self._handle_new_file(event.dest_path)
    
    def _is_audio_file(self, file_path: str) -> bool:
        """Check if file is an audio file based on patterns"""
        file_path = Path(file_path)
        return any(file_path.match(pattern) for pattern in self.processor.config.input.file_patterns)
    
    def _handle_new_file(self, file_path: str):
        """Handle new audio file detection"""
        if file_path not in self.processed_files:
            logger.info(f"New audio file detected: {file_path}")
            self.processor.add_to_queue(file_path)
            self.processed_files.add(file_path)

class BackgroundProcessor:
    """Background processor for continuous audio file monitoring and transcription"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.transcriber = UnifiedVoiceTranscriber(
            model_size=config.transcription.whisper_model_size,
            enable_speaker_diarization=config.transcription.enable_speaker_diarization
        )
        
        # Processing queue
        self.processing_queue = queue.Queue(maxsize=config.performance.processing_queue_size)
        self.processing_results = {}
        
        # Threading
        self.observer = None
        self.processing_thread = None
        self.running = False
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'files_failed': 0,
            'total_processing_time': 0,
            'current_queue_size': 0
        }
    
    def start(self):
        """Start background processing"""
        if self.running:
            logger.warning("Background processor is already running")
            return
        
        logger.info("Starting background processor...")
        self.running = True
        
        # Start file monitoring
        self._start_file_monitoring()
        
        # Start processing thread
        self._start_processing_thread()
        
        logger.info("Background processor started successfully")
    
    def stop(self):
        """Stop background processing"""
        if not self.running:
            return
        
        logger.info("Stopping background processor...")
        self.running = False
        
        # Stop file monitoring
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        # Stop processing thread
        if self.processing_thread:
            self.processing_thread.join()
        
        logger.info("Background processor stopped")
    
    def _start_file_monitoring(self):
        """Start monitoring input directories for new files"""
        self.observer = Observer()
        
        for watch_dir in self.config.input.watch_dirs:
            if os.path.exists(watch_dir):
                handler = AudioFileHandler(self)
                self.observer.schedule(handler, watch_dir, recursive=True)
                logger.info(f"Monitoring directory: {watch_dir}")
            else:
                logger.warning(f"Watch directory does not exist: {watch_dir}")
        
        self.observer.start()
    
    def _start_processing_thread(self):
        """Start the main processing thread"""
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
    
    def _processing_loop(self):
        """Main processing loop"""
        with ThreadPoolExecutor(max_workers=self.config.performance.max_concurrent_processes) as executor:
            while self.running:
                try:
                    # Get file from queue with timeout
                    try:
                        file_path = self.processing_queue.get(timeout=1)
                        self.stats['current_queue_size'] = self.processing_queue.qsize()
                    except queue.Empty:
                        continue
                    
                    # Submit for processing
                    future = executor.submit(self._process_file, file_path)
                    future.add_done_callback(self._on_processing_complete)
                    
                except Exception as e:
                    logger.error(f"Error in processing loop: {e}")
                    time.sleep(1)
    
    def _process_file(self, file_path: str) -> Dict[str, Any]:
        """Process a single audio file"""
        start_time = time.time()
        result = {
            'file_path': file_path,
            'status': 'processing',
            'start_time': start_time,
            'error': None
        }
        
        try:
            logger.info(f"Processing file: {file_path}")
            
            # Check if file still exists
            if not os.path.exists(file_path):
                result['status'] = 'skipped'
                result['error'] = 'File no longer exists'
                return result
            
            # Wait for file to be fully written
            self._wait_for_file_ready(file_path)
            
            # Process with transcription
            transcription_result = self.transcriber.transcribe_audio(file_path)
            
            if transcription_result:
                result['status'] = 'completed'
                result['transcription'] = transcription_result
                result['processing_time'] = time.time() - start_time
                
                # Save transcription
                self._save_transcription(file_path, transcription_result)
                
                logger.info(f"Successfully processed: {file_path}")
            else:
                result['status'] = 'failed'
                result['error'] = 'Transcription returned no result'
                logger.error(f"Transcription failed for: {file_path}")
        
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            result['processing_time'] = time.time() - start_time
            logger.error(f"Error processing {file_path}: {e}")
        
        return result
    
    def _wait_for_file_ready(self, file_path: str, timeout: int = 30):
        """Wait for file to be fully written"""
        start_time = time.time()
        last_size = -1
        
        while time.time() - start_time < timeout:
            try:
                current_size = os.path.getsize(file_path)
                if current_size == last_size and current_size > 0:
                    # File size hasn't changed, likely fully written
                    break
                last_size = current_size
                time.sleep(0.5)
            except OSError:
                time.sleep(0.5)
    
    def _save_transcription(self, file_path: str, transcription_result: Dict[str, Any]):
        """Save transcription to output directory"""
        try:
            # Create output filename
            input_file = Path(file_path)
            output_filename = f"{input_file.stem}_transcription.md"
            output_path = Path(self.config.output.base_dir) / output_filename
            
            # Generate content
            content = self._generate_output_content(file_path, transcription_result)
            
            # Write file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Transcription saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving transcription: {e}")
    
    def _generate_output_content(self, file_path: str, transcription_result: Dict[str, Any]) -> str:
        """Generate markdown output content"""
        input_file = Path(file_path)
        
        lines = [
            f"# {input_file.stem} - Voice Memo Transcription",
            "",
            f"**File:** {input_file.name}",
            f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Language:** {transcription_result.get('language', 'Unknown')}",
            f"**Duration:** {transcription_result.get('duration', 'Unknown')}",
            f"**Model Used:** Whisper {self.config.transcription.whisper_model_size}",
            "",
            "## Transcription",
            "",
            transcription_result.get('text', 'No transcription available')
        ]
        
        # Add speaker analysis if enabled and available
        if (self.config.output.include_speakers and 
            transcription_result.get('speaker_segments')):
            lines.extend([
                "",
                "## Speaker Analysis",
                ""
            ])
            
            for i, segment in enumerate(transcription_result.get('speaker_segments', [])):
                lines.extend([
                    f"**Speaker {segment.get('speaker', i)}** "
                    f"({segment.get('start_time', 'Unknown')} - "
                    f"{segment.get('end_time', 'Unknown')})",
                    f"{segment.get('text', '')}",
                    ""
                ])
        
        return "\n".join(lines)
    
    def _on_processing_complete(self, future):
        """Callback when processing completes"""
        try:
            result = future.result()
            self.processing_results[result['file_path']] = result
            
            # Update statistics
            if result['status'] == 'completed':
                self.stats['files_processed'] += 1
                self.stats['total_processing_time'] += result.get('processing_time', 0)
            else:
                self.stats['files_failed'] += 1
            
            logger.info(f"Processing completed for {result['file_path']}: {result['status']}")
            
        except Exception as e:
            logger.error(f"Error in processing completion callback: {e}")
    
    def add_to_queue(self, file_path: str):
        """Add file to processing queue"""
        try:
            self.processing_queue.put(file_path, timeout=5)
            logger.info(f"Added to queue: {file_path}")
        except queue.Full:
            logger.warning(f"Processing queue is full, skipping: {file_path}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        stats = self.stats.copy()
        stats['current_queue_size'] = self.processing_queue.qsize()
        stats['running'] = self.running
        
        if stats['files_processed'] > 0:
            stats['average_processing_time'] = (
                stats['total_processing_time'] / stats['files_processed']
            )
        else:
            stats['average_processing_time'] = 0
        
        return stats
    
    def print_stats(self):
        """Print current statistics"""
        stats = self.get_stats()
        
        print("📊 Background Processor Statistics")
        print("=" * 40)
        print(f"Status: {'🟢 Running' if stats['running'] else '🔴 Stopped'}")
        print(f"Files Processed: {stats['files_processed']}")
        print(f"Files Failed: {stats['files_failed']}")
        print(f"Current Queue: {stats['current_queue_size']}")
        print(f"Average Time: {stats['average_processing_time']:.2f}s")
        print(f"Total Time: {stats['total_processing_time']:.2f}s")
    
    def process_existing_files(self):
        """Process existing files in monitored directories"""
        logger.info("Processing existing files in monitored directories...")
        
        for watch_dir in self.config.input.watch_dirs:
            if os.path.exists(watch_dir):
                self._scan_directory_for_files(watch_dir)
    
    def _scan_directory_for_files(self, directory: str):
        """Scan directory for existing audio files"""
        try:
            for pattern in self.config.input.file_patterns:
                for file_path in Path(directory).rglob(pattern):
                    if file_path.is_file():
                        self.add_to_queue(str(file_path))
                        logger.info(f"Found existing file: {file_path}")
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
