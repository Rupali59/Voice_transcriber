# 🎤 Voice Transcriber

A modern, AI-powered web application for transcribing audio files using OpenAI's Whisper model. Features real-time progress tracking, speaker diarization, and a beautiful responsive interface.

## ✨ Features

- **🎯 AI-Powered Transcription** - Uses OpenAI Whisper models (Tiny, Base, Small, Medium, Large)
- **👥 Speaker Diarization** - Identifies different speakers in audio files
- **🌍 Multi-Language Support** - Auto-detect or specify language
- **📱 Modern Web Interface** - Beautiful, responsive design with drag-and-drop upload
- **⚡ Real-time Progress** - Live updates during transcription with WebSocket
- **📁 Multiple File Formats** - Supports WAV, MP3, M4A, FLAC, OGG, WMA, AAC, MP4
- **💾 Large File Support** - Handle files up to 500MB
- **📄 Markdown Output** - Download transcriptions in formatted Markdown
- **🐳 Docker Ready** - Easy deployment with Docker and Docker Compose
- **🔧 Production Ready** - Proper error handling, logging, and monitoring

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker (optional, for containerized deployment)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Voice_transcriber
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app_main.py
   ```

4. **Access the application**
   - Open your browser and go to `http://localhost:5001`

### Docker Deployment

1. **Quick deployment**
   ```bash
   ./deploy.sh
   ```

2. **Manual deployment**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Open your browser and go to `http://localhost:5001`

## 📖 Usage

### 1. Upload Audio File
- Drag and drop an audio file onto the upload area
- Or click to browse and select a file
- Supported formats: WAV, MP3, M4A, FLAC, OGG, WMA, AAC, MP4
- Maximum file size: 500MB

### 2. Configure Options
- **AI Model**: Choose the Whisper model size
  - **Tiny**: Fastest, lowest accuracy
  - **Base**: Good balance (recommended)
  - **Small**: Better accuracy, slower
  - **Medium**: High accuracy, slower
  - **Large**: Best accuracy, slowest
- **Speaker Diarization**: Enable to identify different speakers
- **Language**: Auto-detect or specify the language

### 3. Start Transcription
- Click "Start Transcription"
- Watch real-time progress updates
- Download the result when complete

## 🏗️ Architecture

The application follows a clean, modular architecture:

```
Voice_transcriber/
├── app/                    # Main application package
│   ├── models/            # Data models
│   ├── routes/            # HTTP handlers
│   ├── services/          # Business logic
│   ├── utils/             # Utilities
│   ├── static/            # Web assets
│   └── templates/         # HTML templates
├── src/                   # Core transcription modules
├── tests/                 # Test files
├── docs/                  # Documentation
├── transcriptions/        # Output files
├── uploads/              # Upload files
└── logs/                 # Log files
```

### Key Components

- **Models**: Data structures for jobs and file uploads
- **Services**: Business logic for transcription, file handling, and job management
- **Routes**: API endpoints and web interface
- **Utils**: Logging, validation, and helper functions

## 🔧 Configuration

### Environment Variables

```bash
# Flask Configuration
FLASK_ENV=development          # development, production, testing
SECRET_KEY=your-secret-key
HOST=0.0.0.0
PORT=5001
DEBUG=true

# File Upload
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=524288000   # 500MB

# Job Management
MAX_CONCURRENT_JOBS=5
JOB_CLEANUP_HOURS=1
FILE_CLEANUP_HOURS=24

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/web_app.log
```

## 📊 API Endpoints

### Main Routes
- `GET /` - Main application page
- `GET /health` - Health check endpoint

### API Routes
- `POST /api/upload` - Upload audio file
- `POST /api/transcribe` - Start transcription
- `GET /api/job/<job_id>` - Get job status
- `GET /api/download/<filename>` - Download transcription
- `GET /api/models` - Get available models

### WebSocket Events
- `connect` - Client connection
- `disconnect` - Client disconnection
- `progress_update` - Real-time progress updates

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/unit/
python -m pytest tests/integration/
```

## 📚 Documentation

Comprehensive documentation is available in the `docs/` folder:

- **[Quick Start Guide](docs/QUICK_START.md)** - Get up and running quickly
- **[Technical Details](docs/TECHNICAL_DETAILS.md)** - In-depth technical information
- **[Performance Reference](docs/PERFORMANCE_QUICK_REFERENCE.md)** - Performance optimization
- **[Web App Guide](docs/WEB_APP_README.md)** - Web application documentation
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Deployment instructions
- **[Refactored Structure](docs/REFACTORED_STRUCTURE.md)** - Architecture overview

## 🚀 Deployment

### Local Development
```bash
python app_main.py
```

### Docker Deployment
```bash
./deploy.sh
```

### Production Deployment
The application is production-ready with:
- Proper error handling and logging
- Health check endpoints
- Resource management and cleanup
- Security best practices

## 🔒 Security Features

- File type validation
- File size limits
- Input sanitization
- Secure file handling
- Error message sanitization
- Environment-based configuration

## 📈 Performance

- Concurrent job processing (configurable limit)
- Automatic file cleanup
- Background processing
- Real-time progress updates
- Optimized resource management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the documentation in the `docs/` folder
2. Review the troubleshooting section
3. Create an issue in the repository
4. Check the logs for detailed error messages

## 🎉 Acknowledgments

- **OpenAI Whisper** - For the amazing AI transcription models
- **Flask** - For the web framework
- **SocketIO** - For real-time communication
- **Docker** - For containerization

---

**Built with ❤️ for easy, accurate, and fast voice transcription**
