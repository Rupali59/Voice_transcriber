"""
Unit tests for API endpoints
Tests the Flask API routes and their functionality
"""

import unittest
import os
import sys
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app import create_app
from app.config import TestingConfig


class TestAPIEndpoints(unittest.TestCase):
    """Test cases for API endpoints"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create test app
        self.app = create_app(TestingConfig)
        self.app.config['TESTING'] = True
        self.app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
        self.app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
        
        self.client = self.app.test_client()
        
        # Mock services
        self.mock_file_service = Mock()
        self.mock_transcription_service = Mock()
        self.mock_job_manager = Mock()
        self.mock_model_cache = Mock()
    
    def tearDown(self):
        """Clean up after tests"""
        # Clean up temp directory
        import shutil
        if os.path.exists(self.app.config['UPLOAD_FOLDER']):
            shutil.rmtree(self.app.config['UPLOAD_FOLDER'])
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        with patch('app.get_transcription_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_all_jobs.return_value = {}
            mock_get_service.return_value = mock_service
            
            response = self.client.get('/health')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['status'], 'healthy')
            self.assertIn('timestamp', data)
            self.assertIn('active_jobs', data)
    
    def test_upload_file_success(self):
        """Test successful file upload"""
        # Create test file
        test_file = BytesIO(b'test audio content')
        test_file.name = 'test.wav'
        
        with patch('app.get_file_service') as mock_get_service:
            # Mock file service
            mock_file_upload = Mock()
            mock_file_upload.filename = 'uuid_test.wav'
            mock_file_upload.original_name = 'test.wav'
            mock_file_upload.size_mb = 0.001
            mock_file_upload.filepath = '/uploads/uuid_test.wav'
            
            mock_service = Mock()
            mock_service.save_uploaded_file.return_value = mock_file_upload
            mock_get_service.return_value = mock_service
            
            response = self.client.post('/api/upload', 
                                      data={'file': (test_file, 'test.wav')},
                                      content_type='multipart/form-data')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertEqual(data['filename'], 'uuid_test.wav')
            self.assertEqual(data['original_name'], 'test.wav')
    
    def test_upload_file_no_file(self):
        """Test upload with no file"""
        response = self.client.post('/api/upload')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('No file provided', data['error'])
    
    def test_upload_file_empty_filename(self):
        """Test upload with empty filename"""
        test_file = BytesIO(b'test content')
        test_file.name = ''
        
        response = self.client.post('/api/upload',
                                  data={'file': (test_file, '')},
                                  content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('No file selected', data['error'])
    
    def test_upload_file_too_large(self):
        """Test upload with file too large"""
        # Create large file content
        large_content = b'x' * (11 * 1024 * 1024)  # 11MB
        test_file = BytesIO(large_content)
        test_file.name = 'large.wav'
        
        response = self.client.post('/api/upload',
                                  data={'file': (test_file, 'large.wav')},
                                  content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 413)
    
    def test_transcribe_success(self):
        """Test successful transcription start"""
        with patch('app.get_transcription_service') as mock_get_service:
            # Mock transcription service
            mock_job = Mock()
            mock_job.job_id = 'test-job-123'
            mock_job.status = 'starting'
            
            mock_service = Mock()
            mock_service.start_transcription.return_value = mock_job
            mock_get_service.return_value = mock_service
            
            response = self.client.post('/api/transcribe',
                                      json={
                                          'filename': 'test.wav',
                                          'model_size': 'base',
                                          'enable_speaker_diarization': True,
                                          'language': 'en'
                                      })
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertEqual(data['job_id'], 'test-job-123')
    
    def test_transcribe_missing_filename(self):
        """Test transcription with missing filename"""
        response = self.client.post('/api/transcribe',
                                  json={
                                      'model_size': 'base',
                                      'enable_speaker_diarization': True,
                                      'language': 'en'
                                  })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('filename', data['error'])
    
    def test_transcribe_file_not_found(self):
        """Test transcription with non-existent file"""
        with patch('app.get_file_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_file_by_filename.return_value = None
            mock_get_service.return_value = mock_service
            
            response = self.client.post('/api/transcribe',
                                      json={
                                          'filename': 'nonexistent.wav',
                                          'model_size': 'base',
                                          'enable_speaker_diarization': True,
                                          'language': 'en'
                                      })
            
            self.assertEqual(response.status_code, 404)
            data = json.loads(response.data)
            self.assertIn('error', data)
            self.assertIn('File not found', data['error'])
    
    def test_get_job_status_success(self):
        """Test getting job status"""
        with patch('app.get_transcription_service') as mock_get_service:
            # Mock job
            mock_job = Mock()
            mock_job.job_id = 'test-job-123'
            mock_job.status = 'completed'
            mock_job.progress = 100
            mock_job.filename = 'test.wav'
            mock_job.original_filename = 'test.wav'
            mock_job.model_size = 'base'
            mock_job.enable_speaker_diarization = True
            mock_job.language = 'en'
            mock_job.start_time = '2024-01-01T12:00:00Z'
            mock_job.end_time = '2024-01-01T12:02:00Z'
            mock_job.result = {'transcription': {'text': 'Test'}}
            mock_job.error = None
            mock_job.file_size_mb = 5.0
            
            # Mock the to_dict method
            mock_job.to_dict.return_value = {
                'job_id': 'test-job-123',
                'status': 'completed',
                'progress': 100,
                'filename': 'test.wav',
                'original_filename': 'test.wav',
                'model_size': 'base',
                'enable_speaker_diarization': True,
                'language': 'en',
                'start_time': '2024-01-01T12:00:00Z',
                'end_time': '2024-01-01T12:02:00Z',
                'result': {'transcription': {'text': 'Test'}},
                'error': None,
                'file_size_mb': 5.0
            }
            
            mock_service = Mock()
            mock_service.get_job.return_value = mock_job
            mock_get_service.return_value = mock_service
            
            response = self.client.get('/api/job/test-job-123')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['job_id'], 'test-job-123')
            self.assertEqual(data['status'], 'completed')
            self.assertEqual(data['progress'], 100)
    
    def test_get_job_status_not_found(self):
        """Test getting status of non-existent job"""
        with patch('app.get_transcription_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_job.return_value = None
            mock_get_service.return_value = mock_service
            
            response = self.client.get('/api/job/nonexistent-job')
            
            self.assertEqual(response.status_code, 404)
            data = json.loads(response.data)
            self.assertIn('error', data)
            self.assertIn('Job not found', data['error'])
    
    def test_download_file_success(self):
        """Test successful file download"""
        # Create test file in transcriptions folder
        test_content = b'# Test Transcription\n\nThis is a test transcription.'
        transcriptions_dir = 'transcriptions'
        os.makedirs(transcriptions_dir, exist_ok=True)
        test_file_path = os.path.join(transcriptions_dir, 'test.md')
        
        with open(test_file_path, 'wb') as f:
            f.write(test_content)
        
        try:
            response = self.client.get('/api/download/test.md')
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, test_content)
        finally:
            # Clean up test file
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
    
    def test_download_file_not_found(self):
        """Test download of non-existent file"""
        response = self.client.get('/api/download/nonexistent.md')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('File not found', data['error'])
    
    def test_get_models(self):
        """Test getting available models"""
        response = self.client.get('/api/models')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('models', data)
        
        models = data['models']
        self.assertEqual(len(models), 5)
        
        # Check model structure
        for model in models:
            self.assertIn('id', model)
            self.assertIn('name', model)
            self.assertIn('description', model)
        
        # Check specific models
        model_ids = [model['id'] for model in models]
        self.assertIn('tiny', model_ids)
        self.assertIn('base', model_ids)
        self.assertIn('small', model_ids)
        self.assertIn('medium', model_ids)
        self.assertIn('large', model_ids)
    
    def test_get_cache_stats(self):
        """Test getting cache statistics"""
        with patch('app.services.model_cache.get_model_cache') as mock_get_cache:
            # Mock cache stats
            mock_stats = {
                'cached_models': ['base', 'small'],
                'cache_size': 2,
                'max_cache_size': 3,
                'model_usage': {
                    'base': {
                        'first_used': '2024-01-01T12:00:00Z',
                        'last_used': '2024-01-01T12:30:00Z',
                        'access_count': 5,
                        'idle_time': 0
                    }
                },
                'memory_usage': {
                    'rss_mb': 2048.5,
                    'vms_mb': 4096.2,
                    'percent': 25.3
                }
            }
            
            mock_cache = Mock()
            mock_cache.get_cache_stats.return_value = mock_stats
            mock_get_cache.return_value = mock_cache
            
            response = self.client.get('/api/cache/stats')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data, mock_stats)
    
    def test_clear_cache(self):
        """Test clearing model cache"""
        with patch('app.services.model_cache.get_model_cache') as mock_get_cache:
            mock_cache = Mock()
            mock_get_cache.return_value = mock_cache
            
            response = self.client.post('/api/cache/clear')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertEqual(data['message'], 'Cache cleared')
            
            mock_cache.clear_cache.assert_called_once()
    
    def test_optimize_memory(self):
        """Test memory optimization"""
        with patch('app.services.model_cache.get_model_cache') as mock_get_cache:
            mock_cache = Mock()
            mock_get_cache.return_value = mock_cache
            
            response = self.client.post('/api/cache/optimize')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertEqual(data['message'], 'Memory optimized')
            
            mock_cache.optimize_memory.assert_called_once()
    
    def test_get_all_requests(self):
        """Test getting all requests"""
        with patch('app.get_request_tracker') as mock_get_tracker:
            # Mock request tracker
            mock_requests = [
                {
                    'request_id': 'req-123',
                    'status': 'completed',
                    'filename': 'test.wav',
                    'timestamp': '2024-01-01T12:00:00Z'
                }
            ]
            
            mock_tracker = Mock()
            mock_tracker.get_all_requests.return_value = mock_requests
            mock_get_tracker.return_value = mock_tracker
            
            response = self.client.get('/api/requests')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('requests', data)
            self.assertEqual(len(data['requests']), 1)
    
    def test_get_requests_with_filters(self):
        """Test getting requests with filters"""
        with patch('app.get_request_tracker') as mock_get_tracker:
            mock_tracker = Mock()
            mock_tracker.get_all_requests.return_value = []
            mock_get_tracker.return_value = mock_tracker
            
            response = self.client.get('/api/requests?status=completed&limit=10')
            
            self.assertEqual(response.status_code, 200)
            mock_tracker.get_all_requests.assert_called_once_with(
                10,
                'completed'
            )
    
    def test_cancel_job_success(self):
        """Test successful job cancellation"""
        with patch('app.get_transcription_service') as mock_get_service:
            mock_service = Mock()
            mock_service.cancel_job.return_value = True
            mock_get_service.return_value = mock_service
            
            response = self.client.post('/api/cancel-job/test-job-123')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertEqual(data['message'], 'Job cancelled successfully')
            
            mock_service.cancel_job.assert_called_once_with('test-job-123')
    
    def test_cancel_job_failure(self):
        """Test job cancellation failure"""
        with patch('app.get_transcription_service') as mock_get_service:
            mock_service = Mock()
            mock_service.cancel_job.return_value = False
            mock_get_service.return_value = mock_service
            
            response = self.client.post('/api/cancel-job/test-job-123')
            
            self.assertEqual(response.status_code, 404)
            data = json.loads(response.data)
            self.assertIn('error', data)
            self.assertIn('Job not found or already completed', data['error'])


class TestAPIErrorHandling(unittest.TestCase):
    """Test cases for API error handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app(TestingConfig)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_invalid_json(self):
        """Test handling of invalid JSON"""
        response = self.client.post('/api/transcribe',
                                  data='invalid json',
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
    
    def test_missing_content_type(self):
        """Test handling of missing content type"""
        response = self.client.post('/api/transcribe',
                                  data='{"filename": "test.wav"}')
        
        self.assertEqual(response.status_code, 400)
    
    def test_service_error_handling(self):
        """Test handling of service errors"""
        # Create test file first
        test_file_path = os.path.join('uploads', 'test.wav')
        os.makedirs('uploads', exist_ok=True)
        with open(test_file_path, 'wb') as f:
            f.write(b'test audio data')
        
        try:
            with patch('app.get_transcription_service') as mock_get_service:
                mock_service = Mock()
                mock_service.start_transcription.side_effect = Exception("Service error")
                mock_get_service.return_value = mock_service
                
                response = self.client.post('/api/transcribe',
                                          json={
                                              'filename': 'test.wav',
                                              'model_size': 'base',
                                              'enable_speaker_diarization': True,
                                              'language': 'en'
                                          })
                
                self.assertEqual(response.status_code, 500)
                data = json.loads(response.data)
                self.assertIn('error', data)
        finally:
            # Clean up test file
            if os.path.exists(test_file_path):
                os.remove(test_file_path)


if __name__ == '__main__':
    unittest.main()
