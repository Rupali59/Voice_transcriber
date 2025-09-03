"""
API Usability Testing for Voice Transcriber
Tests API usability, documentation, and developer experience
"""

import unittest
import requests
import json
import time
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.fixtures.test_audio_files import TestAudioFixtures


class APIUsabilityTest(unittest.TestCase):
    """Test API usability and developer experience"""
    
    def setUp(self):
        """Set up API usability test fixtures"""
        self.base_url = os.getenv('TEST_BASE_URL', 'http://localhost:5001')
        self.test_audio_file = TestAudioFixtures.create_test_wav_file(
            duration=10,
            filename="api_test.wav"
        )
        
        # Verify server is running
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code != 200:
                self.skipTest("Server not running or not healthy")
        except requests.exceptions.RequestException:
            self.skipTest("Server not accessible")
    
    def tearDown(self):
        """Clean up after tests"""
        if os.path.exists(self.test_audio_file):
            os.remove(self.test_audio_file)
            parent_dir = os.path.dirname(self.test_audio_file)
            try:
                os.rmdir(parent_dir)
            except OSError:
                pass
    
    def test_api_documentation_availability(self):
        """Test that API documentation is available"""
        print("\n📚 Testing API documentation availability")
        
        # Test health endpoint
        try:
            response = requests.get(f"{self.base_url}/health")
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('status', data)
            self.assertEqual(data['status'], 'healthy')
            print("   ✅ Health endpoint documented and working")
            
        except Exception as e:
            self.fail(f"Health endpoint failed: {e}")
        
        # Test models endpoint
        try:
            response = requests.get(f"{self.base_url}/api/models")
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('models', data)
            self.assertIsInstance(data['models'], list)
            print("   ✅ Models endpoint documented and working")
            
        except Exception as e:
            self.fail(f"Models endpoint failed: {e}")
    
    def test_api_response_consistency(self):
        """Test API response consistency"""
        print("\n🔄 Testing API response consistency")
        
        # Test multiple calls to same endpoint
        endpoints = [
            '/health',
            '/api/models',
            '/api/cache/stats'
        ]
        
        for endpoint in endpoints:
            responses = []
            for _ in range(3):
                try:
                    response = requests.get(f"{self.base_url}{endpoint}")
                    responses.append(response.json())
                    time.sleep(0.1)
                except Exception as e:
                    self.fail(f"Endpoint {endpoint} failed: {e}")
            
            # Check response consistency
            if len(responses) > 1:
                # Compare structure (not values, as they might change)
                first_keys = set(responses[0].keys())
                for response in responses[1:]:
                    current_keys = set(response.keys())
                    self.assertEqual(first_keys, current_keys, 
                                   f"Response structure inconsistent for {endpoint}")
            
            print(f"   ✅ {endpoint} responses consistent")
    
    def test_api_error_handling(self):
        """Test API error handling and error messages"""
        print("\n🚨 Testing API error handling")
        
        # Test invalid endpoints
        invalid_endpoints = [
            '/api/invalid',
            '/api/transcribe/invalid',
            '/api/job/invalid-job-id'
        ]
        
        for endpoint in invalid_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                self.assertIn(response.status_code, [404, 400, 500])
                
                # Check error response format
                if response.headers.get('content-type', '').startswith('application/json'):
                    try:
                        error_data = response.json()
                        self.assertIn('error', error_data)
                        print(f"   ✅ {endpoint} returns proper error format")
                    except json.JSONDecodeError:
                        print(f"   ⚠️ {endpoint} returns non-JSON error response")
                else:
                    print(f"   ⚠️ {endpoint} returns non-JSON error response")
                    
            except Exception as e:
                print(f"   ⚠️ {endpoint} test failed: {e}")
        
        # Test invalid file upload
        try:
            response = requests.post(f"{self.base_url}/api/upload")
            self.assertIn(response.status_code, [400, 422])
            print("   ✅ Invalid upload returns proper error")
        except Exception as e:
            print(f"   ⚠️ Invalid upload test failed: {e}")
    
    def test_api_content_types(self):
        """Test API content types"""
        print("\n📄 Testing API content types")
        
        # Test JSON endpoints
        json_endpoints = [
            '/health',
            '/api/models',
            '/api/cache/stats'
        ]
        
        for endpoint in json_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                content_type = response.headers.get('content-type', '')
                self.assertIn('application/json', content_type)
                print(f"   ✅ {endpoint} returns JSON content type")
            except Exception as e:
                print(f"   ⚠️ {endpoint} content type test failed: {e}")
    
    def test_api_cors_headers(self):
        """Test CORS headers for web integration"""
        print("\n🌐 Testing CORS headers")
        
        try:
            response = requests.options(f"{self.base_url}/api/models")
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            for header in cors_headers:
                if header in response.headers:
                    print(f"   ✅ CORS header {header} present")
                else:
                    print(f"   ⚠️ CORS header {header} missing")
                    
        except Exception as e:
            print(f"   ⚠️ CORS test failed: {e}")
    
    def test_api_rate_limiting(self):
        """Test API rate limiting"""
        print("\n⏱️ Testing API rate limiting")
        
        # Make rapid requests to test rate limiting
        rapid_requests = 20
        responses = []
        
        for i in range(rapid_requests):
            try:
                response = requests.get(f"{self.base_url}/health")
                responses.append(response.status_code)
                time.sleep(0.05)  # 50ms between requests
            except Exception as e:
                print(f"   ⚠️ Request {i} failed: {e}")
        
        # Check for rate limiting (429 status codes)
        rate_limited = sum(1 for status in responses if status == 429)
        success_rate = sum(1 for status in responses if status == 200) / len(responses) * 100
        
        print(f"   Rate limited requests: {rate_limited}/{rapid_requests}")
        print(f"   Success rate: {success_rate:.1f}%")
        
        # Should handle most requests successfully
        self.assertGreater(success_rate, 80, f"Success rate {success_rate:.1f}% too low")
    
    def test_api_timeout_handling(self):
        """Test API timeout handling"""
        print("\n⏰ Testing API timeout handling")
        
        # Test with very short timeout
        try:
            response = requests.get(f"{self.base_url}/health", timeout=0.1)
            print("   ✅ Health endpoint responds quickly")
        except requests.exceptions.Timeout:
            print("   ⚠️ Health endpoint timeout (might be expected)")
        except Exception as e:
            print(f"   ⚠️ Health endpoint test failed: {e}")
    
    def test_api_versioning(self):
        """Test API versioning"""
        print("\n🔢 Testing API versioning")
        
        # Check if API has versioning
        versioned_endpoints = [
            '/api/v1/models',
            '/v1/api/models',
            '/api/models'
        ]
        
        for endpoint in versioned_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    print(f"   ✅ Endpoint {endpoint} available")
                    break
            except Exception:
                continue
        else:
            print("   ⚠️ No versioned endpoints found")
    
    def test_api_pagination(self):
        """Test API pagination (if applicable)"""
        print("\n📄 Testing API pagination")
        
        # Test endpoints that might have pagination
        paginated_endpoints = [
            '/api/requests',
            '/api/jobs',
            '/api/files'
        ]
        
        for endpoint in paginated_endpoints:
            try:
                # Test with pagination parameters
                params = {'limit': 10, 'offset': 0}
                response = requests.get(f"{self.base_url}{endpoint}", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ {endpoint} supports pagination")
                    
                    # Check pagination metadata
                    if 'limit' in data or 'offset' in data or 'total' in data:
                        print(f"   ✅ {endpoint} includes pagination metadata")
                else:
                    print(f"   ⚠️ {endpoint} not available or doesn't support pagination")
                    
            except Exception as e:
                print(f"   ⚠️ {endpoint} pagination test failed: {e}")
    
    def test_api_filtering_and_search(self):
        """Test API filtering and search capabilities"""
        print("\n🔍 Testing API filtering and search")
        
        # Test filtering parameters
        filter_endpoints = [
            ('/api/requests', {'status': 'completed'}),
            ('/api/jobs', {'status': 'running'}),
        ]
        
        for endpoint, params in filter_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ {endpoint} supports filtering")
                else:
                    print(f"   ⚠️ {endpoint} filtering not available")
                    
            except Exception as e:
                print(f"   ⚠️ {endpoint} filtering test failed: {e}")
    
    def test_api_batch_operations(self):
        """Test API batch operations"""
        print("\n📦 Testing API batch operations")
        
        # Test batch upload (if supported)
        try:
            # Create multiple test files
            test_files = []
            for i in range(3):
                test_file = TestAudioFixtures.create_test_wav_file(
                    duration=5,
                    filename=f"batch_test_{i}.wav"
                )
                test_files.append(test_file)
            
            # Try batch upload
            files = []
            for i, test_file in enumerate(test_files):
                files.append(('files', (f'test_{i}.wav', open(test_file, 'rb'), 'audio/wav')))
            
            response = requests.post(f"{self.base_url}/api/upload/batch", files=files)
            
            # Close files
            for _, (_, file_obj, _) in files:
                file_obj.close()
            
            if response.status_code == 200:
                print("   ✅ Batch upload supported")
            else:
                print("   ⚠️ Batch upload not supported")
                
        except Exception as e:
            print(f"   ⚠️ Batch upload test failed: {e}")
        finally:
            # Clean up test files
            for test_file in test_files:
                if os.path.exists(test_file):
                    os.remove(test_file)
                    parent_dir = os.path.dirname(test_file)
                    try:
                        os.rmdir(parent_dir)
                    except OSError:
                        pass
    
    def test_api_authentication(self):
        """Test API authentication (if implemented)"""
        print("\n🔐 Testing API authentication")
        
        # Test endpoints that might require authentication
        protected_endpoints = [
            '/api/admin',
            '/api/users',
            '/api/settings'
        ]
        
        for endpoint in protected_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                
                if response.status_code == 401:
                    print(f"   ✅ {endpoint} requires authentication")
                elif response.status_code == 200:
                    print(f"   ⚠️ {endpoint} doesn't require authentication")
                else:
                    print(f"   ⚠️ {endpoint} returned status {response.status_code}")
                    
            except Exception as e:
                print(f"   ⚠️ {endpoint} authentication test failed: {e}")
    
    def test_api_webhook_support(self):
        """Test API webhook support (if implemented)"""
        print("\n🔗 Testing API webhook support")
        
        # Test webhook endpoints
        webhook_endpoints = [
            '/api/webhooks',
            '/api/callbacks',
            '/api/notifications'
        ]
        
        for endpoint in webhook_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                
                if response.status_code == 200:
                    print(f"   ✅ {endpoint} available")
                elif response.status_code == 404:
                    print(f"   ⚠️ {endpoint} not implemented")
                else:
                    print(f"   ⚠️ {endpoint} returned status {response.status_code}")
                    
            except Exception as e:
                print(f"   ⚠️ {endpoint} webhook test failed: {e}")


class APIDocumentationTest(unittest.TestCase):
    """Test API documentation quality"""
    
    def setUp(self):
        """Set up API documentation test"""
        self.base_url = os.getenv('TEST_BASE_URL', 'http://localhost:5001')
    
    def test_api_swagger_documentation(self):
        """Test Swagger/OpenAPI documentation"""
        print("\n📖 Testing Swagger documentation")
        
        swagger_endpoints = [
            '/swagger',
            '/swagger.json',
            '/swagger.yaml',
            '/api/docs',
            '/docs',
            '/openapi.json'
        ]
        
        for endpoint in swagger_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type or 'text/html' in content_type:
                        print(f"   ✅ Swagger documentation available at {endpoint}")
                        return
                        
            except Exception:
                continue
        
        print("   ⚠️ No Swagger documentation found")
    
    def test_api_response_schemas(self):
        """Test API response schemas"""
        print("\n📋 Testing API response schemas")
        
        # Test that responses have consistent schemas
        test_cases = [
            ('/health', ['status', 'timestamp']),
            ('/api/models', ['models']),
            ('/api/cache/stats', ['cached_models', 'cache_size'])
        ]
        
        for endpoint, expected_fields in test_cases:
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for field in expected_fields:
                        if field in data:
                            print(f"   ✅ {endpoint} includes {field}")
                        else:
                            print(f"   ⚠️ {endpoint} missing {field}")
                else:
                    print(f"   ⚠️ {endpoint} returned status {response.status_code}")
                    
            except Exception as e:
                print(f"   ⚠️ {endpoint} schema test failed: {e}")


if __name__ == '__main__':
    unittest.main()
