# Performance Guide - Voice Transcriber

Optimization strategies and performance tuning for the Voice Transcriber application.

## 🎯 Performance Overview

### Key Performance Metrics

- **Transcription Speed**: Time to process audio files
- **Memory Usage**: RAM consumption during processing
- **CPU Utilization**: Processor usage during transcription
- **Concurrent Jobs**: Number of simultaneous transcriptions
- **File Processing**: Upload and download speeds

### Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Transcription Speed | 0.1x real-time | 10min audio = 1min processing |
| Memory Usage | <8GB | For large model processing |
| Concurrent Jobs | 3-5 | Depends on system resources |
| File Upload | <30s | For 100MB files |
| Response Time | <200ms | API response times |

## 🚀 Optimization Strategies

### 1. Model Selection

Choose the right Whisper model for your needs:

| Model | Speed | Memory | Accuracy | Use Case |
|-------|-------|--------|----------|----------|
| **Tiny** | 10x real-time | 1GB | 70% | Quick drafts, testing |
| **Base** | 4x real-time | 2GB | 80% | General use (recommended) |
| **Small** | 2x real-time | 3GB | 85% | Important content |
| **Medium** | 1x real-time | 5GB | 90% | Professional use |
| **Large** | 0.5x real-time | 8GB | 95% | Critical accuracy |

**Recommendation**: Start with **Base** model for best balance.

### 2. System Resource Optimization

#### Memory Management
```python
# Optimize memory usage
import gc
import torch

def optimize_memory():
    """Optimize memory usage"""
    # Clear cache
    torch.cuda.empty_cache() if torch.cuda.is_available() else None
    gc.collect()
    
    # Set memory fraction
    torch.cuda.set_per_process_memory_fraction(0.8)
```

#### CPU Optimization
```python
# Set optimal thread count
import os
os.environ['OMP_NUM_THREADS'] = '4'  # Adjust based on CPU cores
os.environ['MKL_NUM_THREADS'] = '4'
```

### 3. File Processing Optimization

#### Audio Preprocessing
```python
def optimize_audio_file(audio_file):
    """Optimize audio file for processing"""
    # Convert to optimal format
    # - Sample rate: 16kHz (Whisper's native rate)
    # - Channels: Mono
    # - Format: WAV
    
    import librosa
    
    # Load and resample
    audio, sr = librosa.load(audio_file, sr=16000, mono=True)
    
    # Save optimized version
    librosa.output.write_wav('optimized.wav', audio, 16000)
    
    return 'optimized.wav'
```

#### Chunk Processing
```python
def process_large_file_in_chunks(audio_file, chunk_size=600):
    """Process large files in chunks"""
    import librosa
    
    # Load audio
    audio, sr = librosa.load(audio_file)
    duration = len(audio) / sr
    
    # Process in chunks
    for start_time in range(0, int(duration), chunk_size):
        end_time = min(start_time + chunk_size, duration)
        chunk = audio[start_time*sr:end_time*sr]
        
        # Process chunk
        yield process_chunk(chunk, sr)
```

### 4. Concurrent Processing

#### Job Queue Management
```python
class OptimizedJobManager:
    def __init__(self, max_concurrent=3):
        self.max_concurrent = max_concurrent
        self.active_jobs = {}
        self.job_queue = queue.PriorityQueue()
        
    def start_job(self, job):
        """Start job with resource management"""
        if len(self.active_jobs) >= self.max_concurrent:
            self.job_queue.put(job)
            return False
        
        # Start job
        self.active_jobs[job.id] = job
        thread = threading.Thread(target=self._process_job, args=(job,))
        thread.start()
        
        return True
    
    def _process_job(self, job):
        """Process job with optimization"""
        try:
            # Optimize memory before processing
            optimize_memory()
            
            # Process job
            result = self.transcription_service.transcribe(job.audio_file)
            
            # Clean up
            del job.audio_file
            optimize_memory()
            
        finally:
            # Remove from active jobs
            del self.active_jobs[job.id]
            
            # Start next job in queue
            if not self.job_queue.empty():
                next_job = self.job_queue.get()
                self.start_job(next_job)
```

## 🔧 Configuration Optimization

### Environment Variables

```bash
# Performance Configuration
MAX_CONCURRENT_JOBS=3              # Adjust based on system
WHISPER_MODEL_CACHE_SIZE=2         # Number of models to keep in memory
AUDIO_CHUNK_SIZE=600               # Chunk size in seconds
ENABLE_GPU_ACCELERATION=True       # Use GPU if available
MEMORY_OPTIMIZATION=True           # Enable memory optimization

# File Processing
MAX_FILE_SIZE=500MB                # Maximum file size
AUDIO_OPTIMIZATION=True            # Optimize audio before processing
CLEANUP_INTERVAL=300               # Cleanup interval (seconds)

# Logging
LOG_LEVEL=WARNING                  # Reduce logging in production
LOG_PERFORMANCE_METRICS=True       # Log performance data
```

### Flask Configuration

```python
class ProductionConfig(Config):
    """Production configuration with performance optimizations"""
    
    # Performance settings
    MAX_CONCURRENT_JOBS = 3
    WHISPER_MODEL_CACHE_SIZE = 2
    
    # Memory optimization
    MEMORY_OPTIMIZATION = True
    ENABLE_GPU_ACCELERATION = True
    
    # File processing
    AUDIO_OPTIMIZATION = True
    AUDIO_CHUNK_SIZE = 600
    
    # Logging
    LOG_LEVEL = 'WARNING'
    LOG_PERFORMANCE_METRICS = True
```

## 📊 Monitoring & Metrics

### Performance Monitoring

```python
import time
import psutil
import logging

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
        self.logger = logging.getLogger('performance')
    
    def start_monitoring(self, job_id):
        """Start monitoring a job"""
        self.metrics[job_id] = {
            'start_time': time.time(),
            'start_memory': psutil.virtual_memory().used,
            'start_cpu': psutil.cpu_percent()
        }
    
    def end_monitoring(self, job_id):
        """End monitoring and log metrics"""
        if job_id not in self.metrics:
            return
        
        metrics = self.metrics[job_id]
        end_time = time.time()
        
        # Calculate metrics
        duration = end_time - metrics['start_time']
        memory_used = psutil.virtual_memory().used - metrics['start_memory']
        cpu_avg = psutil.cpu_percent()
        
        # Log performance data
        self.logger.info(f"Job {job_id} completed in {duration:.2f}s, "
                        f"Memory: {memory_used/1024/1024:.2f}MB, "
                        f"CPU: {cpu_avg:.1f}%")
        
        # Clean up
        del self.metrics[job_id]
```

### System Resource Monitoring

```python
def monitor_system_resources():
    """Monitor system resources"""
    import psutil
    
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Memory usage
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    memory_available = memory.available / 1024 / 1024 / 1024  # GB
    
    # Disk usage
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    disk_free = disk.free / 1024 / 1024 / 1024  # GB
    
    return {
        'cpu_percent': cpu_percent,
        'memory_percent': memory_percent,
        'memory_available_gb': memory_available,
        'disk_percent': disk_percent,
        'disk_free_gb': disk_free
    }
```

## 🚀 Production Optimization

### 1. Hardware Recommendations

#### Minimum Requirements
- **CPU**: 4 cores, 2.5GHz
- **RAM**: 8GB
- **Storage**: 50GB SSD
- **Network**: 100Mbps

#### Recommended Configuration
- **CPU**: 8 cores, 3.0GHz
- **RAM**: 16GB
- **Storage**: 100GB SSD
- **Network**: 1Gbps
- **GPU**: NVIDIA GPU with 8GB VRAM (optional)

### 2. Docker Optimization

```dockerfile
# Optimized Dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV OMP_NUM_THREADS=4
ENV MKL_NUM_THREADS=4

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 transcriber
USER transcriber

EXPOSE 5001

CMD ["python", "app_main.py"]
```

### 3. Load Balancing

```yaml
# docker-compose.yml with load balancing
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - transcriber1
      - transcriber2
      - transcriber3

  transcriber1:
    build: .
    environment:
      - INSTANCE_ID=1
      - MAX_CONCURRENT_JOBS=2
    volumes:
      - ./uploads:/app/uploads
      - ./transcriptions:/app/transcriptions

  transcriber2:
    build: .
    environment:
      - INSTANCE_ID=2
      - MAX_CONCURRENT_JOBS=2
    volumes:
      - ./uploads:/app/uploads
      - ./transcriptions:/app/transcriptions

  transcriber3:
    build: .
    environment:
      - INSTANCE_ID=3
      - MAX_CONCURRENT_JOBS=2
    volumes:
      - ./uploads:/app/uploads
      - ./transcriptions:/app/transcriptions
```

## 📈 Benchmarking

### Performance Testing

```python
import time
import psutil
import threading

class PerformanceBenchmark:
    def __init__(self):
        self.results = []
    
    def benchmark_transcription(self, audio_file, model_size='base', iterations=5):
        """Benchmark transcription performance"""
        results = []
        
        for i in range(iterations):
            # Monitor system resources
            start_time = time.time()
            start_memory = psutil.virtual_memory().used
            start_cpu = psutil.cpu_percent()
            
            # Run transcription
            result = self.transcribe(audio_file, model_size)
            
            # Calculate metrics
            duration = time.time() - start_time
            memory_used = psutil.virtual_memory().used - start_memory
            cpu_avg = psutil.cpu_percent()
            
            results.append({
                'iteration': i + 1,
                'duration': duration,
                'memory_used': memory_used,
                'cpu_avg': cpu_avg,
                'audio_duration': result['duration']
            })
        
        return results
    
    def calculate_metrics(self, results):
        """Calculate performance metrics"""
        durations = [r['duration'] for r in results]
        memory_usage = [r['memory_used'] for r in results]
        cpu_usage = [r['cpu_avg'] for r in results]
        
        return {
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'avg_memory': sum(memory_usage) / len(memory_usage),
            'avg_cpu': sum(cpu_usage) / len(cpu_usage),
            'real_time_factor': results[0]['audio_duration'] / (sum(durations) / len(durations))
        }
```

## 🛠️ Troubleshooting Performance Issues

### Common Performance Problems

1. **Slow Transcription**
   - Check model size (use smaller model)
   - Verify system resources
   - Check for memory leaks
   - Optimize audio file format

2. **High Memory Usage**
   - Reduce concurrent jobs
   - Use smaller models
   - Enable memory optimization
   - Check for memory leaks

3. **High CPU Usage**
   - Limit concurrent jobs
   - Use CPU-optimized models
   - Check for infinite loops
   - Optimize file processing

4. **File Upload Issues**
   - Check file size limits
   - Verify network connection
   - Check disk space
   - Optimize file format

### Performance Debugging

```python
import cProfile
import pstats

def profile_transcription(audio_file):
    """Profile transcription performance"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run transcription
    result = transcribe(audio_file)
    
    profiler.disable()
    
    # Save profile results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
    
    return result
```

---

**For more information, see the [Technical Reference](TECHNICAL_REFERENCE.md) and [Troubleshooting Guide](TROUBLESHOOTING.md).**
