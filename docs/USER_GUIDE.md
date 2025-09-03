# User Guide - Voice Transcriber

Complete guide to using the Voice Transcriber web application.

## 🎯 Overview

Voice Transcriber is a web-based application that converts audio files into text using advanced AI models. It supports multiple languages, speaker identification, and real-time progress tracking.

## 🚀 Getting Started

### 1. Access the Application
- Open your web browser
- Navigate to `http://localhost:5001` (or your deployed URL)
- You'll see the main interface

### 2. Upload an Audio File
- Click "Choose File" or drag and drop an audio file
- Supported formats: WAV, MP3, M4A, FLAC, OGG
- Maximum file size: 500MB

### 3. Configure Transcription Settings
- **Model Size**: Choose between Tiny, Base, Small, Medium, or Large
  - **Tiny**: Fastest, lowest accuracy
  - **Base**: Good balance (recommended)
  - **Small**: Better accuracy, slower
  - **Medium**: High accuracy, slower
  - **Large**: Best accuracy, slowest
- **Language**: Select language or use "Auto-detect"
- **Speaker Diarization**: Enable to identify different speakers

### 4. Start Transcription
- Click "Start Transcription"
- Watch real-time progress updates
- Download results when complete

## 🎛️ Interface Guide

### Main Dashboard
- **File Upload Area**: Drag and drop or click to select files
- **Settings Panel**: Configure transcription options
- **Progress Display**: Real-time status and progress
- **Results Section**: Download and view transcriptions

### Navigation
- **Home**: Main transcription interface
- **History**: View past transcriptions (if enabled)
- **Settings**: Application preferences

## 📊 Understanding Results

### Transcription Output
- **Text**: Full transcription in markdown format
- **Timestamps**: Time markers for each segment
- **Speakers**: Speaker identification (if enabled)
- **Language**: Detected language
- **Confidence**: Transcription confidence scores

### File Formats
- **Markdown (.md)**: Human-readable format with timestamps
- **JSON**: Machine-readable format with metadata
- **TXT**: Plain text format

## 🔧 Advanced Features

### Speaker Diarization
When enabled, the system identifies different speakers:
- **Speaker 1, Speaker 2, etc.**: Different people speaking
- **Timestamps**: When each speaker talks
- **Segments**: Individual speech segments

### Language Detection
- **Auto-detect**: Automatically identifies the language
- **Manual selection**: Choose from supported languages
- **Multi-language**: Handles mixed-language content

### Model Selection Guide
Choose the right model for your needs:

| Model | Speed | Accuracy | Use Case |
|-------|-------|----------|----------|
| Tiny | Very Fast | Basic | Quick drafts, testing |
| Base | Fast | Good | General use, balanced |
| Small | Medium | Better | Important content |
| Medium | Slow | High | Professional use |
| Large | Very Slow | Best | Critical accuracy needed |

## 📱 Mobile Usage

The web interface is mobile-responsive:
- **Touch-friendly**: Works on tablets and phones
- **Responsive design**: Adapts to screen size
- **File upload**: Supports mobile file selection

## 🔒 Privacy & Security

- **Local processing**: Audio files processed locally
- **No cloud upload**: Files stay on your server
- **Secure storage**: Temporary files are cleaned up
- **Access control**: Configure as needed

## 💡 Tips & Best Practices

### Audio Quality
- **Clear audio**: Use good quality recordings
- **Minimize background noise**: Better results with clean audio
- **Appropriate volume**: Not too loud or too quiet
- **Stable recording**: Avoid interruptions

### File Preparation
- **Supported formats**: Use WAV, MP3, or M4A for best results
- **File size**: Larger files take longer to process
- **Naming**: Use descriptive filenames

### Performance Optimization
- **Model selection**: Choose appropriate model size
- **Concurrent jobs**: Limit simultaneous transcriptions
- **System resources**: Ensure adequate RAM and CPU

## 🆘 Troubleshooting

### Common Issues

**File won't upload**
- Check file format is supported
- Verify file size is under 500MB
- Ensure stable internet connection

**Transcription fails**
- Check audio file isn't corrupted
- Verify sufficient disk space
- Try a different model size

**Slow performance**
- Use smaller model for faster processing
- Close other applications
- Check system resources

**Poor accuracy**
- Use higher quality audio
- Try a larger model
- Check language settings

### Getting Help
1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Review application logs
3. Try different settings
4. Contact support if issues persist

## 📚 Additional Resources

- **[API Reference](API_REFERENCE.md)**: For developers and integration
- **[Technical Reference](TECHNICAL_REFERENCE.md)**: Architecture and implementation
- **[Performance Guide](PERFORMANCE_GUIDE.md)**: Optimization tips
- **[Deployment Guide](DEPLOYMENT.md)**: Setup and configuration

---

**Need help?** Check the troubleshooting guide or create an issue for support.