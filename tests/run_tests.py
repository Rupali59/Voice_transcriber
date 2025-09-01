#!/usr/bin/env python3
"""
Test runner for Voice Transcriber system
Runs all tests with proper configuration and reporting
"""

import sys
import os
import unittest
import time
from pathlib import Path

# Add src to path
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

def run_all_tests():
    """Run all test suites"""
    print("🎯 Voice Transcriber Test Suite")
    print("=" * 50)
    print(f"Python Version: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Test Directory: {Path(__file__).parent}")
    print("=" * 50)
    
    start_time = time.time()
    
    # Run test suites
    unit_success = run_unit_tests()
    integration_success = run_integration_tests()
    performance_success = run_performance_tests()
    
    total_time = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    print(f"Unit Tests: {'✅ PASSED' if unit_success else '❌ FAILED'}")
    print(f"Integration Tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    print(f"Performance Tests: {'✅ PASSED' if performance_success else '❌ FAILED'}")
    print(f"Total Time: {total_time:.2f} seconds")
    
    overall_success = unit_success and integration_success and performance_success
    print(f"\nOverall Result: {'🎉 ALL TESTS PASSED' if overall_success else '💥 SOME TESTS FAILED'}")
    
    return overall_success

def run_specific_test(test_path):
    """Run a specific test file"""
    print(f"🎯 Running Specific Test: {test_path}")
    print("=" * 50)
    
    # Load and run specific test
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_path)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        # Run specific test
        test_path = sys.argv[1]
        success = run_specific_test(test_path)
    else:
        # Run all tests
        success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
