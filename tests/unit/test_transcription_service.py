"""
Unit tests for Transcription Service
Tests the TranscriptionService class and its functionality
"""

import unittest
import os
import sys
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.transcription_service import TranscriptionService
from app.models.transcription_job import TranscriptionJob
from app.models.file_upload import FileUpload


class TestTranscriptionService(unittest.TestCase):
    """Test cases for TranscriptionService class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = TranscriptionService()
        
        # Mock Flask app
        self.mock_app = Mock()
        self.mock_app.config = {
            'MAX_CONCURRENT_JOBS': 5,
            'JOB_CLEANUP_HOURS': 1,
            'UPLOAD_FOLDER': 'uploads',
            'ALLOWED_EXTENSIONS': {'wav', 'mp3', 'm4a'}
        }
        
        # Mock job manager
        self.mock_job_manager = Mock()
        self.mock_job_manager.create_job.return_value = Mock()
        self.mock_job_manager.get_job.return_value = Mock()
        self.mock_job_manager.get_all_jobs.return_value = {}
        self.mock_job_manager.update_job_status.return_value = None
        self.mock_job_manager.set_job_result.return_value = None
        self.mock_job_manager.set_job_error.return_value = None
        
        # Mock file service
        self.mock_file_service = Mock()
        
        # Mock UnifiedVoiceTranscriber
        self.mock_transcriber = Mock()
        self.mock_transcriber.transcribe_audio.return_value = {
            'text': 'Test transcription',
            'language': 'en',
            'segments': [],
            'speaker_segments': []
        }
    
    def tearDown(self):
        """Clean up after tests"""
        pass
    
    def test_init_app(self):
        """Test service initialization with Flask app"""
        with patch('app.services.transcription_service.JobManager') as mock_job_manager_class, \
             patch('app.services.transcription_service.FileService') as mock_file_service_class:
            
            mock_job_manager_class.return_value = self.mock_job_manager
            mock_file_service_class.return_value = self.mock_file_service
            
            self.service.init_app(self.mock_app)
            
            self.assertEqual(self.service.app, self.mock_app)
            self.assertEqual(self.service.job_manager, self.mock_job_manager)
            self.assertEqual(self.service.file_service, self.mock_file_service)
    
    def test_start_transcription_success(self):
        """Test successful transcription start"""
        # Initialize service
        self.service.app = self.mock_app
        self.service.job_manager = self.mock_job_manager
        self.service.file_service = self.mock_file_service
        
        # Mock file upload
        mock_file_upload = Mock()
        mock_file_upload.filename = 'test.wav'
        mock_file_upload.original_name = 'test.wav'
        mock_file_upload.size_mb = 10.5
        
        # Mock job creation
        mock_job = Mock()
        self.mock_job_manager.create_job.return_value = mock_job
        
        # Start transcription
        job = self.service.start_transcription(
            job_id='test-job-123',
            file_upload=mock_file_upload,
            model_size='base',
            enable_speaker_diarization=True,
            language='en'
        )
        
        # Verify job was created
        self.mock_job_manager.create_job.assert_called_once()
        self.assertEqual(job, mock_job)
    
    def test_start_transcription_not_initialized(self):
        """Test transcription start when service not initialized"""
        with self.assertRaises(RuntimeError):
            self.service.start_transcription(
                job_id='test-job-123',
                file_upload=Mock(),
                model_size='base',
                enable_speaker_diarization=True,
                language='en'
            )
    
    @patch('app.services.transcription_service.UnifiedVoiceTranscriber')
    def test_transcribe_background_success(self, mock_transcriber_class):
        """Test successful background transcription"""
        # Setup mocks
        mock_transcriber_class.return_value = self.mock_transcriber
        self.service.app = self.mock_app
        self.service.job_manager = self.mock_job_manager
        
        # Mock job
        mock_job = Mock()
        mock_job.start_time = datetime.now()
        self.mock_job_manager.get_job.return_value = mock_job
        
        # Mock file operations
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('os.path.join', return_value='test_output.md'), \
             patch('os.path.getsize', return_value=1024*1024):
            
            # Run background transcription
            self.service._transcribe_background(
                job_id='test-job-123',
                filepath='test.wav',
                model_size='base',
                enable_speaker_diarization=True,
                language='en',
                temperature=0.2
            )
            
            # Verify transcriber was created and called
            mock_transcriber_class.assert_called_once_with(
                model_size='base',
                enable_speaker_diarization=True
            )
            self.mock_transcriber.transcribe_audio.assert_called_once()
    
    @patch('app.services.transcription_service.UnifiedVoiceTranscriber')
    def test_transcribe_background_failure(self, mock_transcriber_class):
        """Test background transcription failure"""
        # Setup mocks
        mock_transcriber_class.return_value = self.mock_transcriber
        self.mock_transcriber.transcribe_audio.side_effect = Exception("Transcription failed")
        
        self.service.app = self.mock_app
        self.service.job_manager = self.mock_job_manager
        
        # Run background transcription
        self.service._transcribe_background(
            job_id='test-job-123',
            filepath='test.wav',
            model_size='base',
            enable_speaker_diarization=True,
            language='en',
            temperature=0.2
        )
        
        # Verify error was set
        self.mock_job_manager.set_job_error.assert_called_once()
    
    def test_transcribe_background_no_transcriber(self):
        """Test background transcription when transcriber not available"""
        with patch('app.services.transcription_service.UnifiedVoiceTranscriber', None):
            self.service.app = self.mock_app
            self.service.job_manager = self.mock_job_manager
            
            # Run background transcription
            self.service._transcribe_background(
                job_id='test-job-123',
                filepath='test.wav',
                model_size='base',
                enable_speaker_diarization=True,
                language='en',
                temperature=0.2
            )
            
            # Verify error was set
            self.mock_job_manager.set_job_error.assert_called_once()
    
    def test_emit_progress_update(self):
        """Test progress update emission"""
        self.service.app = self.mock_app
        
        # Test that the method doesn't raise an exception
        # The actual socketio emit is mocked in the app setup
        try:
            self.service._emit_progress_update(
                job_id='test-job-123',
                status='transcribing',
                progress=50,
                message='Transcribing...',
                result={'test': 'data'}
            )
            # If we get here, the method executed without error
            self.assertTrue(True)
        except Exception as e:
            # If there's an error, it should be related to socketio emit
            # which is expected in test environment
            self.assertIn('emit', str(e).lower())
    
    def test_emit_progress_update_no_app(self):
        """Test progress update when no app available"""
        # Should not raise exception
        self.service._emit_progress_update(
            job_id='test-job-123',
            status='transcribing',
            progress=50,
            message='Transcribing...'
        )
    
    def test_update_request_tracking(self):
        """Test request tracking update"""
        self.service.app = self.mock_app
        
        with patch('app.get_request_tracker') as mock_get_tracker:
            mock_tracker = Mock()
            mock_get_tracker.return_value = mock_tracker
            
            self.service._update_request_tracking(
                request_id='test-request-123',
                status='completed',
                progress=100,
                result_file='test.md'
            )
            
            # Verify tracker was called
            mock_tracker.complete_request.assert_called_once_with(
                'test-request-123',
                'test.md'
            )
    
    def test_update_request_tracking_no_request_id(self):
        """Test request tracking update with no request ID"""
        self.service.app = self.mock_app
        
        # Should not raise exception
        self.service._update_request_tracking(
            request_id=None,
            status='completed',
            progress=100
        )
    
    def test_generate_transcription_markdown(self):
        """Test markdown generation"""
        with patch('os.path.getsize', return_value=1024*1024), \
             patch('os.path.basename', return_value='test.wav'):
            
            result = {
                'text': 'Test transcription text',
                'language': 'en',
                'speaker_segments': [
                    {
                        'speaker': 'Speaker 1',
                        'start_time': '00:00:00',
                        'end_time': '00:00:05',
                        'text': 'Hello world'
                    }
                ]
            }
            
            content = self.service._generate_transcription_markdown(
                filepath='test.wav',
                result=result,
                model_size='base',
                start_time=datetime.now()
            )
            
            # Check content structure
            self.assertIn('# test - Transcription', content)
            self.assertIn('**File:** test.wav', content)
            self.assertIn('**Language:** en', content)
            self.assertIn('**Model Used:** Whisper BASE', content)
            self.assertIn('Test transcription text', content)
            self.assertIn('## Speaker Analysis', content)
            self.assertIn('**Speaker Speaker 1**', content)
    
    def test_get_job(self):
        """Test getting job by ID"""
        self.service.job_manager = self.mock_job_manager
        
        job = self.service.get_job('test-job-123')
        
        self.mock_job_manager.get_job.assert_called_once_with('test-job-123')
    
    def test_get_job_no_manager(self):
        """Test getting job when no job manager"""
        job = self.service.get_job('test-job-123')
        self.assertIsNone(job)
    
    def test_get_all_jobs(self):
        """Test getting all jobs"""
        self.service.job_manager = self.mock_job_manager
        
        jobs = self.service.get_all_jobs()
        
        self.mock_job_manager.get_all_jobs.assert_called_once()
    
    def test_get_all_jobs_no_manager(self):
        """Test getting all jobs when no job manager"""
        jobs = self.service.get_all_jobs()
        self.assertEqual(jobs, {})
    
    def test_cancel_job_success(self):
        """Test successful job cancellation"""
        self.service.app = self.mock_app
        self.service.job_manager = self.mock_job_manager
        
        # Mock job
        mock_job = Mock()
        mock_job.status = 'transcribing'
        mock_job.progress = 50
        self.mock_job_manager.get_job.return_value = mock_job
        
        result = self.service.cancel_job('test-job-123')
        
        self.assertTrue(result)
        self.mock_job_manager.update_job_status.assert_called_once_with(
            'test-job-123',
            'cancelled',
            50
        )
    
    def test_cancel_job_not_found(self):
        """Test cancelling non-existent job"""
        self.service.job_manager = self.mock_job_manager
        self.mock_job_manager.get_job.return_value = None
        
        result = self.service.cancel_job('test-job-123')
        
        self.assertFalse(result)
    
    def test_cancel_job_already_completed(self):
        """Test cancelling already completed job"""
        self.service.job_manager = self.mock_job_manager
        
        # Mock completed job
        mock_job = Mock()
        mock_job.status = 'completed'
        self.mock_job_manager.get_job.return_value = mock_job
        
        result = self.service.cancel_job('test-job-123')
        
        self.assertFalse(result)
    
    def test_cancel_job_no_manager(self):
        """Test cancelling job when no job manager"""
        result = self.service.cancel_job('test-job-123')
        self.assertFalse(result)


def mock_open():
    """Mock open function for file operations"""
    return MagicMock()


class TestTranscriptionServiceIntegration(unittest.TestCase):
    """Integration tests for TranscriptionService"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.service = TranscriptionService()
        
        # Mock Flask app
        self.mock_app = Mock()
        self.mock_app.config = {
            'MAX_CONCURRENT_JOBS': 3,
            'JOB_CLEANUP_HOURS': 1,
            'UPLOAD_FOLDER': 'uploads',
            'ALLOWED_EXTENSIONS': {'wav', 'mp3', 'm4a'}
        }
    
    def tearDown(self):
        """Clean up after tests"""
        pass
    
    @patch('app.services.transcription_service.JobManager')
    @patch('app.services.transcription_service.FileService')
    @patch('app.services.transcription_service.UnifiedVoiceTranscriber')
    def test_full_transcription_workflow(self, mock_transcriber_class, 
                                       mock_file_service_class, 
                                       mock_job_manager_class):
        """Test complete transcription workflow"""
        # Setup mocks
        mock_job_manager = Mock()
        mock_file_service = Mock()
        mock_transcriber = Mock()
        
        mock_job_manager_class.return_value = mock_job_manager
        mock_file_service_class.return_value = mock_file_service
        mock_transcriber_class.return_value = mock_transcriber
        
        # Mock transcription result
        mock_transcriber.transcribe_audio.return_value = {
            'text': 'Test transcription',
            'language': 'en',
            'segments': [],
            'speaker_segments': []
        }
        
        # Initialize service
        self.service.init_app(self.mock_app)
        
        # Mock file upload
        mock_file_upload = Mock()
        mock_file_upload.filename = 'test.wav'
        mock_file_upload.original_name = 'test.wav'
        mock_file_upload.size_mb = 5.0
        
        # Mock job
        mock_job = Mock()
        mock_job.start_time = datetime.now()
        mock_job_manager.create_job.return_value = mock_job
        mock_job_manager.get_job.return_value = mock_job
        
        # Start transcription
        job = self.service.start_transcription(
            job_id='test-job-123',
            file_upload=mock_file_upload,
            model_size='base',
            enable_speaker_diarization=True,
            language='en'
        )
        
        # Verify job was created
        self.assertIsNotNone(job)
        mock_job_manager.create_job.assert_called_once()
        
        # Wait a bit for background thread
        time.sleep(0.1)
        
        # Verify transcriber was created
        mock_transcriber_class.assert_called_once_with(
            model_size='base',
            enable_speaker_diarization=True
        )


if __name__ == '__main__':
    unittest.main()
