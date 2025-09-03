#!/usr/bin/env python3
"""
Comprehensive test runner for Voice Transcriber system
Runs all tests with proper configuration and reporting
"""

import sys
import os
import unittest
import time
import argparse
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def run_unit_tests():
    """Run unit tests"""
    print("🧪 Running Unit Tests...")
    print("=" * 50)
    
    # Discover and run unit tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / "unit"
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_integration_tests():
    """Run integration tests"""
    print("\n🔗 Running Integration Tests...")
    print("=" * 50)
    
    # Discover and run integration tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / "integration"
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_performance_tests():
    """Run performance tests"""
    print("\n🚀 Running Performance Tests...")
    print("=" * 50)
    
    # Discover and run performance tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / "performance"
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_load_tests():
    """Run load tests"""
    print("\n⚡ Running Load Tests...")
    print("=" * 50)
    
    # Discover and run load tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / "load"
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_ux_tests():
    """Run UX tests"""
    print("\n🎨 Running UX Tests...")
    print("=" * 50)
    
    # Discover and run UX tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / "ux"
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_pytest_tests():
    """Run tests using pytest with coverage"""
    print("\n🔬 Running Pytest Tests with Coverage...")
    print("=" * 50)
    
    try:
        # Run pytest with coverage
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "--cov=app",
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml",
            "-v"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except FileNotFoundError:
        print("⚠️  Pytest not found. Install with: pip install pytest pytest-cov")
        return False

def run_specific_test_category(category):
    """Run tests for a specific category"""
    print(f"🎯 Running {category.title()} Tests...")
    print("=" * 50)
    
    test_dir = Path(__file__).parent / category
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return False
    
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_specific_test_file(test_file):
    """Run a specific test file"""
    print(f"🎯 Running Specific Test: {test_file}")
    print("=" * 50)
    
    test_path = Path(__file__).parent / test_file
    if not test_path.exists():
        print(f"❌ Test file not found: {test_path}")
        return False
    
    # Load and run specific test
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(str(test_path.with_suffix('')).replace('/', '.'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_all_tests():
    """Run all test suites"""
    print("🎯 Voice Transcriber Comprehensive Test Suite")
    print("=" * 60)
    print(f"Python Version: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Test Directory: {Path(__file__).parent}")
    print("=" * 60)
    
    start_time = time.time()
    
    # Run test suites
    unit_success = run_unit_tests()
    integration_success = run_integration_tests()
    performance_success = run_performance_tests()
    load_success = run_load_tests()
    ux_success = run_ux_tests()
    
    total_time = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    print(f"Unit Tests: {'✅ PASSED' if unit_success else '❌ FAILED'}")
    print(f"Integration Tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    print(f"Performance Tests: {'✅ PASSED' if performance_success else '❌ FAILED'}")
    print(f"Load Tests: {'✅ PASSED' if load_success else '❌ FAILED'}")
    print(f"UX Tests: {'✅ PASSED' if ux_success else '❌ FAILED'}")
    print(f"Total Time: {total_time:.2f} seconds")
    
    overall_success = unit_success and integration_success and performance_success and load_success and ux_success
    print(f"\nOverall Result: {'🎉 ALL TESTS PASSED' if overall_success else '💥 SOME TESTS FAILED'}")
    
    return overall_success

def run_quick_tests():
    """Run quick tests only (unit tests)"""
    print("⚡ Running Quick Tests (Unit Tests Only)...")
    print("=" * 50)
    
    start_time = time.time()
    success = run_unit_tests()
    total_time = time.time() - start_time
    
    print(f"\nQuick Tests {'✅ PASSED' if success else '❌ FAILED'} in {total_time:.2f} seconds")
    return success

def run_model_cache_tests():
    """Run model cache specific tests"""
    print("🗄️ Running Model Cache Tests...")
    print("=" * 50)
    
    start_time = time.time()
    
    # Run model cache unit tests
    unit_success = run_specific_test_file("unit/test_model_cache.py")
    
    # Run model cache integration tests
    integration_success = run_specific_test_file("integration/test_model_cache_integration.py")
    
    # Run model cache performance tests
    performance_success = run_specific_test_file("performance/test_model_cache_performance.py")
    
    total_time = time.time() - start_time
    
    print(f"\nModel Cache Tests Summary:")
    print(f"Unit Tests: {'✅ PASSED' if unit_success else '❌ FAILED'}")
    print(f"Integration Tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    print(f"Performance Tests: {'✅ PASSED' if performance_success else '❌ FAILED'}")
    print(f"Total Time: {total_time:.2f} seconds")
    
    overall_success = unit_success and integration_success and performance_success
    print(f"\nModel Cache Tests: {'🎉 ALL PASSED' if overall_success else '💥 SOME FAILED'}")
    
    return overall_success

def main():
    """Main test runner with argument parsing"""
    parser = argparse.ArgumentParser(description="Voice Transcriber Test Runner")
    parser.add_argument("--category", choices=["unit", "integration", "performance", "load", "ux"], 
                       help="Run tests for specific category")
    parser.add_argument("--file", help="Run specific test file")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only")
    parser.add_argument("--model-cache", action="store_true", help="Run model cache tests only")
    parser.add_argument("--load-only", action="store_true", help="Run load tests only")
    parser.add_argument("--ux-only", action="store_true", help="Run UX tests only")
    parser.add_argument("--pytest", action="store_true", help="Run tests using pytest")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    
    args = parser.parse_args()
    
    if args.quick:
        success = run_quick_tests()
    elif args.model_cache:
        success = run_model_cache_tests()
    elif args.load_only:
        success = run_load_tests()
    elif args.ux_only:
        success = run_ux_tests()
    elif args.pytest:
        success = run_pytest_tests()
    elif args.category:
        success = run_specific_test_category(args.category)
    elif args.file:
        success = run_specific_test_file(args.file)
    else:
        # Default: run all tests
        success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
