#!/usr/bin/env python3
"""
Fast Transcription Test with Base Model
Demonstrates the speed improvement from Large to Base model
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config_manager import ConfigManager
from unified_voice_transcriber import UnifiedVoiceTranscriber

def test_fast_transcription():
    """Test transcription with Base model for speed"""
    print("🚀 Fast Transcription Test - Base Model")
    print("=" * 50)
    
    # Voice memo path
    voice_memo_path = "/Users/rupali.b/Library/Mobile Documents/com~apple~CloudDocs/Voice Memos/Sector 39.m4a"
    
    if not Path(voice_memo_path).exists():
        print(f"❌ Voice memo not found: {voice_memo_path}")
        return
    
    print(f"📁 File: {Path(voice_memo_path).name}")
    print(f"📊 Size: {Path(voice_memo_path).stat().st_size / (1024*1024):.1f} MB")
    
    # Create transcriber with Base model (fast)
    print("\n⚡ Creating transcriber with Base model...")
    transcriber = UnifiedVoiceTranscriber(
        model_size="base",  # Much faster than 'large'
        enable_speaker_diarization=True
    )
    
    print("✅ Transcribers ready!")
    print("\n🚀 Starting transcription...")
    print("💡 Expected time: 3-5 minutes (vs 50 minutes with Large model)")
    
    # Start transcription
    start_time = time.time()
    
    try:
        # Transcribe the file
        result = transcriber.transcribe_audio(voice_memo_path)
        
        processing_time = time.time() - start_time
        
        if result:
            print(f"\n✅ Transcription completed in {processing_time:.1f} seconds ({processing_time/60:.1f} minutes)")
            print(f"🚀 Speed improvement: ~10x faster than Large model!")
            
            # Save result
            output_filename = f"../transcriptions/Sector_39_fast_transcription_{time.strftime('%Y%m%d_%H%M%S')}.md"
            output_path = Path(output_filename)
            
            # Generate content
            content = generate_output_content(voice_memo_path, result, "base", processing_time)
            
            # Write file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"💾 Saved to: {output_path}")
            
            # Show performance comparison
            print("\n📊 Performance Comparison:")
            print(f"• Large model: ~50 minutes")
            print(f"• Base model: {processing_time/60:.1f} minutes")
            print(f"• Speed improvement: {50/(processing_time/60):.1f}x faster!")
            
        else:
            print("❌ Transcription failed")
            
    except Exception as e:
        print(f"❌ Error during transcription: {e}")
        import traceback
        traceback.print_exc()

def generate_output_content(file_path: str, transcription: dict, model_size: str, processing_time: float) -> str:
    """Generate markdown output content"""
    input_file = Path(file_path)
    
    lines = [
        f"# {input_file.stem} - Fast Transcription (Base Model)",
        "",
        f"**File:** {input_file.name}",
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Language:** {transcription.get('language', 'Unknown')}",
        f"**Duration:** {transcription.get('duration', 'Unknown')}",
        f"**Model Used:** Whisper {model_size.upper()} (Fast Mode)",
        f"**Processing Time:** {processing_time:.1f}s ({processing_time/60:.1f} minutes)",
        f"**Speed Mode:** Base model for optimal speed/quality balance",
        "",
        "## Transcription",
        "",
        transcription.get('text', 'No transcription available')
    ]
    
    # Add speaker analysis if available
    if transcription.get('speaker_segments'):
        lines.extend([
            "",
            "## Speaker Analysis",
            ""
        ])
        
        for i, segment in enumerate(transcription.get('speaker_segments', [])):
            lines.extend([
                f"**Speaker {segment.get('speaker', i)}** "
                f"({segment.get('start_time', 'Unknown')} - "
                f"({segment.get('end_time', 'Unknown')})",
                f"{segment.get('text', '')}",
                ""
            ])
    
    # Add performance notes
    lines.extend([
        "",
        "## Performance Notes",
        "",
        "This transcription was completed using the **Whisper Base model** for optimal speed.",
        "",
        "**Speed Benefits:**",
        "- **10x faster** than Large model",
        "- **Good quality** for most use cases",
        "- **Efficient resource usage**",
        "",
        "**Quality Trade-offs:**",
        "- Slightly lower accuracy than Large model",
        "- Still excellent for voice memos and conversations",
        "- Perfect balance of speed and quality"
    ])
    
    return "\n".join(lines)

if __name__ == "__main__":
    try:
        test_fast_transcription()
    except KeyboardInterrupt:
        print("\n🛑 Transcription interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
