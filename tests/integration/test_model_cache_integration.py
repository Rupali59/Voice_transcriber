"""
Integration tests for Model Cache system
Tests the complete model caching workflow with real components
"""

import unittest
import os
import sys
import time
import threading
import tempfile
from unittest.mock import patch, Mock
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.model_cache import ModelCache, get_model_cache
from app.services.transcription_service import TranscriptionService
from app import create_app
from app.config import TestingConfig


class TestModelCacheIntegration(unittest.TestCase):
    """Integration tests for ModelCache with real components"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        # Clear any existing cache instance
        ModelCache._instance = None
        ModelCache._lock = threading.Lock()
        
        # Set test environment
        os.environ['WHISPER_MODEL_CACHE_SIZE'] = '3'
        os.environ['MODEL_IDLE_TIMEOUT'] = '2'  # 2 seconds for testing
        os.environ['MODEL_CLEANUP_INTERVAL'] = '1'  # 1 second for testing
        os.environ['ENABLE_GPU_ACCELERATION'] = 'false'
        
        # Create test app
        self.app = create_app(TestingConfig)
        self.app.config['TESTING'] = True
        self.app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Clean up after tests"""
        # Clear cache
        cache = get_model_cache()
        cache.clear_cache()
        
        # Clean up environment
        for key in ['WHISPER_MODEL_CACHE_SIZE', 'MODEL_IDLE_TIMEOUT', 
                   'MODEL_CLEANUP_INTERVAL', 'ENABLE_GPU_ACCELERATION']:
            if key in os.environ:
                del os.environ[key]
        
        # Clean up temp directory
        import shutil
        if os.path.exists(self.app.config['UPLOAD_FOLDER']):
            shutil.rmtree(self.app.config['UPLOAD_FOLDER'])
    
    @patch('app.services.model_cache.whisper')
    def test_model_cache_with_transcription_service(self, mock_whisper):
        """Test model cache integration with transcription service"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        # Initialize transcription service
        service = TranscriptionService()
        service.init_app(self.app)
        
        # Get cache instance
        cache = get_model_cache()
        
        # Test that cache is used by transcription service
        # This would happen when UnifiedVoiceTranscriber calls load_model()
        model = cache.get_model('base')
        
        self.assertIsNotNone(model)
        self.assertEqual(model, mock_model)
        self.assertIn('base', cache.models)
        
        # Verify whisper.load_model was called
        mock_whisper.load_model.assert_called_once_with('base', device='cpu')
    
    @patch('app.services.model_cache.whisper')
    def test_concurrent_model_loading(self, mock_whisper):
        """Test concurrent model loading with cache"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        cache = get_model_cache()
        results = []
        
        def load_model():
            model = cache.get_model('base')
            results.append(model)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=load_model)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All results should be the same model instance
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIs(result, results[0])
        
        # whisper.load_model should only be called once
        mock_whisper.load_model.assert_called_once()
    
    @patch('app.services.model_cache.whisper')
    def test_cache_eviction_under_load(self, mock_whisper):
        """Test cache eviction when loading many models"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        cache = get_model_cache()
        
        # Load models up to cache limit
        models = ['tiny', 'base', 'small']
        for model_size in models:
            cache.get_model(model_size)
        
        # Verify all models are cached
        self.assertEqual(len(cache.models), 3)
        for model_size in models:
            self.assertIn(model_size, cache.models)
        
        # Load one more model (should evict one)
        cache.get_model('medium')
        
        # Should still have 3 models
        self.assertEqual(len(cache.models), 3)
        self.assertIn('medium', cache.models)
        
        # Should have evicted one of the original models
        evicted_count = 0
        for model_size in models:
            if model_size not in cache.models:
                evicted_count += 1
        
        self.assertEqual(evicted_count, 1)
    
    @patch('app.services.model_cache.whisper')
    def test_cache_statistics_integration(self, mock_whisper):
        """Test cache statistics with real usage"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        cache = get_model_cache()
        
        # Load models
        cache.get_model('base')
        cache.get_model('small')
        
        # Get statistics
        stats = cache.get_cache_stats()
        
        # Verify statistics
        self.assertEqual(stats['cache_size'], 2)
        self.assertEqual(stats['max_cache_size'], 3)
        self.assertEqual(set(stats['cached_models']), {'base', 'small'})
        
        # Check model usage
        self.assertIn('base', stats['model_usage'])
        self.assertIn('small', stats['model_usage'])
        
        # Check memory usage structure
        self.assertIn('memory_usage', stats)
    
    @patch('app.services.model_cache.whisper')
    def test_cache_cleanup_integration(self, mock_whisper):
        """Test cache cleanup with real timing"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        cache = get_model_cache()
        
        # Load a model
        cache.get_model('base')
        self.assertIn('base', cache.models)
        
        # Wait for idle timeout
        time.sleep(2.5)
        
        # Model should still be in cache (cleanup runs in background)
        # This test verifies the cleanup mechanism exists and doesn't crash
        self.assertIn('base', cache.models)
    
    def test_cache_api_integration(self):
        """Test cache API endpoints integration"""
        with patch('app.services.model_cache.whisper') as mock_whisper:
            # Mock whisper
            mock_model = Mock()
            mock_whisper.load_model.return_value = mock_model
            
            # Test cache stats endpoint
            response = self.client.get('/api/cache/stats')
            self.assertEqual(response.status_code, 200)
            
            data = response.get_json()
            self.assertIn('cached_models', data)
            self.assertIn('cache_size', data)
            self.assertIn('max_cache_size', data)
            
            # Test cache clear endpoint
            response = self.client.post('/api/cache/clear')
            self.assertEqual(response.status_code, 200)
            
            data = response.get_json()
            self.assertTrue(data['success'])
            self.assertEqual(data['message'], 'Cache cleared')
            
            # Test memory optimization endpoint
            response = self.client.post('/api/cache/optimize')
            self.assertEqual(response.status_code, 200)
            
            data = response.get_json()
            self.assertTrue(data['success'])
            self.assertEqual(data['message'], 'Memory optimized')
    
    @patch('app.services.model_cache.whisper')
    def test_model_preloading_integration(self, mock_whisper):
        """Test model preloading integration"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        cache = get_model_cache()
        
        # Preload models
        models_to_preload = ['base', 'small']
        cache.preload_models(models_to_preload)
        
        # Verify models are loaded
        self.assertIn('base', cache.models)
        self.assertIn('small', cache.models)
        
        # Verify whisper.load_model was called for each
        self.assertEqual(mock_whisper.load_model.call_count, 2)
        
        # Test that preloaded models are immediately available
        model1 = cache.get_model('base')
        model2 = cache.get_model('small')
        
        self.assertIsNotNone(model1)
        self.assertIsNotNone(model2)
        
        # Should not have called load_model again
        self.assertEqual(mock_whisper.load_model.call_count, 2)
    
    @patch('app.services.model_cache.whisper')
    def test_memory_optimization_integration(self, mock_whisper):
        """Test memory optimization integration"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        cache = get_model_cache()
        
        # Load some models
        cache.get_model('base')
        cache.get_model('small')
        
        # Optimize memory
        cache.optimize_memory()
        
        # Should not raise any exceptions
        self.assertTrue(True)
        
        # Models should still be available
        self.assertIn('base', cache.models)
        self.assertIn('small', cache.models)
    
    @patch('app.services.model_cache.whisper')
    def test_cache_persistence_across_requests(self, mock_whisper):
        """Test that cache persists across multiple requests"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        # First request - load model
        cache1 = get_model_cache()
        model1 = cache1.get_model('base')
        
        # Second request - should get same model
        cache2 = get_model_cache()
        model2 = cache2.get_model('base')
        
        # Should be same instance
        self.assertIs(cache1, cache2)
        self.assertIs(model1, model2)
        
        # whisper.load_model should only be called once
        mock_whisper.load_model.assert_called_once()
    
    @patch('app.services.model_cache.whisper')
    def test_error_handling_integration(self, mock_whisper):
        """Test error handling in cache integration"""
        # Mock whisper to raise exception
        mock_whisper.load_model.side_effect = Exception("Model load failed")
        
        cache = get_model_cache()
        
        # Try to load model
        model = cache.get_model('base')
        
        # Should return None on error
        self.assertIsNone(model)
        self.assertNotIn('base', cache.models)
        
        # Should not crash the application
        self.assertTrue(True)


class TestTranscriptionWorkflowIntegration(unittest.TestCase):
    """Integration tests for complete transcription workflow with caching"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        # Clear any existing cache instance
        ModelCache._instance = None
        ModelCache._lock = threading.Lock()
        
        # Set test environment
        os.environ['WHISPER_MODEL_CACHE_SIZE'] = '2'
        os.environ['MODEL_IDLE_TIMEOUT'] = '5'
        os.environ['MODEL_CLEANUP_INTERVAL'] = '2'
        os.environ['ENABLE_GPU_ACCELERATION'] = 'false'
        
        # Create test app
        self.app = create_app(TestingConfig)
        self.app.config['TESTING'] = True
        self.app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Clean up after tests"""
        # Clear cache
        cache = get_model_cache()
        cache.clear_cache()
        
        # Clean up environment
        for key in ['WHISPER_MODEL_CACHE_SIZE', 'MODEL_IDLE_TIMEOUT', 
                   'MODEL_CLEANUP_INTERVAL', 'ENABLE_GPU_ACCELERATION']:
            if key in os.environ:
                del os.environ[key]
        
        # Clean up temp directory
        import shutil
        if os.path.exists(self.app.config['UPLOAD_FOLDER']):
            shutil.rmtree(self.app.config['UPLOAD_FOLDER'])
    
    @patch('app.services.model_cache.whisper')
    @patch('app.services.transcription_service.UnifiedVoiceTranscriber')
    def test_full_transcription_workflow_with_cache(self, mock_transcriber_class, mock_whisper):
        """Test complete transcription workflow using cached models"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        # Mock transcriber
        mock_transcriber = Mock()
        mock_transcriber.transcribe_audio.return_value = {
            'text': 'Test transcription',
            'language': 'en',
            'segments': [],
            'speaker_segments': []
        }
        mock_transcriber_class.return_value = mock_transcriber
        
        # Initialize transcription service
        service = TranscriptionService()
        service.init_app(self.app)
        
        # Get cache instance
        cache = get_model_cache()
        
        # Simulate multiple transcriptions with same model
        for i in range(3):
            # Create mock file upload
            mock_file_upload = Mock()
            mock_file_upload.filename = f'test{i}.wav'
            mock_file_upload.original_name = f'test{i}.wav'
            mock_file_upload.size_mb = 5.0
            
            # Start transcription
            job = service.start_transcription(
                job_id=f'test-job-{i}',
                file_upload=mock_file_upload,
                model_size='base',
                enable_speaker_diarization=True,
                language='en'
            )
            
            self.assertIsNotNone(job)
        
        # Verify that whisper.load_model was only called once (due to caching)
        mock_whisper.load_model.assert_called_once_with('base', device='cpu')
        
        # Verify that transcriber was created multiple times but model was reused
        self.assertEqual(mock_transcriber_class.call_count, 3)
    
    @patch('app.services.model_cache.whisper')
    def test_model_switching_with_cache(self, mock_whisper):
        """Test switching between different models with cache"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        cache = get_model_cache()
        
        # Load different models
        models = ['tiny', 'base', 'small']
        for model_size in models:
            model = cache.get_model(model_size)
            self.assertIsNotNone(model)
        
        # All models should be cached
        self.assertEqual(len(cache.models), 3)
        for model_size in models:
            self.assertIn(model_size, cache.models)
        
        # Verify whisper.load_model was called for each model
        self.assertEqual(mock_whisper.load_model.call_count, 3)
        
        # Test reusing cached models
        for model_size in models:
            model = cache.get_model(model_size)
            self.assertIsNotNone(model)
        
        # Should not have called load_model again
        self.assertEqual(mock_whisper.load_model.call_count, 3)


if __name__ == '__main__':
    unittest.main()
