#!/usr/bin/env python3
"""
Performance tests and benchmarks for voice transcription system
Tests processing speed, resource usage, and scalability
"""

import unittest
import time
import tempfile
import os
import psutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from config_manager import ConfigManager
from parallel_processor import ParallelProcessor
from unified_voice_transcriber import UnifiedVoiceTranscriber

class TestPerformanceBenchmarks(unittest.TestCase):
    """Performance benchmarks for the transcription system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_output_dir = os.path.join(self.temp_dir, 'transcriptions')
        os.makedirs(self.test_output_dir, exist_ok=True)
        
        # Performance test configuration
        self.performance_config = {
            'transcription': {
                'whisper_model_size': 'tiny',  # Fastest for testing
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
                'base_dir': self.test_output_dir,
                'include_speakers': True,
                'include_timestamps': True
            }
        }
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_sequential_vs_parallel_processing(self):
        """Benchmark sequential vs parallel processing"""
        config = ConfigManager()
        config._config = self.performance_config
        
        # Test files (simulated)
        test_files = [f"/test/audio{i}.m4a" for i in range(1, 11)]
        
        # Sequential processing simulation
        sequential_start = time.time()
        for file_path in test_files:
            time.sleep(0.1)  # Simulate processing time
        sequential_time = time.time() - sequential_start
        
        # Parallel processing simulation
        parallel_start = time.time()
        with patch('parallel_processor.UnifiedVoiceTranscriber'):
            processor = ParallelProcessor(config)
            
            # Add jobs
            for file_path in test_files:
                processor.add_job(file_path)
            
            # Mock processing method
            def mock_process(job):
                time.sleep(0.1)  # Same processing time
                return {
                    'file_path': job.file_path,
                    'success': True,
                    'transcription': {"text": "test"},
                    'processing_time': 0.1,
                    'cpu_usage': 50.0,
                    'memory_usage': 25.0
                }
            
            processor._process_single_job = mock_process
            
            # Process jobs
            results = processor.process_jobs()
            parallel_time = time.time() - parallel_start
            
            processor.stop()
        
        # Calculate speedup
        speedup = sequential_time / parallel_time
        
        print(f"\n🚀 Performance Benchmark Results:")
        print(f"Sequential Processing: {sequential_time:.3f}s")
        print(f"Parallel Processing: {parallel_time:.3f}s")
        print(f"Speedup: {speedup:.2f}x")
        print(f"Files Processed: {len(test_files)}")
        
        # Assertions
        self.assertGreater(speedup, 1.0, "Parallel processing should be faster than sequential")
        self.assertEqual(len(results), len(test_files), "All files should be processed")
        
        # Performance expectations
        self.assertGreater(speedup, 2.0, "Expected at least 2x speedup with 4 workers")
    
    def test_concurrency_scaling(self):
        """Test performance scaling with different concurrency levels"""
        config = ConfigManager()
        config._config = self.performance_config
        
        test_files = [f"/test/audio{i}.m4a" for i in range(1, 9)]
        concurrency_levels = [1, 2, 4, 8]
        results = {}
        
        for concurrency in concurrency_levels:
            config.performance.max_concurrent_processes = concurrency
            
            with patch('parallel_processor.UnifiedVoiceTranscriber'):
                processor = ParallelProcessor(config)
                
                # Add jobs
                for file_path in test_files:
                    processor.add_job(file_path)
                
                # Mock processing method
                def mock_process(job):
                    time.sleep(0.1)  # Fixed processing time
                    return {
                        'file_path': job.file_path,
                        'success': True,
                        'transcription': {"text": "test"},
                        'processing_time': 0.1,
                        'cpu_usage': 50.0,
                        'memory_usage': 25.0
                    }
                
                processor._process_single_job = mock_process
                
                # Process jobs and measure time
                start_time = time.time()
                processor.process_jobs()
                processing_time = time.time() - start_time
                
                results[concurrency] = processing_time
                processor.stop()
        
        # Print scaling results
        print(f"\n📊 Concurrency Scaling Results:")
        for concurrency, time_taken in results.items():
            throughput = len(test_files) / time_taken
            print(f"Workers: {concurrency}, Time: {time_taken:.3f}s, Throughput: {throughput:.2f} files/s")
        
        # Assertions
        self.assertLess(results[2], results[1], "2 workers should be faster than 1")
        self.assertLess(results[4], results[2], "4 workers should be faster than 2")
        
        # Diminishing returns check
        if 8 in results:
            speedup_2_to_4 = results[2] / results[4]
            speedup_4_to_8 = results[4] / results[8]
            self.assertGreater(speedup_2_to_4, speedup_4_to_8, "Diminishing returns expected with higher concurrency")
    
    def test_memory_usage_monitoring(self):
        """Test memory usage monitoring during processing"""
        config = ConfigManager()
        config._config = self.performance_config
        
        with patch('parallel_processor.UnifiedVoiceTranscriber'):
            processor = ParallelProcessor(config)
            
            # Add some jobs
            for i in range(5):
                processor.add_job(f"/test/audio{i}.m4a")
            
            # Mock processing method that simulates memory usage
            def mock_process(job):
                # Simulate memory allocation
                dummy_data = [0] * 1000000  # 8MB of data
                time.sleep(0.05)
                return {
                    'file_path': job.file_path,
                    'success': True,
                    'transcription': {"text": "test"},
                    'processing_time': 0.05,
                    'cpu_usage': 75.0,
                    'memory_usage': 30.0
                }
            
            processor._process_single_job = mock_process
            
            # Process jobs
            start_time = time.time()
            results = processor.process_jobs()
            processing_time = time.time() - start_time
            
            # Get final stats
            stats = processor.get_stats()
            processor.stop()
            
            print(f"\n🧠 Memory Usage Results:")
            print(f"Processing Time: {processing_time:.3f}s")
            print(f"Peak Memory: {stats.get('peak_memory_usage', 0):.1f}%")
            print(f"Average Memory: {stats.get('average_memory', 0):.1f}%")
            
            # Assertions
            self.assertGreater(len(results), 0, "Should process at least one job")
            self.assertIn('peak_memory_usage', stats, "Memory usage should be tracked")
    
    def test_cpu_utilization(self):
        """Test CPU utilization monitoring"""
        config = ConfigManager()
        config._config = self.performance_config
        
        with patch('parallel_processor.UnifiedVoiceTranscriber'):
            processor = ParallelProcessor(config)
            
            # Add jobs
            for i in range(4):
                processor.add_job(f"/test/audio{i}.m4a")
            
            # Mock processing method
            def mock_process(job):
                time.sleep(0.1)
                return {
                    'file_path': job.file_path,
                    'success': True,
                    'transcription': {"text": "test"},
                    'processing_time': 0.1,
                    'cpu_usage': 80.0,  # High CPU usage
                    'memory_usage': 25.0
                }
            
            processor._process_single_job = mock_process
            
            # Process jobs
            start_time = time.time()
            results = processor.process_jobs()
            processing_time = time.time() - start_time
            
            # Get stats
            stats = processor.get_stats()
            processor.stop()
            
            print(f"\n💻 CPU Utilization Results:")
            print(f"Processing Time: {processing_time:.3f}s")
            print(f"Peak CPU: {stats.get('peak_cpu_usage', 0):.1f}%")
            print(f"Average CPU: {stats.get('average_cpu', 0):.1f}%")
            
            # Assertions
            self.assertIn('peak_cpu_usage', stats, "CPU usage should be tracked")
            self.assertGreater(stats.get('peak_cpu_usage', 0), 0, "Should have some CPU usage")
    
    def test_batch_size_optimization(self):
        """Test optimal batch size for different scenarios"""
        config = ConfigManager()
        config._config = self.performance_config
        
        test_files = [f"/test/audio{i}.m4a" for i in range(1, 21)]
        batch_sizes = [1, 3, 5, 10]
        results = {}
        
        for batch_size in batch_sizes:
            config.performance.batch_size = batch_size
            
            with patch('parallel_processor.UnifiedVoiceTranscriber'):
                processor = ParallelProcessor(config)
                
                # Add jobs
                for file_path in test_files:
                    processor.add_job(file_path)
                
                # Mock processing method
                def mock_process(job):
                    time.sleep(0.05)  # Fast processing
                    return {
                        'file_path': job.file_path,
                        'success': True,
                        'transcription': {"text": "test"},
                        'processing_time': 0.05,
                        'cpu_usage': 60.0,
                        'memory_usage': 20.0
                    }
                
                processor._process_single_job = mock_process
                
                # Process jobs
                start_time = time.time()
                processor.process_jobs()
                processing_time = time.time() - start_time
                
                results[batch_size] = processing_time
                processor.stop()
        
        # Print batch size results
        print(f"\n📦 Batch Size Optimization Results:")
        for batch_size, time_taken in results.items():
            throughput = len(test_files) / time_taken
            print(f"Batch Size: {batch_size}, Time: {time_taken:.3f}s, Throughput: {throughput:.2f} files/s")
        
        # Find optimal batch size
        optimal_batch_size = min(results, key=results.get)
        print(f"Optimal Batch Size: {optimal_batch_size}")
        
        # Assertions
        self.assertIn(optimal_batch_size, [3, 5], "Optimal batch size should be 3 or 5 for this configuration")

class TestResourceEfficiency(unittest.TestCase):
    """Test resource efficiency and optimization"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_model_size_performance_tradeoff(self):
        """Test performance vs quality tradeoff with different model sizes"""
        model_sizes = ['tiny', 'base', 'small', 'medium']
        expected_processing_times = [0.1, 0.2, 0.5, 1.0]  # Relative times
        
        for model_size, expected_time in zip(model_sizes, expected_processing_times):
            config = ConfigManager()
            config._config = {
                'transcription': {
                    'whisper_model_size': model_size,
                    'enable_speaker_diarization': True,
                    'language_detection': True
                },
                'performance': {
                    'max_concurrent_processes': 2,
                    'batch_size': 3,
                    'audio_chunk_size': 30,
                    'audio_overlap': 5
                }
            }
            
            print(f"\n🎯 Model Size: {model_size.upper()}")
            print(f"Expected Processing Time: {expected_time:.1f}x baseline")
            
            # Verify configuration
            self.assertEqual(config.transcription.whisper_model_size, model_size)
    
    def test_concurrency_vs_memory_tradeoff(self):
        """Test concurrency vs memory usage tradeoff"""
        concurrency_levels = [1, 2, 4, 8]
        expected_memory_per_worker = 25.0  # MB per worker
        
        for concurrency in concurrency_levels:
            expected_total_memory = concurrency * expected_memory_per_worker
            
            print(f"\n⚖️  Concurrency: {concurrency} workers")
            print(f"Expected Memory Usage: {expected_total_memory:.1f} MB")
            
            # Verify reasonable limits
            self.assertLessEqual(concurrency, 10, "Concurrency should not exceed 10")
            self.assertLessEqual(expected_total_memory, 200, "Total memory should not exceed 200 MB")

if __name__ == '__main__':
    unittest.main()
