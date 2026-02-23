# Model Caching Guide for EchoScribe

This guide explains how to ensure models are always cached and available for immediate use in the EchoScribe Voice Transcriber application.

## Overview

The model caching system has been enhanced to provide:
- **Persistent Caching**: Models stay loaded across restarts
- **Always-On Caching**: Priority models are always kept in memory
- **Intelligent Preloading**: Automatic warmup of frequently used models
- **Memory Management**: Smart eviction and optimization
- **Health Monitoring**: Real-time cache health and performance tracking

## Configuration

### Environment Variables

Add these variables to your `.env` file to configure model caching:

```bash
# Model Cache Configuration
WHISPER_MODEL_CACHE_SIZE=5                    # Maximum models to cache (default: 5)
MODEL_IDLE_TIMEOUT=3600                      # Idle timeout in seconds (default: 1 hour)
MODEL_CLEANUP_INTERVAL=600                   # Cleanup check interval (default: 10 minutes)
ENABLE_GPU_ACCELERATION=true                 # Enable GPU acceleration

# Persistent Model Cache Configuration
PERSISTENT_MODEL_CACHE=true                  # Enable persistent caching
ALWAYS_KEEP_MODELS=true                      # Always keep priority models loaded
WARMUP_MODELS=base,small,medium             # Models to warm up on startup
PRIORITY_MODELS=base,small                   # Models that should never be evicted
MODEL_CACHE_DIR=model_cache                  # Directory for cache metadata
```

### Model Sizes and Memory Requirements

| Model | Size (MB) | Speed | Accuracy | Use Case |
|-------|-----------|-------|----------|----------|
| tiny  | 39        | ⚡⚡⚡⚡⚡ | ⭐⭐     | Fastest, basic accuracy |
| base  | 74        | ⚡⚡⚡⚡   | ⭐⭐⭐   | Balanced speed/accuracy |
| small | 244       | ⚡⚡⚡     | ⭐⭐⭐⭐ | Better accuracy |
| medium| 769       | ⚡⚡       | ⭐⭐⭐⭐⭐| High accuracy |
| large | 1550      | ⚡         | ⭐⭐⭐⭐⭐| Best accuracy |

## Caching Strategies

### 1. Always-On Caching (Recommended)

**Configuration:**
```bash
ALWAYS_KEEP_MODELS=true
PRIORITY_MODELS=base,small
PERSISTENT_MODEL_CACHE=true
```

**Benefits:**
- Priority models never get evicted
- Instant response for common model sizes
- Consistent performance
- No cold starts

**Memory Usage:**
- Base + Small: ~318MB
- Base + Small + Medium: ~1087MB

### 2. Smart Caching

**Configuration:**
```bash
ALWAYS_KEEP_MODELS=false
PERSISTENT_MODEL_CACHE=true
WARMUP_MODELS=base,small
```

**Benefits:**
- Automatic model management
- Memory optimization
- Good balance of performance and resource usage

### 3. Minimal Caching

**Configuration:**
```bash
ALWAYS_KEEP_MODELS=false
PERSISTENT_MODEL_CACHE=false
WHISPER_MODEL_CACHE_SIZE=2
```

**Benefits:**
- Lowest memory usage
- Models loaded on demand
- Good for resource-constrained environments

## API Endpoints

### Get Cache Status
```bash
GET /api/cache/models
```

**Response:**
```json
{
  "success": true,
  "stats": {
    "cached_models": ["base", "small"],
    "cache_size": 2,
    "max_cache_size": 5,
    "hit_rate": 85.5,
    "memory_usage": {
      "rss_mb": 1024.5,
      "percent": 45.2
    }
  },
  "health": {
    "status": "healthy",
    "priority_coverage": 100,
    "message": "All systems operational"
  },
  "loaded_models": ["base", "small"],
  "available_models": ["tiny", "base", "small", "medium", "large"]
}
```

### Preload Models
```bash
POST /api/cache/models/preload
Content-Type: application/json

{
  "models": ["base", "small", "medium"]
}
```

### Ensure Models Loaded
```bash
POST /api/cache/models/ensure
Content-Type: application/json

{
  "models": ["base", "small"]
}
```

### Warm Up Priority Models
```bash
POST /api/cache/models/priority/warmup
```

### Get Model Status
```bash
GET /api/cache/models/base/status
```

### Reload Model
```bash
POST /api/cache/models/base/reload
```

### Clear Cache
```bash
POST /api/cache/clear
```

### Optimize Memory
```bash
POST /api/cache/optimize
```

## Python API Usage

### Basic Usage
```python
from app.services.model_cache_manager import get_model_cache_manager

# Get cache manager
cache_manager = get_model_cache_manager()

# Get a model (loads if not cached)
model = cache_manager.get_model('base')

# Preload models
cache_manager.preload_models(['base', 'small', 'medium'])

# Ensure models are loaded
cache_manager.ensure_models_loaded(['base', 'small'])

# Warm up priority models
cache_manager.warmup_priority_models()

# Get cache statistics
stats = cache_manager.get_cache_stats()

# Get cache health
health = cache_manager.get_cache_health()

# Check if model is loaded
is_loaded = cache_manager.is_model_loaded('base')

# Get loaded models
loaded = cache_manager.get_loaded_models()
```

### Advanced Usage
```python
# Force reload a model
cache_manager.force_reload_model('base')

# Get detailed model status
status = cache_manager.get_model_status('base')
print(f"Model loaded: {status['loaded']}")
print(f"Usage count: {status['usage']['access_count']}")
print(f"Is priority: {status['is_priority']}")

# Clear all models
cache_manager.clear_cache()

# Optimize memory
cache_manager.optimize_memory()
```

## Monitoring and Health Checks

### Cache Health Status

**Healthy:**
- All priority models loaded
- Hit rate > 50%
- Memory usage < 90%

**Warning:**
- Some priority models not loaded
- Low hit rate (< 50%)
- High memory usage (> 90%)

**Error:**
- Cache system unavailable
- Critical errors

### Performance Metrics

- **Hit Rate**: Percentage of requests served from cache
- **Load Time**: Time to load models
- **Memory Usage**: RAM consumption
- **Eviction Count**: Number of models evicted
- **Access Count**: How often each model is used

## Best Practices

### 1. Production Setup

**Recommended Configuration:**
```bash
# Always keep essential models
ALWAYS_KEEP_MODELS=true
PRIORITY_MODELS=base,small

# Preload common models
WARMUP_MODELS=base,small,medium

# Enable persistent caching
PERSISTENT_MODEL_CACHE=true

# Reasonable cache size
WHISPER_MODEL_CACHE_SIZE=5

# Longer idle timeout for production
MODEL_IDLE_TIMEOUT=7200  # 2 hours
```

### 2. Development Setup

**Configuration:**
```bash
# Smaller cache for development
WHISPER_MODEL_CACHE_SIZE=3
PRIORITY_MODELS=base

# Faster cleanup for testing
MODEL_CLEANUP_INTERVAL=300  # 5 minutes
MODEL_IDLE_TIMEOUT=1800     # 30 minutes
```

### 3. Resource-Constrained Setup

**Configuration:**
```bash
# Minimal cache
WHISPER_MODEL_CACHE_SIZE=2
PRIORITY_MODELS=base
WARMUP_MODELS=base

# Disable persistent cache
PERSISTENT_MODEL_CACHE=false
ALWAYS_KEEP_MODELS=false
```

## Troubleshooting

### Common Issues

**1. Models Not Staying Loaded**
- Check `ALWAYS_KEEP_MODELS=true`
- Verify `PRIORITY_MODELS` includes desired models
- Check memory usage and available RAM

**2. High Memory Usage**
- Reduce `WHISPER_MODEL_CACHE_SIZE`
- Remove models from `PRIORITY_MODELS`
- Enable `ALWAYS_KEEP_MODELS=false`

**3. Slow Model Loading**
- Enable `PERSISTENT_MODEL_CACHE=true`
- Add models to `WARMUP_MODELS`
- Check GPU availability

**4. Cache Not Working**
- Verify Whisper is installed
- Check logs for errors
- Ensure sufficient disk space for cache directory

### Debug Commands

```bash
# Check cache status
curl http://localhost:5001/api/cache/models

# Check specific model
curl http://localhost:5001/api/cache/models/base/status

# Warm up priority models
curl -X POST http://localhost:5001/api/cache/models/priority/warmup

# Clear and reload
curl -X POST http://localhost:5001/api/cache/clear
curl -X POST http://localhost:5001/api/cache/models/preload \
  -H "Content-Type: application/json" \
  -d '{"models": ["base", "small"]}'
```

### Log Monitoring

**Key Log Messages:**
- `ModelCache initialized` - Cache system started
- `Using cached model` - Model served from cache
- `Loading Whisper model` - Model being loaded
- `Evicting least used model` - Model being evicted
- `Priority model not loaded` - Warning about missing priority model

## Performance Optimization

### Memory Optimization

1. **Monitor Memory Usage:**
   ```python
   stats = cache_manager.get_cache_stats()
   memory = stats['memory_usage']
   print(f"Memory usage: {memory['percent']:.1f}%")
   ```

2. **Optimize When Needed:**
   ```python
   if memory['percent'] > 80:
       cache_manager.optimize_memory()
   ```

3. **Clear Unused Models:**
   ```python
   # Clear all and reload only needed models
   cache_manager.clear_cache()
   cache_manager.preload_models(['base', 'small'])
   ```

### Load Time Optimization

1. **Preload on Startup:**
   ```python
   # In your startup code
   cache_manager.preload_models(['base', 'small', 'medium'])
   ```

2. **Warm Up Priority Models:**
   ```python
   # Ensure priority models are always ready
   cache_manager.warmup_priority_models()
   ```

3. **Background Loading:**
   ```python
   # Load models in background
   import threading
   threading.Thread(
       target=cache_manager.preload_models,
       args=(['medium', 'large'],)
   ).start()
   ```

## Integration with Transcription Service

The model cache integrates seamlessly with the transcription service:

```python
from app.services.model_cache_manager import get_model_cache_manager
from app.services.transcription_service import TranscriptionService

# Get cache manager
cache_manager = get_model_cache_manager()

# Ensure model is loaded before transcription
cache_manager.ensure_models_loaded(['base'])

# Transcription service will use cached model
transcription_service = TranscriptionService()
result = transcription_service.transcribe_audio(audio_file, model_size='base')
```

## Monitoring Dashboard

Create a simple monitoring dashboard:

```python
@app.route('/admin/cache-dashboard')
def cache_dashboard():
    cache_manager = get_model_cache_manager()
    stats = cache_manager.get_cache_stats()
    health = cache_manager.get_cache_health()
    
    return render_template('admin/cache_dashboard.html', 
                         stats=stats, health=health)
```

This comprehensive model caching system ensures that your Whisper models are always available for immediate use, providing the best possible performance for your Voice Transcriber application.
