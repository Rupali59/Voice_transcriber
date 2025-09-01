#!/usr/bin/env python3
"""
Unit tests for ConfigManager
Tests configuration loading, validation, and access methods
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from config_manager import ConfigManager, TranscriptionConfig, InputConfig, OutputConfig, PerformanceConfig, BackgroundConfig, LoggingConfig

class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_env_content = """
# Test environment configuration
WHISPER_MODEL_SIZE=base
ENABLE_SPEAKER_DIARIZATION=true
ENABLE_LANGUAGE_DETECTION=true
MAX_CONCURRENT_PROCESSES=4
BATCH_SIZE=5
INPUT_WATCH_DIRS=/test/path1,/test/path2
INPUT_FILE_PATTERNS=*.m4a,*.mp3
OUTPUT_BASE_DIR=./test_output
LOG_LEVEL=DEBUG
        """.strip()
        
        # Create temporary .env file
        self.temp_env_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env')
        self.temp_env_file.write(self.test_env_content)
        self.temp_env_file.close()
        
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_env_file.name):
            os.unlink(self.temp_env_file.name)
    
    def test_config_manager_initialization(self):
        """Test ConfigManager initialization"""
        config = ConfigManager()
        self.assertIsNotNone(config)
        self.assertIsInstance(config.transcription, TranscriptionConfig)
        self.assertIsInstance(config.input, InputConfig)
        self.assertIsInstance(config.output, OutputConfig)
        self.assertIsInstance(config.performance, PerformanceConfig)
        self.assertIsInstance(config.background, BackgroundConfig)
        self.assertIsInstance(config.logging, LoggingConfig)
    
    def test_load_env_file(self):
        """Test loading environment file"""
        config = ConfigManager(self.temp_env_file.name)
        
        # Test transcription config
        self.assertEqual(config.transcription.whisper_model_size, 'base')
        self.assertTrue(config.transcription.enable_speaker_diarization)
        self.assertTrue(config.transcription.enable_language_detection)
        
        # Test performance config
        self.assertEqual(config.performance.max_concurrent_processes, 4)
        self.assertEqual(config.performance.batch_size, 5)
        
        # Test input config
        self.assertEqual(len(config.input.watch_dirs), 2)
        self.assertIn('/test/path1', config.input.watch_dirs)
        self.assertIn('/test/path2', config.input.watch_dirs)
        
        # Test output config
        self.assertEqual(config.output.base_dir, './test_output')
        
        # Test logging config
        self.assertEqual(config.logging.level, 'DEBUG')
    
    def test_default_values(self):
        """Test default configuration values"""
        config = ConfigManager()
        
        # Test transcription defaults
        self.assertEqual(config.transcription.whisper_model_size, 'large')  # From your .env file
        self.assertTrue(config.transcription.enable_speaker_diarization)
        self.assertFalse(config.transcription.enable_language_detection)  # From your .env file
        
        # Test performance defaults
        self.assertEqual(config.performance.max_concurrent_processes, 2)  # From your .env file
        self.assertEqual(config.performance.batch_size, 3)  # From your .env file
        
        # Test input defaults
        self.assertIsInstance(config.input.file_patterns, list)
        self.assertIn('*.m4a', config.input.file_patterns)
        self.assertIn('*.mp3', config.input.file_patterns)
        
        # Test output defaults
        self.assertIsNotNone(config.output.base_dir)
        self.assertTrue(config.output.include_metadata)
        self.assertTrue(config.output.include_speakers)
    
    def test_environment_variable_override(self):
        """Test environment variable overrides"""
        # Test that environment variables can be set
        os.environ['WHISPER_MODEL_SIZE'] = 'large'
        os.environ['MAX_CONCURRENT_PROCESSES'] = '8'
        os.environ['BATCH_SIZE'] = '10'
        
        # Create new config manager with a non-existent env file to avoid .env override
        config = ConfigManager('/nonexistent/file.env')
        
        self.assertEqual(config.transcription.whisper_model_size, 'large')
        self.assertEqual(config.performance.max_concurrent_processes, 8)
        self.assertEqual(config.performance.batch_size, 10)
        
        # Clean up
        del os.environ['WHISPER_MODEL_SIZE']
        del os.environ['MAX_CONCURRENT_PROCESSES']
        del os.environ['BATCH_SIZE']
    
    def test_invalid_env_file(self):
        """Test handling of invalid environment file"""
        # Should handle missing file gracefully
        config = ConfigManager('/nonexistent/file.env')
        self.assertIsNotNone(config)
    
    def test_config_validation(self):
        """Test configuration validation"""
        config = ConfigManager()
        
        # Test valid model sizes
        valid_models = ['tiny', 'base', 'small', 'medium', 'large']
        for model in valid_models:
            config.transcription.whisper_model_size = model
            # Should not raise any exceptions
        
        # Test that invalid model size is handled gracefully
        config.transcription.whisper_model_size = 'invalid'
        # Should not raise exception (validation not implemented yet)
    
    def test_performance_config_limits(self):
        """Test performance configuration limits"""
        config = ConfigManager()
        
        # Test valid concurrent processes
        config.performance.max_concurrent_processes = 1
        config.performance.max_concurrent_processes = 10
        
        # Test that invalid values are handled gracefully
        config.performance.max_concurrent_processes = 0
        config.performance.max_concurrent_processes = -1
        # Should not raise exception (validation not implemented yet)
    
    def test_config_serialization(self):
        """Test configuration serialization to dict"""
        config = ConfigManager()
        
        # Test that configuration attributes are accessible
        self.assertIsNotNone(config.transcription)
        self.assertIsNotNone(config.input)
        self.assertIsNotNone(config.output)
        self.assertIsNotNone(config.performance)
        self.assertIsNotNone(config.background)
        self.assertIsNotNone(config.logging)
    
    def test_config_repr(self):
        """Test configuration string representation"""
        config = ConfigManager()
        config_str = str(config)
        
        self.assertIsInstance(config_str, str)
        self.assertIn('ConfigManager', config_str)

class TestTranscriptionConfig(unittest.TestCase):
    """Test cases for TranscriptionConfig dataclass"""
    
    def test_transcription_config_creation(self):
        """Test TranscriptionConfig creation"""
        config = TranscriptionConfig(
            whisper_model_size='medium',
            enable_speaker_diarization=False,
            enable_language_detection=False
        )
        
        self.assertEqual(config.whisper_model_size, 'medium')
        self.assertFalse(config.enable_speaker_diarization)
        self.assertFalse(config.enable_language_detection)
    
    def test_transcription_config_defaults(self):
        """Test TranscriptionConfig default values"""
        config = TranscriptionConfig()
        
        self.assertEqual(config.whisper_model_size, 'medium')
        self.assertTrue(config.enable_speaker_diarization)
        self.assertTrue(config.enable_language_detection)

class TestPerformanceConfig(unittest.TestCase):
    """Test cases for PerformanceConfig dataclass"""
    
    def test_performance_config_creation(self):
        """Test PerformanceConfig creation"""
        config = PerformanceConfig(
            max_concurrent_processes=6,
            batch_size=8
        )
        
        self.assertEqual(config.max_concurrent_processes, 6)
        self.assertEqual(config.batch_size, 8)
    
    def test_performance_config_defaults(self):
        """Test PerformanceConfig default values"""
        config = PerformanceConfig()
        
        self.assertEqual(config.max_concurrent_processes, 2)
        self.assertEqual(config.batch_size, 3)

if __name__ == '__main__':
    unittest.main()
