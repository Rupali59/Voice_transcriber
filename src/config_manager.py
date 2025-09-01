"""
Configuration Manager for Voice Transcriber
Handles environment-based configuration with defaults and validation
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

@dataclass
class TranscriptionConfig:
    """Configuration for transcription processing"""
    whisper_model_size: str = "medium"
    enable_speaker_diarization: bool = True
    enable_language_detection: bool = True
    enable_partial_transcription: bool = True
    audio_chunk_size: int = 30
    audio_overlap: int = 5
    silence_threshold: int = -40
    sample_rate: int = 16000

@dataclass
class InputConfig:
    """Configuration for input file monitoring"""
    watch_dirs: List[str] = None
    file_patterns: List[str] = None
    poll_interval: int = 30
    
    def __post_init__(self):
        if self.watch_dirs is None:
            self.watch_dirs = [
                str(Path.home() / "Music" / "Voice Memos"),
                str(Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "Voice Memos"),
                str(Path.home() / "Documents" / "Recordings")
            ]
        if self.file_patterns is None:
            self.file_patterns = ["*.m4a", "*.mp3", "*.wav", "*.aac", "*.flac"]

@dataclass
class OutputConfig:
    """Configuration for output generation"""
    base_dir: str = None
    format: str = "markdown"
    include_metadata: bool = True
    include_speakers: bool = True
    
    def __post_init__(self):
        if self.base_dir is None:
            self.base_dir = str(Path.home() / "Documents" / "Voice_Transcriptions")

@dataclass
class PerformanceConfig:
    """Configuration for performance optimization"""
    batch_size: int = 3
    max_concurrent_processes: int = 2
    processing_queue_size: int = 100
    retry_attempts: int = 3
    retry_delay: int = 60

@dataclass
class BackgroundConfig:
    """Configuration for background processing"""
    enable_background_processing: bool = True
    enable_progress_bars: bool = True

@dataclass
class LoggingConfig:
    """Configuration for logging"""
    level: str = "INFO"
    file: str = None
    
    def __post_init__(self):
        if self.file is None:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            self.file = str(log_dir / "transcriber.log")

class ConfigManager:
    """Manages all configuration for the voice transcriber"""
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self.transcription = TranscriptionConfig()
        self.input = InputConfig()
        self.output = OutputConfig()
        self.performance = PerformanceConfig()
        self.background = BackgroundConfig()
        self.logging = LoggingConfig()
        
        self._load_environment()
        self._setup_logging()
    
    def _load_environment(self):
        """Load configuration from environment file and variables"""
        # Load .env file if it exists
        if os.path.exists(self.env_file):
            self._load_env_file()
        
        # Override with environment variables
        self._load_env_vars()
        
        # Validate configuration
        self._validate_config()
    
    def _load_env_file(self):
        """Load configuration from .env file"""
        try:
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
        except Exception as e:
            print(f"Warning: Could not load .env file: {e}")
    
    def _load_env_vars(self):
        """Load configuration from environment variables"""
        # Transcription config
        self.transcription.whisper_model_size = os.getenv(
            'WHISPER_MODEL_SIZE', self.transcription.whisper_model_size
        )
        self.transcription.enable_speaker_diarization = self._parse_bool(
            os.getenv('ENABLE_SPEAKER_DIARIZATION', 'true')
        )
        self.transcription.enable_language_detection = self._parse_bool(
            os.getenv('ENABLE_LANGUAGE_DETECTION', 'true')
        )
        self.transcription.enable_partial_transcription = self._parse_bool(
            os.getenv('ENABLE_PARTIAL_TRANSCRIPTION', 'true')
        )
        self.transcription.audio_chunk_size = int(os.getenv(
            'AUDIO_CHUNK_SIZE', self.transcription.audio_chunk_size
        ))
        self.transcription.audio_overlap = int(os.getenv(
            'AUDIO_OVERLAP', self.transcription.audio_overlap
        ))
        self.transcription.silence_threshold = int(os.getenv(
            'SILENCE_THRESHOLD', self.transcription.silence_threshold
        ))
        self.transcription.sample_rate = int(os.getenv(
            'SAMPLE_RATE', self.transcription.sample_rate
        ))
        
        # Input config
        input_dirs = os.getenv('INPUT_WATCH_DIRS')
        if input_dirs:
            self.input.watch_dirs = [d.strip() for d in input_dirs.split(',')]
        
        file_patterns = os.getenv('INPUT_FILE_PATTERNS')
        if file_patterns:
            self.input.file_patterns = [p.strip() for p in file_patterns.split(',')]
        
        self.input.poll_interval = int(os.getenv(
            'INPUT_POLL_INTERVAL', self.input.poll_interval
        ))
        
        # Output config
        output_dir = os.getenv('OUTPUT_BASE_DIR')
        if output_dir:
            self.output.base_dir = output_dir
        
        self.output.format = os.getenv('OUTPUT_FORMAT', self.output.format)
        self.output.include_metadata = self._parse_bool(
            os.getenv('OUTPUT_INCLUDE_METADATA', 'true')
        )
        self.output.include_speakers = self._parse_bool(
            os.getenv('OUTPUT_INCLUDE_SPEAKERS', 'true')
        )
        
        # Performance config
        self.performance.batch_size = int(os.getenv(
            'BATCH_SIZE', self.performance.batch_size
        ))
        self.performance.max_concurrent_processes = int(os.getenv(
            'MAX_CONCURRENT_PROCESSES', self.performance.max_concurrent_processes
        ))
        self.performance.processing_queue_size = int(os.getenv(
            'PROCESSING_QUEUE_SIZE', self.performance.processing_queue_size
        ))
        self.performance.retry_attempts = int(os.getenv(
            'RETRY_ATTEMPTS', self.performance.retry_attempts
        ))
        self.performance.retry_delay = int(os.getenv(
            'RETRY_DELAY', self.performance.retry_delay
        ))
        
        # Background config
        self.background.enable_background_processing = self._parse_bool(
            os.getenv('ENABLE_BACKGROUND_PROCESSING', 'true')
        )
        self.background.enable_progress_bars = self._parse_bool(
            os.getenv('ENABLE_PROGRESS_BARS', 'true')
        )
        
        # Logging config
        self.logging.level = os.getenv('LOG_LEVEL', self.logging.level)
        log_file = os.getenv('LOG_FILE')
        if log_file:
            self.logging.file = log_file
    
    def _parse_bool(self, value: str) -> bool:
        """Parse boolean string values"""
        if isinstance(value, bool):
            return value
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def _validate_config(self):
        """Validate configuration values"""
        # Ensure output directory exists
        Path(self.output.base_dir).mkdir(parents=True, exist_ok=True)
        
        # Validate model size
        valid_models = ['tiny', 'base', 'small', 'medium', 'large']
        if self.transcription.whisper_model_size not in valid_models:
            print(f"Warning: Invalid model size '{self.transcription.whisper_model_size}', using 'base'")
            self.transcription.whisper_model_size = 'base'
        
        # Validate numeric values
        if self.transcription.audio_chunk_size < 10:
            self.transcription.audio_chunk_size = 10
        if self.transcription.audio_overlap < 0:
            self.transcription.audio_overlap = 0
        if self.performance.batch_size < 1:
            self.performance.batch_size = 1
        if self.performance.max_concurrent_processes < 1:
            self.performance.max_concurrent_processes = 1
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.logging.level.upper(), logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_file_path = Path(self.logging.file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file_path),
                logging.StreamHandler()
            ]
        )
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration"""
        return {
            'transcription': {
                'model_size': self.transcription.whisper_model_size,
                'speaker_diarization': self.transcription.enable_speaker_diarization,
                'language_detection': self.transcription.enable_language_detection,
                'partial_transcription': self.transcription.enable_partial_transcription
            },
            'input': {
                'watch_dirs': self.input.watch_dirs,
                'file_patterns': self.input.file_patterns,
                'poll_interval': self.input.poll_interval
            },
            'output': {
                'base_dir': self.output.base_dir,
                'format': self.output.format,
                'include_metadata': self.output.include_metadata,
                'include_speakers': self.output.include_speakers
            },
            'performance': {
                'batch_size': self.performance.batch_size,
                'max_concurrent_processes': self.performance.max_concurrent_processes,
                'retry_attempts': self.performance.retry_attempts
            },
            'background': {
                'enable_background_processing': self.background.enable_background_processing,
                'enable_progress_bars': self.background.enable_progress_bars
            }
        }
    
    def print_config(self):
        """Print current configuration"""
        print("🔧 Voice Transcriber Configuration")
        print("=" * 50)
        
        summary = self.get_config_summary()
        for section, config in summary.items():
            print(f"\n📁 {section.title()}:")
            for key, value in config.items():
                if isinstance(value, list):
                    print(f"   {key}: {', '.join(value)}")
                else:
                    print(f"   {key}: {value}")
        
        print(f"\n📝 Log file: {self.logging.file}")
        print(f"📊 Log level: {self.logging.level}")
