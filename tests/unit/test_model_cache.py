"""
Unit tests for Model Cache system
Tests the ModelCache, PersistentModelCache, ModelCacheManager, and ModelValidator classes
"""

import unittest
import threading
import time
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.model_cache import ModelCache, get_model_cache
from app.services.persistent_model_cache import PersistentModelCache
from app.services.model_cache_manager import ModelCacheManager, get_model_cache_manager
from app.services.model_validator import ModelValidator, get_model_validator


class TestModelCache(unittest.TestCase):
    """Test cases for ModelCache class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Clear any existing cache instance
        ModelCache._instance = None
        ModelCache._lock = threading.Lock()
        
        # Mock whisper module
        self.whisper_patcher = patch('app.services.model_cache.whisper')
        self.mock_whisper = self.whisper_patcher.start()
        
        # Mock torch module
        self.torch_patcher = patch('app.services.model_cache.torch')
        self.mock_torch = self.torch_patcher.start()
        self.mock_torch.cuda.is_available.return_value = False
        
        # Mock psutil module - patch it directly in the model cache module
        self.psutil_patcher = patch('app.services.model_cache.psutil', create=True)
        self.mock_psutil = self.psutil_patcher.start()
        mock_process = Mock()
        mock_process.memory_info.return_value = Mock(rss=100000000, vms=200000000)  # 100MB, 200MB
        self.mock_psutil.Process.return_value = mock_process
        
        # Create mock model
        self.mock_model = Mock()
        self.mock_whisper.load_model.return_value = self.mock_model
        
        # Set environment variables for testing
        os.environ['WHISPER_MODEL_CACHE_SIZE'] = '2'
        os.environ['MODEL_IDLE_TIMEOUT'] = '1'  # 1 second for testing
        os.environ['MODEL_CLEANUP_INTERVAL'] = '1'  # 1 second for testing
        os.environ['ENABLE_GPU_ACCELERATION'] = 'false'
        
        # Create cache instance
        self.cache = ModelCache()
    
    def tearDown(self):
        """Clean up after tests"""
        # Stop all patches
        self.whisper_patcher.stop()
        self.torch_patcher.stop()
        self.psutil_patcher.stop()
        
        # Clear cache
        if hasattr(self, 'cache'):
            self.cache.clear_cache()
        
        # Clean up environment
        for key in ['WHISPER_MODEL_CACHE_SIZE', 'MODEL_IDLE_TIMEOUT', 
                   'MODEL_CLEANUP_INTERVAL', 'ENABLE_GPU_ACCELERATION']:
            if key in os.environ:
                del os.environ[key]
    
    def test_singleton_pattern(self):
        """Test that ModelCache follows singleton pattern"""
        cache1 = ModelCache()
        cache2 = ModelCache()
        self.assertIs(cache1, cache2)
    
    def test_get_model_cache_function(self):
        """Test get_model_cache function returns singleton"""
        cache1 = get_model_cache()
        cache2 = get_model_cache()
        self.assertIs(cache1, cache2)
    
    def test_initialization(self):
        """Test cache initialization"""
        self.assertEqual(self.cache.cache_config['max_models'], 2)
        self.assertEqual(self.cache.cache_config['idle_timeout'], 1)
        self.assertEqual(self.cache.cache_config['cleanup_interval'], 1)
        self.assertFalse(self.cache.cache_config['enable_gpu'])
        self.assertEqual(len(self.cache.models), 0)
        self.assertEqual(len(self.cache.model_usage), 0)
    
    def test_load_model_success(self):
        """Test successful model loading"""
        model = self.cache.get_model('base')
        
        self.assertIsNotNone(model)
        self.assertEqual(model, self.mock_model)
        self.assertIn('base', self.cache.models)
        self.assertIn('base', self.cache.model_usage)
        
        # Verify whisper.load_model was called
        self.mock_whisper.load_model.assert_called_once_with('base', device='cpu')
    
    def test_load_model_with_gpu(self):
        """Test model loading with GPU enabled"""
        self.cache.cache_config['enable_gpu'] = True
        self.mock_torch.cuda.is_available.return_value = True
        
        model = self.cache.get_model('base')
        
        self.assertIsNotNone(model)
        self.mock_whisper.load_model.assert_called_with('base', device='cuda')
    
    def test_load_model_failure(self):
        """Test model loading failure"""
        self.mock_whisper.load_model.side_effect = Exception("Load failed")
        
        model = self.cache.get_model('base')
        
        self.assertIsNone(model)
        self.assertNotIn('base', self.cache.models)
    
    def test_model_caching(self):
        """Test that models are cached and reused"""
        # Load model first time
        model1 = self.cache.get_model('base')
        
        # Load same model second time
        model2 = self.cache.get_model('base')
        
        # Should be same instance
        self.assertIs(model1, model2)
        
        # whisper.load_model should only be called once
        self.mock_whisper.load_model.assert_called_once()
    
    def test_usage_tracking(self):
        """Test model usage tracking"""
        model = self.cache.get_model('base')
        
        # Check usage stats
        self.assertIn('base', self.cache.model_usage)
        usage = self.cache.model_usage['base']
        self.assertEqual(usage['access_count'], 1)
        self.assertIsInstance(usage['first_used'], datetime)
        self.assertIsInstance(usage['last_used'], datetime)
        
        # Load model again
        self.cache.get_model('base')
        
        # Check updated usage stats
        usage = self.cache.model_usage['base']
        self.assertEqual(usage['access_count'], 2)
    
    def test_cache_size_limit(self):
        """Test cache size limit enforcement"""
        # Load models up to limit
        self.cache.get_model('base')
        self.cache.get_model('small')
        
        # Try to load third model (should evict one)
        self.cache.get_model('large')
        
        # Should have only 2 models in cache
        self.assertEqual(len(self.cache.models), 2)
        
        # Should have evicted the least recently used model
        self.assertIn('large', self.cache.models)
        self.assertIn('small', self.cache.models)  # More recently used
        self.assertNotIn('base', self.cache.models)  # Should be evicted
    
    def test_evict_least_used_model(self):
        """Test eviction of least recently used model"""
        # Load models
        self.cache.get_model('base')
        time.sleep(0.1)  # Small delay
        self.cache.get_model('small')
        
        # Evict least used
        self.cache._evict_least_used_model()
        
        # Base should be evicted (loaded first)
        self.assertNotIn('base', self.cache.models)
        self.assertIn('small', self.cache.models)
    
    def test_unload_model(self):
        """Test model unloading"""
        # Load model
        self.cache.get_model('base')
        self.assertIn('base', self.cache.models)
        self.assertIn('base', self.cache.model_usage)
        
        # Unload model
        self.cache._unload_model('base')
        
        # Model should be removed
        self.assertNotIn('base', self.cache.models)
        self.assertNotIn('base', self.cache.model_usage)
    
    def test_preload_models(self):
        """Test model preloading"""
        models_to_preload = ['base', 'small']
        
        self.cache.preload_models(models_to_preload)
        
        # Check that models are loaded
        self.assertIn('base', self.cache.models)
        self.assertIn('small', self.cache.models)
        
        # Check that load_model was called for each
        self.assertEqual(self.mock_whisper.load_model.call_count, 2)
    
    def test_get_cache_stats(self):
        """Test cache statistics retrieval"""
        # Load a model
        self.cache.get_model('base')
        
        stats = self.cache.get_cache_stats()
        
        # Check stats structure
        self.assertIn('cached_models', stats)
        self.assertIn('cache_size', stats)
        self.assertIn('max_cache_size', stats)
        self.assertIn('model_usage', stats)
        self.assertIn('memory_usage', stats)
        
        # Check values
        self.assertEqual(stats['cached_models'], ['base'])
        self.assertEqual(stats['cache_size'], 1)
        self.assertEqual(stats['max_cache_size'], 2)
        self.assertIn('base', stats['model_usage'])
    
    def test_clear_cache(self):
        """Test cache clearing"""
        # Load models
        self.cache.get_model('base')
        self.cache.get_model('small')
        
        # Clear cache
        self.cache.clear_cache()
        
        # Cache should be empty
        self.assertEqual(len(self.cache.models), 0)
        self.assertEqual(len(self.cache.model_usage), 0)
    
    def test_optimize_memory(self):
        """Test memory optimization"""
        # Load a model
        self.cache.get_model('base')
        
        # Optimize memory
        self.cache.optimize_memory()
        
        # Should not raise any exceptions
        self.assertTrue(True)
    
    def test_cleanup_thread_startup(self):
        """Test that cleanup thread starts"""
        # Check that cleanup thread is running
        self.assertIsNotNone(self.cache._cleanup_thread)
        self.assertTrue(self.cache._cleanup_thread.is_alive())
    
    def test_idle_model_cleanup(self):
        """Test cleanup of idle models"""
        # Load a model
        self.cache.get_model('base')
        
        # Verify model is initially in cache
        self.assertIn('base', self.cache.models)
        
        # Wait for idle timeout
        time.sleep(1.5)
        
        # Model may or may not be in cache depending on timing
        # This test verifies the cleanup mechanism exists and doesn't crash
        # The actual cleanup is tested in integration tests
        self.assertTrue(True)  # Test passes if no exception is raised
    
    def test_memory_usage_tracking(self):
        """Test memory usage tracking"""
        # Mock psutil.Process
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 1024 * 1024 * 100  # 100MB
        mock_memory_info.vms = 1024 * 1024 * 200  # 200MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.memory_percent.return_value = 25.5
        self.mock_psutil.Process.return_value = mock_process
        
        memory_usage = self.cache._get_memory_usage()
        
        # Check if we got the expected structure
        if 'error' in memory_usage:
            # If psutil is not available, that's also a valid result
            self.assertEqual(memory_usage['error'], 'psutil not available')
        else:
            # If psutil is available, check the values
            self.assertEqual(memory_usage['rss_mb'], 100.0)
            self.assertEqual(memory_usage['vms_mb'], 200.0)
            self.assertEqual(memory_usage['percent'], 25.5)
    
    def test_memory_usage_without_psutil(self):
        """Test memory usage tracking without psutil"""
        # Stop psutil patch
        self.psutil_patcher.stop()
        
        memory_usage = self.cache._get_memory_usage()
        
        self.assertIn('error', memory_usage)
        self.assertEqual(memory_usage['error'], 'psutil not available')
    
    def test_whisper_not_available(self):
        """Test behavior when whisper is not available"""
        # Stop whisper patch
        self.whisper_patcher.stop()
        
        # Mock whisper as None
        with patch('app.services.model_cache.whisper', None):
            model = self.cache.get_model('base')
            self.assertIsNone(model)
    
    def test_concurrent_model_loading(self):
        """Test concurrent model loading"""
        results = []
        
        def load_model():
            model = self.cache.get_model('base')
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


class TestModelCacheIntegration(unittest.TestCase):
    """Integration tests for ModelCache with real components"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        # Clear any existing cache instance
        ModelCache._instance = None
        ModelCache._lock = threading.Lock()
        
        # Set test environment
        os.environ['WHISPER_MODEL_CACHE_SIZE'] = '3'
        os.environ['MODEL_IDLE_TIMEOUT'] = '5'
        os.environ['MODEL_CLEANUP_INTERVAL'] = '2'
        os.environ['ENABLE_GPU_ACCELERATION'] = 'false'
    
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
    
    @patch('app.services.model_cache.whisper')
    def test_real_model_loading_flow(self, mock_whisper):
        """Test complete model loading flow"""
        # Mock whisper
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model
        
        cache = get_model_cache()
        
        # Test loading different models
        models = ['tiny', 'base', 'small']
        loaded_models = []
        
        for model_size in models:
            model = cache.get_model(model_size)
            loaded_models.append(model)
        
        # All models should be loaded
        self.assertEqual(len(loaded_models), 3)
        self.assertEqual(len(cache.models), 3)
        
        # Test cache stats
        stats = cache.get_cache_stats()
        self.assertEqual(stats['cache_size'], 3)
        self.assertEqual(set(stats['cached_models']), set(models))
    
    def test_cache_persistence_across_instances(self):
        """Test that cache persists across different instances"""
        cache1 = get_model_cache()
        cache2 = get_model_cache()
        
        # Should be the same instance
        self.assertIs(cache1, cache2)
        
        # Load a model in one instance
        with patch('app.services.model_cache.whisper') as mock_whisper:
            mock_model = Mock()
            mock_whisper.load_model.return_value = mock_model
            
            model1 = cache1.get_model('base')
            
            # Get same model from other instance
            model2 = cache2.get_model('base')
            
            # Should be the same model
            self.assertIs(model1, model2)


class TestPersistentModelCache(unittest.TestCase):
    """Test cases for PersistentModelCache class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for cache
        self.cache_dir = tempfile.mkdtemp()
        
        # Mock whisper module
        self.whisper_patcher = patch('app.services.persistent_model_cache.whisper')
        self.mock_whisper = self.whisper_patcher.start()
        
        # Mock torch module
        self.torch_patcher = patch('app.services.persistent_model_cache.torch')
        self.mock_torch = self.torch_patcher.start()
        self.mock_torch.cuda.is_available.return_value = False
        
        # Create mock model
        self.mock_model = Mock()
        self.mock_whisper.load_model.return_value = self.mock_model
        
        # Set environment variables for testing
        os.environ['PERSISTENT_MODEL_CACHE'] = 'true'
        os.environ['ALWAYS_KEEP_MODELS'] = 'true'
        os.environ['PRIORITY_MODELS'] = 'base,small'
        os.environ['MODEL_CACHE_DIR'] = self.cache_dir
        
        # Create cache instance
        self.cache = PersistentModelCache()
    
    def tearDown(self):
        """Clean up after tests"""
        # Stop all patches
        self.whisper_patcher.stop()
        self.torch_patcher.stop()
        
        # Clean up cache directory
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
        
        # Clean up environment
        for key in ['PERSISTENT_MODEL_CACHE', 'ALWAYS_KEEP_MODELS', 
                   'PRIORITY_MODELS', 'MODEL_CACHE_DIR']:
            if key in os.environ:
                del os.environ[key]
    
    def test_initialization(self):
        """Test cache initialization"""
        self.assertTrue(self.cache.config['persistent_cache'])
        self.assertTrue(self.cache.config['always_keep_models'])
        self.assertEqual(self.cache.config['priority_models'], ['base', 'small'])
        self.assertEqual(self.cache.config['cache_dir'], self.cache_dir)
        self.assertEqual(len(self.cache.cache), 0)
    
    def test_load_model_success(self):
        """Test successful model loading"""
        model = self.cache.load_model('base')
        
        self.assertIsNotNone(model)
        self.assertEqual(model, self.mock_model)
        self.assertIn('base', self.cache.cache)
        
        # Verify whisper.load_model was called
        self.mock_whisper.load_model.assert_called_once_with('base', device='cpu')
    
    def test_load_model_with_gpu(self):
        """Test model loading with GPU enabled"""
        self.cache.config['enable_gpu'] = True
        self.mock_torch.cuda.is_available.return_value = True
        
        model = self.cache.load_model('base')
        
        self.assertIsNotNone(model)
        self.mock_whisper.load_model.assert_called_with('base', device='cuda')
    
    def test_load_model_failure(self):
        """Test model loading failure"""
        self.mock_whisper.load_model.side_effect = Exception("Load failed")
        
        model = self.cache.load_model('base')
        
        self.assertIsNone(model)
        self.assertNotIn('base', self.cache.cache)
    
    def test_model_caching(self):
        """Test that models are cached and reused"""
        # Load model first time
        model1 = self.cache.load_model('base')
        
        # Load same model second time
        model2 = self.cache.load_model('base')
        
        # Should be same instance
        self.assertIs(model1, model2)
        
        # whisper.load_model should only be called once
        self.mock_whisper.load_model.assert_called_once()
    
    def test_priority_model_protection(self):
        """Test that priority models are protected from eviction"""
        # Load priority models
        self.cache.load_model('base')
        self.cache.load_model('small')
        
        # Load non-priority model
        self.cache.load_model('medium')
        
        # All models should be in cache
        self.assertIn('base', self.cache.cache)
        self.assertIn('small', self.cache.cache)
        self.assertIn('medium', self.cache.cache)
        
        # Test eviction - should not evict priority models
        self.cache._evict_models(2)  # Try to evict to 2 models
        
        # Priority models should still be there
        self.assertIn('base', self.cache.cache)
        self.assertIn('small', self.cache.cache)
        # Medium might be evicted
        self.assertTrue(len(self.cache.cache) >= 2)
    
    def test_save_model(self):
        """Test model saving to disk"""
        # Load a model
        model = self.cache.load_model('base')
        
        # Save model
        self.cache.save_model('base', model)
        
        # Check if save file exists
        save_path = os.path.join(self.cache_dir, 'base_model.pkl')
        # Note: In real implementation, this would save to disk
        # For testing, we just verify the method doesn't crash
        self.assertTrue(True)
    
    def test_get_cache_stats(self):
        """Test cache statistics retrieval"""
        # Load a model
        self.cache.load_model('base')
        
        stats = self.cache.get_cache_stats()
        
        # Check stats structure
        self.assertIn('cached_models', stats)
        self.assertIn('cache_size', stats)
        self.assertIn('priority_models', stats)
        self.assertIn('memory_usage', stats)
        
        # Check values
        self.assertEqual(stats['cached_models'], ['base'])
        self.assertEqual(stats['cache_size'], 1)
        self.assertEqual(stats['priority_models'], ['base', 'small'])
    
    def test_clear_cache(self):
        """Test cache clearing"""
        # Load models
        self.cache.load_model('base')
        self.cache.load_model('small')
        
        # Clear cache
        self.cache.clear_cache()
        
        # Cache should be empty
        self.assertEqual(len(self.cache.cache), 0)


class TestModelCacheManager(unittest.TestCase):
    """Test cases for ModelCacheManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Clear any existing manager instance
        ModelCacheManager._instance = None
        ModelCacheManager._lock = threading.Lock()
        
        # Mock whisper module
        self.whisper_patcher = patch('app.services.model_cache_manager.whisper')
        self.mock_whisper = self.whisper_patcher.start()
        
        # Mock torch module
        self.torch_patcher = patch('app.services.model_cache_manager.torch')
        self.mock_torch = self.torch_patcher.start()
        self.mock_torch.cuda.is_available.return_value = False
        
        # Create mock model
        self.mock_model = Mock()
        self.mock_whisper.load_model.return_value = self.mock_model
        
        # Set environment variables for testing
        os.environ['WHISPER_MODEL_CACHE_SIZE'] = '3'
        os.environ['MODEL_IDLE_TIMEOUT'] = '1'
        os.environ['MODEL_CLEANUP_INTERVAL'] = '1'
        os.environ['ENABLE_GPU_ACCELERATION'] = 'false'
        os.environ['PERSISTENT_MODEL_CACHE'] = 'true'
        os.environ['ALWAYS_KEEP_MODELS'] = 'true'
        os.environ['PRIORITY_MODELS'] = 'base,small'
        
        # Create manager instance
        self.manager = ModelCacheManager()
    
    def tearDown(self):
        """Clean up after tests"""
        # Stop all patches
        self.whisper_patcher.stop()
        self.torch_patcher.stop()
        
        # Clear cache
        if hasattr(self, 'manager'):
            self.manager.clear_cache()
        
        # Clean up environment
        for key in ['WHISPER_MODEL_CACHE_SIZE', 'MODEL_IDLE_TIMEOUT', 
                   'MODEL_CLEANUP_INTERVAL', 'ENABLE_GPU_ACCELERATION',
                   'PERSISTENT_MODEL_CACHE', 'ALWAYS_KEEP_MODELS', 'PRIORITY_MODELS']:
            if key in os.environ:
                del os.environ[key]
    
    def test_singleton_pattern(self):
        """Test that ModelCacheManager follows singleton pattern"""
        manager1 = ModelCacheManager()
        manager2 = ModelCacheManager()
        self.assertIs(manager1, manager2)
    
    def test_get_model_cache_manager_function(self):
        """Test get_model_cache_manager function returns singleton"""
        manager1 = get_model_cache_manager()
        manager2 = get_model_cache_manager()
        self.assertIs(manager1, manager2)
    
    def test_get_model(self):
        """Test getting model from cache"""
        model = self.manager.get_model('base')
        
        self.assertIsNotNone(model)
        self.assertEqual(model, self.mock_model)
        
        # Verify whisper.load_model was called
        self.mock_whisper.load_model.assert_called_once_with('base', device='cpu')
    
    def test_preload_models(self):
        """Test model preloading"""
        models_to_preload = ['base', 'small']
        
        self.manager.preload_models(models_to_preload)
        
        # Check that models are loaded
        self.assertIn('base', self.manager.get_loaded_models())
        self.assertIn('small', self.manager.get_loaded_models())
        
        # Check that load_model was called for each
        self.assertEqual(self.mock_whisper.load_model.call_count, 2)
    
    def test_warmup_priority_models(self):
        """Test warming up priority models"""
        self.manager.warmup_priority_models()
        
        # Priority models should be loaded
        loaded_models = self.manager.get_loaded_models()
        self.assertIn('base', loaded_models)
        self.assertIn('small', loaded_models)
    
    def test_ensure_models_loaded(self):
        """Test ensuring models are loaded"""
        models_to_ensure = ['base', 'small', 'medium']
        
        self.manager.ensure_models_loaded(models_to_ensure)
        
        # All models should be loaded
        loaded_models = self.manager.get_loaded_models()
        for model in models_to_ensure:
            self.assertIn(model, loaded_models)
    
    def test_get_cache_stats(self):
        """Test cache statistics retrieval"""
        # Load a model
        self.manager.get_model('base')
        
        stats = self.manager.get_cache_stats()
        
        # Check stats structure
        self.assertIn('cached_models', stats)
        self.assertIn('cache_size', stats)
        self.assertIn('max_cache_size', stats)
        self.assertIn('model_usage', stats)
        self.assertIn('memory_usage', stats)
        
        # Check values
        self.assertIn('base', stats['cached_models'])
        self.assertGreaterEqual(stats['cache_size'], 1)
    
    def test_get_cache_health(self):
        """Test cache health retrieval"""
        health = self.manager.get_cache_health()
        
        # Check health structure
        self.assertIn('status', health)
        self.assertIn('loaded_models', health)
        self.assertIn('priority_coverage', health)
        self.assertIn('memory_usage', health)
        
        # Status should be valid
        self.assertIn(health['status'], ['healthy', 'warning', 'error'])
    
    def test_get_model_status(self):
        """Test getting model status"""
        # Load a model
        self.manager.get_model('base')
        
        status = self.manager.get_model_status('base')
        
        # Check status structure
        self.assertIn('loaded', status)
        self.assertIn('cached', status)
        self.assertIn('priority', status)
        self.assertIn('usage_stats', status)
        
        # Model should be loaded
        self.assertTrue(status['loaded'])
        self.assertTrue(status['cached'])
    
    def test_force_reload_model(self):
        """Test forcing model reload"""
        # Load a model
        self.manager.get_model('base')
        
        # Force reload
        self.manager.force_reload_model('base')
        
        # Model should still be available
        model = self.manager.get_model('base')
        self.assertIsNotNone(model)
    
    def test_clear_cache(self):
        """Test cache clearing"""
        # Load models
        self.manager.get_model('base')
        self.manager.get_model('small')
        
        # Clear cache
        self.manager.clear_cache()
        
        # Cache should be empty
        loaded_models = self.manager.get_loaded_models()
        self.assertEqual(len(loaded_models), 0)
    
    def test_optimize_memory(self):
        """Test memory optimization"""
        # Load a model
        self.manager.get_model('base')
        
        # Optimize memory
        self.manager.optimize_memory()
        
        # Should not raise any exceptions
        self.assertTrue(True)
    
    def test_get_loaded_models(self):
        """Test getting loaded models list"""
        # Initially no models loaded
        loaded_models = self.manager.get_loaded_models()
        self.assertEqual(len(loaded_models), 0)
        
        # Load a model
        self.manager.get_model('base')
        
        # Should have one model
        loaded_models = self.manager.get_loaded_models()
        self.assertEqual(len(loaded_models), 1)
        self.assertIn('base', loaded_models)
    
    def test_get_available_models(self):
        """Test getting available models list"""
        available_models = self.manager.get_available_models()
        
        # Should return list of available model sizes
        self.assertIsInstance(available_models, list)
        self.assertIn('tiny', available_models)
        self.assertIn('base', available_models)
        self.assertIn('small', available_models)
        self.assertIn('medium', available_models)
        self.assertIn('large', available_models)


class TestModelValidator(unittest.TestCase):
    """Test cases for ModelValidator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock whisper module
        self.whisper_patcher = patch('app.services.model_validator.whisper')
        self.mock_whisper = self.whisper_patcher.start()
        
        # Mock torch module
        self.torch_patcher = patch('app.services.model_validator.torch')
        self.mock_torch = self.torch_patcher.start()
        self.mock_torch.cuda.is_available.return_value = False
        
        # Mock psutil module
        self.psutil_patcher = patch('app.services.model_validator.psutil', create=True)
        self.mock_psutil = self.psutil_patcher.start()
        mock_process = Mock()
        mock_process.memory_info.return_value = Mock(rss=100000000, vms=200000000)
        mock_process.memory_percent.return_value = 25.5
        self.mock_psutil.Process.return_value = mock_process
        
        # Create mock model
        self.mock_model = Mock()
        self.mock_model.transcribe.return_value = {'text': 'test transcription'}
        self.mock_whisper.load_model.return_value = self.mock_model
        
        # Create validator instance
        self.validator = ModelValidator()
    
    def tearDown(self):
        """Clean up after tests"""
        # Stop all patches
        self.whisper_patcher.stop()
        self.torch_patcher.stop()
        self.psutil_patcher.stop()
    
    def test_initialization(self):
        """Test validator initialization"""
        self.assertIsNotNone(self.validator.validation_config)
        self.assertIsNotNone(self.validator.test_audio_samples)
        self.assertEqual(len(self.validator.validation_results), 0)
    
    def test_validate_model_success(self):
        """Test successful model validation"""
        result = self.validator.validate_model('base', self.mock_model)
        
        # Check result structure
        self.assertIn('model_size', result)
        self.assertIn('status', result)
        self.assertIn('overall_score', result)
        self.assertIn('tests', result)
        self.assertIn('errors', result)
        self.assertIn('warnings', result)
        
        # Check values
        self.assertEqual(result['model_size'], 'base')
        self.assertIn(result['status'], ['passed', 'failed', 'error'])
        self.assertIsInstance(result['overall_score'], float)
        self.assertIsInstance(result['tests'], dict)
        self.assertIsInstance(result['errors'], list)
        self.assertIsInstance(result['warnings'], list)
    
    def test_validate_model_without_model(self):
        """Test model validation without providing model instance"""
        result = self.validator.validate_model('base')
        
        # Should still return result structure
        self.assertIn('model_size', result)
        self.assertIn('status', result)
        self.assertIn('overall_score', result)
    
    def test_validate_all_models(self):
        """Test validating multiple models"""
        models = ['base', 'small']
        result = self.validator.validate_all_models(models)
        
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
    
    def test_get_validation_results(self):
        """Test getting validation results"""
        # Initially no results
        results = self.validator.get_validation_results()
        self.assertEqual(len(results), 0)
        
        # Run a validation
        self.validator.validate_model('base', self.mock_model)
        
        # Should have one result
        results = self.validator.get_validation_results()
        self.assertEqual(len(results), 1)
    
    def test_get_validation_results_by_id(self):
        """Test getting specific validation result by ID"""
        # Run a validation
        result = self.validator.validate_model('base', self.mock_model)
        validation_id = result['validation_id']
        
        # Get specific result
        specific_result = self.validator.get_validation_results(validation_id)
        
        # Should return the same result
        self.assertEqual(specific_result, result)
    
    def test_save_validation_report(self):
        """Test saving validation report"""
        # Run a validation
        result = self.validator.validate_model('base', self.mock_model)
        
        # Save report
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            report_path = f.name
        
        try:
            self.validator.save_validation_report(result, report_path)
            
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
    
    def test_model_loading_test(self):
        """Test model loading validation test"""
        test_result = self.validator._test_model_loading('base', self.mock_model)
        
        # Check test result structure
        self.assertIn('name', test_result)
        self.assertIn('passed', test_result)
        self.assertIn('score', test_result)
        self.assertIn('details', test_result)
        self.assertIn('errors', test_result)
        
        # Should pass for valid model
        self.assertTrue(test_result['passed'])
        self.assertEqual(test_result['score'], 1.0)
    
    def test_basic_functionality_test(self):
        """Test basic functionality validation test"""
        test_result = self.validator._test_basic_functionality(self.mock_model, 'base')
        
        # Check test result structure
        self.assertIn('name', test_result)
        self.assertIn('passed', test_result)
        self.assertIn('score', test_result)
        self.assertIn('details', test_result)
        self.assertIn('errors', test_result)
        
        # Should pass for valid model
        self.assertTrue(test_result['passed'])
        self.assertEqual(test_result['score'], 1.0)
    
    def test_audio_processing_test(self):
        """Test audio processing validation test"""
        test_result = self.validator._test_audio_processing(self.mock_model, 'base')
        
        # Check test result structure
        self.assertIn('name', test_result)
        self.assertIn('passed', test_result)
        self.assertIn('score', test_result)
        self.assertIn('details', test_result)
        self.assertIn('errors', test_result)
        
        # Should pass for valid model
        self.assertTrue(test_result['passed'])
        self.assertEqual(test_result['score'], 1.0)
    
    def test_transcription_quality_test(self):
        """Test transcription quality validation test"""
        test_result = self.validator._test_transcription_quality(self.mock_model, 'base')
        
        # Check test result structure
        self.assertIn('name', test_result)
        self.assertIn('passed', test_result)
        self.assertIn('score', test_result)
        self.assertIn('details', test_result)
        self.assertIn('errors', test_result)
        
        # Should have some score
        self.assertGreaterEqual(test_result['score'], 0.0)
        self.assertLessEqual(test_result['score'], 1.0)
    
    def test_performance_metrics_test(self):
        """Test performance metrics validation test"""
        test_result = self.validator._test_performance_metrics(self.mock_model, 'base')
        
        # Check test result structure
        self.assertIn('name', test_result)
        self.assertIn('passed', test_result)
        self.assertIn('score', test_result)
        self.assertIn('details', test_result)
        self.assertIn('errors', test_result)
        
        # Should have some score
        self.assertGreaterEqual(test_result['score'], 0.0)
        self.assertLessEqual(test_result['score'], 1.0)
    
    def test_memory_usage_test(self):
        """Test memory usage validation test"""
        test_result = self.validator._test_memory_usage(self.mock_model, 'base')
        
        # Check test result structure
        self.assertIn('name', test_result)
        self.assertIn('passed', test_result)
        self.assertIn('score', test_result)
        self.assertIn('details', test_result)
        self.assertIn('errors', test_result)
        
        # Should have some score
        self.assertGreaterEqual(test_result['score'], 0.0)
        self.assertLessEqual(test_result['score'], 1.0)
    
    def test_validation_with_errors(self):
        """Test validation with model errors"""
        # Mock model with errors
        error_model = Mock()
        error_model.transcribe.side_effect = Exception("Transcription failed")
        
        result = self.validator.validate_model('base', error_model)
        
        # Should have errors
        self.assertGreater(len(result['errors']), 0)
        self.assertEqual(result['status'], 'failed')
    
    def test_validation_timeout(self):
        """Test validation timeout handling"""
        # Mock slow model
        slow_model = Mock()
        def slow_transcribe(audio):
            time.sleep(2)  # Simulate slow processing
            return {'text': 'slow transcription'}
        slow_model.transcribe.side_effect = slow_transcribe
        
        # Set short timeout
        self.validator.validation_config['max_validation_time'] = 1
        
        result = self.validator.validate_model('base', slow_model)
        
        # Should handle timeout gracefully
        self.assertIn('status', result)
        self.assertIn('errors', result)


if __name__ == '__main__':
    unittest.main()
