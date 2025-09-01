#!/bin/bash

# Voice Transcriber - File Processing Script
# Handles processing of individual audio files

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

echo -e "${BLUE}🎤 File Processor${NC}"
echo "=================="

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

# Function to validate audio file
validate_audio_file() {
    local file_path="$1"
    
    # Check if file exists
    if [ ! -f "$file_path" ]; then
        echo -e "${RED}❌ File not found: $file_path${NC}"
        return 1
    fi
    
    # Check if file is readable
    if [ ! -r "$file_path" ]; then
        echo -e "${RED}❌ File not readable: $file_path${NC}"
        return 1
    fi
    
    # Check file size
    local file_size=$(stat -f%z "$file_path" 2>/dev/null || stat -c%s "$file_path" 2>/dev/null || echo "0")
    if [ "$file_size" -eq 0 ]; then
        echo -e "${RED}❌ File is empty: $file_path${NC}"
        return 1
    fi
    
    # Check file extension
    local file_ext="${file_path##*.}"
    local valid_extensions=("m4a" "mp3" "wav" "aac" "flac" "m4b")
    
    local is_valid=false
    for ext in "${valid_extensions[@]}"; do
        if [ "$file_ext" = "$ext" ]; then
            is_valid=true
            break
        fi
    done
    
    if [ "$is_valid" = false ]; then
        echo -e "${YELLOW}⚠️  Unsupported file extension: .$file_ext${NC}"
        echo "   Supported formats: ${valid_extensions[*]}"
        echo "   Proceeding anyway..."
    fi
    
    return 0
}

# Function to show file information
show_file_info() {
    local file_path="$1"
    
    echo -e "${BLUE}📄 File Information${NC}"
    echo "=================="
    
    # Basic file info
    local filename=$(basename "$file_path")
    local file_size=$(ls -lh "$file_path" | awk '{print $5}')
    local file_date=$(ls -l "$file_path" | awk '{print $6, $7, $8}')
    local file_perms=$(ls -l "$file_path" | awk '{print $1}')
    
    echo "   Name: $filename"
    echo "   Size: $file_size"
    echo "   Modified: $file_date"
    echo "   Permissions: $file_perms"
    
    # Audio file specific info (if ffprobe is available)
    if command -v ffprobe &> /dev/null; then
        echo ""
        echo "   🎵 Audio Details:"
        
        # Get duration
        local duration=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$file_path" 2>/dev/null)
        if [ -n "$duration" ] && [ "$duration" != "N/A" ]; then
            echo "     Duration: ${duration}s"
        fi
        
        # Get audio codec
        local codec=$(ffprobe -v quiet -select_streams a:0 -show_entries stream=codec_name -of csv=p=0 "$file_path" 2>/dev/null)
        if [ -n "$codec" ] && [ "$codec" != "N/A" ]; then
            echo "     Codec: $codec"
        fi
        
        # Get sample rate
        local sample_rate=$(ffprobe -v quiet -select_streams a:0 -show_entries stream=sample_rate -of csv=p=0 "$file_path" 2>/dev/null)
        if [ -n "$sample_rate" ] && [ "$sample_rate" != "N/A" ]; then
            echo "     Sample Rate: ${sample_rate}Hz"
        fi
    fi
    
    echo ""
}

# Function to process audio file
process_audio_file() {
    local file_path="$1"
    
    echo -e "${BLUE}🎤 Processing Audio File${NC}"
    echo "========================="
    
    # Validate file
    if ! validate_audio_file "$file_path"; then
        return 1
    fi
    
    # Show file information
    show_file_info "$file_path"
    
    # Check configuration and environment
    if ! check_config || ! activate_venv; then
        return 1
    fi
    
    # Change to project directory
    cd "$PROJECT_DIR"
    
    echo "🚀 Starting transcription..."
    echo "   This may take a while depending on file size and complexity..."
    echo ""
    
    # Process the file
    python3 src/transcriber_cli.py --file "$file_path"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ File processing completed successfully!${NC}"
        
        # Show output location
        local filename=$(basename "$file_path")
        local output_file="${filename%.*}_transcription.md"
        local output_path="$PROJECT_DIR/transcriptions/$output_file"
        
        if [ -f "$output_path" ]; then
            echo "📝 Transcription saved to: $output_path"
            
            # Show file size
            local output_size=$(ls -lh "$output_path" | awk '{print $5}')
            echo "📊 Output size: $output_size"
        fi
    else
        echo ""
        echo -e "${RED}❌ File processing failed${NC}"
        return 1
    fi
}

# Function to show help
show_help() {
    echo -e "\n${BLUE}📖 File Processor Help${NC}"
    echo "====================="
    echo ""
    echo "Usage: $0 <audio_file_path>"
    echo ""
    echo "Description:"
    echo "  Processes a single audio file and generates a transcription"
    echo ""
    echo "Arguments:"
    echo "  audio_file_path    Path to the audio file to process"
    echo ""
    echo "Supported Formats:"
    echo "  m4a, mp3, wav, aac, flac, m4b"
    echo ""
    echo "Examples:"
    echo "  $0 /path/to/voice_memo.m4a"
    echo "  $0 ~/Music/Voice\ Memos/recording.mp3"
    echo "  $0 ./audio_file.wav"
    echo ""
    echo "Note: The transcription will be saved in the transcriptions/ directory"
    echo "      with the same name as the input file plus '_transcription.md'"
}

# Main function
main() {
    local file_path="$1"
    
    # Check if file path is provided
    if [ -z "$file_path" ]; then
        echo -e "${RED}❌ No file path provided${NC}"
        echo ""
        show_help
        exit 1
    fi
    
    # Process the file
    process_audio_file "$file_path"
}

# Run main function
main "$@"
