#!/usr/bin/env python3
"""
Comprehensive Test Runner for EchoScribe
Runs all unit, integration, and validation tests for the model caching and validation system
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"Command: {command}")
    print()
    
    start_time = time.time()
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED ({duration:.2f}s)")
            if result.stdout:
                print("Output:")
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} - FAILED ({duration:.2f}s)")
            if result.stderr:
                print("Error:")
                print(result.stderr)
            if result.stdout:
                print("Output:")
                print(result.stdout)
            return False
    except Exception as e:
        duration = time.time() - start_time
        print(f"💥 {description} - ERROR ({duration:.2f}s): {e}")
        return False

def run_tests(test_type, verbose=False, coverage=False, specific_test=None):
    """Run tests based on type"""
    base_cmd = "python -m pytest"
    
    if verbose:
        base_cmd += " -v"
    
    if coverage:
        base_cmd += " --cov=app --cov-report=html --cov-report=term"
    
    if specific_test:
        base_cmd += f" {specific_test}"
    
    # Test configurations
    test_configs = {
        'unit': {
            'command': f"{base_cmd} tests/unit/",
            'description': "Unit Tests - Model Cache, Validation, and API Endpoints"
        },
        'integration': {
            'command': f"{base_cmd} tests/integration/",
            'description': "Integration Tests - Complete Workflow and Component Integration"
        },
        'validation': {
            'command': f"{base_cmd} tests/unit/test_model_cache.py::TestModelValidator",
            'description': "Model Validation Tests - Comprehensive Model Testing"
        },
        'caching': {
            'command': f"{base_cmd} tests/unit/test_model_cache.py::TestPersistentModelCache tests/unit/test_model_cache.py::TestModelCacheManager",
            'description': "Model Caching Tests - Persistent Cache and Cache Manager"
        },
        'api': {
            'command': f"{base_cmd} tests/unit/test_api_endpoints.py",
            'description': "API Endpoint Tests - All API Routes and Validation Endpoints"
        },
        'performance': {
            'command': f"{base_cmd} tests/performance/",
            'description': "Performance Tests - Model Cache Performance and Benchmarks"
        },
        'load': {
            'command': f"{base_cmd} tests/load/",
            'description': "Load Tests - Concurrent Load and System Limits"
        },
        'all': {
            'command': f"{base_cmd} tests/",
            'description': "All Tests - Complete Test Suite"
        }
    }
    
    if test_type not in test_configs:
        print(f"❌ Unknown test type: {test_type}")
        print(f"Available types: {', '.join(test_configs.keys())}")
        return False
    
    config = test_configs[test_type]
    return run_command(config['command'], config['description'])

def run_validation_script():
    """Run the model validation script"""
    script_path = project_root / "scripts" / "validate_models.py"
    command = f"python {script_path} --models base small --verbose"
    return run_command(command, "Model Validation Script - Real Model Testing")

def run_test_validation_script():
    """Run the test validation script"""
    script_path = project_root / "scripts" / "test_model_validation.py"
    command = f"python {script_path}"
    return run_command(command, "Test Validation Script - System Health Check")

def check_dependencies():
    """Check if all required dependencies are available"""
    print(f"\n{'='*60}")
    print("🔍 Checking Dependencies")
    print(f"{'='*60}")
    
    dependencies = [
        ('pytest', 'pytest'),
        ('whisper', 'openai-whisper'),
        ('torch', 'torch'),
        ('flask', 'flask'),
        ('numpy', 'numpy'),
        ('psutil', 'psutil')
    ]
    
    missing_deps = []
    
    for dep_name, pip_name in dependencies:
        try:
            __import__(dep_name)
            print(f"✅ {dep_name}")
        except ImportError:
            print(f"❌ {dep_name} (install with: pip install {pip_name})")
            missing_deps.append(pip_name)
    
    if missing_deps:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install " + " ".join(missing_deps))
        return False
    else:
        print("\n✅ All dependencies available")
        return True

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description='Comprehensive Test Runner for EchoScribe')
    parser.add_argument('--type', '-t', 
                       choices=['unit', 'integration', 'validation', 'caching', 'api', 'performance', 'load', 'all'],
                       default='all',
                       help='Type of tests to run (default: all)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--coverage', '-c', action='store_true',
                       help='Generate coverage report')
    parser.add_argument('--specific', '-s',
                       help='Run specific test file or test function')
    parser.add_argument('--skip-deps', action='store_true',
                       help='Skip dependency check')
    parser.add_argument('--validation-script', action='store_true',
                       help='Run model validation script')
    parser.add_argument('--test-script', action='store_true',
                       help='Run test validation script')
    
    args = parser.parse_args()
    
    print("🚀 EchoScribe Comprehensive Test Runner")
    print("=" * 60)
    print(f"Test Type: {args.type}")
    print(f"Verbose: {args.verbose}")
    print(f"Coverage: {args.coverage}")
    print(f"Specific Test: {args.specific or 'None'}")
    print()
    
    # Check dependencies
    if not args.skip_deps:
        if not check_dependencies():
            print("\n❌ Dependency check failed. Use --skip-deps to continue anyway.")
            return 1
    
    # Run tests
    start_time = time.time()
    success = True
    
    # Run main tests
    if not run_tests(args.type, args.verbose, args.coverage, args.specific):
        success = False
    
    # Run validation script if requested
    if args.validation_script:
        if not run_validation_script():
            success = False
    
    # Run test validation script if requested
    if args.test_script:
        if not run_test_validation_script():
            success = False
    
    total_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    if success:
        print(f"✅ All tests completed successfully! ({total_time:.2f}s)")
        print("\n💡 Next steps:")
        print("   1. Check coverage report: open htmlcov/index.html")
        print("   2. Run model validation: python scripts/validate_models.py")
        print("   3. Test API endpoints: curl http://localhost:5001/api/validate/models/health-check")
    else:
        print(f"❌ Some tests failed! ({total_time:.2f}s)")
        print("\n💡 Troubleshooting:")
        print("   1. Check test output above for specific errors")
        print("   2. Verify dependencies: pip install -r requirements.txt")
        print("   3. Check configuration: python scripts/validate_models.py --help")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
