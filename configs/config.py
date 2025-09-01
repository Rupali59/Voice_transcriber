"""
Configuration file for Voice Transcriber
"""

import os
from pathlib import Path

# Default settings
DEFAULT_MODEL_SIZE = "base"  # Options: tiny, base, small, medium, large
DEFAULT_OUTPUT_DIR = Path.home() / "Documents" / "Voice_Memo_Transcriptions"

# Audio processing settings
AUDIO_SETTINGS = {
    "min_silence_len": 1000,  # Minimum silence length in milliseconds
    "silence_thresh": -40,     # Silence threshold in dB
    "preferred_format": "wav"  # Preferred format for conversion
}

# Supported audio formats
SUPPORTED_FORMATS = [
    '.mp3', '.m4a', '.wav', '.aac', '.flac', '.ogg', '.wma'
]

# Voice memo search locations (relative to user home directory)
VOICE_MEMO_LOCATIONS = [
    # Apple Voice Memos - Primary locations
    "Library/Application Support/com.apple.VoiceMemos/Recordings",
    "Library/Application Support/com.apple.VoiceMemos/Documents",
    "Library/Application Support/com.apple.VoiceMemos/Data",
    
    # iCloud Voice Memos
    "Library/Mobile Documents/com~apple~VoiceMemos",
    "Library/Mobile Documents/com~apple~VoiceMemos/Documents",
    "Library/Mobile Documents/com~apple~CloudDocs/Voice Memos",
    "iCloud Drive/VoiceMemos",
    "iCloud Drive/Voice Memos",
    
    # Music and Media folders
    "Music/Voice Memos",
    "Music/Recordings",
    "Music/Audio Recordings",
    
    # Documents and Downloads
    "Documents/Voice Recordings",
    "Documents/Audio Recordings",
    "Documents/Recordings",
    "Downloads/Voice Memos",
    "Downloads/Audio Recordings",
    "Downloads/Recordings",
    
    # Desktop
    "Desktop/Voice Memos",
    "Desktop/Recordings",
    
    # WhatsApp and Telegram voice messages
    "Library/Group Containers/group.net.whatsapp.WhatsApp.shared/Media",
    "Library/Group Containers/group.net.whatsapp.WhatsAppSMB.shared/Media",
    "Library/Group Containers/*/Telegram/Media",
    
    # General search locations
    "Music",
    "Documents",
    "Downloads",
    "Desktop"
]

# Environment-specific paths (macOS specific)
MACOS_VOICE_MEMO_PATHS = [
    "~/Library/Application Support/com.apple.VoiceMemos",
    "~/Library/Mobile Documents/com~apple~VoiceMemos",
    "~/Library/Mobile Documents/com~apple~CloudDocs/Voice Memos",
    "~/Music/Voice Memos",
    "~/iCloud Drive/VoiceMemos",
    "~/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/Media",
    "~/Library/Group Containers/group.net.whatsapp.WhatsAppSMB.shared/Media"
]

# File patterns to identify voice memos
VOICE_MEMO_PATTERNS = [
    "*Voice Memo*",
    "*Recording*",
    "*Memo*",
    "*Voice*",
    "*Audio*"
]

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(levelname)s - %(message)s",
    "file": None  # Set to a file path if you want to log to file
}

# Whisper model settings
WHISPER_SETTINGS = {
    "device": "auto",  # auto, cpu, or cuda
    "download_root": None,  # Directory to store downloaded models
    "in_memory": False  # Whether to load model into memory
}

# Processing settings
PROCESSING_SETTINGS = {
    "enable_speaker_diarization": True,
    "create_analysis_reports": True,
    "overwrite_existing": False,
    "batch_size": 5  # Number of files to process simultaneously
}
