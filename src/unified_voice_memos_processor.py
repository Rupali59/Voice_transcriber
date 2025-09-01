#!/usr/bin/env python3
"""
Unified Voice Memos Processor - Multi-language with Speaker Diarization
Automatically finds and processes voice memos from common locations
"""

import os
import sys
import shutil
from pathlib import Path
from unified_voice_transcriber import UnifiedVoiceTranscriber
import argparse
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnifiedVoiceMemosProcessor:
    def __init__(self, model_size="base", enable_speaker_diarization=True):
        """
        Initialize the unified voice memos processor
        
        Args:
            model_size (str): Whisper model size
            enable_speaker_diarization (bool): Whether to enable speaker identification
        """
        self.transcriber = UnifiedVoiceTranscriber(
            model_size=model_size,
            enable_speaker_diarization=enable_speaker_diarization
        )
        self.voice_memo_locations = self._get_voice_memo_locations()
        
    def _get_voice_memo_locations(self):
        """Get common locations where voice memos might be stored"""
        home = Path.home()
        
        locations = [
            # macOS Voice Memos app location
            home / "Library" / "Application Support" / "com.apple.VoiceMemos" / "Recordings",
            
            # Common recording directories
            home / "Music" / "Voice Memos",
            home / "Documents" / "Voice Recordings",
            home / "Downloads" / "Voice Memos",
            home / "Desktop" / "Voice Memos",
            
            # iOS Voice Memos (if synced via iCloud)
            home / "Library" / "Mobile Documents" / "com~apple~VoiceMemos",
            
            # Other common audio directories
            home / "Music",
            home / "Documents",
            home / "Downloads",
            
            # WhatsApp voice messages (if exported)
            home / "Downloads" / "WhatsApp Voice Messages",
            home / "Documents" / "WhatsApp Audio",
            
            # Telegram voice messages (if exported)
            home / "Downloads" / "Telegram Voice Messages",
            home / "Documents" / "Telegram Audio",
            
            # Additional common locations
            home / "Desktop" / "Recordings",
            home / "Pictures" / "Voice Recordings",
            home / "Movies" / "Voice Recordings"
        ]
        
        # Filter to only existing directories
        existing_locations = [loc for loc in locations if loc.exists()]
        return existing_locations
    
    def find_voice_memos(self, custom_paths=None, recursive=True):
        """
        Find voice memo files in common locations
        
        Args:
            custom_paths (list): Additional paths to search
            recursive (bool): Whether to search recursively
            
        Returns:
            list: List of found audio files
        """
        audio_files = []
        search_paths = self.voice_memo_locations.copy()
        
        if custom_paths:
            search_paths.extend([Path(p) for p in custom_paths if Path(p).exists()])
        
        supported_formats = self.transcriber.supported_formats
        
        for search_path in search_paths:
            logger.info(f"Searching in: {search_path}")
            
            try:
                if recursive:
                    for ext in supported_formats:
                        files = list(search_path.rglob(f"*{ext}"))
                        audio_files.extend(files)
                else:
                    for ext in supported_formats:
                        files = list(search_path.glob(f"*{ext}"))
                        audio_files.extend(files)
                        
            except PermissionError:
                logger.warning(f"Permission denied accessing: {search_path}")
            except Exception as e:
                logger.warning(f"Error searching {search_path}: {e}")
        
        # Remove duplicates and sort by modification time
        unique_files = list(set(audio_files))
        unique_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return unique_files
    
    def process_voice_memos(self, output_dir=None, custom_paths=None, recursive=True):
        """
        Process all found voice memos with unified language support
        
        Args:
            output_dir (str): Output directory for transcriptions
            custom_paths (list): Additional paths to search
            recursive (bool): Whether to search recursively
            
        Returns:
            dict: Processing results
        """
        # Find voice memos
        audio_files = self.find_voice_memos(custom_paths, recursive)
        
        if not audio_files:
            logger.info("No voice memo files found.")
            return {"processed": 0, "errors": 0, "files": []}
        
        logger.info(f"Found {len(audio_files)} voice memo files")
        
        # Set output directory
        if not output_dir:
            output_dir = Path.home() / "Documents" / "Voice_Memo_Transcriptions"
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Process each file
        results = {
            "processed": 0,
            "errors": 0,
            "files": []
        }
        
        for audio_file in audio_files:
            try:
                logger.info(f"Processing: {audio_file.name}")
                
                # Create a subdirectory for this file's transcription
                file_output_dir = output_dir / audio_file.stem
                os.makedirs(file_output_dir, exist_ok=True)
                
                # Process the voice memo
                output_file = self.transcriber.process_voice_memo(
                    str(audio_file), 
                    str(file_output_dir)
                )
                
                results["processed"] += 1
                results["files"].append({
                    "input": str(audio_file),
                    "output": output_file,
                    "status": "success"
                })
                
                logger.info(f"✓ Successfully processed: {audio_file.name}")
                
            except Exception as e:
                logger.error(f"✗ Error processing {audio_file.name}: {e}")
                results["errors"] += 1
                results["files"].append({
                    "input": str(audio_file),
                    "output": None,
                    "status": "error",
                    "error": str(e)
                })
        
        return results
    
    def create_summary_report(self, results, output_dir):
        """
        Create a summary report of all processed voice memos
        
        Args:
            results (dict): Processing results
            output_dir (str): Output directory
        """
        try:
            report_path = Path(output_dir) / "transcription_summary.md"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("# Voice Memo Transcription Summary\n")
                f.write("*Multi-language transcription summary*\n\n")
                
                f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write(f"**Total files found:** {len(results['files'])}\n")
                f.write(f"**Successfully processed:** {results['processed']}\n")
                f.write(f"**Errors:** {results['errors']}\n\n")
                
                f.write("## File Details / फ़ाइल विवरण\n\n")
                f.write("| File | Status | Output |\n")
                f.write("|------|--------|--------|\n")
                
                for file_info in results["files"]:
                    filename = Path(file_info["input"]).name
                    status = file_info["status"]
                    output = file_info["output"] if file_info["output"] else "N/A"
                    
                    f.write(f"| {filename} | {status} | {output} |\n")
                
                if results["errors"] > 0:
                    f.write("\n## Error Details / त्रुटि विवरण\n\n")
                    for file_info in results["files"]:
                        if file_info["status"] == "error":
                            filename = Path(file_info["input"]).name
                            error = file_info.get("error", "Unknown error")
                            f.write(f"**{filename}**: {error}\n")
                
                # Add unified features information
                f.write("\n## Features / विशेषताएं\n\n")
                f.write("- **Multi-language Support**: English, Hindi, Hinglish, and more\n")
                f.write("- **Automatic Language Detection**: No need to specify language\n")
                f.write("- **Speaker Diarization**: Automatic speaker identification\n")
                f.write("- **Bilingual Output**: Hindi and English text in markdown\n")
                f.write("- **Timestamped Segments**: Easy navigation through conversation\n")
                f.write("- **Speaker Summary**: List of all detected speakers\n")
                f.write("- **Smart Search**: Finds voice memos from common locations\n")
            
            logger.info(f"Summary report created: {report_path}")
            
        except Exception as e:
            logger.error(f"Error creating summary report: {e}")
    
    def create_language_analysis(self, results, output_dir):
        """
        Create a detailed language analysis report
        
        Args:
            results (dict): Processing results
            output_dir (str): Output directory
        """
        try:
            analysis_path = Path(output_dir) / "language_analysis.md"
            
            with open(analysis_path, 'w', encoding='utf-8') as f:
                f.write("# Language Analysis Report\n")
                f.write("*भाषा विश्लेषण रिपोर्ट*\n\n")
                
                f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Analyze successful transcriptions for language information
                successful_files = [f for f in results["files"] if f["status"] == "success"]
                
                if not successful_files:
                    f.write("No successful transcriptions to analyze.\n")
                    return
                
                f.write(f"**Files analyzed:** {len(successful_files)}\n\n")
                
                # Group by language
                language_counts = {}
                total_speakers = 0
                
                for file_info in successful_files:
                    try:
                        # Read the transcription file to get language info
                        output_path = Path(file_info["output"])
                        if output_path.exists():
                            with open(output_path, 'r', encoding='utf-8') as tf:
                                content = tf.read()
                                
                                # Extract language information
                                language = "Unknown"
                                if "Language:" in content:
                                    for line in content.split('\n'):
                                        if "Language:" in line:
                                            language = line.split("Language:")[1].strip()
                                            break
                                
                                # Count speakers
                                speakers = set()
                                for line in content.split('\n'):
                                    if '|' in line and 'Speaker' in line:
                                        parts = line.split('|')
                                        if len(parts) >= 3:
                                            speaker = parts[2].strip()
                                            if speaker and speaker != 'Speaker':
                                                speakers.add(speaker)
                                
                                speaker_count = len(speakers)
                                total_speakers += speaker_count
                                
                                # Update language counts
                                if language not in language_counts:
                                    language_counts[language] = {"count": 0, "speakers": 0}
                                language_counts[language]["count"] += 1
                                language_counts[language]["speakers"] += speaker_count
                                
                    except Exception as e:
                        logger.warning(f"Could not analyze {file_info['input']}: {e}")
                
                # Write language statistics
                f.write("## Language Statistics / भाषा आंकड़े\n\n")
                f.write("| Language | Files | Speakers | Avg Speakers/File |\n")
                f.write("|----------|-------|----------|-------------------|\n")
                
                for language, stats in language_counts.items():
                    avg_speakers = stats["speakers"] / stats["count"]
                    f.write(f"| {language} | {stats['count']} | {stats['speakers']} | {avg_speakers:.1f} |\n")
                
                f.write(f"\n**Total unique conversations:** {len(successful_files)}\n")
                f.write(f"**Average speakers per file:** {total_speakers / len(successful_files):.1f}\n")
                
                # Language-specific insights
                f.write("\n## Language Insights / भाषा अंतर्दृष्टि\n\n")
                
                if "Hindi" in language_counts or "हिंदी" in language_counts:
                    f.write("- **Hindi Content**: Found Hindi/Hinglish voice memos\n")
                    f.write("- **Bilingual Support**: Mixed language content handled\n")
                
                if "English" in language_counts:
                    f.write("- **English Content**: English voice memos processed\n")
                
                # Recommendations
                f.write("\n## Recommendations / सिफारिशें\n\n")
                f.write("- **Multi-language**: Tool automatically detects and handles different languages\n")
                f.write("- **Speaker Diarization**: Works with any language for speaker identification\n")
                f.write("- **Quality**: Use larger models for better accuracy in all languages\n")
            
            logger.info(f"Language analysis created: {analysis_path}")
            
        except Exception as e:
            logger.error(f"Error creating language analysis: {e}")

def main():
    parser = argparse.ArgumentParser(description="Process voice memos with unified multi-language support and speaker diarization")
    parser.add_argument("-o", "--output", help="Output directory for transcriptions")
    parser.add_argument("-m", "--model", default="base", 
                       choices=["tiny", "base", "small", "medium", "large"],
                       help="Whisper model size (default: base)")
    parser.add_argument("-p", "--paths", nargs="+", 
                       help="Additional paths to search for voice memos")
    parser.add_argument("--no-recursive", action="store_true", 
                       help="Disable recursive search")
    parser.add_argument("--no-speaker-diarization", action="store_true",
                       help="Disable speaker diarization")
    parser.add_argument("--list-locations", action="store_true",
                       help="List common voice memo locations and exit")
    parser.add_argument("--create-analysis", action="store_true",
                       help="Create detailed language and speaker analysis reports")
    
    args = parser.parse_args()
    
    try:
        processor = UnifiedVoiceMemosProcessor(
            model_size=args.model,
            enable_speaker_diarization=not args.no_speaker_diarization
        )
        
        if args.list_locations:
            print("Common voice memo locations:")
            for i, location in enumerate(processor.voice_memo_locations, 1):
                print(f"{i}. {location}")
            return
        
        # Process voice memos
        results = processor.process_voice_memos(
            output_dir=args.output,
            custom_paths=args.paths,
            recursive=not args.no_recursive
        )
        
        # Create summary report
        if results["processed"] > 0 or results["errors"] > 0:
            output_dir = args.output or Path.home() / "Documents" / "Voice_Memo_Transcriptions"
            processor.create_summary_report(results, output_dir)
            
            # Create analysis reports if requested
            if args.create_analysis:
                processor.create_language_analysis(results, output_dir)
        
        # Print summary
        print(f"\n{'='*60}")
        print("UNIFIED VOICE MEMO PROCESSING SUMMARY")
        print("एकीकृत वॉइस मेमो प्रोसेसिंग सारांश")
        print(f"{'='*60}")
        print(f"Total files found: {len(results['files'])}")
        print(f"Successfully processed: {results['processed']}")
        print(f"Errors: {results['errors']}")
        
        if results["processed"] > 0:
            print(f"\nTranscriptions saved to: {output_dir}")
            print("A summary report has been created: transcription_summary.md")
            
            if args.create_analysis:
                print("A language analysis report has been created: language_analysis.md")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
