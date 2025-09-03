"""
Analytics Service for Voice Transcriber Application
Provides centralized tracking management for Google Analytics and Hotjar
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from flask import current_app, request, session
from app.utils.logger import get_logger

logger = get_logger(__name__)

class AnalyticsService:
    """Centralized analytics service for tracking user interactions"""
    
    def __init__(self):
        self.config = current_app.config
        self.session_id = self._generate_session_id()
        self.user_properties = {}
        
    def _generate_session_id(self) -> str:
        """Generate a unique session ID for analytics tracking"""
        return f"session_{int(time.time() * 1000)}_{hash(request.remote_addr) % 10000}"
    
    def _is_analytics_enabled(self) -> bool:
        """Check if analytics is enabled in configuration"""
        return self.config.get('ENABLE_ANALYTICS', False)
    
    def _is_google_analytics_enabled(self) -> bool:
        """Check if Google Analytics is enabled"""
        return (self._is_analytics_enabled() and 
                self.config.get('ENABLE_GOOGLE_ANALYTICS', False) and
                self.config.get('GOOGLE_ANALYTICS_ID'))
    
    def _is_hotjar_enabled(self) -> bool:
        """Check if Hotjar is enabled"""
        return (self._is_analytics_enabled() and 
                self.config.get('ENABLE_HOTJAR', False) and
                self.config.get('HOTJAR_SITE_ID'))
    
    def get_analytics_config(self) -> Dict[str, Any]:
        """Get analytics configuration for frontend"""
        config = {
            'enabled': self._is_analytics_enabled(),
            'google_analytics': {
                'enabled': self._is_google_analytics_enabled(),
                'measurement_id': self.config.get('GOOGLE_ANALYTICS_ID') if self._is_google_analytics_enabled() else None
            },
            'hotjar': {
                'enabled': self._is_hotjar_enabled(),
                'site_id': self.config.get('HOTJAR_SITE_ID') if self._is_hotjar_enabled() else None
            },
            'debug': self.config.get('ANALYTICS_DEBUG', False),
            'session_id': self.session_id
        }
        return config
    
    def track_page_view(self, page_title: str, page_path: str = None) -> None:
        """Track page view event"""
        if not self._is_analytics_enabled():
            return
            
        page_path = page_path or request.path
        event_data = {
            'event_name': 'page_view',
            'page_title': page_title,
            'page_path': page_path,
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.session_id,
            'user_agent': request.headers.get('User-Agent', ''),
            'referrer': request.headers.get('Referer', ''),
            'ip_address': request.remote_addr
        }
        
        self._log_analytics_event('page_view', event_data)
    
    def track_file_upload(self, file_name: str, file_size: int, file_type: str) -> None:
        """Track file upload event"""
        if not self._is_analytics_enabled():
            return
            
        event_data = {
            'event_name': 'file_upload',
            'file_name': file_name,
            'file_size': file_size,
            'file_type': file_type,
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.session_id,
            'ip_address': request.remote_addr
        }
        
        self._log_analytics_event('file_upload', event_data)
    
    def track_transcription_start(self, model: str, language: str, speaker_diarization: bool, 
                                temperature: float, file_size: int) -> None:
        """Track transcription start event"""
        if not self._is_analytics_enabled():
            return
            
        event_data = {
            'event_name': 'transcription_start',
            'model': model,
            'language': language,
            'speaker_diarization': speaker_diarization,
            'temperature': temperature,
            'file_size': file_size,
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.session_id,
            'ip_address': request.remote_addr
        }
        
        self._log_analytics_event('transcription_start', event_data)
    
    def track_transcription_complete(self, job_id: str, model: str, language: str, 
                                   processing_time: float, file_size: int, 
                                   transcript_length: int, success: bool = True) -> None:
        """Track transcription completion event"""
        if not self._is_analytics_enabled():
            return
            
        event_data = {
            'event_name': 'transcription_complete',
            'job_id': job_id,
            'model': model,
            'language': language,
            'processing_time': processing_time,
            'file_size': file_size,
            'transcript_length': transcript_length,
            'success': success,
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.session_id,
            'ip_address': request.remote_addr
        }
        
        self._log_analytics_event('transcription_complete', event_data)
    
    def track_transcription_error(self, job_id: str, error_type: str, error_message: str, 
                                model: str, file_size: int) -> None:
        """Track transcription error event"""
        if not self._is_analytics_enabled():
            return
            
        event_data = {
            'event_name': 'transcription_error',
            'job_id': job_id,
            'error_type': error_type,
            'error_message': error_message,
            'model': model,
            'file_size': file_size,
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.session_id,
            'ip_address': request.remote_addr
        }
        
        self._log_analytics_event('transcription_error', event_data)
    
    def track_user_interaction(self, interaction_type: str, element_id: str = None, 
                             element_class: str = None, additional_data: Dict = None) -> None:
        """Track general user interaction events"""
        if not self._is_analytics_enabled():
            return
            
        event_data = {
            'event_name': 'user_interaction',
            'interaction_type': interaction_type,
            'element_id': element_id,
            'element_class': element_class,
            'additional_data': additional_data or {},
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.session_id,
            'ip_address': request.remote_addr
        }
        
        self._log_analytics_event('user_interaction', event_data)
    
    def track_download(self, file_name: str, file_type: str, file_size: int) -> None:
        """Track file download event"""
        if not self._is_analytics_enabled():
            return
            
        event_data = {
            'event_name': 'file_download',
            'file_name': file_name,
            'file_type': file_type,
            'file_size': file_size,
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.session_id,
            'ip_address': request.remote_addr
        }
        
        self._log_analytics_event('file_download', event_data)
    
    def track_performance_metric(self, metric_name: str, metric_value: float, 
                               unit: str = None, context: Dict = None) -> None:
        """Track performance metrics"""
        if not self._is_analytics_enabled():
            return
            
        event_data = {
            'event_name': 'performance_metric',
            'metric_name': metric_name,
            'metric_value': metric_value,
            'unit': unit,
            'context': context or {},
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.session_id,
            'ip_address': request.remote_addr
        }
        
        self._log_analytics_event('performance_metric', event_data)
    
    def set_user_property(self, property_name: str, property_value: Any) -> None:
        """Set user property for analytics"""
        self.user_properties[property_name] = property_value
    
    def get_user_properties(self) -> Dict[str, Any]:
        """Get current user properties"""
        return self.user_properties.copy()
    
    def _log_analytics_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Log analytics event for debugging and analysis"""
        try:
            if self.config.get('ANALYTICS_DEBUG', False):
                logger.info(f"Analytics Event: {event_type}", extra=event_data)
            
            # Store in session for frontend access if needed
            if 'analytics_events' not in session:
                session['analytics_events'] = []
            
            session['analytics_events'].append(event_data)
            
            # Keep only last 50 events in session
            if len(session['analytics_events']) > 50:
                session['analytics_events'] = session['analytics_events'][-50:]
                
        except Exception as e:
            logger.error(f"Error logging analytics event: {e}")
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary for current session"""
        events = session.get('analytics_events', [])
        
        summary = {
            'session_id': self.session_id,
            'total_events': len(events),
            'event_types': {},
            'user_properties': self.get_user_properties(),
            'session_start': events[0]['timestamp'] if events else None,
            'last_activity': events[-1]['timestamp'] if events else None
        }
        
        # Count event types
        for event in events:
            event_name = event.get('event_name', 'unknown')
            summary['event_types'][event_name] = summary['event_types'].get(event_name, 0) + 1
        
        return summary


# Global analytics service instance
analytics_service = AnalyticsService()
