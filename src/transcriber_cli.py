#!/usr/bin/env python3
"""
Command Line Interface for Voice Transcriber
Supports parameters, environment configuration, and background processing
"""

import argparse
import sys
import signal
import time
from pathlib import Path
from typing import List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import ConfigManager
from background_processor import BackgroundProcessor
from unified_voice_transcriber import UnifiedVoiceTranscriber

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully"""
    print("\n🛑 Received interrupt signal, shutting down gracefully...")
    if hasattr(signal_handler, 'processor') and signal_handler.processor:
        signal_handler.processor.stop()
    sys.exit(0)

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Voice Transcriber - Transcribe audio files with high accuracy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start background processing
  python3 transcriber_cli.py --background
  
  # Process specific file
  python3 transcriber_cli.py --file /path/to/audio.m4a
  
  # Process directory
  python3 transcriber_cli.py --dir /path/to/audio/files
  
  # Show configuration
  python3 transcriber_cli.py --config
  
  # Show statistics
  python3 transcriber_cli.py --stats
        """
    )
    
    # Operation modes
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--background', '-b',
        action='store_true',
        help='Start background processing (monitor directories)'
    )
    mode_group.add_argument(
        '--file', '-f',
        type=str,
        help='Process single audio file'
    )
    mode_group.add_argument(
        '--dir', '-d',
        type=str,
        help='Process all audio files in directory'
    )
    
    # Configuration options
    parser.add_argument(
        '--env', '-e',
        type=str,
        default='.env',
        help='Environment configuration file (default: .env)'
    )
    parser.add_argument(
        '--model', '-m',
        type=str,
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        help='Override Whisper model size'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Override output directory'
    )
    parser.add_argument(
        '--no-speakers',
        action='store_true',
        help='Disable speaker diarization'
    )
    parser.add_argument(
        '--no-language-detection',
        action='store_true',
        help='Disable automatic language detection'
    )
    
    # Information options
    parser.add_argument(
        '--config', '-c',
        action='store_true',
        help='Show current configuration'
    )
    parser.add_argument(
        '--stats', '-s',
        action='store_true',
        help='Show processing statistics'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser

def process_single_file(file_path: str, config: ConfigManager, args: argparse.Namespace):
    """Process a single audio file"""
    print(f"🎤 Processing single file: {file_path}")
    
    # Override config if specified
    if args.model:
        config.transcription.whisper_model_size = args.model
    if args.output:
        config.output.base_dir = args.output
    if args.no_speakers:
        config.transcription.enable_speaker_diarization = False
    if args.no_language_detection:
        config.transcription.enable_language_detection = False
    
    # Initialize transcriber
    transcriber = UnifiedVoiceTranscriber(
        model_size=config.transcription.whisper_model_size,
        enable_speaker_diarization=config.transcription.enable_speaker_diarization
    )
    
    try:
        # Process file
        result = transcriber.transcribe_audio(file_path)
        
        if result:
            print("✅ Transcription completed successfully!")
            print(f"   Language: {result.get('language', 'Unknown')}")
            print(f"   Duration: {result.get('duration', 'Unknown')}")
            print(f"   Text length: {len(result.get('text', ''))} characters")
            
            # Save transcription
            output_path = Path(config.output.base_dir) / f"{Path(file_path).stem}_transcription.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# {Path(file_path).stem} - Transcription\n\n")
                f.write(f"**File:** {Path(file_path).name}\n")
                f.write(f"**Language:** {result.get('language', 'Unknown')}\n")
                f.write(f"**Duration:** {result.get('duration', 'Unknown')}\n\n")
                f.write("## Transcription\n\n")
                f.write(result.get('text', 'No transcription available'))
                
                if result.get('speaker_segments'):
                    f.write("\n\n## Speaker Analysis\n\n")
                    for i, segment in enumerate(result.get('speaker_segments', [])):
                        f.write(f"**Speaker {segment.get('speaker', i)}** "
                               f"({segment.get('start_time', 'Unknown')} - "
                               f"{segment.get('end_time', 'Unknown')})\n")
                        f.write(f"{segment.get('text', '')}\n\n")
            
            print(f"📝 Transcription saved to: {output_path}")
        else:
            print("❌ Transcription failed")
            return 1
            
    except Exception as e:
        print(f"❌ Error processing file: {e}")
        return 1
    
    return 0

def process_directory(dir_path: str, config: ConfigManager, args: argparse.Namespace):
    """Process all audio files in a directory"""
    print(f"📁 Processing directory: {dir_path}")
    
    # Override config if specified
    if args.model:
        config.transcription.whisper_model_size = args.model
    if args.output:
        config.output.base_dir = args.output
    if args.no_speakers:
        config.transcription.enable_speaker_diarization = False
    if args.no_language_detection:
        config.transcription.enable_language_detection = False
    
    # Initialize transcriber
    transcriber = UnifiedVoiceTranscriber(
        model_size=config.transcription.whisper_model_size,
        enable_speaker_diarization=config.transcription.enable_speaker_diarization
    )
    
    # Find audio files
    audio_files = []
    for pattern in config.input.file_patterns:
        audio_files.extend(Path(dir_path).rglob(pattern))
    
    if not audio_files:
        print("❌ No audio files found in directory")
        return 1
    
    print(f"🎵 Found {len(audio_files)} audio files")
    
    # Process files
    success_count = 0
    for i, file_path in enumerate(audio_files, 1):
        print(f"\n[{i}/{len(audio_files)}] Processing: {file_path.name}")
        
        try:
            result = transcriber.transcribe_audio(str(file_path))
            
            if result:
                # Save transcription
                output_path = Path(config.output.base_dir) / f"{file_path.stem}_transcription.md"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {file_path.stem} - Transcription\n\n")
                    f.write(f"**File:** {file_path.name}\n")
                    f.write(f"**Language:** {result.get('language', 'Unknown')}\n")
                    f.write(f"**Duration:** {result.get('duration', 'Unknown')}\n\n")
                    f.write("## Transcription\n\n")
                    f.write(result.get('text', 'No transcription available'))
                
                print(f"✅ Saved: {output_path}")
                success_count += 1
            else:
                print(f"❌ Failed: {file_path.name}")
                
        except Exception as e:
            print(f"❌ Error: {file_path.name} - {e}")
    
    print(f"\n📊 Processing complete: {success_count}/{len(audio_files)} successful")
    return 0 if success_count == len(audio_files) else 1

def start_background_processing(config: ConfigManager, args: argparse.Namespace):
    """Start background processing mode"""
    print("🚀 Starting background processing...")
    
    # Override config if specified
    if args.model:
        config.transcription.whisper_model_size = args.model
    if args.output:
        config.output.base_dir = args.output
    if args.no_speakers:
        config.transcription.enable_speaker_diarization = False
    if args.no_language_detection:
        config.transcription.enable_language_detection = False
    
    # Initialize background processor
    processor = BackgroundProcessor(config)
    
    # Store processor reference for signal handler
    signal_handler.processor = processor
    
    try:
        # Start processing
        processor.start()
        
        # Process existing files first
        processor.process_existing_files()
        
        print("✅ Background processing started")
        print("📁 Monitoring directories for new audio files...")
        print("💡 Press Ctrl+C to stop")
        
        # Keep running
        while processor.running:
            time.sleep(5)
            if args.verbose:
                processor.print_stats()
    
    except KeyboardInterrupt:
        print("\n🛑 Stopping background processing...")
    finally:
        processor.stop()
        print("✅ Background processing stopped")

def main():
    """Main entry point"""
    setup_signal_handlers()
    
    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = ConfigManager(args.env)
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return 1
    
    # Set log level
    if args.verbose:
        config.logging.level = "DEBUG"
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Show configuration if requested
    if args.config:
        config.print_config()
        return 0
    
    # Determine operation mode
    if args.background:
        start_background_processing(config, args)
    elif args.file:
        return process_single_file(args.file, config, args)
    elif args.dir:
        return process_directory(args.dir, config, args)
    elif args.stats:
        print("📊 No statistics available (background processing not running)")
        return 0
    else:
        # No operation specified, show help
        parser.print_help()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
