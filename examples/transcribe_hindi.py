#!/usr/bin/env python3
"""
Simple script to transcribe the Hindi voice memo using local Whisper
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from unified_voice_transcriber import UnifiedVoiceTranscriber

def main():
    print("🎤 Hindi Voice Memo Transcription")
    print("=" * 40)
    
    # File path
    audio_file = "/Users/rupali.b/Library/Mobile Documents/com~apple~CloudDocs/Voice Memos/Sector 39.m4a"
    
    # Check if file exists
    if not os.path.exists(audio_file):
        print(f"❌ File not found: {audio_file}")
        return
    
    print(f"📁 Input file: {audio_file}")
    print(f"📊 File size: {os.path.getsize(audio_file) / (1024*1024):.1f} MB")
    
    # Create transcriber with large model for best Hindi accuracy
    print("\n🤖 Loading Whisper large model (this may take a few minutes on first run)...")
    transcriber = UnifiedVoiceTranscriber(
        model_size="large",  # Best accuracy for Hindi
        enable_speaker_diarization=True
    )
    
    try:
        print("🎯 Starting transcription...")
        result = transcriber.transcribe_audio(audio_file, output_dir="../transcriptions")
        
        print(f"\n✅ Transcription completed successfully!")
        print(f"🌍 Detected language: {result.get('language', 'Unknown')}")
        
        # Save the transcription to a markdown file
        output_filename = f"Sector_39_transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        output_path = f"../transcriptions/{output_filename}"
        
        # Create metadata for the file
        metadata = {
            "File Name": "Sector 39.m4a",
            "File Size": f"{os.path.getsize(audio_file) / (1024*1024):.1f} MB",
            "Language": result.get('language', 'Unknown'),
            "Model Used": "Whisper Large",
            "Transcription Date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Save as markdown
        transcriber.save_transcription_markdown(result, output_path, metadata)
        
        print(f"📁 Transcription saved to: {output_path}")
        print(f"👥 Speakers detected: {len(set([seg.get('speaker', 'Unknown') for seg in result.get('segments', [])]))}")
        print(f"⏱️  Audio duration: {result.get('segments', [{}])[-1].get('end', 0):.1f} seconds")
        
        print(f"\n📝 Check the transcriptions folder for your Hindi transcription!")
        
    except Exception as e:
        print(f"❌ Error during transcription: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
