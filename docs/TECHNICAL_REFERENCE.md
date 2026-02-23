# Technical Reference - Voice Transcriber

Comprehensive technical documentation for developers and system administrators.

## ⚡ Quick Start
- **What this covers**: Complete technical architecture, implementation details, and development setup
- **Time needed**: 20-30 minutes for full read, 5-10 minutes for quick overview
- **Prerequisites**: Basic understanding of Python, Flask, and web development
- **Skip to**: [Architecture Overview](#-architecture-overview) | [Development Setup](#-development-setup) | [API Integration](#-api-integration)

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │  Flask Server   │    │  Transcription  │
│                 │◄──►│                 │◄──►│    Service      │
│  - HTML/CSS/JS  │    │  - REST API     │    │  - Whisper AI   │
│  - WebSocket    │    │  - WebSocket    │    │  - File Proc    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Upload   │    │   Job Manager   │    │   File Storage  │
│                 │    │                 │    │                 │
│  - Validation   │    │  - Queue Mgmt   │    │  - Temp Files   │
│  - Processing   │    │  - Status Track │    │  - Cleanup      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Technologies

- **Backend**: Python 3.9+, Flask, SocketIO
- **AI Engine**: OpenAI Whisper
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Real-time**: WebSocket for progress updates
- **Storage**: Local file system with cleanup
- **Deployment**: Docker, Docker Compose

## 📁 Project Structure

```
app/
├── __init__.py              # Flask app initialization
├── config.py                # Configuration management
├── models/                  # Data models
│   ├── file_upload.py       # File upload model
│   └── transcription_job.py # Job tracking model
├── routes/                  # API endpoints
│   ├── main.py             # Main web routes
│   ├── api.py              # REST API endpoints
│   ├── admin.py            # Admin interface
│   └── socketio_events.py  # WebSocket handlers
├── services/               # Business logic
│   ├── file_service.py     # File management
│   ├── job_manager.py      # Job queue management
│   ├── transcription_service.py # Core transcription logic
│   └── request_tracker.py  # Request monitoring
├── static/                 # Web assets
│   ├── css/style.css       # Styling
│   ├── js/app.js          # Frontend logic
│   └── images/            # Static images
├── templates/              # HTML templates
│   ├── index.html         # Main interface
│   ├── layouts/           # Layout templates
│   └── components/        # Reusable components
└── utils/                  # Utilities
    ├── logger.py          # Logging configuration
    └── validators.py      # Input validation
```

## 🔧 Configuration

### Environment Variables

```bash
# Application Settings
FLASK_ENV=production          # Environment (development/production)
FLASK_DEBUG=False            # Debug mode
SECRET_KEY=your-secret-key   # Flask secret key

# Server Configuration
HOST=0.0.0.0                # Server host
PORT=5001                   # Server port
MAX_CONTENT_LENGTH=524288000 # Max file size (500MB)

# Transcription Settings
MAX_CONCURRENT_JOBS=5        # Max simultaneous jobs
DEFAULT_MODEL_SIZE=base      # Default Whisper model
ENABLE_SPEAKER_DIARIZATION=True # Default speaker diarization

# Model Cache Configuration
WHISPER_MODEL_CACHE_SIZE=3   # Max models to keep in memory
MODEL_IDLE_TIMEOUT=1800      # Idle timeout in seconds (30 min)
MODEL_CLEANUP_INTERVAL=300   # Cleanup interval in seconds (5 min)
ENABLE_GPU_ACCELERATION=true # Use GPU if available
PRELOAD_MODELS=base,small    # Models to preload on startup

# File Management
UPLOAD_FOLDER=uploads        # Upload directory
TRANSCRIPTION_FOLDER=transcriptions # Output directory
CLEANUP_INTERVAL=3600        # Cleanup interval (seconds)

# Logging
LOG_LEVEL=INFO              # Logging level
LOG_FILE=logs/transcriber.log # Log file path
```

### Configuration Classes

```python
class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    UPLOAD_FOLDER = 'uploads'
    TRANSCRIPTION_FOLDER = 'transcriptions'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'
```

## 🔌 API Architecture

### REST Endpoints

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | `/` | Main web interface | - |
| GET | `/health` | Health check | - |
| POST | `/api/upload` | Upload audio file | `file` (multipart) |
| POST | `/api/transcribe` | Start transcription | `filename`, `model_size`, `language`, `speaker_diarization` |
| GET | `/api/job/{job_id}` | Get job status | `job_id` |
| GET | `/api/download/{filename}` | Download result | `filename` |
| GET | `/api/models` | List available models | - |

### WebSocket Events

| Event | Direction | Description | Data |
|-------|-----------|-------------|------|
| `connect` | Server → Client | Connection established | `{message: "Connected"}` |
| `progress_update` | Server → Client | Job progress update | `{job_id, status, progress, result}` |
| `join_job` | Client → Server | Join job room | `{job_id}` |
| `leave_job` | Client → Server | Leave job room | `{job_id}` |

## 🧠 Transcription Service

### Model Cache System

The application uses an intelligent model caching system to optimize performance:

```python
class ModelCache:
    """Singleton model cache manager"""
    
    def __init__(self):
        self.models = {}  # Cached models
        self.model_usage = {}  # Usage statistics
        self.cache_config = {
            'max_models': 3,  # Maximum cached models
            'idle_timeout': 1800,  # 30 minutes
            'cleanup_interval': 300,  # 5 minutes
            'enable_gpu': True
        }
    
    def get_model(self, model_size):
        """Get cached model or load if not cached"""
        if model_size in self.models:
            self._update_usage(model_size)
            return self.models[model_size]
        return self._load_model(model_size)
    
    def _load_model(self, model_size):
        """Load and cache a new model"""
        device = "cuda" if self.cache_config['enable_gpu'] else "cpu"
        model = whisper.load_model(model_size, device=device)
        self.models[model_size] = model
        return model
```

### Whisper Model Integration

```python
class TranscriptionService:
    def __init__(self):
        self.model_cache = get_model_cache()
    
    def transcribe(self, audio_file, model_size='base', 
                   language='auto', enable_speaker_diarization=True):
        """Transcribe audio file using cached model"""
        model = self.model_cache.get_model(model_size)
        result = model.transcribe(
            audio_file,
            language=language if language != 'auto' else None
        )
        return self.process_result(result, enable_speaker_diarization)
```

### Job Management

```python
class JobManager:
    def __init__(self, max_concurrent=5):
        self.max_concurrent = max_concurrent
        self.active_jobs = {}
        self.job_queue = queue.Queue()
    
    def start_job(self, job_id, audio_file, options):
        """Start transcription job"""
        if len(self.active_jobs) >= self.max_concurrent:
            raise TooManyJobsError("Maximum concurrent jobs reached")
        
        job = TranscriptionJob(job_id, audio_file, options)
        self.active_jobs[job_id] = job
        
        # Start transcription in background thread
        thread = threading.Thread(target=self._process_job, args=(job,))
        thread.start()
        
        return job
```

## 📊 Data Models

### TranscriptionJob

```python
class TranscriptionJob:
    def __init__(self, job_id, filename, options):
        self.job_id = job_id
        self.filename = filename
        self.original_filename = options.get('original_filename')
        self.model_size = options.get('model_size', 'base')
        self.language = options.get('language', 'auto')
        self.enable_speaker_diarization = options.get('enable_speaker_diarization', True)
        
        self.status = 'starting'
        self.progress = 0
        self.start_time = datetime.utcnow()
        self.end_time = None
        self.result = None
        self.error = None
```

### FileUpload

```python
class FileUpload:
    def __init__(self, filename, original_name, filepath, size_bytes):
        self.filename = filename
        self.original_name = original_name
        self.filepath = filepath
        self.size_bytes = size_bytes
        self.upload_time = datetime.utcnow()
        self.content_type = self._detect_content_type()
```

## 🔒 Security Considerations

### File Upload Security

- **File type validation**: Only allow audio formats
- **File size limits**: Maximum 500MB per file
- **Filename sanitization**: Prevent path traversal attacks
- **Temporary storage**: Files are cleaned up after processing

### API Security

- **Rate limiting**: Prevent abuse with request limits
- **Input validation**: Validate all input parameters
- **Error handling**: Don't expose sensitive information
- **CORS configuration**: Configure cross-origin requests

### Data Privacy

- **Local processing**: No data sent to external services
- **Temporary files**: Automatic cleanup of uploaded files
- **No persistent storage**: Transcriptions stored temporarily
- **Access control**: Configure as needed for your environment

## 📈 Performance Optimization

### Model Loading

- **Lazy loading**: Load models only when needed
- **Model caching**: Keep frequently used models in memory
- **Memory management**: Unload unused models

### File Processing

- **Streaming**: Process large files in chunks
- **Parallel processing**: Multiple jobs when resources allow
- **Cleanup**: Regular cleanup of temporary files

### Database Optimization

- **Connection pooling**: Reuse database connections
- **Query optimization**: Efficient database queries
- **Indexing**: Proper database indexes

## 🧪 Testing

### Test Structure

```
tests/
├── unit/                   # Unit tests
│   ├── test_config_manager.py
│   └── test_parallel_processor.py
├── integration/            # Integration tests
│   ├── test_end_to_end.py
│   └── test_transcriber_workflow.py
├── performance/            # Performance tests
│   └── test_performance_benchmarks.py
└── fixtures/               # Test data
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/performance/

# Run with coverage
python -m pytest --cov=app tests/
```

## 🚀 Deployment

### Docker Configuration

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5001

CMD ["python", "app_main.py"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  transcriber:
    build: .
    ports:
      - "5001:5001"
    volumes:
      - ./uploads:/app/uploads
      - ./transcriptions:/app/transcriptions
      - ./logs:/app/logs
    environment:
      - FLASK_ENV=production
      - MAX_CONCURRENT_JOBS=3
```

## 📝 Logging

### Log Configuration

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    if not app.debug:
        file_handler = RotatingFileHandler(
            'logs/transcriber.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
```

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about application flow
- **WARNING**: Something unexpected happened
- **ERROR**: A serious problem occurred
- **CRITICAL**: A very serious error occurred

## 📚 Related Documentation

- **Before reading this**: [Main Documentation](README.md) - Overview and quick start
- **After reading this**: 
  - [API Reference](API_REFERENCE.md) - Complete API documentation
  - [Deployment Guide](DEPLOYMENT.md) - Production deployment
  - [Performance Guide](PERFORMANCE_GUIDE.md) - Optimization strategies
- **For users**: [User Guide](USER_GUIDE.md) - End-user documentation
- **Troubleshooting**: [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions

---

**Built with ❤️ by Tathya** - Making voice transcription accessible and efficient.