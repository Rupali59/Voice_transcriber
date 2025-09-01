#!/usr/bin/env python3
"""
Unit tests for ParallelProcessor
Tests parallel processing, job management, and resource handling
"""

import unittest
import time
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from concurrent.futures import ThreadPoolExecutor

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from parallel_processor import ParallelProcessor, ProcessingJob, ProcessingResult
from config_manager import ConfigManager

class TestProcessingJob(unittest.TestCase):
    """Test cases for ProcessingJob dataclass"""
    
    def test_processing_job_creation(self):
        """Test ProcessingJob creation"""
        job = ProcessingJob(
            file_path="/test/audio.m4a",
            priority=5,
            estimated_duration=120.0
        )
        
        self.assertEqual(job.file_path, "/test/audio.m4a")
        self.assertEqual(job.priority, 5)
        self.assertEqual(job.estimated_duration, 120.0)
        self.assertIsNotNone(job.created_at)
    
    def test_processing_job_defaults(self):
        """Test ProcessingJob default values"""
        job = ProcessingJob("/test/audio.m4a")
        
        self.assertEqual(job.file_path, "/test/audio.m4a")
        self.assertEqual(job.priority, 0)
        self.assertIsNone(job.estimated_duration)
        self.assertIsNotNone(job.created_at)
    
    def test_processing_job_ordering(self):
        """Test ProcessingJob priority ordering"""
        job1 = ProcessingJob("/test/audio1.m4a", priority=10)
        job2 = ProcessingJob("/test/audio2.m4a", priority=5)
        job3 = ProcessingJob("/test/audio3.m4a", priority=10)
        
        # Higher priority first
        self.assertLess(job1, job2)  # job1 (priority 10) < job2 (priority 5)
        self.assertGreater(job2, job1)  # job2 (priority 5) > job1 (priority 10)
        
        # Same priority, earlier creation time first
        self.assertLess(job1, job3)  # job1 created before job3

class TestProcessingResult(unittest.TestCase):
    """Test cases for ProcessingResult dataclass"""
    
    def test_processing_result_creation(self):
        """Test ProcessingResult creation"""
        result = ProcessingResult(
            file_path="/test/audio.m4a",
            success=True,
            transcription={"text": "test transcription"},
            processing_time=5.5,
            cpu_usage=75.0,
            memory_usage=30.0
        )
        
        self.assertEqual(result.file_path, "/test/audio.m4a")
        self.assertTrue(result.success)
        self.assertEqual(result.transcription, {"text": "test transcription"})
        self.assertEqual(result.processing_time, 5.5)
        self.assertEqual(result.cpu_usage, 75.0)
        self.assertEqual(result.memory_usage, 30.0)
    
    def test_processing_result_defaults(self):
        """Test ProcessingResult default values"""
        result = ProcessingResult("/test/audio.m4a", True)
        
        self.assertEqual(result.file_path, "/test/audio.m4a")
        self.assertTrue(result.success)
        self.assertIsNone(result.transcription)
        self.assertIsNone(result.error)
        self.assertEqual(result.processing_time, 0.0)
        self.assertEqual(result.cpu_usage, 0.0)
        self.assertEqual(result.memory_usage, 0.0)

class TestParallelProcessor(unittest.TestCase):
    """Test cases for ParallelProcessor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock config
        self.mock_config = MagicMock()
        self.mock_config.performance.max_concurrent_processes = 2
        self.mock_config.performance.batch_size = 3
        self.mock_config.transcription.whisper_model_size = 'base'
        self.mock_config.transcription.enable_speaker_diarization = True
        self.mock_config.output.base_dir = './test_output'
        self.mock_config.output.include_speakers = True
        
        # Create temporary output directory
        self.temp_output_dir = tempfile.mkdtemp()
        self.mock_config.output.base_dir = self.temp_output_dir
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_output_dir):
            shutil.rmtree(self.temp_output_dir)
    
    @patch('parallel_processor.UnifiedVoiceTranscriber')
    def test_parallel_processor_initialization(self, mock_transcriber_class):
        """Test ParallelProcessor initialization"""
        mock_transcriber = MagicMock()
        mock_transcriber_class.return_value = mock_transcriber
        
        processor = ParallelProcessor(self.mock_config)
        
        self.assertIsNotNone(processor)
        self.assertEqual(processor.max_concurrent, 2)
        self.assertEqual(processor.batch_size, 3)
        self.assertEqual(len(processor.transcriber_pool), 2)
        self.assertTrue(processor.monitoring)
        self.assertIsNotNone(processor.monitor_thread)
    
    def test_add_job(self):
        """Test adding jobs to the queue"""
        processor = ParallelProcessor(self.mock_config)
        
        # Add a job
        result = processor.add_job("/test/audio.m4a", priority=5)
        
        self.assertTrue(result)
        self.assertEqual(processor.stats['jobs_submitted'], 1)
        self.assertEqual(processor.job_queue.qsize(), 1)
    
    def test_add_batch(self):
        """Test adding multiple jobs as a batch"""
        processor = ParallelProcessor(self.mock_config)
        
        files = ["/test/audio1.m4a", "/test/audio2.m4a", "/test/audio3.m4a"]
        added_count = processor.add_batch(files, priority=3)
        
        self.assertEqual(added_count, 3)
        self.assertEqual(processor.stats['jobs_submitted'], 3)
        self.assertEqual(processor.job_queue.qsize(), 3)
    
    def test_process_jobs_empty_queue(self):
        """Test processing jobs when queue is empty"""
        processor = ParallelProcessor(self.mock_config)
        
        results = processor.process_jobs()
        
        self.assertEqual(results, {})
        self.assertEqual(processor.stats['jobs_completed'], 0)
    
    @patch('parallel_processor.UnifiedVoiceTranscriber')
    def test_process_jobs_success(self, mock_transcriber_class):
        """Test successful job processing"""
        # Mock transcriber
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe_audio.return_value = {"text": "test transcription"}
        mock_transcriber_class.return_value = mock_transcriber
        
        processor = ParallelProcessor(self.mock_config)
        
        # Add test jobs
        processor.add_job("/test/audio1.m4a")
        processor.add_job("/test/audio2.m4a")
        
        # Mock the processing method
        def mock_process(job):
            return ProcessingResult(
                file_path=job.file_path,
                success=True,
                transcription={"text": "test transcription"},
                processing_time=1.0,
                cpu_usage=50.0,
                memory_usage=25.0
            )
        
        processor._process_single_job = mock_process
        
        # Process jobs
        results = processor.process_jobs()
        
        self.assertEqual(len(results), 2)
        self.assertEqual(processor.stats['jobs_completed'], 2)
        self.assertEqual(processor.stats['jobs_failed'], 0)
        
        # Check that all jobs were successful
        for result in results.values():
            self.assertTrue(result.success)
    
    @patch('parallel_processor.UnifiedVoiceTranscriber')
    def test_process_jobs_with_failures(self, mock_transcriber_class):
        """Test job processing with some failures"""
        # Mock transcriber
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe_audio.side_effect = Exception("Processing failed")
        mock_transcriber_class.return_value = mock_transcriber
        
        processor = ParallelProcessor(self.mock_config)
        
        # Add test jobs
        processor.add_job("/test/audio1.m4a")
        processor.add_job("/test/audio2.m4a")
        
        # Mock the processing method to simulate failures
        def mock_process(job):
            if "audio1" in job.file_path:
                return ProcessingResult(
                    file_path=job.file_path,
                    success=False,
                    error="Processing failed",
                    processing_time=1.0
                )
            else:
                return ProcessingResult(
                    file_path=job.file_path,
                    success=True,
                    transcription={"text": "test transcription"},
                    processing_time=1.0
                )
        
        processor._process_single_job = mock_process
        
        # Process jobs
        results = processor.process_jobs()
        
        self.assertEqual(len(results), 2)
        self.assertEqual(processor.stats['jobs_completed'], 1)
        self.assertEqual(processor.stats['jobs_failed'], 1)
        
        # Check results
        failed_job = results["/test/audio1.m4a"]
        successful_job = results["/test/audio2.m4a"]
        
        self.assertFalse(failed_job.success)
        self.assertEqual(failed_job.error, "Processing failed")
        self.assertTrue(successful_job.success)
    
    def test_get_stats(self):
        """Test statistics retrieval"""
        processor = ParallelProcessor(self.mock_config)
        
        # Add some jobs and process them
        processor.add_job("/test/audio1.m4a")
        processor.add_job("/test/audio2.m4a")
        
        stats = processor.get_stats()
        
        self.assertIn('jobs_submitted', stats)
        self.assertIn('jobs_completed', stats)
        self.assertIn('jobs_failed', stats)
        self.assertIn('queue_size', stats)
        self.assertIn('active_jobs', stats)
        
        self.assertEqual(stats['jobs_submitted'], 2)
        self.assertEqual(stats['queue_size'], 2)
    
    def test_stop_processor(self):
        """Test stopping the parallel processor"""
        processor = ParallelProcessor(self.mock_config)
        
        # Verify monitoring is active
        self.assertTrue(processor.monitoring)
        self.assertTrue(processor.monitor_thread.is_alive())
        
        # Stop processor
        processor.stop()
        
        # Verify monitoring is stopped
        self.assertFalse(processor.monitoring)
    
    @patch('parallel_processor.psutil.cpu_percent')
    @patch('parallel_processor.psutil.virtual_memory')
    def test_resource_monitoring(self, mock_memory, mock_cpu):
        """Test resource monitoring functionality"""
        # Mock system resources
        mock_cpu.return_value = 75.0
        mock_memory_instance = MagicMock()
        mock_memory_instance.percent = 45.0
        mock_memory.return_value = mock_memory_instance
        
        processor = ParallelProcessor(self.mock_config)
        
        # Wait a bit for monitoring to collect data
        time.sleep(0.1)
        
        # Stop processor to end monitoring
        processor.stop()
        
        # Check that some resource data was collected
        stats = processor.get_stats()
        self.assertIn('current_cpu', stats)
        self.assertIn('current_memory', stats)

if __name__ == '__main__':
    unittest.main()
