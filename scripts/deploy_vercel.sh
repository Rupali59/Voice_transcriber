#!/bin/bash

# EchoScribe Vercel Deployment Script
# This script helps deploy the Voice Transcriber application to Vercel

set -e  # Exit on any error

echo "🚀 EchoScribe Vercel Deployment Script"
echo "======================================"

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
    echo "✅ Vercel CLI installed"
else
    echo "✅ Vercel CLI found"
fi

# Check if user is logged in
if ! vercel whoami &> /dev/null; then
    echo "🔐 Please log in to Vercel:"
    vercel login
fi

echo "👤 Logged in as: $(vercel whoami)"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Please initialize git first:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    exit 1
fi

echo "✅ Git repository found"

# Check if vercel.json exists
if [ ! -f "vercel.json" ]; then
    echo "❌ vercel.json not found. Please ensure deployment files are present."
    exit 1
fi

echo "✅ Vercel configuration found"

# Check if requirements-vercel.txt exists
if [ ! -f "requirements-vercel.txt" ]; then
    echo "❌ requirements-vercel.txt not found. Please ensure deployment files are present."
    exit 1
fi

echo "✅ Vercel requirements found"

# Set up environment variables
echo "🔧 Setting up environment variables..."

# Required environment variables
ENV_VARS=(
    "FLASK_ENV=production"
    "PYTHONPATH=."
    "ENABLE_GPU_ACCELERATION=false"
    "WHISPER_MODEL_CACHE_SIZE=2"
    "MODEL_IDLE_TIMEOUT=1800"
    "MODEL_CLEANUP_INTERVAL=300"
    "PERSISTENT_MODEL_CACHE=true"
    "ALWAYS_KEEP_MODELS=true"
    "PRIORITY_MODELS=base,small"
    "WARMUP_MODELS=base,small"
)

# Optional environment variables (ask user)
echo "📝 Optional environment variables:"
read -p "Enter Google Analytics ID (or press Enter to skip): " GA_ID
if [ ! -z "$GA_ID" ]; then
    ENV_VARS+=("GOOGLE_ANALYTICS_ID=$GA_ID")
    ENV_VARS+=("ENABLE_ANALYTICS=true")
    ENV_VARS+=("ENABLE_GOOGLE_ANALYTICS=true")
fi

read -p "Enter Hotjar Site ID (or press Enter to skip): " HOTJAR_ID
if [ ! -z "$HOTJAR_ID" ]; then
    ENV_VARS+=("HOTJAR_SITE_ID=$HOTJAR_ID")
    ENV_VARS+=("ENABLE_HOTJAR=true")
fi

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."

# First deployment (or update)
if [ -f ".vercel/project.json" ]; then
    echo "📦 Updating existing project..."
    vercel --prod
else
    echo "🆕 Creating new project..."
    vercel
fi

# Set environment variables
echo "🔧 Setting environment variables..."
for env_var in "${ENV_VARS[@]}"; do
    key=$(echo $env_var | cut -d'=' -f1)
    value=$(echo $env_var | cut -d'=' -f2-)
    echo "Setting $key..."
    vercel env add "$key" "$value" production
done

echo "✅ Environment variables set"

# Get deployment URL
echo "🌐 Getting deployment URL..."
DEPLOYMENT_URL=$(vercel ls --json | jq -r '.[0].url' 2>/dev/null || echo "https://your-project.vercel.app")

echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo "🌐 URL: $DEPLOYMENT_URL"
echo ""
echo "📋 Next Steps:"
echo "1. Test your deployment: curl $DEPLOYMENT_URL/health"
echo "2. Test file upload: curl -X POST -F 'file=@test.wav' $DEPLOYMENT_URL/api/upload"
echo "3. Check logs: vercel logs"
echo "4. Monitor performance: vercel dashboard"
echo ""
echo "🔧 Useful Commands:"
echo "• View logs: vercel logs"
echo "• Redeploy: vercel --prod"
echo "• Check status: vercel ls"
echo "• Remove deployment: vercel remove"
echo ""
echo "📚 Documentation: docs/VERCEL_DEPLOYMENT_GUIDE.md"
echo ""
echo "Happy transcribing! 🎤✨"
