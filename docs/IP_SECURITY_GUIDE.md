# IP-based File Management & DoS Protection Guide

## Overview

The Voice Transcriber now includes comprehensive IP-based file management with DoS protection. This system tracks files by IP address and implements multiple layers of protection against abuse.

## Features

### 🛡️ DoS Protection
- **Rate Limiting**: Maximum requests per time window per IP
- **File Quotas**: Limits on total files and storage per IP
- **24-hour Limits**: Daily limits to prevent sustained abuse
- **Automatic Blocking**: IPs that exceed limits are automatically blocked
- **Resource Monitoring**: Real-time tracking of IP usage

### 📁 IP-based File Management
- **Isolated Storage**: Each IP's files are stored in separate directories
- **File Tracking**: Complete audit trail of all uploaded files
- **Access Control**: IPs can only access their own files
- **Automatic Cleanup**: Old files are automatically removed
- **Quota Management**: Real-time quota tracking and enforcement

## Configuration

### Environment Variables

```bash
# IP-based DoS Protection Configuration
MAX_FILES_PER_IP=50            # Maximum files per IP address
MAX_SIZE_MB_PER_IP=1000        # Maximum storage per IP (1GB)
MAX_FILES_24H_PER_IP=20        # Maximum files per 24 hours per IP
MAX_SIZE_24H_MB_PER_IP=500     # Maximum storage per 24 hours per IP (500MB)
RATE_LIMIT_WINDOW_SECONDS=3600 # Rate limit window (1 hour)
MAX_REQUESTS_PER_WINDOW=100    # Maximum requests per window per IP
IP_CLEANUP_INTERVAL_HOURS=24   # How often to cleanup old files
IP_FILE_RETENTION_HOURS=72     # How long to keep files (3 days)
```

### Default Limits

| Setting | Default Value | Description |
|---------|---------------|-------------|
| Max Files per IP | 50 | Total files an IP can upload |
| Max Size per IP | 1000 MB | Total storage per IP |
| Max Files 24h | 20 | Files per 24-hour period |
| Max Size 24h | 500 MB | Storage per 24-hour period |
| Rate Limit Window | 3600 seconds | Time window for rate limiting |
| Max Requests | 100 | Requests per window |
| File Retention | 72 hours | How long files are kept |

## API Endpoints

### User Endpoints (IP-based)

#### Get My Files
```http
GET /api/my-files
```
Returns all files uploaded by the current IP address.

#### Get My Quota
```http
GET /api/my-quota
```
Returns quota information for the current IP address.

#### Delete My File
```http
DELETE /api/my-files/{filename}
```
Deletes a specific file uploaded by the current IP address.

#### Cleanup My Files
```http
POST /api/my-files/cleanup
```
Deletes all files for the current IP address.

### Admin Endpoints

#### IP Dashboard
```http
GET /admin/ip/
```
Web interface for managing IP-based file storage.

#### Get IP Statistics
```http
GET /admin/ip/stats
```
Returns overall statistics about IP usage.

#### Get IP Details
```http
GET /admin/ip/ip/{ip_address}
```
Returns detailed information about a specific IP.

#### Block IP
```http
POST /admin/ip/ip/{ip_address}/block
Content-Type: application/json

{
  "reason": "Abuse detected",
  "hours": 24
}
```

#### Unblock IP
```http
POST /admin/ip/ip/{ip_address}/unblock
```

#### Cleanup IP Files
```http
POST /admin/ip/ip/{ip_address}/cleanup
```

## File Storage Structure

```
uploads/
├── .ip_quotas.json          # IP quota tracking data
├── .ip_files.json           # IP file records
├── ip_a1b2c3d4e5f6g7h8/    # Hashed IP directory
│   ├── 1640995200_a1b2c3d4_file1.wav
│   ├── 1640995300_a1b2c3d4_file2.mp3
│   └── ...
├── ip_f9e8d7c6b5a4938271/   # Another IP directory
│   ├── 1640995400_f9e8d7c6_file1.wav
│   └── ...
└── ...
```

## Security Features

### 1. IP Isolation
- Each IP's files are stored in separate directories
- IP addresses are hashed for security
- No cross-IP file access possible

### 2. Rate Limiting
- Sliding window rate limiting
- Configurable request limits
- Automatic IP blocking for violations

### 3. Quota Management
- Multiple quota types (total, 24-hour)
- Real-time quota tracking
- Automatic enforcement

### 4. File Validation
- File type validation
- File size limits
- Secure filename generation

### 5. Automatic Cleanup
- Background cleanup of old files
- Configurable retention periods
- Resource optimization

## Monitoring & Administration

### IP Dashboard
Access the admin dashboard at `/admin/ip/` to:
- View overall statistics
- Monitor top IPs by usage
- Manage blocked IPs
- Cleanup files manually
- View detailed IP information

### Logging
All IP-based activities are logged:
- File uploads and deletions
- Quota violations
- IP blocking/unblocking
- Cleanup operations

## Best Practices

### 1. Configuration
- Set appropriate limits based on your use case
- Monitor usage patterns and adjust limits
- Use strong secret keys for production

### 2. Monitoring
- Regularly check the IP dashboard
- Monitor for abuse patterns
- Review blocked IPs periodically

### 3. Maintenance
- Regular cleanup of old files
- Monitor disk usage
- Review and adjust quotas as needed

### 4. Security
- Use HTTPS in production
- Implement proper authentication
- Monitor for suspicious activity
- Regular security audits

## Troubleshooting

### Common Issues

#### IP Blocked
If an IP is blocked:
1. Check the admin dashboard for the reason
2. Review the IP's usage patterns
3. Unblock if appropriate
4. Adjust limits if needed

#### Quota Exceeded
If quotas are too restrictive:
1. Review current usage patterns
2. Adjust environment variables
3. Consider different limits for different user types

#### File Not Found
If files are missing:
1. Check if they were cleaned up due to age
2. Verify the IP has access to the file
3. Check file retention settings

### Performance Considerations

- Large numbers of IPs may impact performance
- Consider database storage for high-traffic scenarios
- Monitor disk I/O for cleanup operations
- Adjust cleanup intervals based on usage

## Migration from Old System

If migrating from the old file system:

1. **Backup existing files**: Ensure all important files are backed up
2. **Update configuration**: Set appropriate limits for your use case
3. **Test thoroughly**: Verify the new system works as expected
4. **Monitor closely**: Watch for any issues during the transition
5. **Clean up old files**: Remove files from the old system after migration

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Review the IP dashboard for usage patterns
3. Verify configuration settings
4. Contact support with specific error details
