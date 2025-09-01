#!/bin/bash

# Voice Transcriber - Parallel Processing Script
# Handles parallel processing of multiple audio files

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

echo -e "${BLUE}🚀 Voice Transcriber - Parallel Processing${NC}"
echo "============================================="

# Function to check virtual environment
check_venv() {
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        echo -e "${RED}❌ Virtual environment not found${NC}"
        echo "💡 Run setup first: ./scripts/setup.sh"
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
        return 1
    fi
}

# Function to check configuration
check_config() {
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        echo -e "${RED}❌ Configuration file not found${NC}"
        echo "💡 Run setup first: ./scripts/setup.sh"
        return 1
    fi
    
    if [ ! -d "$PROJECT_DIR/src" ]; then
        echo -e "${RED}❌ Source code not found${NC}"
        echo "💡 Run setup first: ./scripts/setup.sh"
        return 1
    fi
    
    return 0
}

# Function to process files in parallel
process_files_parallel() {
    local files="$1"
    local concurrent="$2"
    local monitor="$3"
    
    echo "🚀 Starting parallel processing..."
    
    # Build command
    cmd="python3 src/parallel_cli.py --files $files"
    
    if [ -n "$concurrent" ]; then
        cmd="$cmd --concurrent $concurrent"
    fi
    
    if [ "$monitor" = "true" ]; then
        cmd="$cmd --monitor"
    fi
    
    cmd="$cmd --stats"
    
    echo "⚡ Command: $cmd"
    echo ""
    
    # Execute parallel processing
    eval $cmd
}

# Function to process directory in parallel
process_directory_parallel() {
    local directory="$1"
    local concurrent="$2"
    local monitor="$3"
    
    echo "🚀 Starting parallel directory processing..."
    
    # Build command
    cmd="python3 src/parallel_cli.py --dir $directory"
    
    if [ -n "$concurrent" ]; then
        cmd="$cmd --concurrent $concurrent"
    fi
    
    if [ "$monitor" = "true" ]; then
        cmd="$cmd --monitor"
    fi
    
    cmd="$cmd --stats"
    
    echo "⚡ Command: $cmd"
    echo ""
    
    # Execute parallel processing
    eval $cmd
}

# Function to show help
show_help() {
    echo -e "\n${BLUE}📖 Parallel Processing Help${NC}"
    echo "============================="
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  files <file1> <file2>...  - Process specific audio files in parallel"
    echo "  dir <directory>           - Process all audio files in a directory"
    echo "  help                      - Show this help message"
    echo ""
    echo "Options:"
    echo "  --concurrent <N>          - Number of concurrent processes (default: from config)"
    echo "  --monitor                 - Enable real-time monitoring"
    echo "  --help                    - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 files audio1.m4a audio2.m4a audio3.m4a"
    echo "  $0 files *.m4a --concurrent 4"
    echo "  $0 dir /path/to/audio/files --monitor"
    echo "  $0 files *.m4a --concurrent 6 --monitor"
    echo ""
    echo "💡 Parallel processing can significantly improve throughput for multiple files!"
}

# Function to parse arguments
parse_arguments() {
    local command=""
    local files=()
    local directory=""
    local concurrent=""
    local monitor="false"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            "files")
                command="files"
                shift
                # Collect all remaining arguments as files
                while [[ $# -gt 0 ]]; do
                    if [[ "$1" == --* ]]; then
                        break
                    fi
                    files+=("$1")
                    shift
                done
                ;;
            "dir")
                command="dir"
                directory="$2"
                shift 2
                ;;
            "--concurrent")
                concurrent="$2"
                shift 2
                ;;
            "--monitor")
                monitor="true"
                shift
                ;;
            "--help"|"help")
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Unknown option: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Validate command
    if [ -z "$command" ]; then
        echo -e "${RED}❌ No command specified${NC}"
        show_help
        exit 1
    fi
    
    # Execute command
    case "$command" in
        "files")
            if [ ${#files[@]} -eq 0 ]; then
                echo -e "${RED}❌ No files specified${NC}"
                exit 1
            fi
            
            if ! check_config || ! activate_venv; then
                exit 1
            fi
            
            process_files_parallel "${files[*]}" "$concurrent" "$monitor"
            ;;
        "dir")
            if [ -z "$directory" ]; then
                echo -e "${RED}❌ No directory specified${NC}"
                exit 1
            fi
            
            if ! check_config || ! activate_venv; then
                exit 1
            fi
            
            process_directory_parallel "$directory" "$concurrent" "$monitor"
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $command${NC}"
            show_help
            exit 1
            ;;
    esac
}

# Main function
main() {
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    parse_arguments "$@"
}

# Run main function
main "$@"
