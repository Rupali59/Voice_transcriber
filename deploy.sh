#!/bin/bash

# Simple Voice Transcriber Deployment Script

set -e

echo "🚀 Voice Transcriber - Simple Deployment"
echo "======================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads transcriptions logs

# Build and start the application
echo "🏗️  Building and starting the application..."
docker-compose down --remove-orphans
docker-compose build
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Application is running successfully!"
    echo ""
    echo "🌐 Access your application at:"
    echo "   http://localhost:5001"
    echo ""
    echo "📊 To view logs:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🛑 To stop the application:"
    echo "   docker-compose down"
else
    echo "❌ Application failed to start. Check logs with:"
    echo "   docker-compose logs"
    exit 1
fi

echo "🎉 Deployment completed successfully!"
