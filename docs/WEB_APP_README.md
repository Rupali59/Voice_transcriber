# Voice Transcriber Web Application

A modern, responsive web interface for AI-powered voice transcription using OpenAI's Whisper model. Features real-time progress tracking, speaker diarization, and multiple model options.

## 🌟 Features

- **Modern Web UI**: Beautiful, responsive interface with drag-and-drop file upload
- **Real-time Progress**: Live updates during transcription with WebSocket connections
- **Multiple AI Models**: Choose from Tiny, Base, Small, Medium, or Large Whisper models
- **Speaker Diarization**: Identify different speakers in audio files
- **Language Support**: Auto-detect or specify language for better accuracy
- **File Format Support**: WAV, MP3, M4A, FLAC, OGG, WMA, AAC, MP4
- **Large File Support**: Handle files up to 500MB
- **Download Results**: Get transcriptions in Markdown format
- **Server Ready**: Production-ready with Docker deployment

## 🚀 Quick Start

### Local Development

1. **Install Dependencies**:
   ```bash
   pip install -r requirements-web.txt
   ```

2. **Run the Application**:
   ```bash
   python web_app.py
   ```

3. **Open in Browser**:
   Navigate to `http://localhost:5001`

### Production Deployment

1. **Using Docker Compose** (Recommended):
   ```bash
   ./deploy.sh
   ```

2. **Manual Docker Build**:
   ```bash
   docker-compose up -d
   ```

3. **Access the Application**:
   - HTTP: `http://localhost`
   - Direct: `http://localhost:5001`

## 📁 Project Structure

```
Voice_transcriber/
├── web_app.py                 # Development web application
├── web_app_production.py      # Production web application
├── templates/
│   └── index.html            # Main web interface
├── static/
│   ├── css/
│   │   └── style.css         # Modern CSS styling
│   └── js/
│       └── app.js            # Frontend JavaScript
├── uploads/                  # Temporary file uploads
├── transcriptions/           # Generated transcriptions
├── logs/                     # Application logs
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose setup
├── nginx.conf               # Nginx reverse proxy config
└── deploy.sh                # Deployment script
```

## 🎯 Usage

### 1. Upload Audio File
- Drag and drop an audio file onto the upload area
- Or click to browse and select a file
- Supported formats: WAV, MP3, M4A, FLAC, OGG, WMA, AAC, MP4
- Maximum file size: 500MB

### 2. Configure Options
- **AI Model**: Choose the Whisper model size
  - Tiny: Fastest, lowest accuracy
  - Base: Good balance (recommended)
  - Small: Better accuracy, slower
  - Medium: High accuracy, slower
  - Large: Best accuracy, slowest
- **Speaker Diarization**: Enable to identify different speakers
- **Language**: Auto-detect or specify the language

### 3. Start Transcription
- Click "Start Transcription"
- Watch real-time progress updates
- Download the result when complete

## 🔧 Configuration

### Environment Variables

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
PORT=5000
HOST=0.0.0.0

# File Upload
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=524288000  # 500MB in bytes

# Python Path
PYTHONPATH=/app/src
```

### Nginx Configuration

The included `nginx.conf` provides:
- Rate limiting for API endpoints
- File upload size limits
- WebSocket support for real-time updates
- Security headers
- Static file serving

## 🐳 Docker Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
# Build and deploy
./deploy.sh

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Docker Services

- **voice-transcriber**: Main Flask application
- **nginx**: Reverse proxy and static file server

## 📊 API Endpoints

### File Upload
```
POST /api/upload
Content-Type: multipart/form-data
Body: file (audio file)
```

### Start Transcription
```
POST /api/transcribe
Content-Type: application/json
Body: {
  "filename": "uploaded_filename",
  "model_size": "base",
  "enable_speaker_diarization": true,
  "language": "auto"
}
```

### Get Job Status
```
GET /api/job/{job_id}
```

### Download Result
```
GET /api/download/{filename}
```

### Health Check
```
GET /health
```

## 🔒 Security Features

- File type validation
- File size limits
- Rate limiting on API endpoints
- Secure file handling
- Input sanitization
- CORS configuration
- Security headers via Nginx

## 📈 Performance

- Concurrent job limiting (max 5 simultaneous)
- Automatic file cleanup (24-hour retention)
- Background processing
- Real-time progress updates
- Optimized for server deployment

## 🛠️ Troubleshooting

### Common Issues

1. **File Upload Fails**:
   - Check file size (max 500MB)
   - Verify file format is supported
   - Ensure uploads directory has write permissions

2. **Transcription Fails**:
   - Check available disk space
   - Verify audio file is not corrupted
   - Check logs for detailed error messages

3. **WebSocket Connection Issues**:
   - Ensure Nginx is properly configured
   - Check firewall settings
   - Verify WebSocket proxy settings

### Logs

- Application logs: `logs/web_app.log`
- Docker logs: `docker-compose logs -f`
- Nginx logs: Available in Docker container

## 🔄 Updates and Maintenance

### Updating the Application
```bash
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Monitoring
- Health check endpoint: `/health`
- Active jobs monitoring via API
- Log file monitoring
- Resource usage via Docker stats

## 📝 License

This project is part of the Voice Transcriber system. See the main project README for license information.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs
3. Create an issue in the repository
4. Check the main project documentation
