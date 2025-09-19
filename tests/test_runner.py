"""
Test runner for the GNN Attack Path project.

Organizes and runs unit and integration tests with proper reporting.
"""
import pytest
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_unit_tests():
    """Run all unit tests."""
    print("🧪 Running Unit Tests...")
    print("=" * 50)
    
    unit_test_dir = project_root / "tests" / "unit"
    result = pytest.main([
        str(unit_test_dir),
        "-v",
        "--tb=short",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov/unit",
        "--junitxml=test-results/unit-tests.xml"
    ])
    
    return result


def run_integration_tests():
    """Run all integration tests."""
    print("\n🔗 Running Integration Tests...")
    print("=" * 50)
    
    integration_test_dir = project_root / "tests" / "integration"
    result = pytest.main([
        str(integration_test_dir),
        "-v",
        "--tb=short",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov/integration",
        "--junitxml=test-results/integration-tests.xml"
    ])
    
    return result


def run_all_tests():
    """Run all tests (unit + integration)."""
    print("🚀 Running All Tests...")
    print("=" * 50)
    
    test_dir = project_root / "tests"
    result = pytest.main([
        str(test_dir),
        "-v",
        "--tb=short",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov/all",
        "--cov-report=xml:coverage.xml",
        "--junitxml=test-results/all-tests.xml"
    ])
    
    return result


def run_specific_module(module_name):
    """Run tests for a specific module."""
    print(f"🎯 Running Tests for {module_name}...")
    print("=" * 50)
    
    test_files = {
        "baseline": "tests/unit/test_baseline_scorers.py",
        "gnn": "tests/unit/test_gnn_models.py",
        "mcp": "tests/unit/test_mcp_components.py",
        "data": "tests/unit/test_data_generation.py",
        "agent": "tests/unit/test_agent_components.py",
        "api": "tests/unit/test_api_endpoints.py",
        "workflow": "tests/integration/test_end_to_end_workflow.py",
        "integration": "tests/integration/test_mcp_integration.py"
    }
    
    if module_name not in test_files:
        print(f"❌ Unknown module: {module_name}")
        print(f"Available modules: {', '.join(test_files.keys())}")
        return 1
    
    test_file = project_root / test_files[module_name]
    result = pytest.main([
        str(test_file),
        "-v",
        "--tb=short",
        "--cov=.",
        "--cov-report=term-missing"
    ])
    
    return result


def main():
    """Main test runner function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="GNN Attack Path Test Runner")
    parser.add_argument(
        "test_type",
        choices=["unit", "integration", "all", "module"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "--module",
        help="Specific module to test (required when test_type=module)"
    )
    
    args = parser.parse_args()
    
    # Create test results directory
    os.makedirs("test-results", exist_ok=True)
    os.makedirs("htmlcov", exist_ok=True)
    
    if args.test_type == "unit":
        result = run_unit_tests()
    elif args.test_type == "integration":
        result = run_integration_tests()
    elif args.test_type == "all":
        result = run_all_tests()
    elif args.test_type == "module":
        if not args.module:
            print("❌ Module name required when using test_type=module")
            return 1
        result = run_specific_module(args.module)
    
    if result == 0:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    return result


if __name__ == "__main__":
    sys.exit(main())
