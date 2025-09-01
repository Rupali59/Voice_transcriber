#!/usr/bin/env python3
"""
Parallel Processing CLI for Voice Transcriber
Handles batch processing of multiple audio files with parallel execution
"""

import argparse
import sys
import signal
import time
from pathlib import Path
from typing import List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import ConfigManager
from parallel_processor import ParallelProcessor

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully"""
    print("\n🛑 Received interrupt signal, shutting down gracefully...")
    if hasattr(signal_handler, 'processor') and signal_handler.processor:
        signal_handler.processor.stop()
    sys.exit(0)

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Parallel Voice Transcriber - Process multiple audio files simultaneously",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process multiple files in parallel
  python3 parallel_cli.py --files file1.m4a file2.m4a file3.m4a

  # Process all files in a directory
  python3 parallel_cli.py --dir /path/to/audio/files

  # Process with custom concurrency
  python3 parallel_cli.py --files *.m4a --concurrent 4

  # Monitor processing in real-time
  python3 parallel_cli.py --files *.m4a --monitor

  # Process with priority (higher numbers = higher priority)
  python3 parallel_cli.py --files file1.m4a --priority 10
        """
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--files', '-f',
        nargs='+',
        help='List of audio files to process'
    )
    input_group.add_argument(
        '--dir', '-d',
        type=str,
        help='Directory containing audio files to process'
    )

    # Processing options
    parser.add_argument(
        '--concurrent', '-c',
        type=int,
        help='Number of concurrent processes (overrides config)'
    )
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        help='Batch size for processing (overrides config)'
    )
    parser.add_argument(
        '--priority', '-p',
        type=int,
        default=0,
        help='Priority for jobs (higher = higher priority)'
    )
    parser.add_argument(
        '--max-jobs', '-m',
        type=int,
        help='Maximum number of jobs to process'
    )

    # Output and monitoring options
    parser.add_argument(
        '--monitor', '-M',
        action='store_true',
        help='Enable real-time monitoring'
    )
    parser.add_argument(
        '--stats', '-s',
        action='store_true',
        help='Show statistics after processing'
    )
    parser.add_argument(
        '--env', '-e',
        type=str,
        default='.env',
        help='Environment configuration file'
    )

    return parser

def find_audio_files(directory: str, config: ConfigManager) -> List[str]:
    """Find audio files in a directory"""
    audio_files = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        print(f"❌ Directory not found: {directory}")
        return []
    
    if not dir_path.is_dir():
        print(f"❌ Not a directory: {directory}")
        return []
    
    for pattern in config.input.file_patterns:
        audio_files.extend([str(f) for f in dir_path.rglob(pattern)])
    
    # Remove duplicates and sort
    audio_files = sorted(list(set(audio_files)))
    
    print(f"🎵 Found {len(audio_files)} audio files in {directory}")
    return audio_files

def process_files_parallel(file_paths: List[str], config: ConfigManager, args: argparse.Namespace):
    """Process files using parallel processor"""
    print(f"🚀 Starting parallel processing of {len(file_paths)} files...")
    
    # Override config if specified
    if args.concurrent:
        config.performance.max_concurrent_processes = args.concurrent
    if args.batch_size:
        config.performance.batch_size = args.batch_size
    
    print(f"⚡ Concurrency: {config.performance.max_concurrent_processes}")
    print(f"📦 Batch Size: {config.performance.batch_size}")
    print(f"🎯 Priority: {args.priority}")
    
    # Initialize parallel processor
    processor = ParallelProcessor(config)
    signal_handler.processor = processor
    
    try:
        # Add all files to the queue
        added_count = processor.add_batch(file_paths, args.priority)
        print(f"✅ Added {added_count} files to processing queue")
        
        if args.monitor:
            # Start monitoring thread
            monitor_thread = start_monitoring(processor)
        
        # Process jobs
        start_time = time.time()
        results = processor.process_jobs(args.max_jobs)
        total_time = time.time() - start_time
        
        # Stop monitoring if enabled
        if args.monitor and monitor_thread.is_alive():
            monitor_thread.join(timeout=1)
        
        # Show results
        show_processing_results(results, total_time)
        
        if args.stats:
            processor.print_stats()
        
        return results
        
    finally:
        processor.stop()

def start_monitoring(processor: ParallelProcessor):
    """Start real-time monitoring in a separate thread"""
    def monitor():
        try:
            while True:
                # Clear screen (works on most terminals)
                print("\033[2J\033[H", end="")
                
                # Show current status
                processor.print_stats()
                
                # Show queue status
                stats = processor.get_stats()
                if stats['queue_size'] > 0:
                    print(f"\n📋 Queue Status: {stats['queue_size']} files pending")
                
                print("\n⏳ Monitoring... (Press Ctrl+C to stop)")
                time.sleep(2)
                
        except KeyboardInterrupt:
            pass
    
    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()
    return monitor_thread

def show_processing_results(results: dict, total_time: float):
    """Show processing results summary"""
    print("\n" + "="*50)
    print("📊 Processing Results Summary")
    print("="*50)
    
    successful = sum(1 for r in results.values() if r.success)
    failed = len(results) - successful
    
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Total Time: {total_time:.2f}s")
    
    if successful > 0:
        avg_time = total_time / successful
        print(f"📈 Average Time per File: {avg_time:.2f}s")
        print(f"🚀 Throughput: {successful/total_time:.2f} files/second")
    
    # Show failed files if any
    if failed > 0:
        print(f"\n❌ Failed Files:")
        for file_path, result in results.items():
            if not result.success:
                print(f"   • {Path(file_path).name}: {result.error}")
    
    # Show successful files
    if successful > 0:
        print(f"\n✅ Successful Files:")
        for file_path, result in results.items():
            if result.success:
                print(f"   • {Path(file_path).name} ({result.processing_time:.2f}s)")

def main():
    """Main entry point"""
    setup_signal_handlers()
    
    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = ConfigManager(args.env)
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return 1
    
    # Get file paths
    if args.files:
        file_paths = args.files
    elif args.dir:
        file_paths = find_audio_files(args.dir, config)
        if not file_paths:
            return 1
    else:
        print("❌ No input files or directory specified")
        return 1
    
    # Validate files exist
    valid_files = []
    for file_path in file_paths:
        if Path(file_path).exists():
            valid_files.append(file_path)
        else:
            print(f"⚠️  File not found: {file_path}")
    
    if not valid_files:
        print("❌ No valid files to process")
        return 1
    
    print(f"🎯 Processing {len(valid_files)} valid files")
    
    # Process files
    try:
        results = process_files_parallel(valid_files, config, args)
        return 0 if all(r.success for r in results.values()) else 1
    except KeyboardInterrupt:
        print("\n🛑 Processing interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        return 1

if __name__ == "__main__":
    import threading
    sys.exit(main())
