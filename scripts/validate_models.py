#!/usr/bin/env python3
"""
Model Validation Script for EchoScribe
Validates that Whisper models are correctly loaded and functioning
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.model_validator import get_model_validator
from app.services.model_cache_manager import get_model_cache_manager

def main():
    """Main validation script"""
    parser = argparse.ArgumentParser(description='Validate Whisper models')
    parser.add_argument('--models', nargs='+', 
                       choices=['tiny', 'base', 'small', 'medium', 'large'],
                       default=['base', 'small'],
                       help='Models to validate (default: base small)')
    parser.add_argument('--output', '-o', 
                       help='Output file for validation report')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--quick', '-q', action='store_true',
                       help='Quick validation (skip some tests)')
    parser.add_argument('--cache-models', action='store_true',
                       help='Use cached models if available')
    parser.add_argument('--preload', action='store_true',
                       help='Preload models before validation')
    
    args = parser.parse_args()
    
    print("🔍 EchoScribe Model Validation")
    print("=" * 50)
    print(f"Models to validate: {', '.join(args.models)}")
    print(f"Quick mode: {args.quick}")
    print(f"Use cache: {args.cache_models}")
    print(f"Preload: {args.preload}")
    print()
    
    # Initialize validator
    validator = get_model_validator()
    
    # Initialize cache manager if using cache
    cache_manager = None
    if args.cache_models or args.preload:
        try:
            cache_manager = get_model_cache_manager()
            print("✅ Cache manager initialized")
        except Exception as e:
            print(f"⚠️  Cache manager failed: {e}")
            cache_manager = None
    
    # Preload models if requested
    if args.preload and cache_manager:
        print(f"🔄 Preloading models: {args.models}")
        try:
            cache_manager.preload_models(args.models)
            print("✅ Models preloaded")
        except Exception as e:
            print(f"⚠️  Preloading failed: {e}")
    
    # Validate models
    print("\n🚀 Starting model validation...")
    start_time = time.time()
    
    try:
        if args.cache_models and cache_manager:
            # Validate using cached models
            results = {}
            for model_size in args.models:
                print(f"\n📋 Validating {model_size}...")
                
                # Get model from cache
                model = cache_manager.get_model(model_size)
                if model is None:
                    print(f"❌ Model {model_size} not available in cache")
                    continue
                
                # Validate model
                result = validator.validate_model(model_size, model)
                results[model_size] = result
                
                # Print result
                status_emoji = "✅" if result['status'] == 'passed' else "❌"
                print(f"{status_emoji} {model_size}: {result['status']} (score: {result['overall_score']:.2f})")
                
                if args.verbose:
                    for test_name, test_result in result['tests'].items():
                        test_emoji = "✅" if test_result['passed'] else "❌"
                        print(f"  {test_emoji} {test_name}: {test_result['score']:.2f}")
        else:
            # Validate all models at once
            results = validator.validate_all_models(args.models)
            
            # Print results
            for model_size, result in results['models'].items():
                status_emoji = "✅" if result['status'] == 'passed' else "❌"
                print(f"{status_emoji} {model_size}: {result['status']} (score: {result['overall_score']:.2f})")
                
                if args.verbose:
                    for test_name, test_result in result['tests'].items():
                        test_emoji = "✅" if test_result['passed'] else "❌"
                        print(f"  {test_emoji} {test_name}: {test_result['score']:.2f}")
        
        validation_time = time.time() - start_time
        print(f"\n⏱️  Validation completed in {validation_time:.2f} seconds")
        
        # Print summary
        if isinstance(results, dict) and 'summary' in results:
            summary = results['summary']
            print(f"\n📊 Summary:")
            print(f"  Total models: {summary['total_models']}")
            print(f"  Passed: {summary['passed_models']}")
            print(f"  Failed: {summary['failed_models']}")
            print(f"  Average score: {summary['average_score']:.2f}")
            print(f"  Overall status: {results['overall_status']}")
        else:
            # Individual results summary
            passed = sum(1 for result in results.values() if result['status'] == 'passed')
            total = len(results)
            avg_score = sum(result['overall_score'] for result in results.values()) / total
            print(f"\n📊 Summary:")
            print(f"  Total models: {total}")
            print(f"  Passed: {passed}")
            print(f"  Failed: {total - passed}")
            print(f"  Average score: {avg_score:.2f}")
        
        # Save report if requested
        if args.output:
            print(f"\n💾 Saving report to: {args.output}")
            validator.save_validation_report(results, args.output)
        elif not args.quick:
            # Auto-save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"model_validation_report_{timestamp}.json"
            print(f"\n💾 Auto-saving report to: {report_file}")
            validator.save_validation_report(results, report_file)
        
        # Exit with appropriate code
        if isinstance(results, dict) and 'overall_status' in results:
            if results['overall_status'] == 'passed':
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            # Check individual results
            all_passed = all(result['status'] == 'passed' for result in results.values())
            sys.exit(0 if all_passed else 1)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
