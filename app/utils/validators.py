"""
Validation utilities
"""

from typing import Dict, Any, List

def validate_file_upload(file, allowed_extensions: set, max_size: int) -> Dict[str, Any]:
    """Validate file upload"""
    errors = []
    
    if not file or file.filename == '':
        errors.append('No file provided')
        return {'valid': False, 'errors': errors}
    
    # Check file extension
    if '.' not in file.filename:
        errors.append('File must have an extension')
    else:
        extension = file.filename.rsplit('.', 1)[1].lower()
        if extension not in allowed_extensions:
            errors.append(f'Invalid file type. Allowed: {", ".join(allowed_extensions)}')
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        errors.append(f'File too large. Maximum size: {max_size_mb:.0f}MB')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'file_size': file_size
    }

def validate_transcription_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate transcription request"""
    errors = []
    
    required_fields = ['filename']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f'Missing required field: {field}')
    
    # Validate model size
    valid_models = ['tiny', 'base', 'small', 'medium', 'large']
    model_size = data.get('model_size', 'base')
    if model_size not in valid_models:
        errors.append(f'Invalid model size. Allowed: {", ".join(valid_models)}')
    
    # Validate boolean fields
    boolean_fields = ['enable_speaker_diarization']
    for field in boolean_fields:
        if field in data and not isinstance(data[field], bool):
            errors.append(f'Field {field} must be boolean')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
