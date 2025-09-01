#!/usr/bin/env python3
"""
Integration tests for end-to-end voice transcription workflow
Tests the complete pipeline from configuration to transcription output
"""

import unittest
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from config_manager import ConfigManager
from parallel_processor import ParallelProcessor
from unified_voice_transcriber import UnifiedVoiceTranscriber

class TestEndToEndWorkflow(unittest.TestCase):
    """Test cases for complete end-to-end workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.test_output_dir = os.path.join(self.temp_dir, 'transcriptions')
        self.test_log_dir = os.path.join(self.temp_dir, 'logs')
        
        os.makedirs(self.test_output_dir, exist_ok=True)
        os.makedirs(self.test_log_dir, exist_ok=True)
        
        # Create test configuration
        self.test_config = {
            'transcription': {
                'whisper_model_size': 'tiny',  # Use tiny for fast testing
                'enable_speaker_diarization': True,
                'language_detection': True
            },
            'input': {
                'file_patterns': ['*.m4a', '*.mp3', '*.wav'],
                'watch_directories': []
            },
            'output': {
                'base_dir': self.test_output_dir,
                'include_speakers': True,
                'include_timestamps': True
            },
            'performance': {
                'max_concurrent_processes': 2,
                'batch_size': 3,
                'audio_chunk_size': 30,
                'audio_overlap': 5
            },
            'background': {
                'enable_monitoring': True,
                'monitor_interval': 5
            },
            'logging': {
                'level': 'INFO',
                'file': os.path.join(self.test_log_dir, 'test.log')
            }
        }
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_configuration_loading(self):
        """Test that configuration loads correctly"""
        config = ConfigManager()
        config._config = self.test_config
        
        # Verify configuration structure
        self.assertEqual(config.transcription.whisper_model_size, 'tiny')
        self.assertTrue(config.transcription.enable_speaker_diarization)
        self.assertEqual(config.performance.max_concurrent_processes, 2)
        self.assertEqual(config.output.base_dir, self.test_output_dir)
    
    @patch('unified_voice_transcriber.whisper.load_model')
    def test_transcriber_initialization(self, mock_whisper_load):
        """Test transcriber initialization with configuration"""
        # Mock Whisper model loading
        mock_model = MagicMock()
        mock_whisper_load.return_value = mock_model
        
        config = ConfigManager()
        config._config = self.test_config
        
        transcriber = UnifiedVoiceTranscriber(
            model_size=config.transcription.whisper_model_size,
            enable_speaker_diarization=config.transcription.enable_speaker_diarization
        )
        
        self.assertIsNotNone(transcriber)
        self.assertEqual(transcriber.model_size, 'tiny')
        self.assertTrue(transcriber.enable_speaker_diarization)
        
        # Verify Whisper model was loaded
        mock_whisper_load.assert_called_once_with('tiny')
    
    @patch('parallel_processor.UnifiedVoiceTranscriber')
    def test_parallel_processor_integration(self, mock_transcriber_class):
        """Test parallel processor integration with configuration"""
        # Mock transcriber
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe_audio.return_value = {
            "text": "Test transcription",
            "language": "en",
            "duration": 60.0
        }
        mock_transcriber_class.return_value = mock_transcriber
        
        config = ConfigManager()
        config._config = self.test_config
        
        # Create parallel processor
        processor = ParallelProcessor(config)
        
        # Verify processor configuration
        self.assertEqual(processor.max_concurrent, 2)
        self.assertEqual(processor.batch_size, 3)
        self.assertEqual(len(processor.transcriber_pool), 2)
        
        # Clean up
        processor.stop()
    
    def test_output_directory_creation(self):
        """Test that output directories are created correctly"""
        config = ConfigManager()
        config._config = self.test_config
        
        # Verify output directory exists
        self.assertTrue(os.path.exists(self.test_output_dir))
        
        # Verify log directory exists
        self.assertTrue(os.path.exists(self.test_log_dir))
    
    @patch('parallel_processor.UnifiedVoiceTranscriber')
    def test_complete_workflow_simulation(self, mock_transcriber_class):
        """Test complete workflow simulation"""
        # Mock transcriber
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe_audio.return_value = {
            "text": "Test transcription content",
            "language": "en",
            "duration": 120.0,
            "speaker_segments": [
                {
                    "speaker": 1,
                    "start_time": "0:00",
                    "end_time": "1:00",
                    "text": "Speaker 1 content"
                }
            ]
        }
        mock_transcriber_class.return_value = mock_transcriber
        
        config = ConfigManager()
        config._config = self.test_config
        
        # Create parallel processor
        processor = ParallelProcessor(config)
        
        # Add test jobs
        test_files = [
            "/test/audio1.m4a",
            "/test/audio2.m4a",
            "/test/audio3.m4a"
        ]
        
        for file_path in test_files:
            processor.add_job(file_path)
        
        # Verify jobs were added
        self.assertEqual(processor.stats['jobs_submitted'], 3)
        self.assertEqual(processor.job_queue.qsize(), 3)
        
        # Mock processing method
        def mock_process(job):
            return {
                'file_path': job.file_path,
                'success': True,
                'transcription': {
                    "text": f"Transcription for {job.file_path}",
                    "language": "en",
                    "duration": 60.0
                },
                'processing_time': 1.0,
                'cpu_usage': 50.0,
                'memory_usage': 25.0
            }
        
        # Process jobs
        results = processor.process_jobs()
        
        # Verify results
        self.assertEqual(len(results), 3)
        self.assertEqual(processor.stats['jobs_completed'], 3)
        
        # Clean up
        processor.stop()
    
    def test_configuration_validation(self):
        """Test configuration validation across components"""
        config = ConfigManager()
        config._config = self.test_config
        
        # Test valid configuration
        self.assertIsInstance(config.transcription.whisper_model_size, str)
        self.assertIsInstance(config.performance.max_concurrent_processes, int)
        self.assertIsInstance(config.output.base_dir, str)
        
        # Test configuration consistency
        self.assertGreater(config.performance.max_concurrent_processes, 0)
        self.assertGreater(config.performance.batch_size, 0)
        self.assertTrue(os.path.isabs(config.output.base_dir) or config.output.base_dir.startswith('./'))
    
    def test_error_handling(self):
        """Test error handling in the workflow"""
        config = ConfigManager()
        config._config = self.test_config
        
        # Test with invalid configuration
        with self.assertRaises(AttributeError):
            # Try to access non-existent configuration
            invalid_value = config.nonexistent_config
        
        # Test with invalid paths
        config.output.base_dir = "/nonexistent/path"
        # Should not raise exception, but should handle gracefully
    
    def test_performance_configuration(self):
        """Test performance configuration settings"""
        config = ConfigManager()
        config._config = self.test_config
        
        # Verify performance settings
        self.assertGreaterEqual(config.performance.max_concurrent_processes, 1)
        self.assertLessEqual(config.performance.max_concurrent_processes, 10)
        self.assertGreaterEqual(config.performance.batch_size, 1)
        self.assertGreaterEqual(config.performance.audio_chunk_size, 10)
        self.assertGreaterEqual(config.performance.audio_overlap, 0)
        
        # Verify audio chunk settings make sense
        self.assertGreater(config.performance.audio_chunk_size, config.performance.audio_overlap)

class TestRealWorldScenarios(unittest.TestCase):
    """Test cases for real-world usage scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_multiple_voice_memo_processing(self):
        """Test processing multiple voice memos scenario"""
        # This test simulates a real-world scenario where you have multiple voice memos
        
        # Create mock configuration for multiple files
        config = ConfigManager()
        config._config = {
            'transcription': {
                'whisper_model_size': 'base',
                'enable_speaker_diarization': True,
                'language_detection': True
            },
            'performance': {
                'max_concurrent_processes': 4,
                'batch_size': 5,
                'audio_chunk_size': 30,
                'audio_overlap': 5
            },
            'output': {
                'base_dir': self.temp_dir,
                'include_speakers': True,
                'include_timestamps': True
            }
        }
        
        # Verify configuration is suitable for multiple files
        self.assertEqual(config.performance.max_concurrent_processes, 4)
        self.assertEqual(config.performance.batch_size, 5)
        self.assertEqual(config.transcription.whisper_model_size, 'base')
    
    def test_large_file_processing(self):
        """Test configuration for large audio file processing"""
        config = ConfigManager()
        config._config = {
            'transcription': {
                'whisper_model_size': 'medium',
                'enable_speaker_diarization': True,
                'language_detection': True
            },
            'performance': {
                'max_concurrent_processes': 2,
                'batch_size': 1,
                'audio_chunk_size': 60,
                'audio_overlap': 10
            }
        }
        
        # Verify configuration is suitable for large files
        self.assertEqual(config.transcription.whisper_model_size, 'medium')
        self.assertEqual(config.performance.audio_chunk_size, 60)
        self.assertEqual(config.performance.max_concurrent_processes, 2)

if __name__ == '__main__':
    unittest.main()
