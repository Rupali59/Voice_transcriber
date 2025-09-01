#!/bin/bash

# Voice Transcriber - Setup Script
# Handles system setup, dependency installation, and environment creation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🚀 Voice Transcriber Setup${NC}"
echo "=========================="

# Function to check Python version
check_python() {
    python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
    required_version="3.8"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        echo -e "${RED}❌ Python 3.8+ required, found: $python_version${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Python version: $python_version${NC}"
    return 0
}

# Function to create virtual environment
create_venv() {
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv "$PROJECT_DIR/venv"
        echo -e "${GREEN}✅ Virtual environment created${NC}"
    else
        echo -e "${GREEN}✅ Virtual environment already exists${NC}"
    fi
}

# Function to install dependencies
install_dependencies() {
    echo "⬆️ Upgrading pip..."
    pip install --upgrade pip
    
    echo "🔥 Installing PyTorch..."
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
    
    echo "📚 Installing dependencies..."
    pip install -r "$PROJECT_DIR/configs/requirements.txt"
}

# Function to create directories
create_directories() {
    echo "📁 Creating directories..."
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/transcriptions"
    echo -e "${GREEN}✅ Directories created${NC}"
}

# Function to setup configuration
setup_config() {
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        echo "⚙️ Creating .env configuration file..."
        cp "$PROJECT_DIR/configs/env_template.txt" "$PROJECT_DIR/.env"
        echo -e "${GREEN}✅ .env file created from template${NC}"
        echo -e "${YELLOW}💡 Edit .env file to configure your settings${NC}"
    else
        echo -e "${GREEN}✅ .env file already exists${NC}"
    fi
}

# Function to test installation
test_installation() {
    echo "🧪 Testing installation..."
    python3 -c "
import whisper
import torch
import librosa
import scipy
import sklearn
import numpy
import watchdog
import tqdm
print('✅ All dependencies installed successfully!')
"
    
    if [ $? -eq 0 ]; then
        echo -e "\n${GREEN}🎉 Setup completed successfully!${NC}"
        return 0
    else
        echo -e "\n${RED}❌ Setup failed. Check the error messages above.${NC}"
        return 1
    fi
}

# Main setup function
main() {
    echo "Starting Voice Transcriber setup..."
    
    # Check Python version
    if ! check_python; then
        exit 1
    fi
    
    # Create virtual environment
    create_venv
    
    # Activate virtual environment
    source "$PROJECT_DIR/venv/bin/activate"
    
    # Install dependencies
    install_dependencies
    
    # Create directories
    create_directories
    
    # Setup configuration
    setup_config
    
    # Test installation
    test_installation
}

# Run main function
main "$@"
