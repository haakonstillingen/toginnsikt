#!/usr/bin/env python3
"""
Route Validation Test Runner

This script runs all route validation tests in the correct order:
1. Unit tests (fast, no external dependencies)
2. Integration tests (with database/API if available)
3. End-to-end tests (full pipeline simulation)

Usage:
    python run_route_validation_tests.py
    python run_route_validation_tests.py --unit-only
    python run_route_validation_tests.py --integration-only
    python run_route_validation_tests.py --e2e-only
"""

import sys
import os
import argparse
import subprocess
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False


def run_unit_tests():
    """Run unit tests"""
    return run_command(
        "python test_route_validation.py",
        "Running Unit Tests"
    )


def run_integration_tests():
    """Run integration tests"""
    return run_command(
        "python test_route_validation_integration.py",
        "Running Integration Tests"
    )


def run_e2e_tests():
    """Run end-to-end tests"""
    return run_command(
        "python test_route_validation_e2e.py",
        "Running End-to-End Tests"
    )


def run_pytest_tests():
    """Run all tests using pytest if available"""
    return run_command(
        "python -m pytest test_route_validation*.py -v --tb=short",
        "Running All Tests with pytest"
    )


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Run route validation tests")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    parser.add_argument("--e2e-only", action="store_true", help="Run only E2E tests")
    parser.add_argument("--pytest", action="store_true", help="Use pytest instead of unittest")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    print("🚀 Route Validation Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    # Check if test files exist
    test_files = [
        "test_route_validation.py",
        "test_route_validation_integration.py", 
        "test_route_validation_e2e.py"
    ]
    
    missing_files = [f for f in test_files if not os.path.exists(f)]
    if missing_files:
        print(f"❌ Missing test files: {missing_files}")
        return 1
    
    # Run tests based on arguments
    if args.pytest:
        success = run_pytest_tests()
    elif args.unit_only:
        success = run_unit_tests()
    elif args.integration_only:
        success = run_integration_tests()
    elif args.e2e_only:
        success = run_e2e_tests()
    else:
        # Run all tests in sequence
        print("\n🔄 Running all test suites...")
        
        unit_success = run_unit_tests()
        integration_success = run_integration_tests()
        e2e_success = run_e2e_tests()
        
        success = unit_success and integration_success and e2e_success
    
    # Print final summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    if success:
        print("✅ All tests passed successfully!")
        print("🎉 Route validation feature is ready for production")
    else:
        print("❌ Some tests failed")
        print("🔧 Please review the test output and fix any issues")
    
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
