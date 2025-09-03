"""
Load Testing for Voice Transcriber
Tests concurrent users, high volume, and system scalability
"""

import unittest
import threading
import time
import requests
import json
import os
import sys
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from io import BytesIO
import tempfile

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.fixtures.test_audio_files import TestAudioFixtures


class LoadTestConfig:
    """Configuration for load tests"""
    
    def __init__(self):
        self.base_url = os.getenv('TEST_BASE_URL', 'http://localhost:5001')
        self.max_concurrent_users = int(os.getenv('MAX_CONCURRENT_USERS', 50))
        self.test_duration = int(os.getenv('TEST_DURATION', 60))  # seconds
        self.requests_per_user = int(os.getenv('REQUESTS_PER_USER', 10))
        self.upload_file_size_mb = float(os.getenv('UPLOAD_FILE_SIZE_MB', 5.0))
        self.timeout = int(os.getenv('REQUEST_TIMEOUT', 30))


class ConcurrentLoadTest(unittest.TestCase):
    """Test concurrent user load"""
    
    def setUp(self):
        """Set up load test fixtures"""
        self.config = LoadTestConfig()
        self.results = {
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'errors': [],
            'start_time': None,
            'end_time': None
        }
        
        # Create test audio file
        self.test_audio_file = TestAudioFixtures.create_test_wav_file(
            duration=30,  # 30 seconds
            filename="load_test_audio.wav"
        )
        
        # Verify server is running
        try:
            response = requests.get(f"{self.config.base_url}/health", timeout=5)
            if response.status_code != 200:
                self.skipTest("Server not running or not healthy")
        except requests.exceptions.RequestException:
            self.skipTest("Server not accessible")
    
    def tearDown(self):
        """Clean up after tests"""
        # Clean up test file
        if os.path.exists(self.test_audio_file):
            os.remove(self.test_audio_file)
            # Remove parent directory if empty
            parent_dir = os.path.dirname(self.test_audio_file)
            try:
                os.rmdir(parent_dir)
            except OSError:
                pass
    
    def test_concurrent_file_uploads(self):
        """Test concurrent file uploads"""
        print(f"\n🚀 Testing concurrent file uploads with {self.config.max_concurrent_users} users")
        
        self.results['start_time'] = time.time()
        
        with ThreadPoolExecutor(max_workers=self.config.max_concurrent_users) as executor:
            # Submit upload tasks
            futures = []
            for user_id in range(self.config.max_concurrent_users):
                future = executor.submit(self._upload_file_worker, user_id)
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result['success']:
                        self.results['successful_requests'] += 1
                        self.results['response_times'].append(result['response_time'])
                    else:
                        self.results['failed_requests'] += 1
                        self.results['errors'].append(result['error'])
                except Exception as e:
                    self.results['failed_requests'] += 1
                    self.results['errors'].append(str(e))
        
        self.results['end_time'] = time.time()
        self._analyze_results("Concurrent File Uploads")
    
    def test_concurrent_transcriptions(self):
        """Test concurrent transcription requests"""
        print(f"\n🎤 Testing concurrent transcriptions with {self.config.max_concurrent_users} users")
        
        # First, upload files for all users
        uploaded_files = []
        with ThreadPoolExecutor(max_workers=self.config.max_concurrent_users) as executor:
            futures = []
            for user_id in range(self.config.max_concurrent_users):
                future = executor.submit(self._upload_file_worker, user_id)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result['success']:
                        uploaded_files.append(result['filename'])
                except Exception:
                    pass
        
        if not uploaded_files:
            self.skipTest("No files uploaded successfully")
        
        self.results['start_time'] = time.time()
        
        # Now test concurrent transcriptions
        with ThreadPoolExecutor(max_workers=self.config.max_concurrent_users) as executor:
            futures = []
            for i, filename in enumerate(uploaded_files[:self.config.max_concurrent_users]):
                future = executor.submit(self._transcribe_worker, i, filename)
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result['success']:
                        self.results['successful_requests'] += 1
                        self.results['response_times'].append(result['response_time'])
                    else:
                        self.results['failed_requests'] += 1
                        self.results['errors'].append(result['error'])
                except Exception as e:
                    self.results['failed_requests'] += 1
                    self.results['errors'].append(str(e))
        
        self.results['end_time'] = time.time()
        self._analyze_results("Concurrent Transcriptions")
    
    def test_sustained_load(self):
        """Test sustained load over time"""
        print(f"\n⏱️ Testing sustained load for {self.config.test_duration} seconds")
        
        self.results['start_time'] = time.time()
        end_time = self.results['start_time'] + self.config.test_duration
        
        with ThreadPoolExecutor(max_workers=self.config.max_concurrent_users) as executor:
            while time.time() < end_time:
                # Submit batch of requests
                futures = []
                for _ in range(min(10, self.config.max_concurrent_users)):
                    future = executor.submit(self._mixed_workload_worker)
                    futures.append(future)
                
                # Wait for batch completion
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result['success']:
                            self.results['successful_requests'] += 1
                            self.results['response_times'].append(result['response_time'])
                        else:
                            self.results['failed_requests'] += 1
                            self.results['errors'].append(result['error'])
                    except Exception as e:
                        self.results['failed_requests'] += 1
                        self.results['errors'].append(str(e))
                
                # Small delay between batches
                time.sleep(0.1)
        
        self.results['end_time'] = time.time()
        self._analyze_results("Sustained Load")
    
    def test_api_endpoint_load(self):
        """Test load on various API endpoints"""
        print(f"\n🔌 Testing API endpoint load")
        
        endpoints = [
            ('/health', 'GET'),
            ('/api/models', 'GET'),
            ('/api/cache/stats', 'GET'),
        ]
        
        self.results['start_time'] = time.time()
        
        with ThreadPoolExecutor(max_workers=self.config.max_concurrent_users) as executor:
            futures = []
            for user_id in range(self.config.max_concurrent_users):
                for endpoint, method in endpoints:
                    future = executor.submit(self._api_endpoint_worker, user_id, endpoint, method)
                    futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result['success']:
                        self.results['successful_requests'] += 1
                        self.results['response_times'].append(result['response_time'])
                    else:
                        self.results['failed_requests'] += 1
                        self.results['errors'].append(result['error'])
                except Exception as e:
                    self.results['failed_requests'] += 1
                    self.results['errors'].append(str(e))
        
        self.results['end_time'] = time.time()
        self._analyze_results("API Endpoint Load")
    
    def _upload_file_worker(self, user_id):
        """Worker function for file upload"""
        try:
            start_time = time.time()
            
            with open(self.test_audio_file, 'rb') as f:
                files = {'file': (f'user_{user_id}_test.wav', f, 'audio/wav')}
                response = requests.post(
                    f"{self.config.base_url}/api/upload",
                    files=files,
                    timeout=self.config.timeout
                )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'response_time': response_time,
                    'filename': data.get('filename')
                }
            else:
                return {
                    'success': False,
                    'response_time': response_time,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'response_time': time.time() - start_time if 'start_time' in locals() else 0,
                'error': str(e)
            }
    
    def _transcribe_worker(self, user_id, filename):
        """Worker function for transcription"""
        try:
            start_time = time.time()
            
            data = {
                'filename': filename,
                'model_size': 'base',
                'enable_speaker_diarization': True,
                'language': 'en'
            }
            
            response = requests.post(
                f"{self.config.base_url}/api/transcribe",
                json=data,
                timeout=self.config.timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'response_time': response_time,
                    'job_id': response.json().get('job_id')
                }
            else:
                return {
                    'success': False,
                    'response_time': response_time,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'response_time': time.time() - start_time if 'start_time' in locals() else 0,
                'error': str(e)
            }
    
    def _mixed_workload_worker(self):
        """Worker function for mixed workload"""
        try:
            start_time = time.time()
            
            # Randomly choose between different operations
            import random
            operation = random.choice(['health', 'models', 'cache_stats'])
            
            if operation == 'health':
                response = requests.get(f"{self.config.base_url}/health", timeout=5)
            elif operation == 'models':
                response = requests.get(f"{self.config.base_url}/api/models", timeout=5)
            elif operation == 'cache_stats':
                response = requests.get(f"{self.config.base_url}/api/cache/stats", timeout=5)
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'response_time': response_time,
                    'operation': operation
                }
            else:
                return {
                    'success': False,
                    'response_time': response_time,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'response_time': time.time() - start_time if 'start_time' in locals() else 0,
                'error': str(e)
            }
    
    def _api_endpoint_worker(self, user_id, endpoint, method):
        """Worker function for API endpoint testing"""
        try:
            start_time = time.time()
            
            if method == 'GET':
                response = requests.get(f"{self.config.base_url}{endpoint}", timeout=5)
            elif method == 'POST':
                response = requests.post(f"{self.config.base_url}{endpoint}", timeout=5)
            
            response_time = time.time() - start_time
            
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'response_time': response_time,
                    'endpoint': endpoint
                }
            else:
                return {
                    'success': False,
                    'response_time': response_time,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'response_time': time.time() - start_time if 'start_time' in locals() else 0,
                'error': str(e)
            }
    
    def _analyze_results(self, test_name):
        """Analyze and report test results"""
        total_requests = self.results['successful_requests'] + self.results['failed_requests']
        success_rate = (self.results['successful_requests'] / total_requests * 100) if total_requests > 0 else 0
        
        duration = self.results['end_time'] - self.results['start_time']
        requests_per_second = total_requests / duration if duration > 0 else 0
        
        if self.results['response_times']:
            avg_response_time = statistics.mean(self.results['response_times'])
            median_response_time = statistics.median(self.results['response_times'])
            p95_response_time = statistics.quantiles(self.results['response_times'], n=20)[18]  # 95th percentile
            max_response_time = max(self.results['response_times'])
        else:
            avg_response_time = median_response_time = p95_response_time = max_response_time = 0
        
        print(f"\n📊 {test_name} Results:")
        print(f"   Total Requests: {total_requests}")
        print(f"   Successful: {self.results['successful_requests']} ({success_rate:.1f}%)")
        print(f"   Failed: {self.results['failed_requests']}")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Requests/sec: {requests_per_second:.2f}")
        print(f"   Avg Response Time: {avg_response_time:.3f}s")
        print(f"   Median Response Time: {median_response_time:.3f}s")
        print(f"   95th Percentile: {p95_response_time:.3f}s")
        print(f"   Max Response Time: {max_response_time:.3f}s")
        
        if self.results['errors']:
            print(f"   Errors: {len(self.results['errors'])}")
            # Show unique errors
            unique_errors = list(set(self.results['errors']))
            for error in unique_errors[:5]:  # Show first 5 unique errors
                print(f"     - {error}")
        
        # Assertions for load test success
        self.assertGreater(success_rate, 95, f"Success rate {success_rate:.1f}% below 95% threshold")
        self.assertLess(avg_response_time, 5.0, f"Average response time {avg_response_time:.3f}s above 5s threshold")
        self.assertLess(p95_response_time, 10.0, f"95th percentile response time {p95_response_time:.3f}s above 10s threshold")
        self.assertGreater(requests_per_second, 1.0, f"Requests per second {requests_per_second:.2f} below 1.0 threshold")


class StressTest(unittest.TestCase):
    """Stress testing to find system limits"""
    
    def setUp(self):
        """Set up stress test fixtures"""
        self.config = LoadTestConfig()
        self.config.max_concurrent_users = 100  # Higher for stress testing
        
        # Create test audio file
        self.test_audio_file = TestAudioFixtures.create_test_wav_file(
            duration=60,  # 60 seconds for stress testing
            filename="stress_test_audio.wav"
        )
    
    def tearDown(self):
        """Clean up after tests"""
        if os.path.exists(self.test_audio_file):
            os.remove(self.test_audio_file)
            parent_dir = os.path.dirname(self.test_audio_file)
            try:
                os.rmdir(parent_dir)
            except OSError:
                pass
    
    def test_memory_stress(self):
        """Test system under memory stress"""
        print(f"\n💾 Testing memory stress with large files")
        
        # Create large audio file
        large_file = TestAudioFixtures.create_large_audio_file(
            duration=600,  # 10 minutes
            filename="large_stress_test.wav"
        )
        
        try:
            results = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for i in range(10):
                    future = executor.submit(self._upload_large_file, i, large_file)
                    futures.append(future)
                
                for future in as_completed(futures):
                    results.append(future.result())
            
            successful_uploads = sum(1 for r in results if r['success'])
            print(f"   Large file uploads: {successful_uploads}/10 successful")
            
            # Should handle at least some large file uploads
            self.assertGreater(successful_uploads, 5, "System should handle at least 5 large file uploads")
            
        finally:
            if os.path.exists(large_file):
                os.remove(large_file)
                parent_dir = os.path.dirname(large_file)
                try:
                    os.rmdir(parent_dir)
                except OSError:
                    pass
    
    def test_concurrent_limit_stress(self):
        """Test system under high concurrent load"""
        print(f"\n⚡ Testing concurrent limit stress with {self.config.max_concurrent_users} users")
        
        results = {
            'successful': 0,
            'failed': 0,
            'response_times': []
        }
        
        with ThreadPoolExecutor(max_workers=self.config.max_concurrent_users) as executor:
            futures = []
            for user_id in range(self.config.max_concurrent_users):
                future = executor.submit(self._stress_worker, user_id)
                futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    results['successful'] += 1
                    results['response_times'].append(result['response_time'])
                else:
                    results['failed'] += 1
        
        success_rate = results['successful'] / (results['successful'] + results['failed']) * 100
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Successful: {results['successful']}")
        print(f"   Failed: {results['failed']}")
        
        if results['response_times']:
            avg_response_time = statistics.mean(results['response_times'])
            print(f"   Average response time: {avg_response_time:.3f}s")
        
        # System should handle high concurrent load reasonably well
        self.assertGreater(success_rate, 80, f"Success rate {success_rate:.1f}% below 80% threshold")
    
    def _upload_large_file(self, user_id, file_path):
        """Upload large file for stress testing"""
        try:
            start_time = time.time()
            
            with open(file_path, 'rb') as f:
                files = {'file': (f'large_user_{user_id}.wav', f, 'audio/wav')}
                response = requests.post(
                    f"{self.config.base_url}/api/upload",
                    files=files,
                    timeout=60  # Longer timeout for large files
                )
            
            response_time = time.time() - start_time
            
            return {
                'success': response.status_code == 200,
                'response_time': response_time,
                'status_code': response.status_code
            }
            
        except Exception as e:
            return {
                'success': False,
                'response_time': 0,
                'error': str(e)
            }
    
    def _stress_worker(self, user_id):
        """Worker for stress testing"""
        try:
            start_time = time.time()
            
            # Try to upload file
            with open(self.test_audio_file, 'rb') as f:
                files = {'file': (f'stress_user_{user_id}.wav', f, 'audio/wav')}
                response = requests.post(
                    f"{self.config.base_url}/api/upload",
                    files=files,
                    timeout=30
                )
            
            response_time = time.time() - start_time
            
            return {
                'success': response.status_code == 200,
                'response_time': response_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'response_time': 0,
                'error': str(e)
            }


if __name__ == '__main__':
    unittest.main()
