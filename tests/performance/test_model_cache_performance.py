"""
Performance tests for Model Cache system
Tests the performance improvements and benchmarks of the caching system
"""

import unittest
import os
import sys
import time
import threading
import statistics
from unittest.mock import patch, Mock
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.model_cache import ModelCache, get_model_cache


class TestModelCachePerformance(unittest.TestCase):
    """Performance tests for ModelCache"""
    
    def setUp(self):
        """Set up performance test fixtures"""
        # Clear any existing cache instance
        ModelCache._instance = None
        ModelCache._lock = threading.Lock()
        
        # Set test environment
        os.environ['WHISPER_MODEL_CACHE_SIZE'] = '3'
        os.environ['MODEL_IDLE_TIMEOUT'] = '10'  # 10 seconds for testing
        os.environ['MODEL_CLEANUP_INTERVAL'] = '5'  # 5 seconds for testing
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
    def test_model_loading_performance(self, mock_whisper):
        """Test model loading performance with and without cache"""
        # Mock whisper with simulated loading time
        def mock_load_model(model_size, device='cpu'):
            time.sleep(0.1)  # Simulate 100ms loading time
            return Mock()
        
        mock_whisper.load_model.side_effect = mock_load_model
        
        cache = get_model_cache()
        
        # Test without cache (first load)
        start_time = time.time()
        model1 = cache.get_model('base')
        first_load_time = time.time() - start_time
        
        self.assertIsNotNone(model1)
        self.assertGreaterEqual(first_load_time, 0.1)  # Should take at least 100ms
        
        # Test with cache (second load)
        start_time = time.time()
        model2 = cache.get_model('base')
        second_load_time = time.time() - start_time
        
        self.assertIsNotNone(model2)
        self.assertIs(model1, model2)  # Should be same instance
        self.assertLess(second_load_time, 0.01)  # Should be much faster (< 10ms)
        
        # Verify performance improvement
        performance_improvement = first_load_time / second_load_time
        self.assertGreater(performance_improvement, 10)  # At least 10x faster
    
    @patch('app.services.model_cache.whisper')
    def test_concurrent_model_loading_performance(self, mock_whisper):
        """Test concurrent model loading performance"""
        # Mock whisper with simulated loading time
        def mock_load_model(model_size, device='cpu'):
            time.sleep(0.05)  # Simulate 50ms loading time
            return Mock()
        
        mock_whisper.load_model.side_effect = mock_load_model
        
        cache = get_model_cache()
        results = []
        load_times = []
        
        def load_model():
            start_time = time.time()
            model = cache.get_model('base')
            load_time = time.time() - start_time
            results.append(model)
            load_times.append(load_time)
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=load_model)
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # All results should be the same model instance
        self.assertEqual(len(results), 10)
        for result in results:
            self.assertIs(result, results[0])
        
        # whisper.load_model should only be called once
        mock_whisper.load_model.assert_called_once()
        
        # Total time should be close to single load time (not 10x)
        self.assertLess(total_time, 0.2)  # Should be much less than 10 * 0.05
        
        # All individual load times should be very fast (cached)
        for load_time in load_times:
            self.assertLess(load_time, 0.01)  # Should be < 10ms
    
    @patch('app.services.model_cache.whisper')
    def test_cache_eviction_performance(self, mock_whisper):
        """Test cache eviction performance"""
        # Mock whisper
        mock_whisper.load_model.return_value = Mock()
        
        cache = get_model_cache()
        
        # Load models up to cache limit
        models = ['tiny', 'base', 'small']
        for model_size in models:
            cache.get_model(model_size)
        
        # Verify all models are cached
        self.assertEqual(len(cache.models), 3)
        
        # Load one more model (should evict one)
        start_time = time.time()
        cache.get_model('medium')
        eviction_time = time.time() - start_time
        
        # Eviction should be fast
        self.assertLess(eviction_time, 0.01)  # Should be < 10ms
        
        # Should still have 3 models
        self.assertEqual(len(cache.models), 3)
        self.assertIn('medium', cache.models)
    
    @patch('app.services.model_cache.whisper')
    def test_memory_usage_performance(self, mock_whisper):
        """Test memory usage and optimization performance"""
        # Mock whisper
        mock_whisper.load_model.return_value = Mock()
        
        cache = get_model_cache()
        
        # Load multiple models
        models = ['tiny', 'base', 'small', 'medium']
        for model_size in models:
            cache.get_model(model_size)
        
        # Test memory optimization performance
        start_time = time.time()
        cache.optimize_memory()
        optimization_time = time.time() - start_time
        
        # Memory optimization should be fast
        self.assertLess(optimization_time, 0.1)  # Should be < 100ms
        
        # Models should still be available
        self.assertGreater(len(cache.models), 0)
    
    @patch('app.services.model_cache.whisper')
    def test_cache_statistics_performance(self, mock_whisper):
        """Test cache statistics retrieval performance"""
        # Mock whisper
        mock_whisper.load_model.return_value = Mock()
        
        cache = get_model_cache()
        
        # Load some models
        cache.get_model('base')
        cache.get_model('small')
        
        # Test statistics retrieval performance
        start_time = time.time()
        stats = cache.get_cache_stats()
        stats_time = time.time() - start_time
        
        # Statistics retrieval should be fast
        self.assertLess(stats_time, 0.01)  # Should be < 10ms
        
        # Verify stats structure
        self.assertIn('cached_models', stats)
        self.assertIn('cache_size', stats)
        self.assertIn('model_usage', stats)
        self.assertIn('memory_usage', stats)
    
    @patch('app.services.model_cache.whisper')
    def test_preloading_performance(self, mock_whisper):
        """Test model preloading performance"""
        # Mock whisper with simulated loading time
        def mock_load_model(model_size, device='cpu'):
            time.sleep(0.1)  # Simulate 100ms loading time
            return Mock()
        
        mock_whisper.load_model.side_effect = mock_load_model
        
        cache = get_model_cache()
        
        # Test preloading performance
        models_to_preload = ['base', 'small']
        
        start_time = time.time()
        cache.preload_models(models_to_preload)
        preload_time = time.time() - start_time
        
        # Preloading should take time for each model
        self.assertGreaterEqual(preload_time, 0.2)  # Should take at least 200ms (2 * 100ms)
        
        # Models should be cached
        for model_size in models_to_preload:
            self.assertIn(model_size, cache.models)
        
        # Test that preloaded models are immediately available
        start_time = time.time()
        model = cache.get_model('base')
        access_time = time.time() - start_time
        
        self.assertIsNotNone(model)
        self.assertLess(access_time, 0.01)  # Should be very fast (< 10ms)
    
    @patch('app.services.model_cache.whisper')
    def test_cleanup_performance(self, mock_whisper):
        """Test cache cleanup performance"""
        # Mock whisper
        mock_whisper.load_model.return_value = Mock()
        
        cache = get_model_cache()
        
        # Load some models
        cache.get_model('base')
        cache.get_model('small')
        
        # Test cache clearing performance
        start_time = time.time()
        cache.clear_cache()
        clear_time = time.time() - start_time
        
        # Cache clearing should be fast
        self.assertLess(clear_time, 0.01)  # Should be < 10ms
        
        # Cache should be empty
        self.assertEqual(len(cache.models), 0)
        self.assertEqual(len(cache.model_usage), 0)
    
    @patch('app.services.model_cache.whisper')
    def test_usage_tracking_performance(self, mock_whisper):
        """Test usage tracking performance"""
        # Mock whisper
        mock_whisper.load_model.return_value = Mock()
        
        cache = get_model_cache()
        
        # Test usage tracking performance
        start_time = time.time()
        
        # Load model multiple times
        for _ in range(100):
            cache.get_model('base')
        
        total_time = time.time() - start_time
        
        # Should be very fast (cached after first load)
        self.assertLess(total_time, 0.1)  # Should be < 100ms for 100 accesses
        
        # Verify usage tracking
        usage = cache.model_usage['base']
        self.assertEqual(usage['access_count'], 100)
        
        # whisper.load_model should only be called once
        mock_whisper.load_model.assert_called_once()
    
    @patch('app.services.model_cache.whisper')
    def test_mixed_workload_performance(self, mock_whisper):
        """Test performance with mixed workload"""
        # Mock whisper with simulated loading time
        def mock_load_model(model_size, device='cpu'):
            time.sleep(0.05)  # Simulate 50ms loading time
            return Mock()
        
        mock_whisper.load_model.side_effect = mock_load_model
        
        cache = get_model_cache()
        
        # Simulate mixed workload
        models = ['tiny', 'base', 'small', 'medium', 'large']
        access_pattern = ['base', 'small', 'base', 'tiny', 'base', 'small', 'medium', 'base']
        
        start_time = time.time()
        
        for model_size in access_pattern:
            cache.get_model(model_size)
        
        total_time = time.time() - start_time
        
        # Should be much faster than loading each model individually
        # (5 models * 50ms = 250ms, but with caching should be much less)
        self.assertLess(total_time, 0.3)  # Should be < 300ms
        
        # Verify that only unique models were loaded
        unique_models = set(access_pattern)
        self.assertEqual(mock_whisper.load_model.call_count, len(unique_models))
    
    @patch('app.services.model_cache.whisper')
    def test_cache_hit_ratio_performance(self, mock_whisper):
        """Test cache hit ratio performance"""
        # Mock whisper
        mock_whisper.load_model.return_value = Mock()
        
        cache = get_model_cache()
        
        # Simulate workload with high cache hit ratio
        access_pattern = ['base'] * 50 + ['small'] * 30 + ['base'] * 20
        
        start_time = time.time()
        
        for model_size in access_pattern:
            cache.get_model(model_size)
        
        total_time = time.time() - start_time
        
        # Should be very fast due to high cache hit ratio
        self.assertLess(total_time, 0.05)  # Should be < 50ms
        
        # Only 2 unique models should have been loaded
        self.assertEqual(mock_whisper.load_model.call_count, 2)
        
        # Verify cache hit ratio
        total_accesses = len(access_pattern)
        cache_misses = mock_whisper.load_model.call_count
        cache_hit_ratio = (total_accesses - cache_misses) / total_accesses
        
        self.assertGreater(cache_hit_ratio, 0.95)  # Should have > 95% hit ratio


class TestModelCacheBenchmarks(unittest.TestCase):
    """Benchmark tests for ModelCache performance"""
    
    def setUp(self):
        """Set up benchmark test fixtures"""
        # Clear any existing cache instance
        ModelCache._instance = None
        ModelCache._lock = threading.Lock()
        
        # Set test environment
        os.environ['WHISPER_MODEL_CACHE_SIZE'] = '5'
        os.environ['MODEL_IDLE_TIMEOUT'] = '30'
        os.environ['MODEL_CLEANUP_INTERVAL'] = '10'
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
    def test_benchmark_model_loading_times(self, mock_whisper):
        """Benchmark model loading times"""
        # Mock whisper with realistic loading times
        loading_times = {
            'tiny': 0.1,    # 100ms
            'base': 0.2,    # 200ms
            'small': 0.5,   # 500ms
            'medium': 1.0,  # 1000ms
            'large': 2.0    # 2000ms
        }
        
        def mock_load_model(model_size, device='cpu'):
            time.sleep(loading_times[model_size])
            return Mock()
        
        mock_whisper.load_model.side_effect = mock_load_model
        
        cache = get_model_cache()
        results = {}
        
        # Benchmark each model size
        for model_size, expected_time in loading_times.items():
            # First load (cache miss)
            start_time = time.time()
            model1 = cache.get_model(model_size)
            first_load_time = time.time() - start_time
            
            # Second load (cache hit)
            start_time = time.time()
            model2 = cache.get_model(model_size)
            second_load_time = time.time() - start_time
            
            results[model_size] = {
                'first_load': first_load_time,
                'second_load': second_load_time,
                'improvement': first_load_time / second_load_time if second_load_time > 0 else float('inf')
            }
            
            # Verify performance
            self.assertGreaterEqual(first_load_time, expected_time * 0.9)  # Allow 10% tolerance
            self.assertLess(second_load_time, 0.01)  # Should be < 10ms
            self.assertGreater(results[model_size]['improvement'], 10)  # At least 10x improvement
        
        # Print benchmark results
        print("\nModel Loading Performance Benchmarks:")
        print("=" * 60)
        for model_size, result in results.items():
            print(f"{model_size:>6}: First={result['first_load']:.3f}s, "
                  f"Second={result['second_load']:.3f}s, "
                  f"Improvement={result['improvement']:.1f}x")
    
    @patch('app.services.model_cache.whisper')
    def test_benchmark_concurrent_access(self, mock_whisper):
        """Benchmark concurrent access performance"""
        # Mock whisper
        mock_whisper.load_model.return_value = Mock()
        
        cache = get_model_cache()
        
        # Benchmark different concurrency levels
        concurrency_levels = [1, 5, 10, 20, 50]
        results = {}
        
        for num_threads in concurrency_levels:
            start_time = time.time()
            
            def load_model():
                cache.get_model('base')
            
            threads = []
            for _ in range(num_threads):
                thread = threading.Thread(target=load_model)
                threads.append(thread)
            
            # Start all threads
            for thread in threads:
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            total_time = time.time() - start_time
            results[num_threads] = total_time
            
            # Reset mock call count
            mock_whisper.reset_mock()
        
        # Print benchmark results
        print("\nConcurrent Access Performance Benchmarks:")
        print("=" * 60)
        for num_threads, total_time in results.items():
            print(f"{num_threads:>2} threads: {total_time:.3f}s total")
        
        # Verify that higher concurrency doesn't significantly increase time
        self.assertLess(results[50], results[1] * 2)  # 50 threads should be < 2x 1 thread


if __name__ == '__main__':
    unittest.main()
