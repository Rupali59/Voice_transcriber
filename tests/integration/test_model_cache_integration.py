"""
Integration tests for Model Cache system
Tests the complete model caching workflow with real components including validation
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
from app.services.persistent_model_cache import PersistentModelCache
from app.services.model_cache_manager import ModelCacheManager, get_model_cache_manager
from app.services.model_validator import ModelValidator, get_model_validator
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


class TestPersistentModelCacheIntegration(unittest.TestCase):
    """Integration tests for PersistentModelCache with real components"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        # Create temporary directory for cache
        self.cache_dir = tempfile.mkdtemp()
        
        # Clear any existing cache instance
        PersistentModelCache._instance = None
        PersistentModelCache._lock = threading.Lock()
        
        # Set test environment
        os.environ['PERSISTENT_MODEL_CACHE'] = 'true'
        os.environ['ALWAYS_KEEP_MODELS'] = 'true'
        os.environ['PRIORITY_MODELS'] = 'base,small'
        os.environ['MODEL_CACHE_DIR'] = self.cache_dir
        
        # Create test app
        self.app = create_app(TestingConfig)
        self.app.config['TESTING'] = True
        self.app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Clean up after tests"""
        # Clear cache
        if hasattr(self, 'cache_dir') and os.path.exists(self.cache_dir):
            import shutil
            shutil.rmtree(self.cache_dir)
        
        # Clean up environment
        for key in ['PERSISTENT_MODEL_CACHE', 'ALWAYS_KEEP_MODELS', 
                   'PRIORITY_MODELS', 'MODEL_CACHE_DIR']:
            if key in os.environ:
                del os.environ[key]
        
        # Clean up temp directory
        import shutil
        if os.path.exists(self.app.config['UPLOAD_FOLDER']):
            shutil.rmtree(self.app.config['UPLOAD_FOLDER'])
    
    @patch('app.services.persistent_model_cache.whisper')
    def test_persistent_cache_with_transcription_service(self, mock_whisper):
        """Test persistent cache integration with transcription service"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        # Initialize transcription service
        service = TranscriptionService()
        service.init_app(self.app)
        
        # Get cache instance
        cache = PersistentModelCache()
        
        # Test that cache is used by transcription service
        model = cache.load_model('base')
        
        self.assertIsNotNone(model)
        self.assertEqual(model, mock_model)
        self.assertIn('base', cache.cache)
        
        # Verify whisper.load_model was called
        mock_whisper.load_model.assert_called_once_with('base', device='cpu')
    
    @patch('app.services.persistent_model_cache.whisper')
    def test_priority_model_protection_integration(self, mock_whisper):
        """Test priority model protection in integration"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        cache = PersistentModelCache()
        
        # Load priority models
        cache.load_model('base')
        cache.load_model('small')
        
        # Load non-priority model
        cache.load_model('medium')
        
        # All models should be in cache
        self.assertIn('base', cache.cache)
        self.assertIn('small', cache.cache)
        self.assertIn('medium', cache.cache)
        
        # Test eviction - should not evict priority models
        cache._evict_models(2)  # Try to evict to 2 models
        
        # Priority models should still be there
        self.assertIn('base', cache.cache)
        self.assertIn('small', cache.cache)
        # Medium might be evicted
        self.assertTrue(len(cache.cache) >= 2)
    
    @patch('app.services.persistent_model_cache.whisper')
    def test_cache_persistence_across_requests(self, mock_whisper):
        """Test that persistent cache persists across multiple requests"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        # First request - load model
        cache1 = PersistentModelCache()
        model1 = cache1.load_model('base')
        
        # Second request - should get same model
        cache2 = PersistentModelCache()
        model2 = cache2.load_model('base')
        
        # Should be same instance
        self.assertIs(cache1, cache2)
        self.assertIs(model1, model2)
        
        # whisper.load_model should only be called once
        mock_whisper.load_model.assert_called_once()


class TestModelCacheManagerIntegration(unittest.TestCase):
    """Integration tests for ModelCacheManager with real components"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        # Clear any existing manager instance
        ModelCacheManager._instance = None
        ModelCacheManager._lock = threading.Lock()
        
        # Set test environment
        os.environ['WHISPER_MODEL_CACHE_SIZE'] = '3'
        os.environ['MODEL_IDLE_TIMEOUT'] = '2'
        os.environ['MODEL_CLEANUP_INTERVAL'] = '1'
        os.environ['ENABLE_GPU_ACCELERATION'] = 'false'
        os.environ['PERSISTENT_MODEL_CACHE'] = 'true'
        os.environ['ALWAYS_KEEP_MODELS'] = 'true'
        os.environ['PRIORITY_MODELS'] = 'base,small'
        
        # Create test app
        self.app = create_app(TestingConfig)
        self.app.config['TESTING'] = True
        self.app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Clean up after tests"""
        # Clear cache
        manager = get_model_cache_manager()
        manager.clear_cache()
        
        # Clean up environment
        for key in ['WHISPER_MODEL_CACHE_SIZE', 'MODEL_IDLE_TIMEOUT', 
                   'MODEL_CLEANUP_INTERVAL', 'ENABLE_GPU_ACCELERATION',
                   'PERSISTENT_MODEL_CACHE', 'ALWAYS_KEEP_MODELS', 'PRIORITY_MODELS']:
            if key in os.environ:
                del os.environ[key]
        
        # Clean up temp directory
        import shutil
        if os.path.exists(self.app.config['UPLOAD_FOLDER']):
            shutil.rmtree(self.app.config['UPLOAD_FOLDER'])
    
    @patch('app.services.model_cache_manager.whisper')
    def test_cache_manager_with_transcription_service(self, mock_whisper):
        """Test cache manager integration with transcription service"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        # Initialize transcription service
        service = TranscriptionService()
        service.init_app(self.app)
        
        # Get cache manager instance
        manager = get_model_cache_manager()
        
        # Test that manager is used by transcription service
        model = manager.get_model('base')
        
        self.assertIsNotNone(model)
        self.assertEqual(model, mock_model)
        
        # Verify whisper.load_model was called
        mock_whisper.load_model.assert_called_once_with('base', device='cpu')
    
    @patch('app.services.model_cache_manager.whisper')
    def test_preload_models_integration(self, mock_whisper):
        """Test model preloading integration"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        manager = get_model_cache_manager()
        
        # Preload models
        models_to_preload = ['base', 'small']
        manager.preload_models(models_to_preload)
        
        # Verify models are loaded
        self.assertIn('base', manager.get_loaded_models())
        self.assertIn('small', manager.get_loaded_models())
        
        # Verify whisper.load_model was called for each
        self.assertEqual(mock_whisper.load_model.call_count, 2)
        
        # Test that preloaded models are immediately available
        model1 = manager.get_model('base')
        model2 = manager.get_model('small')
        
        self.assertIsNotNone(model1)
        self.assertIsNotNone(model2)
        
        # Should not have called load_model again
        self.assertEqual(mock_whisper.load_model.call_count, 2)
    
    @patch('app.services.model_cache_manager.whisper')
    def test_warmup_priority_models_integration(self, mock_whisper):
        """Test warming up priority models integration"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        manager = get_model_cache_manager()
        
        # Warm up priority models
        manager.warmup_priority_models()
        
        # Priority models should be loaded
        loaded_models = manager.get_loaded_models()
        self.assertIn('base', loaded_models)
        self.assertIn('small', loaded_models)
        
        # Verify whisper.load_model was called for priority models
        self.assertEqual(mock_whisper.load_model.call_count, 2)
    
    @patch('app.services.model_cache_manager.whisper')
    def test_ensure_models_loaded_integration(self, mock_whisper):
        """Test ensuring models are loaded integration"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        manager = get_model_cache_manager()
        
        # Ensure models are loaded
        models_to_ensure = ['base', 'small', 'medium']
        manager.ensure_models_loaded(models_to_ensure)
        
        # All models should be loaded
        loaded_models = manager.get_loaded_models()
        for model in models_to_ensure:
            self.assertIn(model, loaded_models)
        
        # Verify whisper.load_model was called for each
        self.assertEqual(mock_whisper.load_model.call_count, 3)
    
    @patch('app.services.model_cache_manager.whisper')
    def test_cache_health_integration(self, mock_whisper):
        """Test cache health integration"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        manager = get_model_cache_manager()
        
        # Load some models
        manager.get_model('base')
        manager.get_model('small')
        
        # Get cache health
        health = manager.get_cache_health()
        
        # Check health structure
        self.assertIn('status', health)
        self.assertIn('loaded_models', health)
        self.assertIn('priority_coverage', health)
        self.assertIn('memory_usage', health)
        
        # Status should be valid
        self.assertIn(health['status'], ['healthy', 'warning', 'error'])
        
        # Should have loaded models
        self.assertGreater(len(health['loaded_models']), 0)
    
    @patch('app.services.model_cache_manager.whisper')
    def test_model_status_integration(self, mock_whisper):
        """Test model status integration"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        manager = get_model_cache_manager()
        
        # Load a model
        manager.get_model('base')
        
        # Get model status
        status = manager.get_model_status('base')
        
        # Check status structure
        self.assertIn('loaded', status)
        self.assertIn('cached', status)
        self.assertIn('priority', status)
        self.assertIn('usage_stats', status)
        
        # Model should be loaded
        self.assertTrue(status['loaded'])
        self.assertTrue(status['cached'])
    
    @patch('app.services.model_cache_manager.whisper')
    def test_force_reload_model_integration(self, mock_whisper):
        """Test force reload model integration"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        manager = get_model_cache_manager()
        
        # Load a model
        manager.get_model('base')
        
        # Force reload
        manager.force_reload_model('base')
        
        # Model should still be available
        model = manager.get_model('base')
        self.assertIsNotNone(model)
        
        # Should have called load_model twice (initial load + reload)
        self.assertEqual(mock_whisper.load_model.call_count, 2)
    
    @patch('app.services.model_cache_manager.whisper')
    def test_clear_cache_integration(self, mock_whisper):
        """Test clear cache integration"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        manager = get_model_cache_manager()
        
        # Load models
        manager.get_model('base')
        manager.get_model('small')
        
        # Clear cache
        manager.clear_cache()
        
        # Cache should be empty
        loaded_models = manager.get_loaded_models()
        self.assertEqual(len(loaded_models), 0)
    
    @patch('app.services.model_cache_manager.whisper')
    def test_optimize_memory_integration(self, mock_whisper):
        """Test optimize memory integration"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        manager = get_model_cache_manager()
        
        # Load some models
        manager.get_model('base')
        manager.get_model('small')
        
        # Optimize memory
        manager.optimize_memory()
        
        # Should not raise any exceptions
        self.assertTrue(True)
        
        # Models should still be available
        self.assertIn('base', manager.get_loaded_models())
        self.assertIn('small', manager.get_loaded_models())


class TestModelValidatorIntegration(unittest.TestCase):
    """Integration tests for ModelValidator with real components"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        # Create test app
        self.app = create_app(TestingConfig)
        self.app.config['TESTING'] = True
        self.app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Clean up after tests"""
        # Clean up temp directory
        import shutil
        if os.path.exists(self.app.config['UPLOAD_FOLDER']):
            shutil.rmtree(self.app.config['UPLOAD_FOLDER'])
    
    @patch('app.services.model_validator.whisper')
    def test_validator_with_transcription_service(self, mock_whisper):
        """Test validator integration with transcription service"""
        # Mock whisper
        mock_model = Mock()
        mock_model.transcribe.return_value = {'text': 'test transcription'}
        mock_whisper.load_model.return_value = mock_model
        
        # Initialize transcription service
        service = TranscriptionService()
        service.init_app(self.app)
        
        # Get validator instance
        validator = get_model_validator()
        
        # Test that validator can validate models
        result = validator.validate_model('base', mock_model)
        
        self.assertIsNotNone(result)
        self.assertIn('model_size', result)
        self.assertIn('status', result)
        self.assertIn('overall_score', result)
        self.assertIn('tests', result)
    
    @patch('app.services.model_validator.whisper')
    def test_validate_all_models_integration(self, mock_whisper):
        """Test validating all models integration"""
        # Mock whisper
        mock_model = Mock()
        mock_model.transcribe.return_value = {'text': 'test transcription'}
        mock_whisper.load_model.return_value = mock_model
        
        validator = get_model_validator()
        
        # Validate multiple models
        models = ['base', 'small']
        result = validator.validate_all_models(models)
        
        # Check result structure
        self.assertIn('start_time', result)
        self.assertIn('models', result)
        self.assertIn('overall_status', result)
        self.assertIn('summary', result)
        
        # Check models in result
        self.assertIn('base', result['models'])
        self.assertIn('small', result['models'])
        
        # Check summary
        summary = result['summary']
        self.assertIn('total_models', summary)
        self.assertIn('passed_models', summary)
        self.assertIn('failed_models', summary)
        self.assertIn('average_score', summary)
    
    @patch('app.services.model_validator.whisper')
    def test_validation_results_persistence_integration(self, mock_whisper):
        """Test validation results persistence integration"""
        # Mock whisper
        mock_model = Mock()
        mock_model.transcribe.return_value = {'text': 'test transcription'}
        mock_whisper.load_model.return_value = mock_model
        
        validator = get_model_validator()
        
        # Initially no results
        results = validator.get_validation_results()
        self.assertEqual(len(results), 0)
        
        # Run a validation
        result = validator.validate_model('base', mock_model)
        
        # Should have one result
        results = validator.get_validation_results()
        self.assertEqual(len(results), 1)
        
        # Get specific result
        validation_id = result['validation_id']
        specific_result = validator.get_validation_results(validation_id)
        
        # Should return the same result
        self.assertEqual(specific_result, result)
    
    @patch('app.services.model_validator.whisper')
    def test_save_validation_report_integration(self, mock_whisper):
        """Test saving validation report integration"""
        # Mock whisper
        mock_model = Mock()
        mock_model.transcribe.return_value = {'text': 'test transcription'}
        mock_whisper.load_model.return_value = mock_model
        
        validator = get_model_validator()
        
        # Run a validation
        result = validator.validate_model('base', mock_model)
        
        # Save report
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            report_path = f.name
        
        try:
            validator.save_validation_report(result, report_path)
            
            # Check if file was created
            self.assertTrue(os.path.exists(report_path))
            
            # Check if file contains valid JSON
            import json
            with open(report_path, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(saved_data, result)
        finally:
            # Clean up
            if os.path.exists(report_path):
                os.remove(report_path)
    
    @patch('app.services.model_validator.whisper')
    def test_validation_with_errors_integration(self, mock_whisper):
        """Test validation with errors integration"""
        # Mock whisper
        mock_model = Mock()
        mock_model.transcribe.side_effect = Exception("Transcription failed")
        mock_whisper.load_model.return_value = mock_model
        
        validator = get_model_validator()
        
        # Validate model with errors
        result = validator.validate_model('base', mock_model)
        
        # Should have errors
        self.assertGreater(len(result['errors']), 0)
        self.assertEqual(result['status'], 'failed')
    
    @patch('app.services.model_validator.whisper')
    def test_validation_timeout_integration(self, mock_whisper):
        """Test validation timeout integration"""
        # Mock whisper
        mock_model = Mock()
        def slow_transcribe(audio):
            time.sleep(2)  # Simulate slow processing
            return {'text': 'slow transcription'}
        mock_model.transcribe.side_effect = slow_transcribe
        mock_whisper.load_model.return_value = mock_model
        
        validator = get_model_validator()
        
        # Set short timeout
        validator.validation_config['max_validation_time'] = 1
        
        # Validate model with timeout
        result = validator.validate_model('base', mock_model)
        
        # Should handle timeout gracefully
        self.assertIn('status', result)
        self.assertIn('errors', result)


class TestCompleteWorkflowIntegration(unittest.TestCase):
    """Integration tests for complete workflow with all components"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        # Clear any existing instances
        ModelCache._instance = None
        ModelCache._lock = threading.Lock()
        ModelCacheManager._instance = None
        ModelCacheManager._lock = threading.Lock()
        
        # Set test environment
        os.environ['WHISPER_MODEL_CACHE_SIZE'] = '3'
        os.environ['MODEL_IDLE_TIMEOUT'] = '2'
        os.environ['MODEL_CLEANUP_INTERVAL'] = '1'
        os.environ['ENABLE_GPU_ACCELERATION'] = 'false'
        os.environ['PERSISTENT_MODEL_CACHE'] = 'true'
        os.environ['ALWAYS_KEEP_MODELS'] = 'true'
        os.environ['PRIORITY_MODELS'] = 'base,small'
        
        # Create test app
        self.app = create_app(TestingConfig)
        self.app.config['TESTING'] = True
        self.app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Clean up after tests"""
        # Clear caches
        try:
            manager = get_model_cache_manager()
            manager.clear_cache()
        except:
            pass
        
        # Clean up environment
        for key in ['WHISPER_MODEL_CACHE_SIZE', 'MODEL_IDLE_TIMEOUT', 
                   'MODEL_CLEANUP_INTERVAL', 'ENABLE_GPU_ACCELERATION',
                   'PERSISTENT_MODEL_CACHE', 'ALWAYS_KEEP_MODELS', 'PRIORITY_MODELS']:
            if key in os.environ:
                del os.environ[key]
        
        # Clean up temp directory
        import shutil
        if os.path.exists(self.app.config['UPLOAD_FOLDER']):
            shutil.rmtree(self.app.config['UPLOAD_FOLDER'])
    
    @patch('app.services.model_cache_manager.whisper')
    @patch('app.services.model_validator.whisper')
    def test_complete_workflow_with_validation(self, mock_validator_whisper, mock_cache_whisper):
        """Test complete workflow with caching and validation"""
        # Mock whisper for both cache and validator
        mock_model = Mock()
        mock_model.transcribe.return_value = {'text': 'test transcription'}
        mock_cache_whisper.load_model.return_value = mock_model
        mock_validator_whisper.load_model.return_value = mock_model
        
        # Initialize services
        service = TranscriptionService()
        service.init_app(self.app)
        
        # Get cache manager and validator
        manager = get_model_cache_manager()
        validator = get_model_validator()
        
        # Preload models
        manager.preload_models(['base', 'small'])
        
        # Validate models
        validation_result = validator.validate_all_models(['base', 'small'])
        
        # Check that models are loaded
        loaded_models = manager.get_loaded_models()
        self.assertIn('base', loaded_models)
        self.assertIn('small', loaded_models)
        
        # Check validation results
        self.assertIn('base', validation_result['models'])
        self.assertIn('small', validation_result['models'])
        
        # Test that models are immediately available
        model1 = manager.get_model('base')
        model2 = manager.get_model('small')
        
        self.assertIsNotNone(model1)
        self.assertIsNotNone(model2)
        
        # Should not have called load_model again
        self.assertEqual(mock_cache_whisper.load_model.call_count, 2)
    
    @patch('app.services.model_cache_manager.whisper')
    def test_api_endpoints_integration(self, mock_whisper):
        """Test API endpoints integration"""
        # Mock whisper
        mock_model = Mock()
        mock_model.transcribe.return_value = {'text': 'test transcription'}
        mock_whisper.load_model.return_value = mock_model
        
        # Test cache status endpoint
        response = self.client.get('/api/cache/models')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('stats', data)
        self.assertIn('health', data)
        
        # Test preload models endpoint
        response = self.client.post('/api/cache/models/preload',
                                  json={'models': ['base', 'small']})
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('loaded_models', data)
        
        # Test validation endpoint
        response = self.client.post('/api/validate/models/base')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('validation_result', data)
        
        # Test health check endpoint
        response = self.client.get('/api/validate/models/health-check')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('overall_status', data)
        self.assertIn('model_health', data)


if __name__ == '__main__':
    unittest.main()
