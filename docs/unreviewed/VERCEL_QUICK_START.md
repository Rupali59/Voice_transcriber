# 🚀 Vercel Quick Start Guide

Deploy your EchoScribe Voice Transcriber to Vercel in minutes!

## ⚡ Quick Deployment (5 minutes)

### 1. Prepare Your Repository
```bash
# Ensure all files are committed
git add .
git commit -m "Ready for Vercel deployment"
git push origin main
```

### 2. Deploy via Vercel Dashboard
1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. Select your repository
4. Click "Deploy" (Vercel will auto-detect Flask)

### 3. Set Environment Variables
In Vercel dashboard → Project Settings → Environment Variables:

```
FLASK_ENV=production
PYTHONPATH=.
ENABLE_GPU_ACCELERATION=false
WHISPER_MODEL_CACHE_SIZE=2
PRIORITY_MODELS=base,small
```

### 4. Test Your Deployment
```bash
# Test the deployment
python scripts/test_vercel_deployment.py https://your-app.vercel.app
```

## 🛠️ Advanced Deployment

### Using Vercel CLI
```bash
# Install Vercel CLI
npm install -g vercel

# Login and deploy
vercel login
vercel

# Set environment variables
vercel env add FLASK_ENV production
vercel env add ENABLE_GPU_ACCELERATION false
# ... add other variables

# Deploy to production
vercel --prod
```

### Using Deployment Script
```bash
# Run the automated deployment script
./scripts/deploy_vercel.sh
```

## 📋 Required Files

Your repository should include:
- ✅ `vercel.json` - Vercel configuration
- ✅ `vercel_app.py` - Vercel entry point
- ✅ `requirements-vercel.txt` - Optimized dependencies
- ✅ `.vercelignore` - Exclude unnecessary files

## 🔧 Configuration

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
  "functions": {
    "vercel_app.py": {
      "maxDuration": 30
    }
  }
}
```

### Environment Variables
| Variable | Value | Description |
|----------|-------|-------------|
| `FLASK_ENV` | `production` | Flask environment |
| `PYTHONPATH` | `.` | Python path |
| `ENABLE_GPU_ACCELERATION` | `false` | Disable GPU (Vercel doesn't support) |
| `WHISPER_MODEL_CACHE_SIZE` | `2` | Smaller cache for serverless |
| `PRIORITY_MODELS` | `base,small` | Models to keep in memory |

## 🧪 Testing

### Test Scripts
```bash
# Test deployment
python scripts/test_vercel_deployment.py https://your-app.vercel.app

# Test model validation
python scripts/test_model_validation.py

# Run comprehensive tests
python scripts/run_comprehensive_tests.py --type all
```

### Manual Testing
```bash
# Health check
curl https://your-app.vercel.app/health

# Get models
curl https://your-app.vercel.app/api/models

# Cache status
curl https://your-app.vercel.app/api/cache/models
```

## 📊 Performance

### Expected Performance
- **Cold Start**: 10-30 seconds (first request)
- **Warm Start**: 1-5 seconds (subsequent requests)
- **Memory Usage**: ~500MB-1GB per function
- **File Size Limit**: 4.5MB per request

### Optimization Tips
1. **Use smaller models**: `tiny`, `base` instead of `large`
2. **Enable caching**: Models stay in memory between requests
3. **Batch requests**: Process multiple files together
4. **Monitor usage**: Check Vercel dashboard for metrics

## 🔍 Monitoring

### Vercel Dashboard
- **Functions**: Monitor execution time and memory
- **Logs**: View real-time logs
- **Analytics**: Track usage and performance

### Useful Commands
```bash
# View logs
vercel logs

# Check deployment status
vercel ls

# Redeploy
vercel --prod
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Import Errors
```
Error: No module named 'app'
```
**Solution**: Set `PYTHONPATH=.` in environment variables

#### 2. Model Loading Failures
```
Error: Model not found
```
**Solution**: Models download on first use, ensure internet connectivity

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

### Debug Steps
1. Check Vercel logs: `vercel logs`
2. Verify environment variables
3. Test locally with Vercel CLI: `vercel dev`
4. Check function memory usage in dashboard

## 💰 Cost Considerations

### Vercel Pricing
- **Hobby**: Free (with limitations)
- **Pro**: $20/month (better performance)
- **Enterprise**: Custom pricing

### Usage Limits
- **Function Duration**: 30s (Hobby), 900s (Pro)
- **Memory**: 1024MB (Hobby), 3008MB (Pro)
- **Bandwidth**: 100GB (Hobby), 1TB (Pro)

## 🎯 Next Steps

1. **Deploy**: Follow the quick start guide above
2. **Test**: Run the test scripts to verify functionality
3. **Monitor**: Set up monitoring and alerts
4. **Optimize**: Adjust settings based on usage patterns
5. **Scale**: Consider upgrading to Pro plan if needed

## 📚 Additional Resources

- **Full Documentation**: [docs/VERCEL_DEPLOYMENT_GUIDE.md](docs/VERCEL_DEPLOYMENT_GUIDE.md)
- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Flask on Vercel**: [vercel.com/docs/frameworks/flask](https://vercel.com/docs/frameworks/flask)

---

**Ready to deploy?** Run `./scripts/deploy_vercel.sh` and follow the prompts! 🚀
