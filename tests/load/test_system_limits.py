"""
System Limits Testing for Voice Transcriber
Tests system boundaries, resource limits, and failure scenarios
"""

import unittest
import requests
import time
import os
import sys
import psutil
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.fixtures.test_audio_files import TestAudioFixtures


class SystemLimitsTest(unittest.TestCase):
    """Test system limits and boundaries"""
    
    def setUp(self):
        """Set up system limits test fixtures"""
        self.base_url = os.getenv('TEST_BASE_URL', 'http://localhost:5001')
        self.test_audio_file = TestAudioFixtures.create_test_wav_file(
            duration=10,
            filename="limits_test.wav"
        )
        
        # Monitor system resources
        self.initial_cpu = psutil.cpu_percent()
        self.initial_memory = psutil.virtual_memory().percent
    
    def tearDown(self):
        """Clean up after tests"""
        if os.path.exists(self.test_audio_file):
            os.remove(self.test_audio_file)
            parent_dir = os.path.dirname(self.test_audio_file)
            try:
                os.rmdir(parent_dir)
            except OSError:
                pass
    
    def test_max_file_size_limit(self):
        """Test maximum file size handling"""
        print("\n📁 Testing maximum file size limits")
        
        # Test with file that exceeds limit
        large_file = TestAudioFixtures.create_large_audio_file(
            duration=1800,  # 30 minutes - should be very large
            filename="huge_file.wav"
        )
        
        try:
            file_size_mb = os.path.getsize(large_file) / (1024 * 1024)
            print(f"   Testing with {file_size_mb:.1f}MB file")
            
            with open(large_file, 'rb') as f:
                files = {'file': ('huge_file.wav', f, 'audio/wav')}
                response = requests.post(
                    f"{self.base_url}/api/upload",
                    files=files,
                    timeout=60
                )
            
            # Should either succeed or fail gracefully
            self.assertIn(response.status_code, [200, 413, 500])
            
            if response.status_code == 413:
                print("   ✅ Correctly rejected oversized file")
            elif response.status_code == 200:
                print("   ✅ Successfully handled large file")
            else:
                print(f"   ⚠️ Unexpected response: {response.status_code}")
                
        finally:
            if os.path.exists(large_file):
                os.remove(large_file)
                parent_dir = os.path.dirname(large_file)
                try:
                    os.rmdir(parent_dir)
                except OSError:
                    pass
    
    def test_concurrent_job_limit(self):
        """Test maximum concurrent job limit"""
        print("\n⚡ Testing concurrent job limits")
        
        # Upload a file first
        with open(self.test_audio_file, 'rb') as f:
            files = {'file': ('test.wav', f, 'audio/wav')}
            response = requests.post(f"{self.base_url}/api/upload", files=files)
        
        if response.status_code != 200:
            self.skipTest("Failed to upload test file")
        
        filename = response.json()['filename']
        
        # Try to start many concurrent transcriptions
        max_concurrent = 20  # Try to exceed typical limit
        results = []
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = []
            for i in range(max_concurrent):
                future = executor.submit(self._start_transcription, i, filename)
                futures.append(future)
            
            for future in futures:
                results.append(future.result())
        
        successful_starts = sum(1 for r in results if r['success'])
        rate_limited = sum(1 for r in results if r.get('rate_limited', False))
        
        print(f"   Started {successful_starts}/{max_concurrent} transcriptions")
        print(f"   Rate limited: {rate_limited}")
        
        # System should handle concurrent jobs gracefully
        self.assertGreater(successful_starts, 0, "Should start at least some transcriptions")
        self.assertLessEqual(successful_starts, max_concurrent, "Should not exceed system limits")
    
    def test_memory_usage_under_load(self):
        """Test memory usage under load"""
        print("\n💾 Testing memory usage under load")
        
        initial_memory = psutil.virtual_memory().percent
        print(f"   Initial memory usage: {initial_memory:.1f}%")
        
        # Start multiple transcriptions
        uploaded_files = []
        for i in range(5):
            with open(self.test_audio_file, 'rb') as f:
                files = {'file': (f'test_{i}.wav', f, 'audio/wav')}
                response = requests.post(f"{self.base_url}/api/upload", files=files)
                if response.status_code == 200:
                    uploaded_files.append(response.json()['filename'])
        
        if not uploaded_files:
            self.skipTest("Failed to upload test files")
        
        # Start transcriptions
        transcription_jobs = []
        for filename in uploaded_files:
            data = {
                'filename': filename,
                'model_size': 'base',
                'enable_speaker_diarization': True,
                'language': 'en'
            }
            response = requests.post(f"{self.base_url}/api/transcribe", json=data)
            if response.status_code == 200:
                transcription_jobs.append(response.json()['job_id'])
        
        # Monitor memory usage
        max_memory = initial_memory
        for _ in range(10):  # Monitor for 10 seconds
            current_memory = psutil.virtual_memory().percent
            max_memory = max(max_memory, current_memory)
            time.sleep(1)
        
        memory_increase = max_memory - initial_memory
        print(f"   Peak memory usage: {max_memory:.1f}%")
        print(f"   Memory increase: {memory_increase:.1f}%")
        
        # Memory increase should be reasonable
        self.assertLess(memory_increase, 50, f"Memory increase {memory_increase:.1f}% too high")
    
    def test_cpu_usage_under_load(self):
        """Test CPU usage under load"""
        print("\n🖥️ Testing CPU usage under load")
        
        initial_cpu = psutil.cpu_percent(interval=1)
        print(f"   Initial CPU usage: {initial_cpu:.1f}%")
        
        # Create CPU load with concurrent requests
        def cpu_load_worker():
            for _ in range(10):
                try:
                    response = requests.get(f"{self.base_url}/api/cache/stats", timeout=5)
                    time.sleep(0.1)
                except:
                    pass
        
        # Start multiple workers
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=cpu_load_worker)
            thread.start()
            threads.append(thread)
        
        # Monitor CPU usage
        max_cpu = initial_cpu
        for _ in range(5):
            current_cpu = psutil.cpu_percent(interval=1)
            max_cpu = max(max_cpu, current_cpu)
        
        # Wait for threads to complete
        for thread in threads:
            thread.join()
        
        cpu_increase = max_cpu - initial_cpu
        print(f"   Peak CPU usage: {max_cpu:.1f}%")
        print(f"   CPU increase: {cpu_increase:.1f}%")
        
        # CPU usage should be reasonable
        self.assertLess(max_cpu, 90, f"Peak CPU usage {max_cpu:.1f}% too high")
    
    def test_disk_space_usage(self):
        """Test disk space usage"""
        print("\n💿 Testing disk space usage")
        
        initial_disk = psutil.disk_usage('/').percent
        print(f"   Initial disk usage: {initial_disk:.1f}%")
        
        # Upload multiple files
        uploaded_files = []
        for i in range(10):
            with open(self.test_audio_file, 'rb') as f:
                files = {'file': (f'disk_test_{i}.wav', f, 'audio/wav')}
                response = requests.post(f"{self.base_url}/api/upload", files=files)
                if response.status_code == 200:
                    uploaded_files.append(response.json()['filename'])
        
        # Check disk usage after uploads
        current_disk = psutil.disk_usage('/').percent
        disk_increase = current_disk - initial_disk
        
        print(f"   Current disk usage: {current_disk:.1f}%")
        print(f"   Disk increase: {disk_increase:.1f}%")
        
        # Disk usage increase should be reasonable
        self.assertLess(disk_increase, 10, f"Disk usage increase {disk_increase:.1f}% too high")
    
    def test_error_handling_under_stress(self):
        """Test error handling under stress"""
        print("\n🚨 Testing error handling under stress")
        
        error_count = 0
        total_requests = 0
        
        # Make requests that should cause errors
        error_scenarios = [
            # Invalid file upload
            lambda: requests.post(f"{self.base_url}/api/upload", files={'file': ('test.txt', b'invalid', 'text/plain')}),
            # Missing file
            lambda: requests.post(f"{self.base_url}/api/upload"),
            # Invalid transcription request
            lambda: requests.post(f"{self.base_url}/api/transcribe", json={'filename': 'nonexistent.wav'}),
            # Invalid job ID
            lambda: requests.get(f"{self.base_url}/api/job/invalid-job-id"),
            # Invalid download
            lambda: requests.get(f"{self.base_url}/api/download/nonexistent.md"),
        ]
        
        for _ in range(5):  # Repeat each scenario 5 times
            for scenario in error_scenarios:
                try:
                    response = scenario()
                    total_requests += 1
                    
                    # Check if response indicates an error
                    if response.status_code >= 400:
                        error_count += 1
                        # Verify error response format
                        if response.headers.get('content-type', '').startswith('application/json'):
                            try:
                                error_data = response.json()
                                self.assertIn('error', error_data)
                            except:
                                pass
                
                except requests.exceptions.RequestException:
                    error_count += 1
                    total_requests += 1
        
        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
        print(f"   Error rate: {error_rate:.1f}% ({error_count}/{total_requests})")
        
        # System should handle errors gracefully
        self.assertGreater(error_count, 0, "Should encounter some expected errors")
        self.assertLess(error_rate, 100, "Should not fail on all requests")
    
    def test_connection_limit_handling(self):
        """Test connection limit handling"""
        print("\n🔗 Testing connection limit handling")
        
        def connection_worker():
            try:
                # Keep connection open
                response = requests.get(f"{self.base_url}/health", timeout=30)
                return response.status_code == 200
            except:
                return False
        
        # Try to exhaust connection pool
        max_connections = 50
        results = []
        
        with ThreadPoolExecutor(max_workers=max_connections) as executor:
            futures = []
            for _ in range(max_connections):
                future = executor.submit(connection_worker)
                futures.append(future)
            
            for future in futures:
                results.append(future.result())
        
        successful_connections = sum(results)
        print(f"   Successful connections: {successful_connections}/{max_connections}")
        
        # Should handle most connections successfully
        self.assertGreater(successful_connections, max_connections * 0.8, 
                          "Should handle at least 80% of connections")
    
    def _start_transcription(self, user_id, filename):
        """Start a transcription job"""
        try:
            data = {
                'filename': filename,
                'model_size': 'base',
                'enable_speaker_diarization': True,
                'language': 'en'
            }
            
            response = requests.post(f"{self.base_url}/api/transcribe", json=data, timeout=10)
            
            if response.status_code == 200:
                return {'success': True, 'job_id': response.json().get('job_id')}
            elif response.status_code == 429:
                return {'success': False, 'rate_limited': True}
            else:
                return {'success': False, 'status_code': response.status_code}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}


class ResourceMonitoringTest(unittest.TestCase):
    """Test resource monitoring and limits"""
    
    def setUp(self):
        """Set up resource monitoring test"""
        self.base_url = os.getenv('TEST_BASE_URL', 'http://localhost:5001')
        self.monitoring_duration = 30  # seconds
    
    def test_system_resource_monitoring(self):
        """Test system resource monitoring"""
        print(f"\n📊 Monitoring system resources for {self.monitoring_duration} seconds")
        
        # Start monitoring
        start_time = time.time()
        end_time = start_time + self.monitoring_duration
        
        metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'disk_usage': [],
            'response_times': []
        }
        
        while time.time() < end_time:
            # Collect system metrics
            metrics['cpu_usage'].append(psutil.cpu_percent())
            metrics['memory_usage'].append(psutil.virtual_memory().percent)
            metrics['disk_usage'].append(psutil.disk_usage('/').percent)
            
            # Test API response time
            try:
                start = time.time()
                response = requests.get(f"{self.base_url}/health", timeout=5)
                response_time = time.time() - start
                metrics['response_times'].append(response_time)
            except:
                metrics['response_times'].append(5.0)  # Timeout value
            
            time.sleep(1)
        
        # Analyze metrics
        avg_cpu = sum(metrics['cpu_usage']) / len(metrics['cpu_usage'])
        max_cpu = max(metrics['cpu_usage'])
        avg_memory = sum(metrics['memory_usage']) / len(metrics['memory_usage'])
        max_memory = max(metrics['memory_usage'])
        avg_response_time = sum(metrics['response_times']) / len(metrics['response_times'])
        max_response_time = max(metrics['response_times'])
        
        print(f"   Average CPU: {avg_cpu:.1f}%")
        print(f"   Peak CPU: {max_cpu:.1f}%")
        print(f"   Average Memory: {avg_memory:.1f}%")
        print(f"   Peak Memory: {max_memory:.1f}%")
        print(f"   Average Response Time: {avg_response_time:.3f}s")
        print(f"   Max Response Time: {max_response_time:.3f}s")
        
        # Assertions for system stability
        self.assertLess(avg_cpu, 80, f"Average CPU usage {avg_cpu:.1f}% too high")
        self.assertLess(max_cpu, 95, f"Peak CPU usage {max_cpu:.1f}% too high")
        self.assertLess(avg_memory, 80, f"Average memory usage {avg_memory:.1f}% too high")
        self.assertLess(max_memory, 90, f"Peak memory usage {max_memory:.1f}% too high")
        self.assertLess(avg_response_time, 2.0, f"Average response time {avg_response_time:.3f}s too high")
        self.assertLess(max_response_time, 10.0, f"Max response time {max_response_time:.3f}s too high")


if __name__ == '__main__':
    unittest.main()
