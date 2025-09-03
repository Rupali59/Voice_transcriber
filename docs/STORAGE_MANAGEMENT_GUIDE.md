# Advanced Storage Management Guide

## Overview

The Voice Transcriber now includes a comprehensive storage management system that automatically handles file cleanup, disk space monitoring, and storage optimization. This system works alongside the IP-based file management to ensure efficient storage usage and prevent disk space issues.

## 🗂️ **Automatic File Cleanup System**

### **Current Implementation**
The system already includes automatic cleanup with these features:

#### **1. IP-based Cleanup (Existing)**
- **Retention Period**: Files automatically deleted after 72 hours (3 days)
- **Cleanup Frequency**: Runs every 24 hours
- **Background Thread**: Continuous operation without blocking

#### **2. Advanced Storage Management (New)**
- **Multi-policy Cleanup**: Age, size, and disk usage based cleanup
- **Smart Cleanup**: Intelligent cleanup based on multiple factors
- **Emergency Cleanup**: Aggressive cleanup when disk usage is critical
- **Real-time Monitoring**: Continuous disk space and usage monitoring

## 🔧 **Configuration Options**

### **Environment Variables**

```bash
# IP-based File Retention (Existing)
IP_FILE_RETENTION_HOURS=72     # How long to keep files (3 days default)
IP_CLEANUP_INTERVAL_HOURS=24   # How often to cleanup (24 hours default)

# Advanced Storage Management (New)
MAX_TOTAL_STORAGE_MB=10000     # Maximum total storage (10GB default)
MAX_DISK_USAGE_PERCENT=80.0    # Maximum disk usage percentage (80% default)
STORAGE_CLEANUP_INTERVAL_HOURS=6  # Storage cleanup frequency (6 hours default)
EMERGENCY_CLEANUP_THRESHOLD=90.0  # Emergency cleanup threshold (90% default)
PRIORITY_CLEANUP_AGE_HOURS=24     # Priority cleanup age (24 hours default)
```

### **Default Settings**

| Setting | Default Value | Description |
|---------|---------------|-------------|
| File Retention | 72 hours | How long files are kept |
| Total Storage Limit | 10GB | Maximum total storage usage |
| Disk Usage Limit | 80% | Maximum disk usage percentage |
| Cleanup Frequency | 6 hours | How often storage cleanup runs |
| Emergency Threshold | 90% | When to trigger emergency cleanup |
| Priority Cleanup Age | 24 hours | Age for priority cleanup |

## 🧠 **Smart Cleanup Policies**

### **1. Age-based Cleanup**
- Removes files older than the specified age
- Configurable retention period
- Preserves recent files

### **2. Size-based Cleanup**
- Reduces total storage to target size
- Removes oldest files first
- Maintains storage limits

### **3. Disk Usage Cleanup**
- Monitors actual disk usage
- Triggers cleanup when usage exceeds limits
- Prevents disk space exhaustion

### **4. Emergency Cleanup**
- Aggressive cleanup when disk usage is critical (>90%)
- Removes files older than 24 hours first
- Then removes files older than 6 hours if needed
- Ensures system stability

## 📊 **Storage Monitoring**

### **Real-time Statistics**
- Total storage usage (MB)
- Total file count
- Disk usage percentage
- Available space
- File age statistics (oldest, newest, average)
- Average file size

### **Health Monitoring**
- Storage health status (healthy, warning, critical)
- Policy compliance tracking
- Cleanup history and logs
- Performance metrics

## 🌐 **API Endpoints**

### **Storage Statistics**
```http
GET /admin/ip/storage/stats
```
Returns comprehensive storage statistics.

### **Storage Health**
```http
GET /admin/ip/storage/health
```
Returns storage health information and status.

### **Smart Cleanup**
```http
POST /admin/ip/storage/cleanup
```
Triggers intelligent cleanup based on all policies.

### **Age-based Cleanup**
```http
POST /admin/ip/storage/cleanup/age
Content-Type: application/json

{
  "max_age_hours": 48
}
```

### **Size-based Cleanup**
```http
POST /admin/ip/storage/cleanup/size
Content-Type: application/json

{
  "target_size_mb": 5000
}
```

### **Emergency Cleanup**
```http
POST /admin/ip/storage/cleanup/emergency
```
Triggers emergency cleanup for critical disk usage.

### **Cleanup Logs**
```http
GET /admin/ip/storage/logs?limit=50
```
Returns recent cleanup activity logs.

## 🔄 **How It Works**

### **1. Background Monitoring**
- Continuous disk space monitoring
- Real-time usage tracking
- Automatic policy enforcement

### **2. Cleanup Triggers**
- **Scheduled**: Regular cleanup every 6 hours
- **Threshold-based**: When limits are exceeded
- **Emergency**: When disk usage is critical
- **Manual**: Admin-triggered cleanup

### **3. Cleanup Process**
1. **Assessment**: Check current storage status
2. **Policy Evaluation**: Determine which policies apply
3. **File Selection**: Choose files for removal (oldest first)
4. **Cleanup Execution**: Remove selected files
5. **Logging**: Record cleanup actions
6. **Verification**: Confirm cleanup results

### **4. File Selection Priority**
1. **Age**: Oldest files removed first
2. **Access**: Less recently accessed files prioritized
3. **Size**: Larger files may be prioritized in emergency situations
4. **IP Isolation**: Each IP's files are managed independently

## 📈 **Storage Health Levels**

### **🟢 Healthy**
- Disk usage < 80%
- Total storage < 10GB
- All policies within limits
- Normal operation

### **🟡 Warning**
- Disk usage 80-90%
- Total storage approaching limits
- Some policies near thresholds
- Monitoring increased

### **🔴 Critical**
- Disk usage > 90%
- Emergency cleanup triggered
- Aggressive file removal
- Immediate action required

## 🛠️ **Best Practices**

### **1. Configuration**
- Set appropriate limits based on your disk capacity
- Monitor usage patterns and adjust accordingly
- Use conservative limits for production environments
- Consider peak usage periods

### **2. Monitoring**
- Regularly check storage health dashboard
- Monitor cleanup logs for patterns
- Set up alerts for critical thresholds
- Review storage growth trends

### **3. Maintenance**
- Perform manual cleanup during low-usage periods
- Review and adjust policies based on usage patterns
- Monitor disk space trends
- Plan for storage expansion if needed

### **4. Emergency Procedures**
- Monitor for critical disk usage alerts
- Have emergency cleanup procedures ready
- Consider temporary storage expansion
- Document cleanup procedures

## 📋 **Storage Management Checklist**

### **Daily**
- [ ] Check storage health dashboard
- [ ] Review cleanup logs
- [ ] Monitor disk usage trends

### **Weekly**
- [ ] Review storage policies
- [ ] Analyze usage patterns
- [ ] Check for storage anomalies
- [ ] Verify cleanup effectiveness

### **Monthly**
- [ ] Adjust storage limits if needed
- [ ] Review and optimize policies
- [ ] Plan for storage expansion
- [ ] Document storage patterns

## 🚨 **Troubleshooting**

### **High Disk Usage**
1. Check storage health dashboard
2. Review recent cleanup logs
3. Trigger manual cleanup
4. Consider emergency cleanup
5. Adjust storage limits if needed

### **Cleanup Not Working**
1. Verify configuration settings
2. Check cleanup logs for errors
3. Ensure proper file permissions
4. Restart the application if needed

### **Storage Growth Issues**
1. Analyze usage patterns
2. Review IP-based quotas
3. Adjust retention periods
4. Consider more aggressive cleanup

### **Performance Issues**
1. Monitor cleanup frequency
2. Check disk I/O during cleanup
3. Adjust cleanup intervals
4. Consider off-peak cleanup scheduling

## 📊 **Monitoring Dashboard**

The admin dashboard at `/admin/ip/` now includes:

- **Storage Statistics**: Real-time storage usage
- **Health Status**: Current storage health level
- **Cleanup History**: Recent cleanup activities
- **Policy Status**: Current policy compliance
- **Manual Controls**: Trigger cleanup operations

## 🔮 **Future Enhancements**

Potential future improvements:

1. **Predictive Cleanup**: ML-based cleanup predictions
2. **Storage Tiering**: Move old files to cheaper storage
3. **Compression**: Compress old files to save space
4. **Backup Integration**: Backup before cleanup
5. **Analytics**: Advanced storage analytics and reporting

## 📞 **Support**

For storage management issues:

1. Check the storage health dashboard
2. Review cleanup logs for errors
3. Verify configuration settings
4. Test manual cleanup operations
5. Contact support with specific error details

The storage management system is designed to be self-maintaining, but regular monitoring and occasional manual intervention may be needed for optimal performance.
