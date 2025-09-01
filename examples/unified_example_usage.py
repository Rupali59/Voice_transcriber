#!/usr/bin/env python3
"""
Example: How to use the Unified Voice Transcriber programmatically
"""

import sys
import os
from pathlib import Path

# Add src directory to path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent / "src"))

from unified_voice_transcriber import UnifiedVoiceTranscriber
from unified_voice_memos_processor import UnifiedVoiceMemosProcessor

def example_single_file():
    """Example: Transcribe a single audio file"""
    print("🎤 Example: Transcribe a single file")
    
    # Create transcriber
    transcriber = UnifiedVoiceTranscriber(
        model_size="base",  # Options: tiny, base, small, medium, large
        enable_speaker_diarization=True
    )
    
    # Example file path (replace with your actual file)
    audio_file = "~/Downloads/sample_audio.mp3"
    
    try:
        # Transcribe the file
        result = transcriber.transcribe(audio_file)
        print(f"✅ Transcription completed!")
        print(f"📁 Output saved to: {result['output_file']}")
        print(f"🌍 Language detected: {result['metadata']['Language Code']}")
        print(f"👥 Speakers detected: {result['metadata']['Speakers Detected']}")
        
    except FileNotFoundError:
        print(f"❌ File not found: {audio_file}")
        print("💡 Please replace with a real audio file path")
    except Exception as e:
        print(f"❌ Error: {e}")

def example_process_all_memos():
    """Example: Process all voice memos found on the system"""
    print("\n🎤 Example: Process all voice memos")
    
    # Create processor
    processor = UnifiedVoiceMemosProcessor(
        model_size="base",
        enable_speaker_diarization=True
    )
    
    try:
        # Process all voice memos
        results = processor.process_all_voice_memos()
        print(f"✅ Processed {len(results)} voice memos!")
        
        # Show summary
        for result in results:
            print(f"📝 {result['file_name']}: {result['status']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def example_custom_locations():
    """Example: Process voice memos from custom locations"""
    print("\n🎤 Example: Custom voice memo locations")
    
    # Create processor
    processor = UnifiedVoiceMemosProcessor(
        model_size="base",
        enable_speaker_diarization=True
    )
    
    # Custom locations to search
    custom_locations = [
        "~/Desktop",
        "~/Downloads", 
        "~/Music"
    ]
    
    try:
        # Process from custom locations
        results = processor.process_voice_memos_from_locations(custom_locations)
        print(f"✅ Processed {len(results)} files from custom locations!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def example_with_analysis():
    """Example: Process with detailed analysis"""
    print("\n🎤 Example: Process with analysis")
    
    # Create processor
    processor = UnifiedVoiceMemosProcessor(
        model_size="base",
        enable_speaker_diarization=True
    )
    
    try:
        # Process with analysis
        results = processor.process_all_voice_memos(create_analysis=True)
        print(f"✅ Processed with analysis!")
        
        # Create summary report
        summary_file = processor.create_summary_report(results)
        print(f"📊 Summary report: {summary_file}")
        
        # Create language analysis
        language_file = processor.create_language_analysis(results)
        print(f"🌍 Language analysis: {language_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🎤 Unified Voice Transcriber - Examples")
    print("=" * 50)
    
    # Run examples
    example_single_file()
    example_process_all_memos()
    example_custom_locations()
    example_with_analysis()
    
    print("\n🎉 Examples completed!")
    print("💡 Check the output files to see the results")
    print("📚 See README.md for more usage options")
