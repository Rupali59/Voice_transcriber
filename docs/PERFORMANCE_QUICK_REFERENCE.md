# 🚀 Performance Quick Reference

## ⚡ CPU Usage Guide

### **Your System: 10 CPU Cores**
- **100%** = 1 core (Low usage)
- **200%** = 2 cores (Good)
- **300%** = 3 cores (Better)
- **400%** = 4 cores (Excellent)
- **500%** = 5 cores (Very High)
- **1000%** = 10 cores (Maximum)

### **Current Status: 240% CPU**
✅ **Excellent Performance**: Using 2.4 cores efficiently
✅ **System Responsive**: 7.6 cores still available
✅ **Optimal Processing**: Transcription progressing quickly

---

## 📊 Performance Monitoring

### **Quick Status Commands**
```bash
# Essential info only
./scripts/transcriber.sh quick

# Detailed status
./scripts/transcriber.sh status

# Real-time monitoring
./scripts/transcriber.sh monitor
```

### **Key Metrics to Watch**
- **CPU Usage**: 100-500% during processing (normal)
- **Memory**: Should remain stable
- **Processing Speed**: 2-10x real-time
- **Output Files**: Appear in `transcriptions/` folder

---

## 🎯 Expected Performance

### **By Audio Length**
| Length | Time | CPU | Memory |
|--------|------|-----|--------|
| **1 min** | 30s-2min | 150-200% | 500MB-1GB |
| **5 min** | 2-8min | 200-300% | 1-2GB |
| **10 min** | 5-15min | 250-400% | 2-4GB |
| **30 min** | 15-45min | 300-500% | 4-8GB |

---

## 🔧 Performance Tuning

### **Environment Variables**
```bash
# .env file settings
WHISPER_MODEL_SIZE=medium    # Speed vs. accuracy
MAX_CONCURRENT_PROCESSES=2   # Concurrency level
BATCH_SIZE=3                 # Batch processing
AUDIO_CHUNK_SIZE=30          # Audio segment size
```

### **Model Selection**
- **tiny**: Fastest, lowest accuracy
- **base**: Balanced speed/accuracy
- **small**: Better accuracy, slower
- **medium**: High accuracy, slower
- **large**: Best accuracy, slowest

---

## 🚨 When to Worry

### **High CPU (>800%)**
- Processing very long files
- Multiple files simultaneously
- **Solution**: Process fewer files at once

### **Memory Issues**
- Large audio files
- Insufficient RAM
- **Solution**: Close other applications

### **Slow Processing**
- Large Whisper model
- Complex audio (multiple speakers)
- **Solution**: Use smaller model

---

## 💡 Best Practices

1. **Monitor Progress**: Use `./scripts/transcriber.sh quick`
2. **Check Resources**: Monitor CPU and memory usage
3. **Optimize Settings**: Adjust `.env` parameters
4. **Batch Processing**: Process multiple files together
5. **Background Mode**: Let system work while you do other tasks

---

## 📚 Full Documentation

- **Complete Technical Details**: `docs/TECHNICAL_DETAILS.md`
- **System Architecture**: Component breakdown and flow
- **Performance Analysis**: Detailed benchmarks and optimization
- **Troubleshooting**: Common issues and solutions

---

**🎯 Remember**: High CPU usage (200-500%) is **normal and expected** during transcription. It means your system is working efficiently! 🚀✨
