# Technical Reference

## Architecture
```
User Input → File Discovery → Audio Processing → Transcription → Output
```

## Core Components
- **Whisper**: Speech-to-text with language detection
- **Speaker Diarization**: Identifies multiple speakers using MFCC features
- **Audio Processing**: Handles various audio formats (MP3, M4A, WAV, etc.)

## API Reference

### UnifiedVoiceTranscriber
```python
UnifiedVoiceTranscriber(
    model_size="base",
    enable_speaker_diarization=True
)
```
- `transcribe_audio(audio_path)` - Transcribe single audio file
- Returns dict with: text, language, duration, speaker_segments

### UnifiedVoiceMemosProcessor
```python
UnifiedVoiceMemosProcessor()
```
- `process_all_voice_memos()` - Process all found voice memos
- `process_from_locations(locations)` - Process from specific paths

## Dependencies
- OpenAI Whisper, PyTorch, Librosa, Scikit-learn
- FFmpeg for audio processing

## Configuration
See `configs/config.py` for voice memo locations and processing settings.
