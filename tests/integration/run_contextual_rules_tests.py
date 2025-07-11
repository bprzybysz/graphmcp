#!/usr/bin/env python3
"""
Test Runner for ContextualRulesEngine Integration Tests

This script provides a comprehensive test runner for the contextual rules engine
integration tests with detailed reporting, performance metrics, and easy execution.

Usage:
    python tests/integration/run_contextual_rules_tests.py [options]

Options:
    --verbose       Show detailed output
    --performance   Run performance tests only
    --fast          Skip performance tests for faster execution
    --pattern       Run tests matching pattern (e.g., --pattern terraform)
"""

import sys
import os
import asyncio
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class IntegrationTestRunner:
    """Comprehensive test runner for contextual rules integration tests."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "performance_metrics": {},
            "start_time": None,
            "end_time": None
        }
    
    def run_tests(self, pattern: str = None, performance_only: bool = False, skip_performance: bool = False):
        """Run the integration tests with specified options."""
        self.results["start_time"] = time.time()
        
        print("🚀 ContextualRulesEngine Integration Test Runner")
        print("=" * 60)
        
        try:
            # Setup test environment
            self._setup_environment()
            
            # Determine which tests to run
            test_commands = self._build_test_commands(pattern, performance_only, skip_performance)
            
            # Run tests
            for test_name, command in test_commands.items():
                print(f"\n📋 Running {test_name}...")
                self._run_test_command(test_name, command)
            
            # Generate final report
            self._generate_report()
            
        except Exception as e:
            print(f"❌ Test runner failed: {e}")
            self.results["errors"].append(f"Runner error: {str(e)}")
            return False
        
        finally:
            self.results["end_time"] = time.time()
        
        return self.results["failed"] == 0
    
    def _setup_environment(self):
        """Setup the test environment."""
        print("🔧 Setting up test environment...")
        
        # Verify virtual environment
        if not os.environ.get("VIRTUAL_ENV"):
            print("⚠️  Warning: Not running in virtual environment")
        
        # Check required modules
        required_modules = [
            "concrete.contextual_rules_engine",
            "concrete.source_type_classifier"
        ]
        
        for module in required_modules:
            try:
                __import__(module)
                if self.verbose:
                    print(f"✅ Module {module} imported successfully")
            except ImportError as e:
                error_msg = f"Failed to import {module}: {e}"
                self.results["errors"].append(error_msg)
                raise ImportError(error_msg)
        
        print("✅ Environment setup complete")
    
    def _build_test_commands(self, pattern: str, performance_only: bool, skip_performance: bool) -> Dict[str, List[str]]:
        """Build pytest commands for different test categories."""
        base_path = "tests/integration/test_contextual_rules_integration.py"
        commands = {}
        
        if performance_only:
            commands["Performance Tests"] = [
                "python", "-m", "pytest", f"{base_path}::TestContextualRulesEnginePerformance", "-v"
            ]
        else:
            # Rule definition tests
            commands["Rule Definitions"] = [
                "python", "-m", "pytest", f"{base_path}::TestContextualRulesEngineIntegration::test_load_infrastructure_rules",
                f"{base_path}::TestContextualRulesEngineIntegration::test_load_config_rules",
                f"{base_path}::TestContextualRulesEngineIntegration::test_load_sql_rules",
                f"{base_path}::TestContextualRulesEngineIntegration::test_load_python_rules",
                f"{base_path}::TestContextualRulesEngineIntegration::test_load_documentation_rules",
                "-v"
            ]
            
            # Framework detection tests
            commands["Framework Detection"] = [
                "python", "-m", "pytest", f"{base_path}::TestContextualRulesEngineIntegration::test_terraform_framework_detection",
                f"{base_path}::TestContextualRulesEngineIntegration::test_helm_framework_detection",
                f"{base_path}::TestContextualRulesEngineIntegration::test_django_framework_detection",
                f"{base_path}::TestContextualRulesEngineIntegration::test_kubernetes_framework_detection",
                "-v"
            ]
            
            # Pattern matching tests
            commands["Pattern Matching"] = [
                "python", "-m", "pytest", f"{base_path}::TestContextualRulesEngineIntegration::test_terraform_resource_pattern_matching",
                f"{base_path}::TestContextualRulesEngineIntegration::test_sql_pattern_matching",
                f"{base_path}::TestContextualRulesEngineIntegration::test_python_connection_pattern_matching",
                "-v"
            ]
            
            # Rule action tests
            commands["Rule Actions"] = [
                "python", "-m", "pytest", f"{base_path}::TestContextualRulesEngineIntegration::test_comment_out_patterns_method",
                f"{base_path}::TestContextualRulesEngineIntegration::test_add_deprecation_notice_method",
                f"{base_path}::TestContextualRulesEngineIntegration::test_remove_matching_lines_method",
                "-v"
            ]
            
            # End-to-end tests
            commands["End-to-End Processing"] = [
                "python", "-m", "pytest", f"{base_path}::TestContextualRulesEngineIntegration::test_terraform_file_processing_end_to_end",
                f"{base_path}::TestContextualRulesEngineIntegration::test_python_django_file_processing_end_to_end",
                f"{base_path}::TestContextualRulesEngineIntegration::test_sql_file_processing_end_to_end",
                "-v"
            ]
            
            # Error handling tests
            commands["Error Handling"] = [
                "python", "-m", "pytest", f"{base_path}::TestContextualRulesEngineIntegration::test_empty_file_processing",
                f"{base_path}::TestContextualRulesEngineIntegration::test_no_matching_patterns",
                f"{base_path}::TestContextualRulesEngineIntegration::test_invalid_regex_pattern_handling",
                "-v"
            ]
            
            # Performance tests (if not skipped)
            if not skip_performance:
                commands["Performance Tests"] = [
                    "python", "-m", "pytest", f"{base_path}::TestContextualRulesEnginePerformance", "-v"
                ]
        
        # Filter by pattern if specified
        if pattern:
            filtered_commands = {}
            for name, command in commands.items():
                if pattern.lower() in name.lower():
                    filtered_commands[name] = command
            commands = filtered_commands
        
        return commands
    
    def _run_test_command(self, test_name: str, command: List[str]):
        """Run a single test command and capture results."""
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per test category
            )
            
            duration = time.time() - start_time
            self.results["performance_metrics"][test_name] = duration
            
            if result.returncode == 0:
                self.results["passed"] += 1
                print(f"✅ {test_name} - PASSED ({duration:.2f}s)")
                
                if self.verbose:
                    print(f"📋 Output:\n{result.stdout}")
                    
            else:
                self.results["failed"] += 1
                error_msg = f"{test_name} - FAILED ({duration:.2f}s)"
                print(f"❌ {error_msg}")
                print(f"📋 Error Output:\n{result.stderr}")
                
                self.results["errors"].append({
                    "test": test_name,
                    "returncode": result.returncode,
                    "stderr": result.stderr,
                    "stdout": result.stdout
                })
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.results["failed"] += 1
            error_msg = f"{test_name} - TIMEOUT ({duration:.2f}s)"
            print(f"⏱️ {error_msg}")
            self.results["errors"].append({
                "test": test_name,
                "error": "Timeout after 5 minutes"
            })
            
        except Exception as e:
            duration = time.time() - start_time
            self.results["failed"] += 1
            error_msg = f"{test_name} - ERROR ({duration:.2f}s): {str(e)}"
            print(f"💥 {error_msg}")
            self.results["errors"].append({
                "test": test_name,
                "error": str(e)
            })
    
    def _generate_report(self):
        """Generate a comprehensive test report."""
        total_duration = self.results["end_time"] - self.results["start_time"]
        total_tests = self.results["passed"] + self.results["failed"]
        
        print("\n" + "=" * 60)
        print("📊 INTEGRATION TEST RESULTS")
        print("=" * 60)
        
        print(f"📈 Summary:")
        print(f"   • Total Tests Run: {total_tests}")
        print(f"   • Passed: {self.results['passed']}")
        print(f"   • Failed: {self.results['failed']}")
        print(f"   • Success Rate: {(self.results['passed']/total_tests*100):.1f}%" if total_tests > 0 else "   • Success Rate: N/A")
        print(f"   • Total Duration: {total_duration:.2f}s")
        
        if self.results["performance_metrics"]:
            print(f"\n⏱️  Performance Breakdown:")
            for test_name, duration in self.results["performance_metrics"].items():
                print(f"   • {test_name}: {duration:.2f}s")
        
        if self.results["errors"]:
            print(f"\n❌ Failed Tests:")
            for error in self.results["errors"]:
                if isinstance(error, dict):
                    print(f"   • {error.get('test', 'Unknown')}: {error.get('error', 'Unknown error')}")
                else:
                    print(f"   • {error}")
        
        # Generate recommendations
        self._generate_recommendations()
    
    def _generate_recommendations(self):
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Performance recommendations
        slow_tests = [
            name for name, duration in self.results["performance_metrics"].items()
            if duration > 30  # Tests taking more than 30 seconds
        ]
        
        if slow_tests:
            recommendations.append(
                f"⚡ Performance: Consider optimizing {', '.join(slow_tests)} (>30s execution time)"
            )
        
        # Coverage recommendations
        if self.results["failed"] > 0:
            recommendations.append(
                "🔧 Quality: Review failed tests and fix underlying issues before production deployment"
            )
        
        if self.results["passed"] == 0:
            recommendations.append(
                "🚨 Critical: No tests passed - verify test environment and dependencies"
            )
        
        # Success recommendations
        if self.results["failed"] == 0 and self.results["passed"] > 0:
            recommendations.append(
                "🎉 Excellent: All integration tests passed - ContextualRulesEngine is ready for production"
            )
        
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   • {rec}")


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Run ContextualRulesEngine integration tests",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed test output"
    )
    
    parser.add_argument(
        "--performance",
        action="store_true", 
        help="Run performance tests only"
    )
    
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip performance tests for faster execution"
    )
    
    parser.add_argument(
        "--pattern",
        type=str,
        help="Run tests matching pattern (e.g., 'terraform' or 'framework')"
    )
    
    args = parser.parse_args()
    
    # Create and run tests
    runner = IntegrationTestRunner(verbose=args.verbose)
    success = runner.run_tests(
        pattern=args.pattern,
        performance_only=args.performance,
        skip_performance=args.fast
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 