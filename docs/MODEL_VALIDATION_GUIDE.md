# Model Validation Guide for EchoScribe

This guide explains how to ensure that Whisper models are correctly loaded, trained, and functioning properly in your EchoScribe Voice Transcriber application.

## Overview

The model validation system provides comprehensive testing to ensure:
- **Model Loading**: Models load correctly without errors
- **Functionality**: Basic transcription functionality works
- **Performance**: Models meet performance requirements
- **Quality**: Transcription quality is acceptable
- **Memory Usage**: Memory consumption is within limits
- **Health Monitoring**: Continuous monitoring of model health

## Quick Start

### 1. Basic Model Validation

**Command Line:**
```bash
# Validate specific models
python scripts/validate_models.py --models base small

# Quick validation of loaded models
python scripts/validate_models.py --quick --cache-models

# Verbose output
python scripts/validate_models.py --models base small --verbose
```

**API:**
```bash
# Health check
curl http://localhost:5001/api/validate/models/health-check

# Validate single model
curl -X POST http://localhost:5001/api/validate/models/base

# Quick validation
curl -X POST http://localhost:5001/api/validate/models/quick
```

### 2. Python API Usage

```python
from app.services.model_validator import get_model_validator
from app.services.model_cache_manager import get_model_cache_manager

# Get validator and cache manager
validator = get_model_validator()
cache_manager = get_model_cache_manager()

# Validate a specific model
model = cache_manager.get_model('base')
result = validator.validate_model('base', model)

print(f"Model status: {result['status']}")
print(f"Overall score: {result['overall_score']:.2f}")
```

## Validation Tests

### 1. Model Loading Test

**Purpose**: Ensures models load correctly and have required methods.

**What it checks:**
- Model loads without errors
- Model has required methods (`transcribe`, `encode`, `decode`)
- Model is on correct device (CPU/GPU)
- Model parameters are accessible

**Example output:**
```json
{
  "name": "Model Loading",
  "passed": true,
  "score": 1.0,
  "details": {
    "device": "cuda:0",
    "model_size": "base",
    "parameters": 74000000,
    "methods_available": ["transcribe", "encode", "decode"]
  }
}
```

### 2. Basic Functionality Test

**Purpose**: Tests basic transcription functionality.

**What it checks:**
- Model can process audio
- `transcribe` method returns valid result
- Result has expected structure
- Processing completes without errors

**Example output:**
```json
{
  "name": "Basic Functionality",
  "passed": true,
  "score": 1.0,
  "details": {
    "transcribe_time": 0.45,
    "result_type": "dict",
    "has_text": true,
    "text_length": 12
  }
}
```

### 3. Audio Processing Test

**Purpose**: Tests audio processing with different sample types.

**What it checks:**
- Handles different audio samples
- Processes audio without errors
- Returns consistent results
- Handles various audio lengths

**Example output:**
```json
{
  "name": "Audio Processing",
  "passed": true,
  "score": 1.0,
  "details": {
    "sine_wave_process_time": 0.42,
    "sine_wave_text_length": 8,
    "complex_wave_process_time": 0.38,
    "complex_wave_text_length": 15
  }
}
```

### 4. Transcription Quality Test

**Purpose**: Assesses transcription quality and accuracy.

**What it checks:**
- Produces reasonable output
- Output length is appropriate
- No obvious artifacts
- Contains readable text

**Example output:**
```json
{
  "name": "Transcription Quality",
  "passed": true,
  "score": 0.8,
  "details": {
    "has_output": true,
    "reasonable_length": true,
    "no_artifacts": true,
    "has_letters": true,
    "transcribed_text": "test audio",
    "quality_score": 0.8
  }
}
```

### 5. Performance Metrics Test

**Purpose**: Measures performance characteristics.

**What it checks:**
- Processing speed (real-time factor)
- Response time
- Throughput (words per second)
- Timeout compliance

**Example output:**
```json
{
  "name": "Performance Metrics",
  "passed": true,
  "score": 0.9,
  "details": {
    "total_time": 0.45,
    "audio_duration": 1.0,
    "real_time_factor": 0.45,
    "words_per_second": 2.67,
    "speed_acceptable": true,
    "within_timeout": true,
    "produces_output": true
  }
}
```

### 6. Memory Usage Test

**Purpose**: Monitors memory consumption.

**What it checks:**
- RAM usage is reasonable
- Memory percentage is acceptable
- Model memory is calculated
- No memory leaks

**Example output:**
```json
{
  "name": "Memory Usage",
  "passed": true,
  "score": 0.85,
  "details": {
    "rss_mb": 1024.5,
    "vms_mb": 2048.2,
    "model_memory_mb": 74.0,
    "memory_percent": 45.2,
    "memory_reasonable": true,
    "memory_percent_ok": true,
    "model_loaded": true
  }
}
```

## API Endpoints

### Health Check
```bash
GET /api/validate/models/health-check
```

**Response:**
```json
{
  "success": true,
  "overall_status": "healthy",
  "cache_health": {
    "status": "healthy",
    "loaded_models": ["base", "small"],
    "priority_coverage": 100
  },
  "model_health": {
    "base": {
      "status": "healthy",
      "can_transcribe": true
    },
    "small": {
      "status": "healthy",
      "can_transcribe": true
    }
  },
  "healthy_count": 2,
  "total_count": 2
}
```

### Validate Single Model
```bash
POST /api/validate/models/{model_size}
```

**Response:**
```json
{
  "success": true,
  "model_size": "base",
  "validation_result": {
    "status": "passed",
    "overall_score": 0.92,
    "tests": {
      "model_loading": { "passed": true, "score": 1.0 },
      "basic_functionality": { "passed": true, "score": 1.0 },
      "audio_processing": { "passed": true, "score": 1.0 },
      "transcription_quality": { "passed": true, "score": 0.8 },
      "performance": { "passed": true, "score": 0.9 },
      "memory_usage": { "passed": true, "score": 0.85 }
    }
  }
}
```

### Validate Multiple Models
```bash
POST /api/validate/models/batch
Content-Type: application/json

{
  "models": ["base", "small", "medium"]
}
```

### Quick Validation
```bash
POST /api/validate/models/quick
```

## Configuration

### Environment Variables

```bash
# Model validation configuration
MODEL_VALIDATION_ENABLED=true
MODEL_VALIDATION_INTERVAL=3600  # 1 hour
MODEL_VALIDATION_TIMEOUT=60     # 60 seconds
MODEL_VALIDATION_THRESHOLD=0.7  # 70% score threshold
```

### Validation Settings

```python
# In model_validator.py
validation_config = {
    'test_duration': 5.0,           # Test audio duration
    'sample_rate': 16000,           # Audio sample rate
    'max_validation_time': 60,      # Max validation time
    'min_accuracy_threshold': 0.7,  # Minimum score threshold
    'enable_gpu': True              # Enable GPU testing
}
```

## Monitoring and Alerts

### 1. Continuous Monitoring

**Setup:**
```python
# Add to your application startup
from app.services.model_validator import get_model_validator

def start_model_monitoring():
    validator = get_model_validator()
    
    # Schedule periodic validation
    import threading
    import time
    
    def monitor_models():
        while True:
            time.sleep(3600)  # Check every hour
            validator.validate_all_models(['base', 'small'])
    
    thread = threading.Thread(target=monitor_models, daemon=True)
    thread.start()
```

### 2. Health Check Integration

**Add to health endpoint:**
```python
@app.route('/health')
def health_check():
    # ... existing health checks ...
    
    # Add model validation
    try:
        from app.services.model_validator import get_model_validator
        validator = get_model_validator()
        
        # Quick health check
        health_status = validator.model_health_check()
        
        return jsonify({
            'status': 'healthy',
            'models': health_status
        })
    except Exception as e:
        return jsonify({
            'status': 'degraded',
            'models': {'error': str(e)}
        }), 503
```

### 3. Alerting

**Setup alerts for model issues:**
```python
def check_model_health():
    validator = get_model_validator()
    cache_manager = get_model_cache_manager()
    
    # Get health status
    health = validator.model_health_check()
    
    # Check for issues
    if health['overall_status'] != 'healthy':
        # Send alert
        send_alert(f"Model health degraded: {health}")
    
    # Check individual models
    for model_size, model_health in health['model_health'].items():
        if model_health['status'] != 'healthy':
            send_alert(f"Model {model_size} is unhealthy: {model_health}")
```

## Troubleshooting

### Common Issues

**1. Model Loading Failures**
```bash
# Check if Whisper is installed
python -c "import whisper; print('Whisper installed')"

# Check model availability
python -c "import whisper; print(whisper.available_models())"

# Test model loading
python -c "import whisper; model = whisper.load_model('base'); print('Model loaded')"
```

**2. GPU Issues**
```bash
# Check CUDA availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Check GPU memory
nvidia-smi

# Test with CPU only
export ENABLE_GPU_ACCELERATION=false
python scripts/validate_models.py --models base
```

**3. Memory Issues**
```bash
# Check memory usage
free -h

# Monitor during validation
python scripts/validate_models.py --models base --verbose

# Check specific model memory
curl http://localhost:5001/api/cache/models/base/status
```

**4. Performance Issues**
```bash
# Check system resources
htop

# Test with smaller models
python scripts/validate_models.py --models tiny

# Check validation timeout
export MODEL_VALIDATION_TIMEOUT=120
python scripts/validate_models.py --models base
```

### Debug Commands

**1. Verbose Validation**
```bash
python scripts/validate_models.py --models base small --verbose
```

**2. Quick Health Check**
```bash
curl -v http://localhost:5001/api/validate/models/health-check
```

**3. Model Status Check**
```bash
curl http://localhost:5001/api/cache/models
```

**4. Individual Model Validation**
```bash
curl -X POST http://localhost:5001/api/validate/models/base
```

## Best Practices

### 1. Regular Validation

**Schedule periodic validation:**
```bash
# Add to crontab
0 */6 * * * cd /path/to/echoscribe && python scripts/validate_models.py --quick
```

**Monitor validation results:**
```python
# Check validation results
results = validator.get_validation_results()
for validation_id, result in results.items():
    if result['status'] != 'passed':
        logger.warning(f"Model validation failed: {result}")
```

### 2. Pre-deployment Validation

**Validate before deployment:**
```bash
# Full validation before deployment
python scripts/validate_models.py --models base small medium --output validation_report.json

# Check validation results
if [ $? -eq 0 ]; then
    echo "All models validated successfully"
    # Proceed with deployment
else
    echo "Model validation failed"
    exit 1
fi
```

### 3. Performance Monitoring

**Monitor model performance:**
```python
# Track validation metrics
def track_validation_metrics():
    results = validator.get_validation_results()
    
    for validation_id, result in results.items():
        metrics = {
            'model_size': result['model_size'],
            'status': result['status'],
            'score': result['overall_score'],
            'duration': result['duration']
        }
        
        # Send to monitoring system
        send_metrics(metrics)
```

### 4. Automated Recovery

**Auto-recovery from model issues:**
```python
def auto_recover_models():
    health = validator.model_health_check()
    
    for model_size, model_health in health['model_health'].items():
        if model_health['status'] != 'healthy':
            logger.warning(f"Model {model_size} is unhealthy, attempting recovery")
            
            # Force reload model
            cache_manager.force_reload_model(model_size)
            
            # Re-validate
            result = validator.validate_model(model_size)
            if result['status'] == 'passed':
                logger.info(f"Model {model_size} recovered successfully")
            else:
                logger.error(f"Model {model_size} recovery failed")
```

## Integration with CI/CD

### 1. Pre-commit Validation

**Add to pre-commit hooks:**
```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Validating models before commit..."
python scripts/validate_models.py --models base --quick

if [ $? -eq 0 ]; then
    echo "Model validation passed"
    exit 0
else
    echo "Model validation failed"
    exit 1
fi
```

### 2. CI Pipeline Integration

**Add to CI pipeline:**
```yaml
# .github/workflows/model-validation.yml
name: Model Validation

on: [push, pull_request]

jobs:
  validate-models:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Validate models
        run: |
          python scripts/validate_models.py --models base small --output validation_report.json
      - name: Upload validation report
        uses: actions/upload-artifact@v2
        with:
          name: validation-report
          path: validation_report.json
```

This comprehensive model validation system ensures that your Whisper models are correctly loaded, trained, and functioning properly, providing confidence in your Voice Transcriber application's reliability and performance.
