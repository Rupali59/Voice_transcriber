# Troubleshooting Guide - Voice Transcriber

Common issues and solutions for the Voice Transcriber application.

## 🚨 Quick Diagnosis

### Health Check
```bash
# Check if the application is running
curl http://localhost:5001/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "active_jobs": 0
}
```

### System Status
```bash
# Check system resources
python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'Disk: {psutil.disk_usage(\"/\").percent}%')
"
```

## 🔧 Common Issues & Solutions

### 1. Application Won't Start

#### Problem: Port Already in Use
```
Error: [Errno 48] Address already in use
```

**Solutions:**
```bash
# Find process using port 5001
lsof -i :5001

# Kill the process
kill -9 <PID>

# Or use a different port
export PORT=5002
python app_main.py
```

#### Problem: Missing Dependencies
```
ModuleNotFoundError: No module named 'flask'
```

**Solutions:**
```bash
# Install dependencies
pip install -r requirements.txt

# Or create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Problem: Permission Denied
```
PermissionError: [Errno 13] Permission denied
```

**Solutions:**
```bash
# Check file permissions
ls -la app_main.py

# Fix permissions
chmod +x app_main.py

# Or run with sudo (not recommended for production)
sudo python app_main.py
```

### 2. File Upload Issues

#### Problem: File Too Large
```
Error: File size exceeds maximum allowed size
```

**Solutions:**
- **Reduce file size**: Compress audio or split into smaller files
- **Increase limit**: Set `MAX_CONTENT_LENGTH` environment variable
- **Use different format**: Convert to more efficient format (WAV, MP3)

#### Problem: Unsupported File Format
```
Error: Unsupported file format
```

**Solutions:**
- **Check format**: Ensure file is WAV, MP3, M4A, FLAC, or OGG
- **Convert file**: Use ffmpeg to convert to supported format
- **Check file extension**: Ensure file has correct extension

#### Problem: Upload Fails
```
Error: Upload failed
```

**Solutions:**
```bash
# Check disk space
df -h

# Check upload directory permissions
ls -la uploads/

# Fix permissions
chmod 755 uploads/
chown -R $USER:$USER uploads/
```

### 3. Transcription Issues

#### Problem: Transcription Fails
```
Error: Transcription failed
```

**Solutions:**
1. **Check audio file**:
   ```bash
   # Test audio file
   ffmpeg -i audio.wav -f null -
   ```

2. **Check system resources**:
   ```bash
   # Monitor resources during transcription
   top -p $(pgrep -f python)
   ```

3. **Check logs**:
   ```bash
   # View application logs
   tail -f logs/transcriber.log
   ```

4. **Try different model**:
   - Use smaller model (tiny, base) for testing
   - Check if model files are corrupted

#### Problem: Poor Transcription Quality
```
Transcription accuracy is low
```

**Solutions:**
- **Improve audio quality**: Use clear, noise-free recordings
- **Use larger model**: Try medium or large model
- **Check language settings**: Ensure correct language is selected
- **Preprocess audio**: Normalize volume and remove background noise

#### Problem: Slow Transcription
```
Transcription takes too long
```

**Solutions:**
- **Use smaller model**: Try tiny or base model
- **Reduce concurrent jobs**: Set `MAX_CONCURRENT_JOBS=1`
- **Check system resources**: Ensure adequate CPU and memory
- **Optimize audio**: Convert to 16kHz mono WAV

### 4. WebSocket Issues

#### Problem: Real-time Updates Not Working
```
No progress updates received
```

**Solutions:**
1. **Check WebSocket connection**:
   ```javascript
   // Test WebSocket connection
   const socket = io('http://localhost:5001');
   socket.on('connect', () => console.log('Connected'));
   socket.on('disconnect', () => console.log('Disconnected'));
   ```

2. **Check firewall settings**:
   ```bash
   # Check if port is accessible
   telnet localhost 5001
   ```

3. **Check browser console**:
   - Open browser developer tools
   - Look for WebSocket errors
   - Check network tab for connection issues

#### Problem: Connection Drops
```
WebSocket connection lost
```

**Solutions:**
- **Check network stability**: Ensure stable internet connection
- **Increase timeout**: Set longer connection timeout
- **Check server logs**: Look for connection errors
- **Restart application**: Sometimes helps with connection issues

### 5. Performance Issues

#### Problem: High Memory Usage
```
Application uses too much memory
```

**Solutions:**
```bash
# Monitor memory usage
ps aux | grep python

# Optimize memory settings
export MAX_CONCURRENT_JOBS=1
export WHISPER_MODEL_CACHE_SIZE=1
```

#### Problem: High CPU Usage
```
Application uses too much CPU
```

**Solutions:**
- **Limit concurrent jobs**: Set `MAX_CONCURRENT_JOBS=1`
- **Use smaller models**: Try tiny or base model
- **Check for infinite loops**: Review application logs
- **Optimize system**: Close other applications

#### Problem: Slow File Processing
```
File processing is slow
```

**Solutions:**
- **Use SSD storage**: Faster disk access
- **Optimize audio format**: Use 16kHz mono WAV
- **Check disk space**: Ensure adequate free space
- **Use faster network**: For remote file access

### 6. Docker Issues

#### Problem: Container Won't Start
```
Docker container fails to start
```

**Solutions:**
```bash
# Check Docker logs
docker logs <container_name>

# Check Docker status
docker ps -a

# Restart container
docker-compose down
docker-compose up -d
```

#### Problem: Volume Mount Issues
```
Files not accessible in container
```

**Solutions:**
```bash
# Check volume mounts
docker inspect <container_name>

# Fix permissions
sudo chown -R 1000:1000 uploads/
sudo chown -R 1000:1000 transcriptions/
```

#### Problem: Port Conflicts
```
Port already in use
```

**Solutions:**
```bash
# Check port usage
netstat -tulpn | grep :5001

# Use different port
docker-compose down
export PORT=5002
docker-compose up -d
```

## 🔍 Debugging Tools

### 1. Log Analysis

```bash
# View real-time logs
tail -f logs/transcriber.log

# Search for errors
grep -i error logs/transcriber.log

# Search for specific job
grep "job_id" logs/transcriber.log
```

### 2. System Monitoring

```bash
# Monitor system resources
htop

# Monitor disk usage
iotop

# Monitor network
nethogs
```

### 3. Application Debugging

```python
# Enable debug mode
export FLASK_DEBUG=True
export LOG_LEVEL=DEBUG

# Run with debugger
python -m pdb app_main.py
```

### 4. Network Debugging

```bash
# Test API endpoints
curl -v http://localhost:5001/health
curl -v http://localhost:5001/api/models

# Test file upload
curl -X POST http://localhost:5001/api/upload \
  -F "file=@test.wav" \
  -v
```

## 📊 Diagnostic Commands

### System Health Check
```bash
#!/bin/bash
echo "=== System Health Check ==="
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory Usage: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
echo "Disk Usage: $(df -h / | awk 'NR==2{printf "%s", $5}')"
echo "Load Average: $(uptime | awk -F'load average:' '{print $2}')"
echo "Active Jobs: $(curl -s http://localhost:5001/health | jq -r '.active_jobs')"
```

### Application Status Check
```bash
#!/bin/bash
echo "=== Application Status ==="
echo "Process Status: $(pgrep -f app_main.py > /dev/null && echo "Running" || echo "Not Running")"
echo "Port Status: $(netstat -tulpn | grep :5001 > /dev/null && echo "Open" || echo "Closed")"
echo "Health Check: $(curl -s http://localhost:5001/health | jq -r '.status')"
echo "API Models: $(curl -s http://localhost:5001/api/models | jq -r '.models | length')"
```

## 🆘 Emergency Recovery

### 1. Application Won't Start
```bash
# Kill all Python processes
pkill -f python

# Clean up temporary files
rm -rf uploads/*
rm -rf transcriptions/*
rm -rf logs/*.log

# Restart application
python app_main.py
```

### 2. Out of Disk Space
```bash
# Clean up old files
find uploads/ -type f -mtime +7 -delete
find transcriptions/ -type f -mtime +7 -delete
find logs/ -name "*.log" -mtime +30 -delete

# Check disk usage
df -h
```

### 3. Memory Issues
```bash
# Clear system cache
sudo sync
sudo echo 3 > /proc/sys/vm/drop_caches

# Restart application
pkill -f python
python app_main.py
```

## 📞 Getting Help

### 1. Check Documentation
- Review [User Guide](USER_GUIDE.md)
- Check [Technical Reference](TECHNICAL_REFERENCE.md)
- See [Performance Guide](PERFORMANCE_GUIDE.md)

### 2. Collect Information
When reporting issues, include:
- **Error messages**: Full error text
- **System information**: OS, Python version, hardware
- **Application logs**: Relevant log entries
- **Steps to reproduce**: How to trigger the issue

### 3. Create Issue Report
```markdown
## Issue Description
Brief description of the problem

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## System Information
- OS: [e.g., Ubuntu 20.04]
- Python: [e.g., 3.9.7]
- Application Version: [e.g., 1.0.0]

## Logs
```
Paste relevant log entries here
```

## Additional Context
Any other relevant information
```

---

**Still having issues?** Check the [Performance Guide](PERFORMANCE_GUIDE.md) or [Technical Reference](TECHNICAL_REFERENCE.md) for more detailed information.
