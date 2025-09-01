# 🔌 Voice Transcriber API Reference

Complete API documentation for the Voice Transcriber web application.

## 🌐 Base URL

- **Development**: `http://localhost:5001`
- **Production**: `https://your-domain.com`

## 📋 API Endpoints

### 🏠 Main Routes

#### GET /
**Description**: Main application page  
**Response**: HTML page with the web interface

---

#### GET /health
**Description**: Health check endpoint  
**Response**: JSON with application status

**Response Example**:
```json
{
  "status": "healthy",
  "timestamp": "2024-09-01T23:20:00.000Z",
  "active_jobs": 2
}
```

---

### 📁 File Upload

#### POST /api/upload
**Description**: Upload an audio file for transcription

**Request**:
- **Content-Type**: `multipart/form-data`
- **Body**: Form data with `file` field

**Request Example**:
```bash
curl -X POST http://localhost:5001/api/upload \
  -F "file=@audio.wav"
```

**Response**:
```json
{
  "success": true,
  "filename": "uuid_audio.wav",
  "original_name": "audio.wav",
  "size_mb": 15.2,
  "filepath": "/app/uploads/uuid_audio.wav"
}
```

**Error Responses**:
- `400 Bad Request`: No file provided or invalid file type
- `413 Request Entity Too Large`: File too large
- `500 Internal Server Error`: Upload failed

---

### 🎤 Transcription

#### POST /api/transcribe
**Description**: Start transcription process

**Request**:
```json
{
  "filename": "uuid_audio.wav",
  "model_size": "base",
  "enable_speaker_diarization": true,
  "language": "auto"
}
```

**Parameters**:
- `filename` (string, required): Uploaded file filename
- `model_size` (string, optional): Whisper model size (`tiny`, `base`, `small`, `medium`, `large`)
- `enable_speaker_diarization` (boolean, optional): Enable speaker identification
- `language` (string, optional): Language code or `auto` for auto-detection

**Response**:
```json
{
  "success": true,
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Transcription started"
}
```

**Error Responses**:
- `400 Bad Request`: Missing filename or invalid parameters
- `404 Not Found`: File not found
- `429 Too Many Requests`: Too many concurrent jobs
- `500 Internal Server Error`: Failed to start transcription

---

#### GET /api/job/{job_id}
**Description**: Get transcription job status

**Response**:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "progress": 100,
  "filename": "uuid_audio.wav",
  "original_filename": "audio.wav",
  "model_size": "base",
  "enable_speaker_diarization": true,
  "language": "en",
  "start_time": "2024-09-01T23:20:00.000Z",
  "end_time": "2024-09-01T23:22:30.000Z",
  "result": {
    "transcription": {
      "text": "Hello, this is a test transcription...",
      "language": "en",
      "segments": [...]
    },
    "output_file": "transcription_123e4567_20240901_232230.md",
    "output_path": "/app/transcriptions/transcription_123e4567_20240901_232230.md"
  },
  "error": null,
  "file_size_mb": 15.2
}
```

**Job Statuses**:
- `starting`: Job is being initialized
- `loading_model`: Loading Whisper model
- `transcribing`: Transcribing audio
- `processing`: Processing results
- `completed`: Transcription completed successfully
- `error`: Transcription failed

---

### 📥 Download

#### GET /api/download/{filename}
**Description**: Download transcription file

**Response**: File download (Markdown format)

**Error Responses**:
- `404 Not Found`: File not found
- `500 Internal Server Error`: Download failed

---

### 🤖 Models

#### GET /api/models
**Description**: Get available Whisper models

**Response**:
```json
{
  "models": [
    {
      "id": "tiny",
      "name": "Tiny",
      "description": "Fastest, lowest accuracy"
    },
    {
      "id": "base",
      "name": "Base",
      "description": "Good balance of speed and accuracy"
    },
    {
      "id": "small",
      "name": "Small",
      "description": "Better accuracy, slower"
    },
    {
      "id": "medium",
      "name": "Medium",
      "description": "High accuracy, slower"
    },
    {
      "id": "large",
      "name": "Large",
      "description": "Best accuracy, slowest"
    }
  ]
}
```

---

## 🔌 WebSocket Events

### Connection
**Event**: `connect`  
**Description**: Client connects to server

**Response**:
```json
{
  "message": "Connected to transcription server"
}
```

---

### Progress Updates
**Event**: `progress_update`  
**Description**: Real-time transcription progress updates

**Data**:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "transcribing",
  "progress": 45,
  "message": "Transcribing audio...",
  "result": {
    "output_file": "transcription_123e4567_20240901_232230.md",
    "language": "en",
    "duration": "2:30",
    "speakers": 2
  }
}
```

---

### Job Room Management
**Event**: `join_job`  
**Description**: Join a job room for updates

**Data**:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Response**:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

---

**Event**: `leave_job`  
**Description**: Leave a job room

**Data**:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Response**:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

---

## 📝 Data Models

### TranscriptionJob
```json
{
  "job_id": "string",
  "status": "string",
  "progress": "number",
  "filename": "string",
  "original_filename": "string",
  "model_size": "string",
  "enable_speaker_diarization": "boolean",
  "language": "string",
  "start_time": "string (ISO 8601)",
  "end_time": "string (ISO 8601)",
  "result": "object",
  "error": "string",
  "file_size_mb": "number"
}
```

### FileUpload
```json
{
  "filename": "string",
  "original_name": "string",
  "filepath": "string",
  "size_bytes": "number",
  "content_type": "string"
}
```

### TranscriptionResult
```json
{
  "text": "string",
  "language": "string",
  "duration": "string",
  "segments": [
    {
      "start": "number",
      "end": "number",
      "text": "string",
      "speaker": "string"
    }
  ],
  "speaker_segments": [
    {
      "speaker": "string",
      "start_time": "string",
      "end_time": "string",
      "text": "string"
    }
  ]
}
```

---

## 🔒 Error Handling

### HTTP Status Codes
- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `413 Request Entity Too Large`: File too large
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Error Response Format
```json
{
  "error": "Error message description"
}
```

---

## 📊 Rate Limits

- **File Upload**: 2 requests per second
- **API Endpoints**: 10 requests per second
- **Concurrent Jobs**: 5 maximum (configurable)

---

## 🔧 Configuration

### Environment Variables
- `MAX_CONCURRENT_JOBS`: Maximum concurrent transcription jobs
- `MAX_CONTENT_LENGTH`: Maximum file size in bytes
- `UPLOAD_FOLDER`: Directory for uploaded files
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

---

## 📚 Examples

### Complete Workflow Example

1. **Upload file**:
```bash
curl -X POST http://localhost:5001/api/upload \
  -F "file=@audio.wav"
```

2. **Start transcription**:
```bash
curl -X POST http://localhost:5001/api/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "uuid_audio.wav",
    "model_size": "base",
    "enable_speaker_diarization": true,
    "language": "auto"
  }'
```

3. **Check job status**:
```bash
curl http://localhost:5001/api/job/123e4567-e89b-12d3-a456-426614174000
```

4. **Download result**:
```bash
curl -O http://localhost:5001/api/download/transcription_123e4567_20240901_232230.md
```

---

## 🆘 Troubleshooting

### Common Issues

1. **File upload fails**:
   - Check file size (max 500MB)
   - Verify file format is supported
   - Ensure proper Content-Type header

2. **Transcription fails**:
   - Check available disk space
   - Verify audio file is not corrupted
   - Check logs for detailed error messages

3. **WebSocket connection issues**:
   - Ensure WebSocket support in client
   - Check firewall settings
   - Verify connection URL

---

**For more information, see the [Technical Reference](TECHNICAL_REFERENCE.md) and [Web App Guide](WEB_APP_README.md).**
