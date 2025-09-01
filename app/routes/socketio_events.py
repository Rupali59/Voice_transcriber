"""
SocketIO event handlers
"""

from flask_socketio import emit
import logging

logger = logging.getLogger(__name__)

def register_socketio_events(socketio):
    """Register SocketIO event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger.info('Client connected')
        emit('connected', {'message': 'Connected to transcription server'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info('Client disconnected')
    
    @socketio.on('join_job')
    def handle_join_job(data):
        """Handle client joining a job room"""
        job_id = data.get('job_id')
        if job_id:
            from flask_socketio import join_room
            join_room(job_id)
            emit('joined_job', {'job_id': job_id})
    
    @socketio.on('leave_job')
    def handle_leave_job(data):
        """Handle client leaving a job room"""
        job_id = data.get('job_id')
        if job_id:
            from flask_socketio import leave_room
            leave_room(job_id)
            emit('left_job', {'job_id': job_id})
