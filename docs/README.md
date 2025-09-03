# Voice Transcriber Documentation

A comprehensive yet minimal documentation system for the Voice Transcriber project.

## 🚀 Quick Start

### Installation & Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app_main.py

# Access at http://localhost:5001
```

### Docker Deployment
```bash
# One-command deployment
./deploy.sh

# Or manually
docker-compose up -d
```

## 📚 Documentation Structure

### Core Documentation
- **[User Guide](USER_GUIDE.md)** - Complete user manual and features
- **[API Reference](API_REFERENCE.md)** - Complete API documentation
- **[Deployment Guide](DEPLOYMENT.md)** - Deployment and configuration
- **[Technical Reference](TECHNICAL_REFERENCE.md)** - Architecture and implementation

### Quick References
- **[Performance Guide](PERFORMANCE_GUIDE.md)** - Optimization and performance tuning
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

## 🎯 For Different Users

### 👤 **End Users**
1. Start with **[User Guide](USER_GUIDE.md)** for complete usage instructions
2. Check **[Troubleshooting](TROUBLESHOOTING.md)** if you encounter issues

### 👨‍💻 **Developers**
1. Review **[Technical Reference](TECHNICAL_REFERENCE.md)** for architecture
2. Use **[API Reference](API_REFERENCE.md)** for integration
3. Check **[Performance Guide](PERFORMANCE_GUIDE.md)** for optimization

### 🚀 **DevOps/Deployment**
1. Start with **[Deployment Guide](DEPLOYMENT.md)**
2. Review **[Performance Guide](PERFORMANCE_GUIDE.md)** for production tuning

## 🏗️ Project Architecture

```
Voice Transcriber/
├── app/                    # Flask web application
│   ├── routes/            # API endpoints and web routes
│   ├── services/          # Business logic and services
│   ├── models/            # Data models
│   └── static/            # Web assets (CSS, JS, images)
├── src/                   # Core transcription logic
├── tests/                 # Test suite
├── docs/                  # Documentation (this folder)
└── requirements.txt       # Python dependencies
```

## 🔧 Key Features

- **Web Interface**: Modern, responsive web UI
- **Real-time Updates**: WebSocket-based progress tracking
- **Multiple Models**: Support for different Whisper model sizes
- **Speaker Diarization**: Automatic speaker identification
- **File Management**: Secure file upload and processing
- **API Access**: RESTful API for integration
- **Docker Support**: Easy deployment with Docker

## 📊 System Requirements

- **Python**: 3.9+
- **Memory**: 4GB+ RAM (8GB+ recommended for large models)
- **Storage**: 2GB+ free space
- **OS**: Linux, macOS, Windows (Docker recommended)

## 🆘 Getting Help

1. **Check the documentation** - Most questions are answered here
2. **Review logs** - Application logs contain detailed information
3. **Check issues** - Look for similar problems in the issue tracker
4. **Create an issue** - Report bugs or ask questions

## 📝 Contributing

This project follows these principles:
- **Minimal yet comprehensive** documentation
- **Clear and concise** explanations
- **Practical examples** and code snippets
- **Up-to-date** with the codebase

---

**Built with ❤️ by Tathya** - Making voice transcription accessible and efficient.