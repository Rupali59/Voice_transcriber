#!/bin/bash

# Voice Transcriber - Configuration Script
# Handles configuration display and management

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

echo -e "${BLUE}🔧 Voice Transcriber Configuration${NC}"
echo "=================================="

# Function to show environment configuration
show_env_config() {
    if [ -f "$PROJECT_DIR/.env" ]; then
        echo -e "${GREEN}📁 Environment file: $PROJECT_DIR/.env${NC}"
        echo "📋 Configuration values:"
        echo ""
        
        # Read and display non-comment, non-empty lines
        while IFS= read -r line; do
            if [[ ! "$line" =~ ^[[:space:]]*# ]] && [[ -n "$line" ]]; then
                echo "   $line"
            fi
        done < "$PROJECT_DIR/.env"
    else
        echo -e "${YELLOW}⚠️  No .env file found${NC}"
        echo "💡 Run setup first: ./scripts/setup.sh"
        return 1
    fi
}

# Function to show project structure
show_project_structure() {
    echo ""
    echo -e "${BLUE}📁 Project Structure${NC}"
    echo "====================="
    echo "   Source: $PROJECT_DIR/src"
    echo "   Configs: $PROJECT_DIR/configs"
    echo "   Transcriptions: $PROJECT_DIR/transcriptions"
    echo "   Logs: $PROJECT_DIR/logs"
    echo "   Virtual Environment: $PROJECT_DIR/venv"
}

# Function to show system information
show_system_info() {
    echo ""
    echo -e "${BLUE}💻 System Information${NC}"
    echo "======================="
    
    # Python version
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version 2>&1)
        echo "   Python: $python_version"
    else
        echo -e "   Python: ${RED}Not found${NC}"
    fi
    
    # Virtual environment
    if [ -d "$PROJECT_DIR/venv" ]; then
        echo -e "   Virtual Environment: ${GREEN}Active${NC}"
    else
        echo -e "   Virtual Environment: ${RED}Not found${NC}"
    fi
}

# Main configuration function
main() {
    echo "Displaying Voice Transcriber configuration..."
    
    # Show environment configuration
    show_env_config
    
    # Show project structure
    show_project_structure
    
    # Show system information
    show_system_info
}

# Run main function
main "$@"
