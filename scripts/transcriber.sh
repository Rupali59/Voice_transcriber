#!/bin/bash

# Voice Transcriber - Comprehensive Management Script
# Handles setup, configuration, and all transcriber operations

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

echo -e "${BLUE}🎤 Voice Transcriber - Management Script${NC}"
echo "=============================================="

# Function to check if virtual environment exists
check_venv() {
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
        return 1
    fi
    return 0
}

# Function to activate virtual environment
activate_venv() {
    if check_venv; then
        source "$PROJECT_DIR/venv/bin/activate"
        echo -e "${GREEN}✅ Virtual environment activated${NC}"
        return 0
    else
        echo -e "${RED}❌ Cannot activate virtual environment${NC}"
        return 1
    fi
}

# Function to setup the system
setup_system() {
    echo -e "\n${BLUE}🚀 Setting up Voice Transcriber...${NC}"
    echo "   Using dedicated setup script..."
    
    # Call the dedicated setup script
    "$SCRIPT_DIR/setup.sh"
}

# Function to show configuration
show_config() {
    echo -e "\n${BLUE}🔧 Showing Configuration...${NC}"
    echo "   Using dedicated config script..."
    
    # Call the dedicated config script
    "$SCRIPT_DIR/config.sh"
}

# Function to find voice memos
find_voice_memos() {
    echo -e "\n${BLUE}🔍 Searching for Voice Memos...${NC}"
    echo "   Using dedicated find script..."
    
    # Call the dedicated find script
    "$SCRIPT_DIR/find.sh"
}

# Function to process voice memos
process_voice_memos() {
    echo -e "\n${BLUE}🎤 Processing Voice Memos...${NC}"
    echo "   Using dedicated process script..."
    
    # Call the dedicated process script
    "$SCRIPT_DIR/process.sh" start
}

# Function to show processing status
show_processing_status() {
    echo -e "\n${BLUE}📊 Processing Status...${NC}"
    echo "   Using dedicated process script..."
    
    # Call the dedicated process script
    "$SCRIPT_DIR/process.sh" status
}

# Function to process specific file
process_file() {
    local file_path="$1"
    
    if [ -z "$file_path" ]; then
        echo -e "${RED}❌ Please provide a file path${NC}"
        return 1
    fi
    
    echo -e "\n${BLUE}🎤 Processing File...${NC}"
    echo "   Using dedicated file script..."
    
    # Call the dedicated file script
    "$SCRIPT_DIR/file.sh" "$file_path"
}

# Function to show help
show_help() {
    echo -e "\n${BLUE}📖 Voice Transcriber Help${NC}"
    echo "======================="
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  setup           - Setup the system (install dependencies, create venv)"
    echo "  config          - Show current configuration"
    echo "  find            - Search for voice memos in common locations"
    echo "  process         - Start background processing of voice memos"
    echo "  status          - Show detailed processing status"
    echo "  quick           - Show quick status (essential info only)"
    echo "  monitor         - Real-time process monitoring"
    echo "  parallel        - Parallel processing of multiple files"
    echo "  file <path>     - Process a specific audio file"
    echo "  help            - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup                    # Setup the system"
    echo "  $0 config                   # Show configuration"
    echo "  $0 find                     # Find voice memos"
    echo "  $0 process                  # Start background processing"
    echo "  $0 status                   # Show detailed status"
    echo "  $0 quick                    # Show quick status"
    echo "  $0 monitor                  # Real-time monitoring"
    echo "  $0 parallel files *.m4a     # Process multiple files in parallel"
    echo "  $0 parallel dir /path       # Process directory in parallel"
    echo "  $0 file /path/to/audio.m4a  # Process specific file"
    echo ""
    echo "For advanced usage, see the README.md file"
}

# Main script logic
main() {
    case "${1:-help}" in
        "setup")
            setup_system
            ;;
        "config")
            show_config
            ;;
        "find")
            find_voice_memos
            ;;
        "process")
            process_voice_memos
            ;;
        "status")
            show_processing_status
            ;;
        "quick")
            echo -e "\n${BLUE}📊 Quick Status...${NC}"
            echo "   Using dedicated process script..."
            "$SCRIPT_DIR/process.sh" quick
            ;;
        "monitor")
            echo -e "\n${BLUE}📊 Real-time Monitoring...${NC}"
            echo "   Using dedicated process script..."
            "$SCRIPT_DIR/process.sh" monitor
            ;;
        "parallel")
            echo -e "\n${BLUE}🚀 Parallel Processing...${NC}"
            echo "   Using dedicated parallel script..."
            shift  # Remove 'parallel' command
            "$SCRIPT_DIR/parallel.sh" "$@"
            ;;
        "file")
            process_file "$2"
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"
