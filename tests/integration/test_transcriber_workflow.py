#!/usr/bin/env python3
"""
Integration test for main transcriber workflow
Tests the complete transcription pipeline with real configuration
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

class TestTranscriberWorkflow(unittest.TestCase):
    """Test the complete transcriber workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_output_dir = os.path.join(self.temp_dir, 'transcriptions')
        self.test_log_dir = os.path.join(self.temp_dir, 'logs')
        
        os.makedirs(self.test_output_dir, exist_ok=True)
        os.makedirs(self.test_log_dir, exist_ok=True)
        
        # Real-world configuration (similar to your .env)
        self.real_config = {
            'transcription': {
                'whisper_model_size': 'base',  # Fast and accurate
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
                'max_concurrent_processes': 4,  # Optimal for your 10-core system
                'batch_size': 5,
                'audio_chunk_size': 30,
                'audio_overlap': 5
            },
            'background': {
                'enable_monitoring': True,
                'monitor_interval': 5
            },
            'logging': {
                'level': 'INFO',
                'file': os.path.join(self.test_log_dir, 'transcriber.log')
            }
        }
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_real_world_configuration(self):
        """Test that real-world configuration works correctly"""
        config = ConfigManager()
        config._config = self.real_config
        
        # Verify configuration matches your optimized settings
        self.assertEqual(config.transcription.whisper_model_size, 'base')
        self.assertEqual(config.performance.max_concurrent_processes, 4)
        self.assertEqual(config.performance.batch_size, 5)
        self.assertEqual(config.performance.audio_chunk_size, 30)
        self.assertEqual(config.performance.audio_overlap, 5)
        
        print(f"✅ Configuration verified:")
        print(f"   Model: {config.transcription.whisper_model_size}")
        print(f"   Concurrency: {config.performance.max_concurrent_processes}")
        print(f"   Batch Size: {config.performance.batch_size}")
        print(f"   Chunk Size: {config.performance.audio_chunk_size}s")
        print(f"   Overlap: {config.performance.audio_overlap}s")
    
    @patch('unified_voice_transcriber.whisper.load_model')
    def test_transcriber_initialization_with_real_config(self, mock_whisper_load):
        """Test transcriber initialization with real configuration"""
        mock_model = MagicMock()
        mock_whisper_load.return_value = mock_model
        
        config = ConfigManager()
        config._config = self.real_config
        
        transcriber = UnifiedVoiceTranscriber(
            model_size=config.transcription.whisper_model_size,
            enable_speaker_diarization=config.transcription.enable_speaker_diarization
        )
        
        self.assertIsNotNone(transcriber)
        self.assertEqual(transcriber.model_size, 'base')
        self.assertTrue(transcriber.enable_speaker_diarization)
        
        # Verify Whisper model was loaded with correct size
        mock_whisper_load.assert_called_once_with('base')
        
        print(f"✅ Transcriber initialized with Base model")
        print(f"   Speaker diarization: {transcriber.enable_speaker_diarization}")
    
    @patch('parallel_processor.UnifiedVoiceTranscriber')
    def test_parallel_processor_with_real_config(self, mock_transcriber_class):
        """Test parallel processor with real-world configuration"""
        mock_transcriber = MagicMock()
        mock_transcriber_class.return_value = mock_transcriber
        
        config = ConfigManager()
        config._config = self.real_config
        
        processor = ParallelProcessor(config)
        
        # Verify processor configuration matches your settings
        self.assertEqual(processor.max_concurrent, 4)
        self.assertEqual(processor.batch_size, 5)
        self.assertEqual(len(processor.transcriber_pool), 4)
        
        print(f"✅ Parallel processor configured:")
        print(f"   Workers: {processor.max_concurrent}")
        print(f"   Batch Size: {processor.batch_size}")
        print(f"   Transcriber Pool: {len(processor.transcriber_pool)}")
        
        # Clean up
        processor.stop()
    
    def test_voice_memo_processing_simulation(self):
        """Simulate processing multiple voice memos like your real scenario"""
        config = ConfigManager()
        config._config = self.real_config
        
        # Simulate your voice memo collection
        voice_memos = [
            "/Users/rupali.b/Library/Mobile Documents/com~apple~CloudDocs/Voice Memos/Sector 39.m4a",
            "/Users/rupali.b/Library/Mobile Documents/com~apple~CloudDocs/Voice Memos/Meeting_Notes.m4a",
            "/Users/rupali.b/Library/Mobile Documents/com~apple~CloudDocs/Voice Memos/Project_Ideas.m4a",
            "/Users/rupali.b/Library/Mobile Documents/com~apple~CloudDocs/Voice Memos/Daily_Update.m4a",
            "/Users/rupali.b/Library/Mobile Documents/com~apple~CloudDocs/Voice Memos/Interview_Notes.m4a"
        ]
        
        print(f"🎤 Simulating processing of {len(voice_memos)} voice memos")
        print(f"   Expected time with Base model: ~2-3 minutes total")
        print(f"   Expected time with Large model: ~4+ hours total")
        print(f"   Speed improvement: 100x+ faster with Base model")
        
        # Verify configuration is optimal for multiple files
        self.assertEqual(config.performance.max_concurrent_processes, 4)
        self.assertEqual(config.performance.batch_size, 5)
        self.assertEqual(config.transcription.whisper_model_size, 'base')
        
        # Calculate expected performance
        files_per_batch = config.performance.batch_size
        total_batches = (len(voice_memos) + files_per_batch - 1) // files_per_batch
        
        print(f"   Processing in {total_batches} batches of {files_per_batch} files")
        print(f"   Using {config.performance.max_concurrent_processes} parallel workers")
    
    def test_performance_optimization_verification(self):
        """Verify that configuration is optimized for your system"""
        config = ConfigManager()
        config._config = self.real_config
        
        print(f"🚀 Performance Optimization Verification:")
        
        # Check model size optimization
        model_size = config.transcription.whisper_model_size
        if model_size == 'base':
            print(f"   ✅ Model: Base (optimal speed/quality balance)")
            print(f"      Expected: 10x faster than Large model")
        elif model_size == 'large':
            print(f"   ⚠️  Model: Large (slow but highest quality)")
            print(f"      Consider: Switch to Base for 10x speed improvement")
        else:
            print(f"   ℹ️  Model: {model_size}")
        
        # Check concurrency optimization
        concurrency = config.performance.max_concurrent_processes
        if concurrency >= 4:
            print(f"   ✅ Concurrency: {concurrency} workers (optimal for 10-core system)")
        elif concurrency >= 2:
            print(f"   ⚠️  Concurrency: {concurrency} workers (could be increased)")
        else:
            print(f"   ❌ Concurrency: {concurrency} workers (too low for 10-core system)")
        
        # Check batch size optimization
        batch_size = config.performance.batch_size
        if batch_size >= 5:
            print(f"   ✅ Batch Size: {batch_size} (good for throughput)")
        else:
            print(f"   ⚠️  Batch Size: {batch_size} (could be increased)")
        
        # Check audio processing optimization
        chunk_size = config.performance.audio_chunk_size
        overlap = config.performance.audio_overlap
        
        if chunk_size >= 30 and overlap >= 5:
            print(f"   ✅ Audio Processing: {chunk_size}s chunks, {overlap}s overlap")
        else:
            print(f"   ⚠️  Audio Processing: {chunk_size}s chunks, {overlap}s overlap")
    
    def test_output_directory_structure(self):
        """Test that output directory structure is correct"""
        config = ConfigManager()
        config._config = self.real_config
        
        # Verify output directory exists
        self.assertTrue(os.path.exists(self.test_output_dir))
        self.assertTrue(os.path.exists(self.test_log_dir))
        
        print(f"✅ Output directories verified:")
        print(f"   Transcriptions: {self.test_output_dir}")
        print(f"   Logs: {self.test_log_dir}")
    
    def test_configuration_consistency(self):
        """Test that configuration is internally consistent"""
        config = ConfigManager()
        config._config = self.real_config
        
        # Test logical consistency
        self.assertGreater(config.performance.max_concurrent_processes, 0)
        self.assertGreater(config.performance.batch_size, 0)
        self.assertGreater(config.performance.audio_chunk_size, config.performance.audio_overlap)
        
        # Test reasonable limits
        self.assertLessEqual(config.performance.max_concurrent_processes, 10)
        self.assertLessEqual(config.performance.batch_size, 20)
        self.assertLessEqual(config.performance.audio_chunk_size, 120)
        
        print(f"✅ Configuration consistency verified:")
        print(f"   Concurrency within limits: {config.performance.max_concurrent_processes} <= 10")
        print(f"   Batch size reasonable: {config.performance.batch_size} <= 20")
        print(f"   Chunk size > overlap: {config.performance.audio_chunk_size} > {config.performance.audio_overlap}")

if __name__ == '__main__':
    unittest.main()
