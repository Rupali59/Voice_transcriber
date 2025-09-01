# 👤 Voice Transcriber User Guide

A comprehensive guide for using the Voice Transcriber web application.

## 🎯 Getting Started

### Accessing the Application

1. **Open your web browser**
2. **Navigate to the application URL**:
   - Local development: `http://localhost:5001`
   - Production: `https://your-domain.com`

### First Time Setup

The application is ready to use immediately - no account creation or setup required!

## 🎤 Uploading Audio Files

### Supported File Formats
- **WAV** - Uncompressed audio (recommended for best quality)
- **MP3** - Compressed audio (most common)
- **M4A** - Apple audio format
- **FLAC** - Lossless compressed audio
- **OGG** - Open source audio format
- **WMA** - Windows Media Audio
- **AAC** - Advanced Audio Coding
- **MP4** - Video files with audio

### File Size Limits
- **Maximum size**: 500MB
- **Recommended**: Under 100MB for faster processing

### Upload Methods

#### Method 1: Drag and Drop
1. **Open the application** in your browser
2. **Drag your audio file** from your computer
3. **Drop it** onto the upload area
4. **Wait for confirmation** that the file was uploaded

#### Method 2: Browse Files
1. **Click** on the upload area
2. **Select** your audio file from the file browser
3. **Wait for confirmation** that the file was uploaded

### Upload Tips
- **Use good quality audio** for better transcription accuracy
- **Avoid background noise** when possible
- **Ensure clear speech** for best results
- **Check file format** is supported before uploading

## ⚙️ Configuration Options

### AI Model Selection

Choose the Whisper model that best fits your needs:

| Model | Speed | Accuracy | Best For |
|-------|-------|----------|----------|
| **Tiny** | ⚡⚡⚡⚡⚡ | ⭐⭐ | Quick drafts, very fast processing |
| **Base** | ⚡⚡⚡⚡ | ⭐⭐⭐ | General use, good balance |
| **Small** | ⚡⚡⚡ | ⭐⭐⭐⭐ | Better accuracy, slightly slower |
| **Medium** | ⚡⚡ | ⭐⭐⭐⭐⭐ | High accuracy, slower processing |
| **Large** | ⚡ | ⭐⭐⭐⭐⭐ | Best accuracy, slowest processing |

**Recommendation**: Start with **Base** model for most use cases.

### Speaker Diarization

**What it does**: Identifies different speakers in your audio file.

**When to enable**:
- ✅ **Interviews** - Multiple people talking
- ✅ **Meetings** - Different participants
- ✅ **Conversations** - Two or more speakers
- ✅ **Podcasts** - Host and guests

**When to disable**:
- ❌ **Single speaker** - One person talking
- ❌ **Music** - No speech to identify
- ❌ **Very short audio** - Under 30 seconds

### Language Selection

**Auto-detect (Recommended)**:
- Automatically detects the language
- Works for most common languages
- Best for mixed-language content

**Specific Language**:
- Choose if you know the exact language
- May provide slightly better accuracy
- Available languages: English, Hindi, Spanish, French, German, Italian, Portuguese, Russian, Japanese, Korean, Chinese

## 🚀 Starting Transcription

### Step-by-Step Process

1. **Upload your audio file** (see Uploading section above)
2. **Configure your options**:
   - Select AI model
   - Enable/disable speaker diarization
   - Choose language or auto-detect
3. **Click "Start Transcription"**
4. **Wait for processing** (see Progress Tracking below)
5. **Download your results** when complete

### What Happens During Transcription

1. **Loading Model** (10% progress)
   - The AI model is loaded into memory
   - This may take a few minutes on first use

2. **Transcribing Audio** (30-80% progress)
   - The audio is processed by the AI
   - This is the longest step

3. **Processing Results** (80-100% progress)
   - Results are formatted and saved
   - Final processing and cleanup

## 📊 Progress Tracking

### Real-time Updates

The application provides live updates during transcription:

- **Progress bar** shows completion percentage
- **Status messages** explain what's happening
- **Time estimates** for completion
- **Error notifications** if something goes wrong

### Understanding Progress

- **0-10%**: Loading AI model
- **10-30%**: Initializing transcription
- **30-80%**: Processing audio (main work)
- **80-100%**: Finalizing and saving results

### Typical Processing Times

| File Length | Tiny Model | Base Model | Large Model |
|-------------|------------|------------|-------------|
| 5 minutes | 30 seconds | 1 minute | 5 minutes |
| 30 minutes | 3 minutes | 10 minutes | 30 minutes |
| 1 hour | 6 minutes | 20 minutes | 1 hour |

*Times are approximate and depend on your computer's performance*

## 📄 Understanding Results

### Output Format

Transcriptions are saved as **Markdown files** with:

- **File information** (name, size, date)
- **Transcription settings** (model used, language)
- **Full transcription text**
- **Speaker analysis** (if enabled)
- **Performance notes**

### Sample Output

```markdown
# audio_file - Transcription

**File:** audio_file.wav
**Date:** 2024-09-01 23:20:00
**Language:** English
**Duration:** 2:30
**Model Used:** Whisper BASE
**Speaker Diarization:** Enabled

## Transcription

Hello, this is a test transcription. The AI has successfully converted the audio to text with high accuracy.

## Speaker Analysis

**Speaker 1** (0:00 - 1:15)
Hello, this is a test transcription.

**Speaker 2** (1:15 - 2:30)
The AI has successfully converted the audio to text with high accuracy.
```

## 💾 Downloading Results

### Download Process

1. **Wait for completion** - Transcription must be 100% complete
2. **Click "Download Transcription"** button
3. **Save the file** to your computer
4. **Open with any text editor** or Markdown viewer

### File Location

- **Filename format**: `transcription_[job_id]_[timestamp].md`
- **File type**: Markdown (.md)
- **Size**: Usually very small (few KB)

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Upload Problems

**Problem**: File upload fails
**Solutions**:
- Check file size (must be under 500MB)
- Verify file format is supported
- Try a different browser
- Check your internet connection

**Problem**: "Invalid file type" error
**Solutions**:
- Convert to supported format (WAV, MP3, M4A, etc.)
- Check file extension is correct
- Try renaming the file

#### Transcription Problems

**Problem**: Transcription fails or stops
**Solutions**:
- Check audio quality (avoid very noisy files)
- Try a different AI model
- Ensure audio contains speech
- Check available disk space

**Problem**: Poor transcription quality
**Solutions**:
- Use higher quality audio
- Try a larger AI model (Medium or Large)
- Enable speaker diarization for multi-speaker content
- Specify the correct language

**Problem**: Very slow processing
**Solutions**:
- Use a smaller AI model (Tiny or Base)
- Check your internet connection
- Close other applications to free up resources
- Try shorter audio files

#### Technical Issues

**Problem**: Page won't load
**Solutions**:
- Check the URL is correct
- Try refreshing the page
- Clear browser cache
- Try a different browser

**Problem**: Progress stops updating
**Solutions**:
- Refresh the page
- Check browser console for errors
- Try a different browser
- Check internet connection

### Getting Help

If you continue to have problems:

1. **Check the logs** - Look for error messages
2. **Try different settings** - Different model, language, etc.
3. **Test with a simple file** - Short, clear audio
4. **Contact support** - Create an issue with details

## 💡 Tips for Best Results

### Audio Quality
- **Use clear audio** without background noise
- **Ensure good microphone quality** for recordings
- **Avoid echo or reverb** in recording environment
- **Keep consistent volume** throughout the audio

### File Preparation
- **Trim unnecessary silence** at beginning/end
- **Use appropriate file format** (WAV for best quality)
- **Keep file size reasonable** (under 100MB when possible)
- **Ensure file is not corrupted**

### Settings Optimization
- **Start with Base model** for most content
- **Enable speaker diarization** for multiple speakers
- **Use auto-detect language** unless you're certain
- **Try different models** if results aren't satisfactory

### Workflow Tips
- **Process files in batches** for efficiency
- **Keep original audio files** as backup
- **Review transcriptions** for accuracy
- **Use consistent naming** for your files

## 🎉 Success Stories

### Best Use Cases

- **Meeting transcriptions** - Convert meeting recordings to searchable text
- **Interview documentation** - Transcribe interviews for analysis
- **Lecture notes** - Convert educational content to text
- **Podcast transcripts** - Create transcripts for accessibility
- **Voice memos** - Convert voice notes to text notes

### Pro Tips

- **Use speaker diarization** for interviews and meetings
- **Try Large model** for important content requiring high accuracy
- **Use Tiny model** for quick drafts and notes
- **Enable auto-detect** for mixed-language content
- **Download results immediately** after completion

---

**Happy transcribing! 🎤✨**

*For technical issues or advanced usage, see the [Technical Reference](TECHNICAL_REFERENCE.md) and [API Reference](API_REFERENCE.md).*
