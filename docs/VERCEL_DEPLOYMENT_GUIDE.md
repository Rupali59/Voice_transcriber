# Vercel Deployment Guide for EchoScribe

This guide explains how to deploy your EchoScribe Voice Transcriber application on Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Vercel CLI** (optional): Install with `npm i -g vercel`

## Quick Deployment

### Method 1: Vercel Dashboard (Recommended)

1. **Connect Repository**:
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository
   - Select your repository

2. **Configure Project**:
   - **Framework Preset**: Flask
   - **Root Directory**: `./` (root of your repository)
   - **Build Command**: Leave empty (Vercel will auto-detect)
   - **Output Directory**: Leave empty

3. **Environment Variables**:
   Add these environment variables in the Vercel dashboard:
   ```
   FLASK_ENV=production
   PYTHONPATH=.
   ENABLE_GPU_ACCELERATION=false
   WHISPER_MODEL_CACHE_SIZE=2
   MODEL_IDLE_TIMEOUT=1800
   MODEL_CLEANUP_INTERVAL=300
   PERSISTENT_MODEL_CACHE=true
   ALWAYS_KEEP_MODELS=true
   PRIORITY_MODELS=base,small
   WARMUP_MODELS=base,small
   ```

4. **Deploy**:
   - Click "Deploy"
   - Wait for deployment to complete
   - Your app will be available at `https://your-project-name.vercel.app`

### Method 2: Vercel CLI

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy from Project Directory**:
   ```bash
   cd /path/to/your/project
   vercel
   ```

4. **Follow the prompts**:
   - Link to existing project or create new
   - Set up project settings
   - Deploy

5. **Set Environment Variables**:
   ```bash
   vercel env add FLASK_ENV
   vercel env add PYTHONPATH
   vercel env add ENABLE_GPU_ACCELERATION
   # ... add other variables
   ```

## Configuration Files

### vercel.json
```json
{
  "version": 2,
  "name": "echoscribe-voice-transcriber",
  "builds": [
    {
      "src": "vercel_app.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "50mb"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "vercel_app.py"
    }
  ],
  "env": {
    "FLASK_ENV": "production",
    "PYTHONPATH": "."
  },
  "functions": {
    "vercel_app.py": {
      "maxDuration": 30
    }
  },
  "regions": ["iad1"],
  "framework": "flask"
}
```

### requirements-vercel.txt
Optimized requirements file for Vercel deployment with smaller package sizes.

### .vercelignore
Excludes unnecessary files from deployment to reduce bundle size.

## Environment Variables

### Required Variables
- `FLASK_ENV=production`
- `PYTHONPATH=.`

### Optional Variables
- `ENABLE_GPU_ACCELERATION=false` (Vercel doesn't support GPU)
- `WHISPER_MODEL_CACHE_SIZE=2` (Reduced for serverless)
- `MODEL_IDLE_TIMEOUT=1800` (30 minutes)
- `MODEL_CLEANUP_INTERVAL=300` (5 minutes)
- `PERSISTENT_MODEL_CACHE=true`
- `ALWAYS_KEEP_MODELS=true`
- `PRIORITY_MODELS=base,small`
- `WARMUP_MODELS=base,small`

### Analytics Variables (Optional)
- `GOOGLE_ANALYTICS_ID=your_ga_id`
- `HOTJAR_SITE_ID=your_hotjar_id`
- `ENABLE_ANALYTICS=true`
- `ENABLE_GOOGLE_ANALYTICS=true`
- `ENABLE_HOTJAR=true`

## Vercel-Specific Optimizations

### 1. Serverless Function Limits
- **Max Duration**: 30 seconds (configurable up to 900s for Pro)
- **Max Memory**: 1024MB (configurable up to 3008MB for Pro)
- **Max Lambda Size**: 50MB (configurable up to 250MB for Pro)

### 2. Model Loading Strategy
```python
# Models are loaded on-demand in serverless functions
# First request will be slower due to cold start
# Subsequent requests will be faster
```

### 3. File Upload Handling
```python
# Vercel has a 4.5MB request body limit
# Large files should be handled via external storage
# Consider using Vercel Blob or AWS S3 for file storage
```

### 4. Static File Serving
```python
# Static files are served from Vercel's CDN
# No additional configuration needed
```

## Deployment Considerations

### 1. Cold Start Performance
- **First Request**: May take 10-30 seconds due to model loading
- **Subsequent Requests**: Much faster (1-5 seconds)
- **Solution**: Use Vercel Pro for better performance

### 2. Memory Usage
- **Whisper Models**: Large memory footprint
- **Recommendation**: Use smaller models (tiny, base) for Vercel
- **Monitoring**: Check Vercel dashboard for memory usage

### 3. File Storage
- **Uploads**: Stored in `/tmp` directory (temporary)
- **Transcriptions**: Stored in `/tmp` directory (temporary)
- **Recommendation**: Use external storage for persistence

### 4. Database
- **Current**: In-memory storage (not persistent)
- **Recommendation**: Use Vercel Postgres or external database

## Monitoring and Debugging

### 1. Vercel Dashboard
- **Functions**: Monitor function performance
- **Logs**: View real-time logs
- **Analytics**: Track usage and performance

### 2. Environment Variables
- **Dashboard**: Manage environment variables
- **CLI**: `vercel env ls` to list variables
- **CLI**: `vercel env pull` to download local `.env`

### 3. Custom Domains
- **Setup**: Add custom domain in Vercel dashboard
- **SSL**: Automatically handled by Vercel
- **CDN**: Global CDN for fast access

## Troubleshooting

### Common Issues

#### 1. Import Errors
```
Error: No module named 'app'
```
**Solution**: Ensure `PYTHONPATH=.` is set in environment variables

#### 2. Model Loading Failures
```
Error: Model not found
```
**Solution**: Models are downloaded on first use, ensure internet connectivity

#### 3. Memory Issues
```
Error: Function exceeded memory limit
```
**Solution**: Reduce `WHISPER_MODEL_CACHE_SIZE` or use smaller models

#### 4. Timeout Issues
```
Error: Function timeout
```
**Solution**: Increase `maxDuration` in vercel.json or optimize model loading

### Debug Commands

```bash
# Check deployment status
vercel ls

# View logs
vercel logs

# Check environment variables
vercel env ls

# Redeploy
vercel --prod
```

## Performance Optimization

### 1. Model Selection
- **Tiny**: Fastest, lowest accuracy
- **Base**: Good balance (recommended for Vercel)
- **Small**: Better accuracy, slower
- **Medium/Large**: Not recommended for Vercel

### 2. Caching Strategy
- **In-Memory**: Models cached in function memory
- **Cold Start**: First request loads models
- **Warm Start**: Subsequent requests use cached models

### 3. Request Optimization
- **File Size**: Keep uploads under 4.5MB
- **Model Size**: Use smaller models for faster processing
- **Batch Processing**: Process multiple files in single request

## Security Considerations

### 1. Environment Variables
- **Sensitive Data**: Store in Vercel environment variables
- **Never Commit**: Don't commit `.env` files
- **Access Control**: Limit access to environment variables

### 2. File Uploads
- **Validation**: Validate file types and sizes
- **Sanitization**: Sanitize filenames and content
- **Temporary Storage**: Files are automatically cleaned up

### 3. API Endpoints
- **Rate Limiting**: Consider implementing rate limiting
- **Authentication**: Add authentication if needed
- **CORS**: Configure CORS for cross-origin requests

## Cost Considerations

### 1. Vercel Pricing
- **Hobby**: Free tier with limitations
- **Pro**: $20/month for better performance
- **Enterprise**: Custom pricing for large scale

### 2. Function Usage
- **Invocations**: Count of function calls
- **Duration**: Total execution time
- **Memory**: Memory usage per function

### 3. Optimization Tips
- **Model Selection**: Use smaller models
- **Caching**: Implement proper caching
- **Batch Processing**: Process multiple requests together

## Next Steps

1. **Deploy**: Follow the deployment steps above
2. **Test**: Test all functionality on Vercel
3. **Monitor**: Set up monitoring and alerts
4. **Optimize**: Optimize based on usage patterns
5. **Scale**: Consider upgrading to Pro plan if needed

## Support

- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Flask on Vercel**: [vercel.com/docs/frameworks/flask](https://vercel.com/docs/frameworks/flask)
- **Community**: [vercel.com/community](https://vercel.com/community)

Your EchoScribe Voice Transcriber is now ready for deployment on Vercel! 🚀
