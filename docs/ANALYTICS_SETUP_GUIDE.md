# Analytics Setup Guide for Voice Transcriber

This guide provides comprehensive instructions for setting up Google Analytics 4 and Hotjar tracking for the Voice Transcriber application.

## Overview

The analytics system provides comprehensive tracking of user interactions, performance metrics, and user behavior patterns. It includes:

- **Google Analytics 4**: Event tracking, user behavior analysis, conversion tracking
- **Hotjar**: Heatmaps, session recordings, user feedback, behavior analytics
- **Custom Analytics Service**: Server-side event tracking and session management

## Environment Configuration

### Required Environment Variables

Add the following variables to your `.env` file:

```bash
# Analytics Configuration
GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX  # Your GA4 Measurement ID
HOTJAR_SITE_ID=1234567            # Your Hotjar Site ID

# Analytics Settings
ENABLE_ANALYTICS=true
ENABLE_GOOGLE_ANALYTICS=true
ENABLE_HOTJAR=true
ANALYTICS_DEBUG=false  # Set to true for development testing
```

### Getting Your Tracking IDs

#### Google Analytics 4
1. Go to [Google Analytics](https://analytics.google.com/)
2. Create a new GA4 property or use existing one
3. Go to Admin → Data Streams → Web
4. Copy your Measurement ID (format: G-XXXXXXXXXX)

#### Hotjar
1. Go to [Hotjar](https://www.hotjar.com/)
2. Create a new site or use existing one
3. Go to Settings → Tracking Code
4. Copy your Site ID (numeric value)

## Features

### Automatic Event Tracking

The system automatically tracks:

#### File Operations
- File uploads (drag & drop, browse)
- File downloads
- File type and size information

#### Transcription Process
- Transcription start with parameters (model, language, temperature, speaker diarization)
- Progress milestones (25%, 50%, 75%, 90%, 100%)
- Completion with processing time and transcript length
- Error tracking with error types and messages

#### User Interactions
- Form field changes (model selection, language, temperature, speaker diarization)
- Button clicks (transcribe, download, view transcript, refresh, cancel)
- Page visibility changes
- Scroll depth tracking (25%, 50%, 75%, 90%, 100%)
- Time on page milestones (30s, 1m, 2m, 5m, 10m)

#### Performance Metrics
- Page load times
- Transcription processing times
- File upload/download times
- Custom performance metrics

### Custom Event Tracking

You can track custom events from JavaScript:

```javascript
// Track custom event
window.analyticsTracker.trackEvent('custom_event', {
    custom_parameter: 'value',
    another_param: 123
});

// Track performance metric
window.analyticsTracker.trackPerformance('custom_metric', 150, 'ms');

// Set user properties
window.analyticsTracker.setUserProperty('user_type', 'premium');
```

### Server-Side Tracking

The analytics service provides server-side tracking for:

```python
from app.services.analytics_service import analytics_service

# Track file upload
analytics_service.track_file_upload('audio.mp3', 1024000, 'audio/mpeg')

# Track transcription start
analytics_service.track_transcription_start(
    model='base',
    language='en',
    speaker_diarization=True,
    temperature=0.2,
    file_size=1024000
)

# Track completion
analytics_service.track_transcription_complete(
    job_id='job_123',
    model='base',
    language='en',
    processing_time=45.2,
    file_size=1024000,
    transcript_length=1500,
    success=True
)
```

## Analytics Dashboard

### Google Analytics 4 Events

Key events to monitor in GA4:

1. **file_upload**: File upload events with file details
2. **transcription_start**: Transcription initiation with parameters
3. **transcription_complete**: Successful completions with metrics
4. **transcription_error**: Error tracking for debugging
5. **file_download**: Download tracking for conversion analysis
6. **user_interaction**: General user interaction patterns
7. **performance_metric**: Performance monitoring
8. **page_view**: Page navigation tracking
9. **scroll_depth**: User engagement measurement
10. **time_on_page**: Session duration analysis

### Hotjar Insights

Monitor in Hotjar:

1. **Heatmaps**: See where users click and scroll
2. **Session Recordings**: Watch user behavior patterns
3. **Feedback**: Collect user feedback on the interface
4. **Surveys**: Gather user satisfaction data
5. **Funnels**: Track conversion paths

## API Endpoints

### Analytics Configuration
```
GET /api/analytics/config
```
Returns analytics configuration for frontend initialization.

### Event Tracking
```
POST /api/analytics/track
```
Track custom events from frontend.

### Analytics Summary
```
GET /api/analytics/summary
```
Get analytics summary for current session.

### User Properties
```
POST /api/analytics/user-properties
```
Set user properties for analytics.

## Privacy and Compliance

### Data Collection
- IP addresses are collected for session tracking
- User interactions are logged with timestamps
- File information (name, size, type) is tracked
- No personal information is collected

### GDPR Compliance
- Analytics can be disabled via environment variables
- Users can opt-out through browser settings
- Data retention follows standard analytics practices

### Cookie Usage
- Google Analytics uses cookies for session tracking
- Hotjar uses cookies for behavior tracking
- No custom cookies are set by the application

## Debugging and Testing

### Enable Debug Mode
Set `ANALYTICS_DEBUG=true` in your environment to see detailed logging.

### Browser Console
Check browser console for analytics events when debug mode is enabled.

### Network Tab
Monitor network requests to verify events are being sent to analytics services.

## Performance Considerations

### Optimization Features
- Events are batched and sent asynchronously
- Analytics scripts load asynchronously
- Minimal impact on page load times
- Server-side tracking is non-blocking

### Resource Usage
- Analytics scripts add ~50KB to page load
- Server-side tracking uses minimal memory
- Event storage is limited to 50 events per session

## Troubleshooting

### Common Issues

1. **Analytics not loading**
   - Check environment variables are set correctly
   - Verify tracking IDs are valid
   - Check browser console for errors

2. **Events not appearing**
   - Ensure analytics is enabled in environment
   - Check network requests in browser dev tools
   - Verify event names match expected format

3. **Performance impact**
   - Analytics scripts load asynchronously
   - Server-side tracking is optimized
   - Consider disabling in development if needed

### Debug Commands

```bash
# Check analytics configuration
curl http://localhost:5001/api/analytics/config

# Get analytics summary
curl http://localhost:5001/api/analytics/summary

# Test event tracking
curl -X POST http://localhost:5001/api/analytics/track \
  -H "Content-Type: application/json" \
  -d '{"event_name": "test_event", "test_param": "value"}'
```

## Advanced Configuration

### Custom Event Parameters
You can add custom parameters to any event:

```javascript
window.analyticsTracker.trackEvent('custom_event', {
    custom_param_1: 'value1',
    custom_param_2: 123,
    custom_param_3: true
});
```

### User Segmentation
Set user properties for segmentation:

```javascript
window.analyticsTracker.setUserProperty('user_type', 'premium');
window.analyticsTracker.setUserProperty('subscription_level', 'pro');
```

### Performance Monitoring
Track custom performance metrics:

```javascript
// Track page load time
window.analyticsTracker.trackPerformance('page_load_time', performance.now(), 'ms');

// Track API response time
window.analyticsTracker.trackPerformance('api_response_time', 250, 'ms');
```

## Maintenance

### Regular Tasks
1. Monitor analytics data quality
2. Review error tracking for issues
3. Update tracking parameters as needed
4. Clean up old analytics data

### Updates
- Analytics service is automatically updated with application updates
- Tracking parameters can be modified without code changes
- New events can be added through configuration

## Support

For issues with analytics setup:
1. Check the troubleshooting section
2. Review environment configuration
3. Verify tracking IDs are correct
4. Check browser console for errors
5. Monitor server logs for analytics errors

The analytics system is designed to be robust and provide comprehensive insights into user behavior while maintaining good performance and privacy standards.
