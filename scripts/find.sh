#!/bin/bash

# Voice Transcriber - Find Script
# Searches for voice memos in common locations

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

echo -e "${BLUE}🔍 Voice Memo Finder${NC}"
echo "====================="

# Common voice memo locations
VOICE_MEMO_LOCATIONS=(
    "$HOME/Library/Mobile Documents/com~apple~CloudDocs/Voice Memos"
    "$HOME/Music/Voice Memos"
    "$HOME/Documents/Recordings"
    "$HOME/Downloads/Voice Memos"
    "$HOME/Desktop/Voice Memos"
    "$HOME/Library/Application Support/Voice Memos"
)

# Audio file extensions to search for
AUDIO_EXTENSIONS=("*.m4a" "*.mp3" "*.wav" "*.aac" "*.flac" "*.m4b")

# Function to check directory accessibility
check_directory() {
    local dir="$1"
    if [ -d "$dir" ]; then
        if [ -r "$dir" ]; then
            return 0
        else
            return 2  # Directory exists but not readable
        fi
    else
        return 1  # Directory doesn't exist
    fi
}

# Function to search for audio files in a directory
search_directory() {
    local dir="$1"
    local found_files=()
    
    echo "📁 Searching: $dir"
    
    for ext in "${AUDIO_EXTENSIONS[@]}"; do
        while IFS= read -r -d '' file; do
            if [ -f "$file" ]; then
                found_files+=("$file")
            fi
        done < <(find "$dir" -type f -name "$ext" -print0 2>/dev/null)
    done
    
    if [ ${#found_files[@]} -gt 0 ]; then
        echo "   🎵 Found ${#found_files[@]} audio file(s):"
        
        # Sort files by modification time (newest first)
        IFS=$'\n' sorted_files=($(sort -r -k6,7 < <(ls -la "${found_files[@]}" 2>/dev/null | head -20)))
        
        for file_info in "${sorted_files[@]}"; do
            if [[ "$file_info" =~ ^- ]]; then  # Only process regular files
                filename=$(echo "$file_info" | awk '{print $9}')
                size=$(echo "$file_info" | awk '{print $5}')
                date=$(echo "$file_info" | awk '{print $6, $7, $8}')
                
                if [ -n "$filename" ] && [ "$filename" != "." ] && [ "$filename" != ".." ]; then
                    echo "      📄 $filename - $size - $date"
                fi
            fi
        done
        
        # Add to global found files
        GLOBAL_FOUND_FILES+=("${found_files[@]}")
        
    else
        echo "   ❌ No audio files found"
    fi
    
    echo ""
}

# Function to show summary
show_summary() {
    echo -e "${BLUE}📊 Search Summary${NC}"
    echo "================="
    
    if [ ${#GLOBAL_FOUND_FILES[@]} -gt 0 ]; then
        echo -e "${GREEN}✅ Found ${#GLOBAL_FOUND_FILES[@]} audio files total${NC}"
        echo ""
        echo "🎯 Next steps:"
        echo "   • Process all files: ./scripts/transcriber.sh process"
        echo "   • Process specific file: ./scripts/transcriber.sh file <path>"
        echo "   • View configuration: ./scripts/transcriber.sh config"
    else
        echo -e "${YELLOW}⚠️  No audio files found in common locations${NC}"
        echo ""
        echo "💡 Suggestions:"
        echo "   • Check if iCloud Drive is enabled"
        echo "   • Verify Voice Memos app sync status"
        echo "   • Check system permissions (Full Disk Access)"
        echo "   • Look in other custom locations"
    fi
}

# Function to check iCloud status
check_icloud_status() {
    echo -e "${BLUE}☁️  iCloud Status Check${NC}"
    echo "====================="
    
    # Check if iCloud Drive is enabled
    if [ -d "$HOME/Library/Mobile Documents/com~apple~CloudDocs" ]; then
        echo -e "   iCloud Drive: ${GREEN}Enabled${NC}"
        
        # Check Voice Memos folder specifically
        if [ -d "$HOME/Library/Mobile Documents/com~apple~CloudDocs/Voice Memos" ]; then
            echo -e "   Voice Memos sync: ${GREEN}Active${NC}"
        else
            echo -e "   Voice Memos sync: ${YELLOW}Not found${NC}"
        fi
    else
        echo -e "   iCloud Drive: ${RED}Not enabled${NC}"
        echo "   💡 Enable in System Preferences → Apple ID → iCloud"
    fi
    
    echo ""
}

# Function to check system permissions
check_permissions() {
    echo -e "${BLUE}🔐 System Permissions${NC}"
    echo "====================="
    
    # Check if we can access protected directories
    protected_dirs=(
        "$HOME/Library"
        "$HOME/Library/Mobile Documents"
        "$HOME/Library/Application Support"
    )
    
    for dir in "${protected_dirs[@]}"; do
        if [ -r "$dir" ]; then
            echo -e "   $dir: ${GREEN}Accessible${NC}"
        else
            echo -e "   $dir: ${RED}Not accessible${NC}"
        fi
    done
    
    echo ""
    echo "💡 If directories are not accessible, grant Full Disk Access to Terminal:"
    echo "   System Preferences → Security & Privacy → Privacy → Full Disk Access"
    echo ""
}

# Main search function
main() {
    echo "Starting voice memo search..."
    echo ""
    
    # Initialize global found files array
    GLOBAL_FOUND_FILES=()
    
    # Check iCloud status
    check_icloud_status
    
    # Check system permissions
    check_permissions
    
    # Search each location
    echo -e "${BLUE}🔍 Searching Locations${NC}"
    echo "====================="
    
    for location in "${VOICE_MEMO_LOCATIONS[@]}"; do
        case $(check_directory "$location") in
            0)  # Directory exists and is readable
                search_directory "$location"
                ;;
            1)  # Directory doesn't exist
                echo "📁 $location - Directory not found"
                echo ""
                ;;
            2)  # Directory exists but not readable
                echo -e "📁 $location - ${RED}Access denied${NC}"
                echo ""
                ;;
        esac
    done
    
    # Show summary
    show_summary
}

# Run main function
main "$@"
