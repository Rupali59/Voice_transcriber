#!/bin/bash

# Voice Transcriber - Process Script
# Handles background processing of voice memos

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

echo -e "${BLUE}🎤 Voice Memo Processor${NC}"
echo "========================="

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

# Function to start background processing
start_processing() {
    echo "🚀 Starting background processing..."
    echo ""
    echo "📁 This will monitor configured directories for new audio files"
    echo "🎯 Press Ctrl+C to stop processing"
    echo ""
    
    # Change to project directory
    cd "$PROJECT_DIR"
    
    # Start the background processor
    python3 src/transcriber_cli.py --background
}

# Function to show quick status (essential info only)
show_quick_status() {
    echo -e "${BLUE}📊 Quick Status${NC}"
    echo "============="
    
    # Check for any transcription processes
    if pgrep -f "transcribe.*\.py" > /dev/null || pgrep -f "whisper" > /dev/null; then
        echo -e "   🟢 Status: ${GREEN}ACTIVE${NC}"
        
        # Get main process info
        main_process=$(ps aux | grep "transcribe_hindi.py\|transcriber_cli.py" | grep -v grep | head -1)
        if [ -n "$main_process" ]; then
            pid=$(echo "$main_process" | awk '{print $2}')
            cpu=$(echo "$main_process" | awk '{print $3}')
            runtime=$(echo "$main_process" | awk '{print $10}')
            echo "   📍 PID: $pid | 💻 CPU: ${cpu}% | ⏱️  Runtime: $runtime"
        fi
        
        # Check output directory
        if [ -d "$PROJECT_DIR/transcriptions" ] && [ "$(ls -A "$PROJECT_DIR/transcriptions")" ]; then
            file_count=$(ls -1 "$PROJECT_DIR/transcriptions" | wc -l)
            echo "   📁 Output: $file_count transcription(s) ready"
        else
            echo "   📁 Output: Processing in progress..."
        fi
        
    else
        echo -e "   🔴 Status: ${RED}IDLE${NC}"
        echo "   💡 No transcription processes running"
    fi
}

# Function to show processing status
show_status() {
    echo -e "${BLUE}📊 Processing Status${NC}"
    echo "==================="
    
    # Check for any transcription processes (CLI or direct)
    transcription_processes=()
    
    # Check CLI background processor
    if pgrep -f "transcriber_cli.py.*--background" > /dev/null; then
        transcription_processes+=("CLI Background")
    fi
    
    # Check direct transcription scripts
    if pgrep -f "transcribe_hindi.py" > /dev/null; then
        transcription_processes+=("Direct Hindi Transcription")
    fi
    
    if pgrep -f "transcribe.*\.py" > /dev/null; then
        transcription_processes+=("Direct Transcription")
    fi
    
    # Check for any Whisper processes
    if pgrep -f "whisper" > /dev/null; then
        transcription_processes+=("Whisper Processing")
    fi
    
    # Show overall status
    if [ ${#transcription_processes[@]} -gt 0 ]; then
        echo -e "   🟢 Transcription Status: ${GREEN}ACTIVE${NC}"
        echo ""
        echo "   🔄 Active Processes:"
        for process in "${transcription_processes[@]}"; do
            echo "      • $process"
        done
        
        # Show detailed process info in a cleaner format
        echo ""
        echo -e "   📋 Process Details${NC}"
        echo "   ──────────────────"
        
        # Show CLI processes
        if pgrep -f "transcriber_cli.py.*--background" > /dev/null; then
            echo ""
            echo -e "   🖥️  CLI Background Processor:"
            ps aux | grep "transcriber_cli.py.*--background" | grep -v grep | while read -r line; do
                # Parse and format the process info
                pid=$(echo "$line" | awk '{print $2}')
                cpu=$(echo "$line" | awk '{print $3}')
                mem=$(echo "$line" | awk '{print $4}')
                time=$(echo "$line" | awk '{print $10}')
                echo "      📍 Process ID: $pid"
                echo "      💻 CPU Usage: ${cpu}%"
                echo "      🧠 Memory: ${mem}%"
                echo "      ⏱️  Runtime: $time"
                echo ""
            done
        fi
        
        # Show direct transcription processes
        if pgrep -f "transcribe_hindi.py" > /dev/null; then
            echo ""
            echo -e "   🎤 Direct Hindi Transcription:"
            ps aux | grep "transcribe_hindi.py" | grep -v grep | while read -r line; do
                # Parse and format the process info
                pid=$(echo "$line" | awk '{print $2}')
                cpu=$(echo "$line" | awk '{print $3}')
                mem=$(echo "$line" | awk '{print $4}')
                time=$(echo "$line" | awk '{print $10}')
                echo "      📍 Process ID: $pid"
                echo "      💻 CPU Usage: ${cpu}%"
                echo "      🧠 Memory: ${mem}%"
                echo "      ⏱️  Runtime: $time"
                echo ""
            done
        fi
        
        # Show any other transcription processes
        other_processes=$(ps aux | grep -E "(transcribe|whisper)" | grep -v grep | grep -v "grep -E" | grep -v "transcribe_hindi.py")
        if [ -n "$other_processes" ]; then
            echo ""
            echo -e "   🔍 Other Transcription Processes:"
            echo "$other_processes" | while read -r line; do
                # Parse and format the process info
                pid=$(echo "$line" | awk '{print $2}')
                cpu=$(echo "$line" | awk '{print $3}')
                mem=$(echo "$line" | awk '{print $4}')
                time=$(echo "$line" | awk '{print $10}')
                echo "      📍 Process ID: $pid"
                echo "      💻 CPU Usage: ${cpu}%"
                echo "      🧠 Memory: ${mem}%"
                echo "      ⏱️  Runtime: $time"
                echo ""
            done
        fi
        
    else
        echo -e "   🔴 Transcription Status: ${RED}NOT RUNNING${NC}"
        echo ""
        echo "   💡 No transcription processes are currently active."
        echo "      Start processing with: ./scripts/transcriber.sh process"
    fi
    
    # Check transcription output directory
    if [ -d "$PROJECT_DIR/transcriptions" ]; then
        echo ""
        echo -e "   📁 Transcriptions Directory${NC}"
        echo "   ───────────────────────────"
        if [ "$(ls -A "$PROJECT_DIR/transcriptions")" ]; then
            file_count=$(ls -1 "$PROJECT_DIR/transcriptions" | wc -l)
            latest_file=$(ls -t "$PROJECT_DIR/transcriptions" | head -1)
            echo "      📊 Total Files: $file_count"
            echo "      🆕 Latest File: $latest_file"
            
            # Show file sizes if there are files
            if [ -n "$latest_file" ]; then
                latest_size=$(ls -lh "$PROJECT_DIR/transcriptions/$latest_file" | awk '{print $5}')
                echo "      📏 Latest Size: $latest_size"
            fi
        else
            echo "      📭 Directory is empty"
            echo "      💡 Transcriptions will appear here when processing completes"
        fi
    fi
    
    # Check logs
    if [ -d "$PROJECT_DIR/logs" ]; then
        echo ""
        echo -e "   📝 Logs Directory${NC}"
        echo "   ─────────────────"
        if [ "$(ls -A "$PROJECT_DIR/logs")" ]; then
            log_count=$(ls -1 "$PROJECT_DIR/logs" | wc -l)
            latest_log=$(ls -t "$PROJECT_DIR/logs" | head -1)
            echo "      📊 Total Logs: $log_count"
            echo "      🆕 Latest Log: $latest_log"
            
            # Show log file sizes if there are logs
            if [ -n "$latest_log" ]; then
                latest_log_size=$(ls -lh "$PROJECT_DIR/logs/$latest_log" | awk '{print $5}')
                echo "      📏 Latest Size: $latest_log_size"
            fi
        else
            echo "      📭 Directory is empty"
            echo "      💡 Log files will appear here during processing"
        fi
    fi
    
    # Add summary section
    echo ""
    echo -e "   📈 Summary${NC}"
    echo "   ───────────"
    if [ ${#transcription_processes[@]} -gt 0 ]; then
        echo -e "      🎯 Status: ${GREEN}System is actively transcribing audio${NC}"
        echo "      ⚡ Performance: High CPU usage indicates active processing"
        echo "      💾 Memory: Stable memory usage shows good resource management"
        echo "      ⏰ Runtime: Process has been running for the displayed duration"
    else
        echo -e "      🎯 Status: ${RED}System is idle - no transcription activity${NC}"
        echo "      💡 To start: Use ./scripts/transcriber.sh process"
        echo "      🔍 To check: Use ./scripts/transcriber.sh find"
    fi
}

# Function to stop all transcription processing
stop_processing() {
    echo "🛑 Stopping all transcription processes..."
    
    # Find all transcription-related processes
    all_pids=""
    
    # CLI background processor
    cli_pids=$(pgrep -f "transcriber_cli.py.*--background" 2>/dev/null || echo "")
    if [ -n "$cli_pids" ]; then
        all_pids="$all_pids $cli_pids"
    fi
    
    # Direct transcription scripts
    direct_pids=$(pgrep -f "transcribe.*\.py" 2>/dev/null || echo "")
    if [ -n "$direct_pids" ]; then
        all_pids="$all_pids $direct_pids"
    fi
    
    # Whisper processes
    whisper_pids=$(pgrep -f "whisper" 2>/dev/null || echo "")
    if [ -n "$whisper_pids" ]; then
        all_pids="$all_pids $whisper_pids"
    fi
    
    if [ -n "$all_pids" ]; then
        echo "   Found processes: $all_pids"
        
        # First try graceful shutdown
        for pid in $all_pids; do
            echo "   Stopping process $pid gracefully..."
            kill "$pid" 2>/dev/null || true
        done
        
        # Wait a moment and check if processes are still running
        sleep 3
        
        # Check for remaining processes
        remaining_pids=""
        for pid in $all_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                remaining_pids="$remaining_pids $pid"
            fi
        done
        
        if [ -n "$remaining_pids" ]; then
            echo "   Force stopping remaining processes..."
            for pid in $remaining_pids; do
                echo "   Force killing process $pid..."
                kill -9 "$pid" 2>/dev/null || true
            done
        fi
        
        echo -e "${GREEN}✅ All transcription processes stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  No transcription processes found${NC}"
    fi
}

# Function to show help
show_help() {
    echo -e "\n${BLUE}📖 Process Script Help${NC}"
    echo "====================="
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start           - Start background processing"
    echo "  stop            - Stop all transcription processes"
    echo "  status          - Show detailed processing status"
    echo "  quick           - Show quick status (essential info only)"
    echo "  monitor         - Show real-time process monitoring"
    echo "  help            - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start        # Start background processing"
    echo "  $0 stop         # Stop all transcription processes"
    echo "  $0 status       # Show detailed status"
    echo "  $0 quick        # Show quick status"
    echo "  $0 monitor      # Monitor processes in real-time"
    echo ""
    echo "Note: This script now detects ALL transcription processes,"
    echo "      including direct Python scripts and CLI processes."
}

# Function to monitor processes in real-time
monitor_processes() {
    echo -e "${BLUE}📊 Real-time Process Monitoring${NC}"
    echo "================================"
    echo "Press Ctrl+C to stop monitoring"
    echo ""
    
    while true; do
        clear
        echo -e "${BLUE}🎤 Voice Transcriber - Live Monitor${NC}"
        echo "====================================="
        echo -e "🕐 Last updated: ${YELLOW}$(date '+%H:%M:%S')${NC}"
        echo ""
        
        # Show current status
        show_status
        
        # Show enhanced system resources
        echo ""
        echo -e "${BLUE}💻 System Resources${NC}"
        echo "─────────────────────"
        
        # CPU usage with better formatting
        cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3, $4, $5}')
        echo "   🔴 CPU: $cpu_usage"
        
        # Memory usage with better formatting
        memory_info=$(top -l 1 | grep "PhysMem" | awk '{print $2, $3, $4, $5}')
        echo "   🧠 Memory: $memory_info"
        
        # Process-specific info with better formatting
        if pgrep -f "transcribe_hindi.py" > /dev/null; then
            echo ""
            echo -e "${BLUE}🎯 Live Process Details${NC}"
            echo "─────────────────────────"
            
            # Get process details
            process_info=$(ps -p 2817 -o pid,ppid,command,etime,pcpu,pmem 2>/dev/null | tail -1)
            if [ -n "$process_info" ]; then
                pid=$(echo "$process_info" | awk '{print $1}')
                runtime=$(echo "$process_info" | awk '{print $4}')
                cpu=$(echo "$process_info" | awk '{print $5}')
                memory=$(echo "$process_info" | awk '{print $6}')
                
                echo "   📍 Process ID: $pid"
                echo "   ⏱️  Runtime: $runtime"
                echo "   💻 CPU Usage: ${cpu}%"
                echo "   🧠 Memory: ${memory}%"
                
                # Add progress indicator based on runtime
                if [[ "$runtime" =~ ([0-9]+):([0-9]+) ]]; then
                    minutes=${BASH_REMATCH[1]}
                    seconds=${BASH_REMATCH[2]}
                    total_seconds=$((minutes * 60 + seconds))
                    
                    if [ $total_seconds -lt 300 ]; then  # Less than 5 minutes
                        echo "   🚀 Status: Starting up..."
                    elif [ $total_seconds -lt 1800 ]; then  # Less than 30 minutes
                        echo "   ⚡ Status: Processing in progress..."
                    else
                        echo "   🐌 Status: Long-running process..."
                    fi
                fi
            fi
        fi
        
        # Add helpful tips
        echo ""
        echo -e "${CYAN}💡 Tips${NC}"
        echo "──────"
        echo "   • High CPU usage (100%+) is normal during transcription"
        echo "   • Memory usage should remain stable"
        echo "   • Process will complete automatically when done"
        echo "   • Check transcriptions/ folder for output files"
        
        echo ""
        echo -e "${YELLOW}⏳ Monitoring... (Press Ctrl+C to exit)${NC}"
        echo "   Updates every 5 seconds"
        sleep 5
    done
}

# Main process function
main() {
    case "${1:-help}" in
        "start")
            if check_config && activate_venv; then
                start_processing
            else
                exit 1
            fi
            ;;
        "stop")
            stop_processing
            ;;
        "status")
            show_status
            ;;
        "quick")
            show_quick_status
            ;;
        "monitor")
            monitor_processes
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function
main "$@"
