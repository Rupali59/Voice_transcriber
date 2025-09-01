#!/bin/bash

# Voice Transcriber - Help Script
# Shows comprehensive usage information and examples

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🎤 Voice Transcriber - Help & Documentation${NC}"
echo "=============================================="

# Function to show main help
show_main_help() {
    echo ""
    echo -e "${CYAN}📖 Main Commands${NC}"
    echo "================"
    echo ""
    echo -e "${GREEN}./scripts/transcriber.sh${NC} - Main management script"
    echo "  setup           - Setup the system (install dependencies, create venv)"
    echo "  config          - Show current configuration"
    echo "  find            - Search for voice memos in common locations"
    echo "  process         - Start background processing of voice memos"
    echo "  file <path>     - Process a specific audio file"
    echo "  help            - Show this help message"
    echo ""
}

# Function to show individual script help
show_script_help() {
    echo -e "${CYAN}🔧 Individual Scripts${NC}"
    echo "====================="
    echo ""
    echo -e "${GREEN}./scripts/setup.sh${NC} - System setup and installation"
    echo "  No arguments needed - runs complete setup"
    echo ""
    echo -e "${GREEN}./scripts/config.sh${NC} - Configuration management"
    echo "  No arguments needed - shows current config"
    echo ""
    echo -e "${GREEN}./scripts/find.sh${NC} - Voice memo discovery"
    echo "  No arguments needed - searches common locations"
    echo ""
    echo -e "${GREEN}./scripts/process.sh${NC} - Background processing"
    echo "  start            - Start background processing"
    echo "  stop             - Stop background processing"
    echo "  status           - Show processing status"
    echo "  help             - Show process script help"
    echo ""
    echo -e "${GREEN}./scripts/file.sh <path>${NC} - Single file processing"
    echo "  <audio_file_path> - Path to audio file to process"
    echo ""
}

# Function to show examples
show_examples() {
    echo -e "${CYAN}💡 Usage Examples${NC}"
    echo "=================="
    echo ""
    echo -e "${YELLOW}1. Initial Setup${NC}"
    echo "   ./scripts/setup.sh"
    echo "   # or"
    echo "   ./scripts/transcriber.sh setup"
    echo ""
    echo -e "${YELLOW}2. Find Voice Memos${NC}"
    echo "   ./scripts/find.sh"
    echo "   # or"
    echo "   ./scripts/transcriber.sh find"
    echo ""
    echo -e "${YELLOW}3. Process Specific File${NC}"
    echo "   ./scripts/file.sh /path/to/voice_memo.m4a"
    echo "   # or"
    echo "   ./scripts/transcriber.sh file /path/to/voice_memo.m4a"
    echo ""
    echo -e "${YELLOW}4. Start Background Processing${NC}"
    echo "   ./scripts/process.sh start"
    echo "   # or"
    echo "   ./scripts/transcriber.sh process"
    echo ""
    echo -e "${YELLOW}5. Check Processing Status${NC}"
    echo "   ./scripts/process.sh status"
    echo ""
    echo -e "${YELLOW}6. Stop Background Processing${NC}"
    echo "   ./scripts/process.sh stop"
    echo ""
}

# Function to show project structure
show_project_structure() {
    echo -e "${CYAN}📁 Project Structure${NC}"
    echo "====================="
    echo ""
    echo "Voice_transcriber/"
    echo "├── src/                          # Source code"
    echo "│   ├── transcriber_cli.py       # Main CLI interface"
    echo "│   ├── config_manager.py        # Configuration management"
    echo "│   ├── background_processor.py  # Background processing"
    echo "│   └── unified_voice_transcriber.py  # Core transcription"
    echo "├── configs/                      # Configuration files"
    echo "│   ├── requirements.txt         # Python dependencies"
    echo "│   └── env_template.txt         # Environment template"
    echo "├── scripts/                      # Management scripts"
    echo "│   ├── transcriber.sh           # Main management script"
    echo "│   ├── setup.sh                 # System setup"
    echo "│   ├── config.sh                # Configuration display"
    echo "│   ├── find.sh                  # Voice memo discovery"
    echo "│   ├── process.sh               # Background processing"
    echo "│   ├── file.sh                  # Single file processing"
    echo "│   └── help.sh                  # This help script"
    echo "├── docs/                         # Documentation"
    echo "├── transcriptions/               # Output transcriptions"
    echo "├── logs/                         # Log files"
    echo "└── .env                          # Environment configuration"
    echo ""
}

# Function to show supported formats
show_supported_formats() {
    echo -e "${CYAN}🎵 Supported Audio Formats${NC}"
    echo "========================="
    echo ""
    echo "  • M4A (Apple Voice Memos, iTunes)"
    echo "  • MP3 (Compressed audio)"
    echo "  • WAV (Uncompressed audio)"
    echo "  • AAC (Advanced Audio Coding)"
    echo "  • FLAC (Free Lossless Audio Codec)"
    echo "  • M4B (Audio book format)"
    echo ""
    echo "Note: The system automatically detects and handles all supported formats."
    echo ""
}

# Function to show features
show_features() {
    echo -e "${CYAN}✨ Key Features${NC}"
    echo "============="
    echo ""
    echo "  🎤 Multi-language transcription (English, Hindi, Hinglish, etc.)"
    echo "  👥 Speaker diarization (identifies multiple speakers)"
    echo "  🔄 Background processing with file monitoring"
    echo "  ⚙️  Environment-based configuration (.env file)"
    echo "  📊 Progress tracking and logging"
    echo "  🚀 Performance optimized with concurrent processing"
    echo "  📱 Apple Voice Memos integration"
    echo "  💾 Markdown output format"
    echo "  🔍 Automatic file discovery"
    echo ""
}

# Function to show troubleshooting
show_troubleshooting() {
    echo -e "${CYAN}🔧 Troubleshooting${NC}"
    echo "=================="
    echo ""
    echo -e "${YELLOW}Common Issues:${NC}"
    echo ""
    echo "  ❌ Virtual environment not found"
    echo "     Solution: Run ./scripts/setup.sh"
    echo ""
    echo "  ❌ Configuration file missing"
    echo "     Solution: Run ./scripts/setup.sh"
    echo ""
    echo "  ❌ Cannot access Voice Memos"
    echo "     Solution: Enable iCloud Drive and grant Full Disk Access"
    echo ""
    echo "  ❌ Dependencies not installed"
    echo "     Solution: Run ./scripts/setup.sh"
    echo ""
    echo "  ❌ Background processing not working"
    echo "     Solution: Check ./scripts/process.sh status"
    echo ""
}

# Function to show next steps
show_next_steps() {
    echo -e "${CYAN}🎯 Next Steps${NC}"
    echo "============="
    echo ""
    echo "1. 📦 Setup: ./scripts/setup.sh"
    echo "2. 🔍 Find: ./scripts/find.sh"
    echo "3. 🎤 Process: ./scripts/process.sh start"
    echo "4. 📊 Monitor: ./scripts/process.sh status"
    echo "5. 📖 Read: Check README.md for detailed documentation"
    echo ""
    echo -e "${GREEN}💡 Tip: Use ./scripts/transcriber.sh for quick access to all functions${NC}"
    echo ""
}

# Main help function
main() {
    show_main_help
    show_script_help
    show_examples
    show_project_structure
    show_supported_formats
    show_features
    show_troubleshooting
    show_next_steps
    
    echo -e "${BLUE}🎉 Happy Transcribing!${NC}"
}

# Run main function
main "$@"
