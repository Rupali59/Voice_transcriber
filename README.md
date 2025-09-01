# 🎤 Production Voice Transcriber

A high-performance, configurable voice transcription system that can transcribe audio recordings in any language with high fidelity. Supports background processing, speaker diarization, and automatic language detection.

## ✨ Features

- **🌍 Multi-language Support**: Automatically detects and transcribes any language
- **🎭 Speaker Diarization**: Identifies multiple speakers in recordings
- **⚡ Background Processing**: Monitors directories for new audio files
- **🔧 Configurable**: Environment-based configuration with sensible defaults
- **📊 Performance Optimized**: Concurrent processing with configurable batch sizes
- **📝 Partial Transcription**: Captures partial results for long recordings
- **🔄 Retry Logic**: Automatic retry with configurable attempts
- **📈 Statistics**: Real-time processing statistics and monitoring

## 🚀 Quick Start

### 1. Setup
```bash
# Clone and setup
git clone <your-repo>
cd Voice_transcriber
./scripts/transcriber.sh setup
```

### 2. Configure
```bash
# Edit environment configuration
cp configs/env_template.txt .env
# Edit .env with your settings
```

### 3. Use
```bash
# Start background processing
python3 src/transcriber_cli.py --background

# Process single file
python3 src/transcriber_cli.py --file /path/to/audio.m4a

# Process directory
python3 src/transcriber_cli.py --dir /path/to/audio/files
```

## 📁 Project Structure

```
Voice_transcriber/
├── src/                          # Source code
│   ├── transcriber_cli.py       # Main CLI interface
│   ├── config_manager.py        # Configuration management
│   ├── background_processor.py  # Background processing
│   └── unified_voice_transcriber.py  # Core transcription
├── configs/                      # Configuration files
│   ├── requirements.txt         # Python dependencies
│   └── env_template.txt         # Environment template
├── scripts/                      # Management scripts
│   ├── transcriber.sh           # Main management script (orchestrates others)
│   ├── setup.sh                 # System setup and installation
│   ├── config.sh                # Configuration management
│   ├── find.sh                  # Voice memo discovery
│   ├── process.sh               # Background processing
│   ├── parallel.sh              # Parallel processing of multiple files
│   ├── file.sh                  # Single file processing
│   └── help.sh                  # Comprehensive help and documentation
├── docs/                         # Documentation
├── transcriptions/               # Output transcriptions
├── logs/                         # Log files
└── .env                          # Environment configuration
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `configs/env_template.txt`:

```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
WHISPER_MODEL_SIZE=medium

# Input Configuration
INPUT_WATCH_DIRS=/path/to/input1,/path/to/input2
INPUT_FILE_PATTERNS=*.m4a,*.mp3,*.wav,*.aac,*.flac
INPUT_POLL_INTERVAL=30

# Output Configuration
OUTPUT_BASE_DIR=/path/to/transcriptions
OUTPUT_FORMAT=markdown
OUTPUT_INCLUDE_METADATA=true
OUTPUT_INCLUDE_SPEAKERS=true

# Processing Configuration
ENABLE_SPEAKER_DIARIZATION=true
ENABLE_LANGUAGE_DETECTION=true
ENABLE_PARTIAL_TRANSCRIPTION=true
BATCH_SIZE=3
MAX_CONCURRENT_PROCESSES=2

# Performance Configuration
AUDIO_CHUNK_SIZE=30
AUDIO_OVERLAP=5
SILENCE_THRESHOLD=-40
SAMPLE_RATE=16000

# Background Processing
ENABLE_BACKGROUND_PROCESSING=true
PROCESSING_QUEUE_SIZE=100
RETRY_ATTEMPTS=3
RETRY_DELAY=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/transcriber.log
ENABLE_PROGRESS_BARS=true
```

## 🎯 Usage Examples

### Management Scripts

#### Main Script (Orchestrates All Functions)
```bash
# Setup the system
./scripts/transcriber.sh setup

# Show configuration
./scripts/transcriber.sh config

# Find voice memos
./scripts/transcriber.sh find

# Start background processing
./scripts/transcriber.sh process

# Process specific file
./scripts/transcriber.sh file /path/to/audio.m4a

# Process multiple files in parallel
./scripts/transcriber.sh parallel files *.m4a
./scripts/transcriber.sh parallel dir /path/to/audio/files

# Show quick status
./scripts/transcriber.sh quick

# Show detailed status
./scripts/transcriber.sh status

# Real-time monitoring
./scripts/transcriber.sh monitor

# Show help
./scripts/transcriber.sh help
```

#### Individual Scripts (Direct Access)
```bash
# Setup
./scripts/setup.sh

# Configuration
./scripts/config.sh

# Find voice memos
./scripts/find.sh

# Background processing
./scripts/process.sh start|stop|status|quick|monitor

# Parallel processing
./scripts/parallel.sh files file1.m4a file2.m4a
./scripts/parallel.sh dir /path/to/audio --concurrent 4 --monitor

# Single file processing
./scripts/file.sh /path/to/audio.m4a

# Comprehensive help
./scripts/help.sh
```

### Background Processing
```bash
# Start monitoring directories for new audio files
python3 src/transcriber_cli.py --background

# With custom configuration
python3 src/transcriber_cli.py --background --model large --output /custom/output
```

### Parallel Processing (New!)
```bash
# Process multiple files simultaneously
./scripts/transcriber.sh parallel files audio1.m4a audio2.m4a audio3.m4a

# Process all files in a directory with custom concurrency
./scripts/transcriber.sh parallel dir /path/to/audio --concurrent 6

# Process with real-time monitoring
./scripts/transcriber.sh parallel files *.m4a --monitor

# Direct CLI usage
python3 src/parallel_cli.py --files file1.m4a file2.m4a --concurrent 4 --monitor
```

**🚀 Benefits of Parallel Processing:**
- **2-4x faster** than sequential processing
- **Optimal resource utilization** across all CPU cores
- **Real-time monitoring** of progress and performance
- **Configurable concurrency** based on your system
- **Batch processing** for large numbers of files

### Single File Processing
```bash
# Process single file with default settings
python3 src/transcriber_cli.py --file /path/to/audio.m4a

# Process with custom model and no speaker detection
python3 src/transcriber_cli.py --file /path/to/audio.m4a --model large --no-speakers
```

### Directory Processing
```bash
# Process all audio files in directory
python3 src/transcriber_cli.py --dir /path/to/audio/files

# Process with custom output directory
python3 src/transcriber_cli.py --dir /path/to/audio/files --output /custom/output
```

### Configuration and Information
```bash
# Show current configuration
python3 src/transcriber_cli.py --config

# Show processing statistics (when background processing is running)
python3 src/transcriber_cli.py --stats

# Enable verbose logging
python3 src/transcriber_cli.py --background --verbose
```

## 🔧 Performance Tuning

### Model Size Selection
- **tiny**: ~39MB, fastest, lowest accuracy
- **base**: ~74MB, good balance, recommended
- **small**: ~244MB, better accuracy, slower
- **medium**: ~769MB, high accuracy, production ready
- **large**: ~1550MB, highest accuracy, slowest

### Concurrency Settings
```bash
# Increase concurrent processes for better performance
MAX_CONCURRENT_PROCESSES=4
BATCH_SIZE=5

# Adjust queue size for high-volume processing
PROCESSING_QUEUE_SIZE=200
```

### Audio Processing
```bash
# Larger chunks for better speaker detection
AUDIO_CHUNK_SIZE=45
AUDIO_OVERLAP=10

# More sensitive silence detection
SILENCE_THRESHOLD=-35
```

## 📊 Monitoring and Statistics

### Real-time Statistics
When running in background mode, statistics are available:
- Files processed successfully
- Files failed
- Current queue size
- Average processing time
- Total processing time

### Log Files
Logs are written to `logs/transcriber.log` with configurable levels:
- INFO: General processing information
- DEBUG: Detailed debugging information
- WARNING: Warning messages
- ERROR: Error messages

## 🚨 Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Grant full disk access to Terminal
   System Preferences → Security & Privacy → Privacy → Full Disk Access
   ```

2. **Audio File Not Found**
   ```bash
   # Check input directories in .env
   INPUT_WATCH_DIRS=/correct/path1,/correct/path2
   ```

3. **Transcription Quality**
   ```bash
   # Use larger model for better accuracy
   WHISPER_MODEL_SIZE=large
   ```

4. **Performance Issues**
   ```bash
   # Reduce concurrent processes
   MAX_CONCURRENT_PROCESSES=1
   BATCH_SIZE=1
   ```
   
   **💡 For detailed performance analysis, see `docs/TECHNICAL_DETAILS.md`**

### Debug Mode
```bash
# Enable verbose logging
python3 src/transcriber_cli.py --background --verbose

# Check configuration
python3 src/transcriber_cli.py --config
```

## 🔄 API Usage

### Programmatic Interface
```python
from src.config_manager import ConfigManager
from src.background_processor import BackgroundProcessor

# Load configuration
config = ConfigManager('.env')

# Start background processing
processor = BackgroundProcessor(config)
processor.start()

# Process existing files
processor.process_existing_files()

# Get statistics
stats = processor.get_stats()
print(stats)
```

## 📚 Documentation

- **Quick Start**: `docs/QUICK_START.md`
- **Technical Reference**: `docs/TECHNICAL_REFERENCE.md`
- **Technical Details**: `docs/TECHNICAL_DETAILS.md` - System architecture, CPU usage, and performance characteristics
- **Performance Reference**: `docs/PERFORMANCE_QUICK_REFERENCE.md` - Quick performance monitoring and troubleshooting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `logs/transcriber.log`
3. Open an issue with detailed information

---

**🎉 Ready to transcribe with production-grade quality and performance!**
