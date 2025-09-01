"""
File upload model
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

@dataclass
class FileUpload:
    """Represents an uploaded file"""
    
    filename: str
    original_name: str
    filepath: str
    size_bytes: int
    content_type: Optional[str] = None
    
    @property
    def size_mb(self) -> float:
        """Get file size in MB"""
        return self.size_bytes / (1024 * 1024)
    
    @property
    def extension(self) -> str:
        """Get file extension"""
        return Path(self.original_name).suffix.lower()
    
    @property
    def exists(self) -> bool:
        """Check if file exists"""
        return os.path.exists(self.filepath)
    
    def delete(self) -> bool:
        """Delete the file"""
        try:
            if self.exists:
                os.remove(self.filepath)
                return True
        except OSError:
            pass
        return False
    
    @classmethod
    def from_file(cls, file, upload_folder: str, unique_filename: str) -> 'FileUpload':
        """Create FileUpload from uploaded file"""
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)
        
        return cls(
            filename=unique_filename,
            original_name=file.filename,
            filepath=filepath,
            size_bytes=os.path.getsize(filepath),
            content_type=file.content_type
        )
