"""
File handling service
"""

import os
import uuid
from pathlib import Path
from typing import Optional
from werkzeug.utils import secure_filename

from app.models.file_upload import FileUpload
from app.config import Config

class FileService:
    """Handles file operations"""
    
    def __init__(self, upload_folder: str, allowed_extensions: set):
        self.upload_folder = upload_folder
        self.allowed_extensions = allowed_extensions
        self._ensure_upload_folder()
    
    def _ensure_upload_folder(self):
        """Ensure upload folder exists"""
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename"""
        filename = secure_filename(original_filename)
        unique_id = str(uuid.uuid4())
        return f"{unique_id}_{filename}"
    
    def save_uploaded_file(self, file, max_size_bytes: int) -> FileUpload:
        """Save uploaded file and return FileUpload object"""
        if not file or file.filename == '':
            raise ValueError("No file provided")
        
        if not self.is_allowed_file(file.filename):
            raise ValueError(f"Invalid file type. Allowed: {', '.join(self.allowed_extensions)}")
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > max_size_bytes:
            raise ValueError(f"File too large. Maximum size: {max_size_bytes / (1024*1024):.0f}MB")
        
        # Generate unique filename
        unique_filename = self.generate_unique_filename(file.filename)
        
        # Save file
        file_upload = FileUpload.from_file(file, self.upload_folder, unique_filename)
        
        return file_upload
    
    def delete_file(self, filepath: str) -> bool:
        """Delete a file"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except OSError:
            pass
        return False
    
    def cleanup_old_files(self, hours: int = 24):
        """Clean up files older than specified hours"""
        import time
        current_time = time.time()
        cutoff_time = current_time - (hours * 60 * 60)
        
        try:
            for filename in os.listdir(self.upload_folder):
                filepath = os.path.join(self.upload_folder, filename)
                if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff_time:
                    os.remove(filepath)
        except OSError:
            pass
    
    def get_uploaded_files(self):
        """Get list of uploaded files (placeholder for now)"""
        # This would typically return a list of FileUpload objects
        # For now, return empty list
        return []
