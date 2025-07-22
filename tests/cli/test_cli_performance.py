"""
Comprehensive CLI Performance and Reliability Tests

This module provides extensive testing of the CLI's performance characteristics,
reliability under various conditions, and stress testing capabilities.
"""

import os
import sys
import time
import psutil
import tempfile
import shutil
import unittest
import subprocess
import signal
import threading
import gc
from pathlib import Path
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import List, Dict, Any, Optional
import json
import resource


# Helper to get the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class PerformanceMetrics:
    """Utility class for capturing and analyzing performance metrics."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.peak_memory = None
        self.cpu_percent = []
        self.process = None
        self.monitoring_thread = None
        self.monitoring_active = False
    
    def start_monitoring(self, process_pid: Optional[int] = None):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.start_memory = psutil.virtual_memory().used
        if process_pid:
            try:
                self.process = psutil.Process(process_pid)
                self.monitoring_active = True
                self.monitoring_thread = threading.Thread(target=self._monitor_process)
                self.monitoring_thread.daemon = True
                self.monitoring_thread.start()
            except psutil.NoSuchProcess:
                pass
    
    def stop_monitoring(self):
        """Stop performance monitoring and return metrics."""
        self.end_time = time.time()
        self.monitoring_active = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
        
        current_memory = psutil.virtual_memory().used
        peak_memory = self.peak_memory or current_memory
        
        return {
            'duration': self.end_time - self.start_time,
            'start_memory_mb': self.start_memory / 1024 / 1024,
            'peak_memory_mb': peak_memory / 1024 / 1024,
            'memory_delta_mb': (current_memory - self.start_memory) / 1024 / 1024,
            'avg_cpu_percent': sum(self.cpu_percent) / len(self.cpu_percent) if self.cpu_percent else 0
        }
    
    def _monitor_process(self):
        """Internal method to monitor process metrics."""
        while self.monitoring_active and self.process:
            try:
                if self.process.is_running():
                    memory_info = self.process.memory_info()
                    if not self.peak_memory or memory_info.rss > self.peak_memory:
                        self.peak_memory = memory_info.rss
                    
                    cpu_percent = self.process.cpu_percent()
                    if cpu_percent is not None:
                        self.cpu_percent.append(cpu_percent)
                
                time.sleep(0.1)  # Sample every 100ms
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break


class TestCLIPerformance(unittest.TestCase):
    """Performance tests for the CLI application."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with resource limits and baseline metrics."""
        # Set resource limits for safety
        if hasattr(resource, 'RLIMIT_AS'):
            try:
                resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 * 1024 * 1024, -1))  # 2GB
            except (ValueError, OSError):
                pass  # Not supported on all systems
    
    def setUp(self):
        """Set up each test with temporary directories and sample data."""
        self.temp_dir = tempfile.mkdtemp()
        self.kb_dir = os.path.join(self.temp_dir, "kb")
        self.large_kb_dir = os.path.join(self.temp_dir, "large_kb")
        self.rdf_output_dir = os.path.join(self.temp_dir, "rdf_output")
        
        os.makedirs(self.kb_dir)
        os.makedirs(self.large_kb_dir)
        os.makedirs(self.rdf_output_dir)
        
        # Create standard test files
        self._create_test_files()
        
        # Create large dataset for performance testing
        self._create_large_dataset()
        
        # Force garbage collection before tests
        gc.collect()
    
    def tearDown(self):
        """Clean up after each test."""
        shutil.rmtree(self.temp_dir)
        gc.collect()
    
    def _create_test_files(self):
        """Create standard test files for basic performance testing."""
        test_files = {
            "simple.md": "# Simple Document\n\nBasic content.",
            "medium.md": self._generate_markdown_content(100),
            "complex.md": self._generate_complex_markdown(50),
        }
        
        for filename, content in test_files.items():
            with open(os.path.join(self.kb_dir, filename), "w", encoding='utf-8') as f:
                f.write(content)
    
    def _create_large_dataset(self):
        """Create a large dataset for stress testing."""
        # Create 100 documents with varying sizes
        for i in range(100):
            size_category = i % 4
            if size_category == 0:  # Small files (1KB)
                content = self._generate_markdown_content(10)
            elif size_category == 1:  # Medium files (10KB) 
                content = self._generate_markdown_content(100)
            elif size_category == 2:  # Large files (100KB)
                content = self._generate_markdown_content(1000)
            else:  # Very large files (1MB)
                content = self._generate_markdown_content(10000)
            
            filename = f"doc_{i:03d}.md"
            with open(os.path.join(self.large_kb_dir, filename), "w", encoding='utf-8') as f:
                f.write(content)
        
        # Create some deeply nested directories
        nested_path = os.path.join(self.large_kb_dir, "deep", "nested", "structure")
        os.makedirs(nested_path)
        with open(os.path.join(nested_path, "deep_file.md"), "w", encoding='utf-8') as f:
            f.write(self._generate_markdown_content(50))
    
    def _generate_markdown_content(self, sections: int) -> str:
        """Generate markdown content with specified number of sections."""
        content = []
        content.append("# Main Document Title\n")
        
        for i in range(sections):
            content.extend([
                f"## Section {i + 1}\n",
                f"This is section {i + 1} with some sample content. ",
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. ",
                "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\n\n",
                f"- List item {i + 1}.1\n",
                f"- List item {i + 1}.2\n",
                f"- List item {i + 1}.3\n\n",
                f"```python\n# Code block {i + 1}\ndef function_{i}():\n    return {i}\n```\n\n",
                f"[Link to section {i}](#section-{i})\n\n"
            ])
        
        return "".join(content)
    
    def _generate_complex_markdown(self, complexity: int) -> str:
        """Generate complex markdown with various elements."""
        content = ["# Complex Document\n\n"]
        
        for i in range(complexity):
            content.extend([
                f"## Complex Section {i}\n\n",
                "| Column 1 | Column 2 | Column 3 |\n",
                "|----------|----------|----------|\n",
                f"| Data {i}.1 | Data {i}.2 | Data {i}.3 |\n",
                f"| Data {i}.4 | Data {i}.5 | Data {i}.6 |\n\n",
                "```yaml\n",
                f"key_{i}:\n",
                f"  nested_key: value_{i}\n",
                f"  list:\n",
                f"    - item_{i}_1\n",
                f"    - item_{i}_2\n",
                "```\n\n",
                f"[[WikiLink {i}]]\n\n",
                f"#tag{i} #category-{i % 5}\n\n",
                f"- [ ] TODO: Task {i}\n",
                f"- [x] DONE: Completed task {i}\n\n"
            ])
        
        return "".join(content)
    
    def run_cli_command(self, args: List[str], timeout: int = 120, **kwargs) -> subprocess.CompletedProcess:
        """Run CLI command with performance monitoring."""
        base_command = ["poetry", "run", "python", "-m", "knowledgebase_processor.cli.main"]
        full_command = base_command + args
        
        return subprocess.run(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=timeout,
            **kwargs
        )
    
    def benchmark_command(self, args: List[str], iterations: int = 3) -> Dict[str, Any]:
        """Benchmark a CLI command over multiple iterations."""
        results = []
        
        for i in range(iterations):
            metrics = PerformanceMetrics()
            metrics.start_monitoring()
            
            try:
                result = self.run_cli_command(args)
                perf_data = metrics.stop_monitoring()
                
                results.append({
                    'iteration': i + 1,
                    'returncode': result.returncode,
                    'stdout_length': len(result.stdout),
                    'stderr_length': len(result.stderr),
                    **perf_data
                })
                
            except subprocess.TimeoutExpired as e:
                perf_data = metrics.stop_monitoring()
                results.append({
                    'iteration': i + 1,
                    'returncode': -1,
                    'error': 'timeout',
                    **perf_data
                })
        
        # Calculate aggregate statistics
        successful_runs = [r for r in results if r['returncode'] == 0]
        if successful_runs:
            durations = [r['duration'] for r in successful_runs]
            memory_deltas = [r['memory_delta_mb'] for r in successful_runs]
            
            return {
                'iterations': iterations,
                'successful_runs': len(successful_runs),
                'avg_duration': sum(durations) / len(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'avg_memory_delta': sum(memory_deltas) / len(memory_deltas),
                'max_memory_delta': max(memory_deltas),
                'results': results
            }
        else:
            return {
                'iterations': iterations,
                'successful_runs': 0,
                'error': 'No successful runs',
                'results': results
            }

    # PERFORMANCE TESTS
    
    def test_cli_startup_time(self):
        """Test CLI startup time with help command."""
        benchmark = self.benchmark_command(["--help"], iterations=5)
        
        self.assertGreater(benchmark['successful_runs'], 0, "Help command should succeed")
        self.assertLess(benchmark['avg_duration'], 5.0, "Help command should complete within 5 seconds")
        self.assertLess(benchmark['max_duration'], 10.0, "No help command should take more than 10 seconds")
        
        print(f"CLI startup time: avg={benchmark['avg_duration']:.3f}s, max={benchmark['max_duration']:.3f}s")
    
    def test_small_file_processing_performance(self):
        """Test performance with small files."""
        args = ["process", "--knowledge-base", self.kb_dir, "--rdf-output-dir", self.rdf_output_dir]
        benchmark = self.benchmark_command(args, iterations=3)
        
        self.assertGreater(benchmark['successful_runs'], 0, "Small file processing should succeed")
        self.assertLess(benchmark['avg_duration'], 30.0, "Small files should process quickly")
        self.assertLess(benchmark['avg_memory_delta'], 100.0, "Memory usage should be reasonable")
        
        print(f"Small files: avg={benchmark['avg_duration']:.3f}s, memory={benchmark['avg_memory_delta']:.1f}MB")
    
    @patch("knowledgebase_processor.services.processing_service.ProcessingService.process_and_load")
    def test_large_dataset_processing_performance(self, mock_process_and_load):
        """Test performance with large dataset."""
        mock_process_and_load.return_value = 0
        
        args = [
            "process-and-load", self.large_kb_dir,
            "--endpoint-url", "http://fake-endpoint:9999/sparql"
        ]
        
        # Single run with extended timeout for large dataset
        metrics = PerformanceMetrics()
        metrics.start_monitoring()
        
        try:
            result = self.run_cli_command(args, timeout=300)  # 5 minute timeout
            perf_data = metrics.stop_monitoring()
            
            self.assertEqual(result.returncode, 0, "Large dataset processing should succeed")
            self.assertLess(perf_data['duration'], 240.0, "Large dataset should process within 4 minutes")
            self.assertLess(perf_data['memory_delta_mb'], 500.0, "Memory usage should stay under 500MB")
            
            print(f"Large dataset: duration={perf_data['duration']:.3f}s, memory={perf_data['memory_delta_mb']:.1f}MB")
            
        except subprocess.TimeoutExpired:
            perf_data = metrics.stop_monitoring()
            self.fail(f"Large dataset processing timed out after {perf_data['duration']:.1f}s")
    
    def test_memory_usage_scaling(self):
        """Test memory usage doesn't grow excessively with file count."""
        # Test with different sized datasets
        datasets = [
            (self.kb_dir, "small"),
            (self.large_kb_dir, "large")
        ]
        
        memory_results = {}
        
        for kb_path, label in datasets:
            args = ["process", "--knowledge-base", kb_path, "--rdf-output-dir", self.rdf_output_dir]
            
            metrics = PerformanceMetrics()
            metrics.start_monitoring()
            
            try:
                result = self.run_cli_command(args, timeout=180)
                perf_data = metrics.stop_monitoring()
                
                if result.returncode == 0:
                    memory_results[label] = perf_data['memory_delta_mb']
                    print(f"Memory usage for {label} dataset: {perf_data['memory_delta_mb']:.1f}MB")
                
            except subprocess.TimeoutExpired:
                perf_data = metrics.stop_monitoring()
                print(f"Dataset {label} timed out after {perf_data['duration']:.1f}s")
        
        # Verify memory scaling is reasonable (not exponential)
        if 'small' in memory_results and 'large' in memory_results:
            # Large dataset has ~33x more files, memory should not scale linearly
            memory_ratio = memory_results['large'] / max(memory_results['small'], 1)
            self.assertLess(memory_ratio, 50.0, f"Memory scaling too aggressive: {memory_ratio:.1f}x")
    
    def test_concurrent_cli_invocations(self):
        """Test handling multiple concurrent CLI invocations."""
        num_concurrent = 3
        args = ["process", "--knowledge-base", self.kb_dir, "--rdf-output-dir", self.rdf_output_dir]
        
        def run_single_command():
            try:
                result = self.run_cli_command(args, timeout=60)
                return {'returncode': result.returncode, 'duration': time.time()}
            except subprocess.TimeoutExpired:
                return {'returncode': -1, 'error': 'timeout'}
            except Exception as e:
                return {'returncode': -1, 'error': str(e)}
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(run_single_command) for _ in range(num_concurrent)]
            results = []
            
            for future in futures:
                try:
                    result = future.result(timeout=90)
                    results.append(result)
                except TimeoutError:
                    results.append({'returncode': -1, 'error': 'executor_timeout'})
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        successful_runs = [r for r in results if r.get('returncode') == 0]
        
        self.assertGreater(len(successful_runs), 0, "At least one concurrent run should succeed")
        self.assertLess(total_duration, 120.0, "Concurrent runs should complete within 2 minutes")
        
        print(f"Concurrent runs: {len(successful_runs)}/{num_concurrent} successful in {total_duration:.1f}s")

    # RELIABILITY TESTS
    
    def test_signal_handling_interrupt(self):
        """Test CLI gracefully handles SIGINT."""
        if os.name == 'nt':
            self.skipTest("Signal handling test not supported on Windows")
        
        args = ["process", "--knowledge-base", self.large_kb_dir, "--rdf-output-dir", self.rdf_output_dir]
        base_command = ["poetry", "run", "python", "-m", "knowledgebase_processor.cli.main"]
        full_command = base_command + args
        
        proc = subprocess.Popen(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=PROJECT_ROOT
        )
        
        # Let it start processing
        time.sleep(2)
        
        # Send SIGINT
        proc.send_signal(signal.SIGINT)
        
        try:
            stdout, stderr = proc.communicate(timeout=30)
            
            # Process should exit gracefully
            self.assertNotEqual(proc.returncode, 0, "Process should exit with error code after SIGINT")
            # Should not crash with unhandled exception
            self.assertNotIn("Traceback", stderr, "Process should not crash with unhandled exception")
            
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            self.fail("Process did not respond to SIGINT within timeout")
    
    def test_signal_handling_terminate(self):
        """Test CLI gracefully handles SIGTERM."""
        if os.name == 'nt':
            self.skipTest("Signal handling test not supported on Windows")
        
        args = ["process", "--knowledge-base", self.large_kb_dir, "--rdf-output-dir", self.rdf_output_dir]
        base_command = ["poetry", "run", "python", "-m", "knowledgebase_processor.cli.main"]
        full_command = base_command + args
        
        proc = subprocess.Popen(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=PROJECT_ROOT
        )
        
        # Let it start processing
        time.sleep(2)
        
        # Send SIGTERM
        proc.terminate()
        
        try:
            stdout, stderr = proc.communicate(timeout=30)
            
            # Process should exit
            self.assertNotEqual(proc.returncode, 0, "Process should exit after SIGTERM")
            
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            self.fail("Process did not respond to SIGTERM within timeout")
    
    def test_malformed_input_handling(self):
        """Test CLI stability with malformed input files."""
        malformed_dir = os.path.join(self.temp_dir, "malformed")
        os.makedirs(malformed_dir)
        
        # Create various malformed files
        malformed_files = {
            "binary.md": b"\x00\x01\x02\xff\xfe\xfd",  # Binary data
            "huge_line.md": "# Title\n" + "A" * 100000 + "\n",  # Very long line
            "unicode.md": "# Title\n\u0000\uffff\u200b\u2028\u2029\n",  # Problematic Unicode
            "empty.md": "",  # Empty file
            "only_spaces.md": "   \n   \t   \n   ",  # Only whitespace
        }
        
        for filename, content in malformed_files.items():
            filepath = os.path.join(malformed_dir, filename)
            mode = 'wb' if isinstance(content, bytes) else 'w'
            encoding = None if isinstance(content, bytes) else 'utf-8'
            
            with open(filepath, mode, encoding=encoding) as f:
                f.write(content)
        
        # Process malformed files
        args = ["process", "--knowledge-base", malformed_dir, "--rdf-output-dir", self.rdf_output_dir]
        
        metrics = PerformanceMetrics()
        metrics.start_monitoring()
        
        try:
            result = self.run_cli_command(args, timeout=60)
            perf_data = metrics.stop_monitoring()
            
            # Should complete without crashing, even if some files fail
            self.assertIn(result.returncode, [0, 1], "CLI should handle malformed files gracefully")
            self.assertNotIn("Traceback", result.stderr, "Should not crash with unhandled exception")
            self.assertLess(perf_data['duration'], 30.0, "Should not hang on malformed files")
            
        except subprocess.TimeoutExpired:
            perf_data = metrics.stop_monitoring()
            self.fail(f"CLI hung on malformed files for {perf_data['duration']:.1f}s")
    
    def test_resource_cleanup_on_error(self):
        """Test proper resource cleanup when errors occur."""
        # Test with invalid endpoint to trigger error path
        args = [
            "process-and-load", self.kb_dir,
            "--endpoint-url", "http://invalid-endpoint:99999/sparql"
        ]
        
        metrics = PerformanceMetrics()
        metrics.start_monitoring()
        
        result = self.run_cli_command(args, timeout=60)
        perf_data = metrics.stop_monitoring()
        
        # Should fail but not hang or leak resources
        self.assertEqual(result.returncode, 1, "Should fail with invalid endpoint")
        self.assertLess(perf_data['duration'], 30.0, "Should fail quickly")
        
        # Memory should not continue growing after process ends
        post_memory = psutil.virtual_memory().used
        self.assertLess(
            abs(perf_data['memory_delta_mb']), 50.0,
            "Should not leak significant memory on error"
        )
    
    def test_argument_parsing_stress(self):
        """Test CLI with various argument combinations."""
        test_cases = [
            # Valid cases
            ["--help"],
            ["process", "--knowledge-base", self.kb_dir],
            ["process", "--knowledge-base", self.kb_dir, "--pattern", "*.md"],
            
            # Edge cases
            ["process", "--knowledge-base", self.kb_dir, "--pattern", ""],
            ["process", "--knowledge-base", self.kb_dir, "--pattern", "*" * 100],
            
            # Invalid cases
            ["invalid-command"],
            ["process"],  # Missing required args
            ["process", "--knowledge-base", "/nonexistent/path"],
        ]
        
        for i, args in enumerate(test_cases):
            with self.subTest(case=i, args=args):
                try:
                    result = self.run_cli_command(args, timeout=30)
                    
                    # Should complete quickly regardless of validity
                    # Valid cases should succeed, invalid should fail gracefully
                    self.assertIn(result.returncode, [0, 1, 2], 
                                f"Unexpected return code for args: {args}")
                    self.assertNotIn("Traceback", result.stderr,
                                   f"Should not crash on args: {args}")
                    
                except subprocess.TimeoutExpired:
                    self.fail(f"Timeout on argument case: {args}")

    # LOAD TESTS
    
    def test_stress_large_file_processing(self):
        """Stress test with very large individual files."""
        # Create a very large markdown file (10MB)
        large_file_dir = os.path.join(self.temp_dir, "large_file")
        os.makedirs(large_file_dir)
        
        large_content = self._generate_markdown_content(50000)  # ~10MB
        large_file_path = os.path.join(large_file_dir, "huge.md")
        
        with open(large_file_path, "w", encoding='utf-8') as f:
            f.write(large_content)
        
        args = ["process", "--knowledge-base", large_file_dir, "--rdf-output-dir", self.rdf_output_dir]
        
        metrics = PerformanceMetrics()
        metrics.start_monitoring()
        
        try:
            result = self.run_cli_command(args, timeout=600)  # 10 minute timeout
            perf_data = metrics.stop_monitoring()
            
            self.assertEqual(result.returncode, 0, "Large file processing should succeed")
            self.assertLess(perf_data['memory_delta_mb'], 1000.0, "Memory usage should be reasonable")
            
            print(f"Large file processing: {perf_data['duration']:.1f}s, {perf_data['memory_delta_mb']:.1f}MB")
            
        except subprocess.TimeoutExpired:
            perf_data = metrics.stop_monitoring()
            self.fail(f"Large file processing timed out after {perf_data['duration']:.1f}s")
    
    def test_stress_many_small_files(self):
        """Stress test with many small files."""
        many_files_dir = os.path.join(self.temp_dir, "many_files")
        os.makedirs(many_files_dir)
        
        # Create 1000 small files
        for i in range(1000):
            filename = f"small_{i:04d}.md"
            content = f"# Small File {i}\n\nThis is small file number {i}.\n"
            
            with open(os.path.join(many_files_dir, filename), "w", encoding='utf-8') as f:
                f.write(content)
        
        args = ["process", "--knowledge-base", many_files_dir, "--rdf-output-dir", self.rdf_output_dir]
        
        metrics = PerformanceMetrics()
        metrics.start_monitoring()
        
        try:
            result = self.run_cli_command(args, timeout=300)  # 5 minute timeout
            perf_data = metrics.stop_monitoring()
            
            self.assertEqual(result.returncode, 0, "Many files processing should succeed")
            self.assertLess(perf_data['memory_delta_mb'], 200.0, "Memory usage should scale reasonably")
            
            print(f"Many files processing: {perf_data['duration']:.1f}s, {perf_data['memory_delta_mb']:.1f}MB")
            
        except subprocess.TimeoutExpired:
            perf_data = metrics.stop_monitoring()
            self.fail(f"Many files processing timed out after {perf_data['duration']:.1f}s")

    # BENCHMARK TESTS
    
    def test_command_performance_comparison(self):
        """Compare performance across different CLI commands."""
        commands = [
            (["--help"], "help"),
            (["process", "--knowledge-base", self.kb_dir, "--rdf-output-dir", self.rdf_output_dir], "process_small"),
        ]
        
        results = {}
        
        for args, label in commands:
            benchmark = self.benchmark_command(args, iterations=3)
            if benchmark['successful_runs'] > 0:
                results[label] = {
                    'avg_duration': benchmark['avg_duration'],
                    'avg_memory': benchmark['avg_memory_delta']
                }
        
        # Print comparison
        print("\nCommand Performance Comparison:")
        for label, metrics in results.items():
            print(f"  {label:20s}: {metrics['avg_duration']:7.3f}s, {metrics['avg_memory']:6.1f}MB")
        
        # Basic assertions
        if 'help' in results:
            self.assertLess(results['help']['avg_duration'], 5.0, "Help should be very fast")
    
    def test_throughput_measurement(self):
        """Measure document processing throughput."""
        # Count files in test directory
        file_count = len([f for f in os.listdir(self.kb_dir) if f.endswith('.md')])
        
        args = ["process", "--knowledge-base", self.kb_dir, "--rdf-output-dir", self.rdf_output_dir]
        benchmark = self.benchmark_command(args, iterations=3)
        
        if benchmark['successful_runs'] > 0:
            throughput = file_count / benchmark['avg_duration']
            print(f"Processing throughput: {throughput:.2f} files/second")
            
            # Should process at least 1 file per 5 seconds on average
            self.assertGreater(throughput, 0.2, "Processing throughput too low")
    
    def test_performance_regression_detection(self):
        """Detect potential performance regressions."""
        # Run the same command multiple times to detect variance
        args = ["process", "--knowledge-base", self.kb_dir, "--rdf-output-dir", self.rdf_output_dir]
        benchmark = self.benchmark_command(args, iterations=5)
        
        if benchmark['successful_runs'] >= 3:
            durations = [r['duration'] for r in benchmark['results'] if r['returncode'] == 0]
            
            # Calculate coefficient of variation (std dev / mean)
            mean_duration = sum(durations) / len(durations)
            variance = sum((d - mean_duration) ** 2 for d in durations) / len(durations)
            std_dev = variance ** 0.5
            cv = std_dev / mean_duration if mean_duration > 0 else 0
            
            print(f"Performance variance: CV={cv:.3f}, range={min(durations):.3f}-{max(durations):.3f}s")
            
            # Performance should be reasonably consistent (CV < 50%)
            self.assertLess(cv, 0.5, f"Performance too variable: {cv:.3f}")


class TestCLIReliability(unittest.TestCase):
    """Reliability and error recovery tests for the CLI."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.kb_dir = os.path.join(self.temp_dir, "kb")
        os.makedirs(self.kb_dir)
        
        # Create basic test file
        with open(os.path.join(self.kb_dir, "test.md"), "w") as f:
            f.write("# Test\nContent")
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def run_cli_command(self, args: List[str], **kwargs) -> subprocess.CompletedProcess:
        """Run CLI command."""
        base_command = ["poetry", "run", "python", "-m", "knowledgebase_processor.cli.main"]
        full_command = base_command + args
        
        return subprocess.run(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=PROJECT_ROOT,
            **kwargs
        )
    
    def test_error_recovery_invalid_config(self):
        """Test recovery from invalid configuration."""
        invalid_config = os.path.join(self.temp_dir, "invalid_config.json")
        with open(invalid_config, "w") as f:
            f.write("invalid json content")
        
        args = ["--config", invalid_config, "process", "--knowledge-base", self.kb_dir]
        result = self.run_cli_command(args, timeout=30)
        
        # Should fail gracefully, not crash
        self.assertNotEqual(result.returncode, 0, "Should fail with invalid config")
        self.assertNotIn("Traceback", result.stderr, "Should not crash")
    
    def test_graceful_degradation_no_permissions(self):
        """Test graceful handling of permission errors."""
        if os.name == 'nt':
            self.skipTest("Permission test not reliable on Windows")
        
        # Create a directory with no read permissions
        no_read_dir = os.path.join(self.temp_dir, "no_read")
        os.makedirs(no_read_dir)
        os.chmod(no_read_dir, 0o000)
        
        try:
            args = ["process", "--knowledge-base", no_read_dir]
            result = self.run_cli_command(args, timeout=30)
            
            # Should handle permission error gracefully
            self.assertNotEqual(result.returncode, 0, "Should fail due to permissions")
            self.assertNotIn("Traceback", result.stderr, "Should not crash")
            
        finally:
            # Restore permissions for cleanup
            os.chmod(no_read_dir, 0o755)
    
    def test_disk_space_handling(self):
        """Test behavior when disk space is limited."""
        # This is hard to test reliably, so we'll mock the scenario
        large_output_dir = os.path.join(self.temp_dir, "large_output")
        os.makedirs(large_output_dir)
        
        # Create a large KB that would generate significant output
        large_kb = os.path.join(self.temp_dir, "large_kb")
        os.makedirs(large_kb)
        
        for i in range(10):
            with open(os.path.join(large_kb, f"doc_{i}.md"), "w") as f:
                f.write("# Large Doc\n" + "Content " * 10000)
        
        args = ["process", "--knowledge-base", large_kb, "--rdf-output-dir", large_output_dir]
        result = self.run_cli_command(args, timeout=60)
        
        # Should either succeed or fail gracefully
        self.assertIn(result.returncode, [0, 1], "Should handle large output gracefully")
        if result.returncode != 0:
            self.assertNotIn("Traceback", result.stderr, "Should not crash on errors")
    
    def test_network_timeout_handling(self):
        """Test handling of network timeouts."""
        # Use a non-routable IP to simulate network timeout
        args = [
            "process-and-load", self.kb_dir,
            "--endpoint-url", "http://10.255.255.1:9999/sparql"
        ]
        
        start_time = time.time()
        result = self.run_cli_command(args, timeout=60)
        duration = time.time() - start_time
        
        # Should timeout reasonably quickly and handle it gracefully
        self.assertNotEqual(result.returncode, 0, "Should fail with unreachable endpoint")
        self.assertLess(duration, 45.0, "Should timeout within reasonable time")
        self.assertNotIn("Traceback", result.stderr, "Should handle timeout gracefully")


if __name__ == "__main__":
    # Configure test runner for performance testing
    import sys
    
    if "--benchmark" in sys.argv:
        sys.argv.remove("--benchmark")
        # Run only benchmark tests
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add benchmark test methods
        suite.addTest(TestCLIPerformance('test_command_performance_comparison'))
        suite.addTest(TestCLIPerformance('test_throughput_measurement'))
        suite.addTest(TestCLIPerformance('test_performance_regression_detection'))
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)
    
    else:
        # Run all tests
        unittest.main(verbosity=2)