#!/usr/bin/env python3
"""
CLI Performance Test Runner

This script provides comprehensive performance testing for the CLI with various
configuration options and reporting capabilities.

Usage:
    python scripts/run_performance_tests.py [--quick] [--benchmark] [--stress] [--report]
"""

import os
import sys
import subprocess
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Any
import tempfile
import shutil

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class PerformanceTestRunner:
    """Comprehensive performance test runner for the CLI."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results = {}
        self.project_root = PROJECT_ROOT
    
    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")
    
    def run_test_suite(self, test_module: str, markers: List[str] = None, 
                      extra_args: List[str] = None) -> Dict[str, Any]:
        """Run a specific test suite and return results."""
        cmd = ["poetry", "run", "pytest", test_module, "-v"]
        
        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])
        
        if extra_args:
            cmd.extend(extra_args)
        
        self.log(f"Running: {' '.join(cmd)}")
        
        start_time = time.time()
        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        duration = time.time() - start_time
        
        return {
            'command': ' '.join(cmd),
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'duration': duration,
            'success': result.returncode == 0
        }
    
    def run_unittest_suite(self, test_module: str, test_class: str = None,
                          timeout: int = 300) -> Dict[str, Any]:
        """Run unittest-based performance tests."""
        cmd = ["poetry", "run", "python", "-m", "pytest", test_module, "-v"]
        
        if test_class:
            cmd.append(f"::{test_class}")
        
        self.log(f"Running unittest suite: {' '.join(cmd)}")
        
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            duration = time.time() - start_time
            
            return {
                'command': ' '.join(cmd),
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'duration': duration,
                'success': result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                'command': ' '.join(cmd),
                'returncode': -1,
                'error': 'timeout',
                'duration': timeout,
                'success': False
            }
    
    def run_benchmark_tests(self) -> Dict[str, Any]:
        """Run pytest-benchmark based performance tests."""
        self.log("Running benchmark tests...")
        
        return self.run_test_suite(
            "tests/cli/test_cli_benchmarks.py",
            extra_args=[
                "--benchmark-only",
                "--benchmark-sort=mean",
                "--benchmark-columns=min,max,mean,stddev,median,ops,rounds",
                "--benchmark-json=benchmark_results.json"
            ]
        )
    
    def run_reliability_tests(self) -> Dict[str, Any]:
        """Run reliability and error recovery tests."""
        self.log("Running reliability tests...")
        
        return self.run_test_suite("tests/cli/test_cli_reliability.py")
    
    def run_stress_tests(self) -> Dict[str, Any]:
        """Run stress tests."""
        self.log("Running stress tests...")
        
        return self.run_test_suite(
            "tests/cli/test_cli_benchmarks.py",
            markers=["stress"],
            extra_args=["--timeout=600"]  # 10 minute timeout for stress tests
        )
    
    def run_memory_tests(self) -> Dict[str, Any]:
        """Run memory-focused tests."""
        self.log("Running memory tests...")
        
        return self.run_test_suite(
            "tests/cli/test_cli_benchmarks.py",
            markers=["memory"]
        )
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run the comprehensive unittest-based performance tests."""
        self.log("Running comprehensive performance tests...")
        
        return self.run_unittest_suite(
            "tests/cli/test_cli_performance.py",
            timeout=600  # 10 minute timeout
        )
    
    def run_quick_tests(self) -> Dict[str, Any]:
        """Run a quick subset of performance tests."""
        self.log("Running quick performance tests...")
        
        # Run just the basic benchmark tests
        return self.run_test_suite(
            "tests/cli/test_cli_benchmarks.py::TestCLIBenchmarks::test_cli_startup_performance"
        )
    
    def generate_report(self, results: Dict[str, Any], output_file: str = None):
        """Generate a comprehensive performance report."""
        report = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'system_info': self.get_system_info(),
            'test_results': results,
            'summary': self.analyze_results(results)
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            self.log(f"Report saved to {output_file}")
        
        self.print_summary_report(report)
    
    def get_system_info(self) -> Dict[str, Any]:
        """Gather system information for the report."""
        try:
            import psutil
            import platform
            
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                'disk_free_gb': psutil.disk_usage('.').free / (1024**3)
            }
        except ImportError:
            return {
                'platform': 'unknown',
                'note': 'psutil not available for detailed system info'
            }
    
    def analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test results and provide summary statistics."""
        summary = {
            'total_suites': len(results),
            'successful_suites': len([r for r in results.values() if r.get('success', False)]),
            'total_duration': sum(r.get('duration', 0) for r in results.values()),
            'issues_found': []
        }
        
        # Analyze for potential issues
        for suite_name, result in results.items():
            if not result.get('success', False):
                summary['issues_found'].append({
                    'suite': suite_name,
                    'issue': 'test_failure',
                    'details': result.get('stderr', '').split('\n')[-5:]  # Last 5 lines
                })
            
            if result.get('duration', 0) > 300:  # More than 5 minutes
                summary['issues_found'].append({
                    'suite': suite_name,
                    'issue': 'slow_execution',
                    'duration': result.get('duration', 0)
                })
        
        return summary
    
    def print_summary_report(self, report: Dict[str, Any]):
        """Print a human-readable summary report."""
        print("\n" + "="*60)
        print("CLI PERFORMANCE TEST REPORT")
        print("="*60)
        
        print(f"Timestamp: {report['timestamp']}")
        print(f"Platform: {report['system_info'].get('platform', 'unknown')}")
        print(f"Python: {report['system_info'].get('python_version', 'unknown')}")
        print(f"CPU Cores: {report['system_info'].get('cpu_count', 'unknown')}")
        print(f"Memory: {report['system_info'].get('memory_total_gb', 'unknown'):.1f} GB")
        
        print("\nTEST RESULTS:")
        print("-" * 40)
        
        summary = report['summary']
        print(f"Total test suites: {summary['total_suites']}")
        print(f"Successful suites: {summary['successful_suites']}")
        print(f"Total duration: {summary['total_duration']:.1f} seconds")
        
        for suite_name, result in report['test_results'].items():
            status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
            duration = result.get('duration', 0)
            print(f"  {suite_name:30s} {status} ({duration:6.1f}s)")
        
        if summary['issues_found']:
            print(f"\nISSUES FOUND ({len(summary['issues_found'])}):")
            print("-" * 40)
            for issue in summary['issues_found']:
                print(f"  🔍 {issue['suite']}: {issue['issue']}")
                if 'duration' in issue:
                    print(f"     Duration: {issue['duration']:.1f}s")
        
        print("\n" + "="*60)


def main():
    """Main entry point for the performance test runner."""
    parser = argparse.ArgumentParser(
        description="CLI Performance Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Suites:
  benchmark    - pytest-benchmark performance tests
  reliability  - Error handling and recovery tests  
  stress       - High-load stress tests
  memory       - Memory usage tests
  comprehensive - Comprehensive unittest-based tests
  quick        - Quick basic performance check

Examples:
  python scripts/run_performance_tests.py --benchmark
  python scripts/run_performance_tests.py --quick --report
  python scripts/run_performance_tests.py --all --report performance_report.json
        """
    )
    
    # Test selection arguments
    parser.add_argument("--benchmark", action="store_true",
                       help="Run pytest-benchmark tests")
    parser.add_argument("--reliability", action="store_true", 
                       help="Run reliability tests")
    parser.add_argument("--stress", action="store_true",
                       help="Run stress tests") 
    parser.add_argument("--memory", action="store_true",
                       help="Run memory tests")
    parser.add_argument("--comprehensive", action="store_true",
                       help="Run comprehensive unittest-based tests")
    parser.add_argument("--quick", action="store_true",
                       help="Run quick performance check")
    parser.add_argument("--all", action="store_true",
                       help="Run all test suites")
    
    # Output arguments
    parser.add_argument("--report", nargs="?", const="performance_report.json",
                       help="Generate JSON report (optional filename)")
    parser.add_argument("--quiet", action="store_true",
                       help="Reduce output verbosity")
    
    args = parser.parse_args()
    
    # If no specific tests selected, show help
    if not any([args.benchmark, args.reliability, args.stress, args.memory, 
               args.comprehensive, args.quick, args.all]):
        parser.print_help()
        return 1
    
    runner = PerformanceTestRunner(verbose=not args.quiet)
    results = {}
    
    try:
        # Install dependencies first
        runner.log("Installing test dependencies...")
        subprocess.run(["poetry", "install", "--with=test"], 
                      cwd=runner.project_root, check=True)
        
        # Run selected test suites
        if args.all or args.quick:
            results['quick'] = runner.run_quick_tests()
        
        if args.all or args.benchmark:
            results['benchmark'] = runner.run_benchmark_tests()
        
        if args.all or args.reliability:
            results['reliability'] = runner.run_reliability_tests()
        
        if args.all or args.stress:
            results['stress'] = runner.run_stress_tests()
        
        if args.all or args.memory:
            results['memory'] = runner.run_memory_tests()
        
        if args.all or args.comprehensive:
            results['comprehensive'] = runner.run_comprehensive_tests()
        
        # Generate report
        if args.report:
            runner.generate_report(results, args.report if isinstance(args.report, str) else None)
        else:
            # Print brief summary
            successful = sum(1 for r in results.values() if r.get('success', False))
            total = len(results)
            total_time = sum(r.get('duration', 0) for r in results.values())
            
            print(f"\nPerformance Test Summary: {successful}/{total} suites passed in {total_time:.1f}s")
            
            if successful < total:
                runner.log("Some test suites failed. Use --report for detailed analysis.", "WARNING")
                return 1
        
        return 0
        
    except KeyboardInterrupt:
        runner.log("Test run interrupted by user", "WARNING")
        return 130
    except Exception as e:
        runner.log(f"Test run failed: {e}", "ERROR")
        return 1


if __name__ == "__main__":
    sys.exit(main())