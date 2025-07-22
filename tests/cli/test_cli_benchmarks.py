"""
CLI Performance Benchmarks using pytest-benchmark

This module provides pytest-benchmark based performance testing for the CLI.
Use: pytest tests/cli/test_cli_benchmarks.py --benchmark-only
"""

import os
import tempfile
import shutil
import subprocess
import psutil
import pytest
from pathlib import Path
from typing import List, Dict
import time
import gc

# Project root for running CLI commands
PROJECT_ROOT = Path(__file__).parent.parent.parent


class CLIBenchmarkFixtures:
    """Shared fixtures for CLI benchmarking."""
    
    @pytest.fixture(scope="session")
    def temp_workspace(self):
        """Create a temporary workspace for all benchmarks."""
        temp_dir = tempfile.mkdtemp(prefix="cli_benchmark_")
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture(scope="session") 
    def small_kb(self, temp_workspace):
        """Create a small knowledge base for benchmarking."""
        kb_dir = Path(temp_workspace) / "small_kb"
        kb_dir.mkdir()
        
        # Create 10 small files
        for i in range(10):
            content = f"""# Document {i}

This is document number {i} with some basic content.

## Section A
Content for section A in document {i}.

## Section B  
Content for section B in document {i}.

- Item 1
- Item 2  
- Item 3

```python
def function_{i}():
    return {i}
```

#tag{i} #category
"""
            (kb_dir / f"doc_{i:02d}.md").write_text(content)
        
        return kb_dir
    
    @pytest.fixture(scope="session")
    def medium_kb(self, temp_workspace):
        """Create a medium knowledge base for benchmarking."""
        kb_dir = Path(temp_workspace) / "medium_kb"
        kb_dir.mkdir()
        
        # Create 50 medium files
        for i in range(50):
            sections = []
            sections.append(f"# Document {i}")
            
            for j in range(20):  # 20 sections per document
                sections.extend([
                    f"## Section {j}",
                    f"This is section {j} of document {i}.",
                    "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                    "",
                    f"### Subsection {j}.1",
                    "More detailed content here.",
                    "",
                    f"```yaml",
                    f"key_{j}: value_{j}",
                    f"nested:",
                    f"  item: {j}",
                    f"```",
                    "",
                    f"- [ ] TODO: Task {j}",
                    f"- [x] DONE: Completed {j}",
                    "",
                    f"[[Link to Document {(i + j) % 50}]]",
                    ""
                ])
            
            content = "\n".join(sections)
            (kb_dir / f"doc_{i:03d}.md").write_text(content)
        
        return kb_dir
    
    @pytest.fixture(scope="session")
    def rdf_output_dir(self, temp_workspace):
        """Create RDF output directory."""
        rdf_dir = Path(temp_workspace) / "rdf_output"
        rdf_dir.mkdir()
        return rdf_dir


# Inherit fixtures
@pytest.mark.usefixtures("small_kb", "medium_kb", "rdf_output_dir")
class TestCLIBenchmarks(CLIBenchmarkFixtures):
    """CLI performance benchmarks using pytest-benchmark."""
    
    def run_cli_command(self, args: List[str], timeout: int = 120) -> subprocess.CompletedProcess:
        """Run a CLI command and return the result."""
        base_command = ["poetry", "run", "python", "-m", "knowledgebase_processor.cli.main"]
        full_command = base_command + args
        
        # Force garbage collection before running
        gc.collect()
        
        return subprocess.run(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=timeout
        )
    
    def cli_startup_benchmark(self):
        """Benchmark CLI startup time."""
        result = self.run_cli_command(["--help"], timeout=30)
        assert result.returncode == 0
        return result
    
    def small_kb_processing_benchmark(self, small_kb, rdf_output_dir):
        """Benchmark small knowledge base processing."""
        args = [
            "process", 
            "--knowledge-base", str(small_kb),
            "--rdf-output-dir", str(rdf_output_dir)
        ]
        result = self.run_cli_command(args, timeout=60)
        assert result.returncode == 0
        return result
    
    def medium_kb_processing_benchmark(self, medium_kb, rdf_output_dir):
        """Benchmark medium knowledge base processing."""
        args = [
            "process",
            "--knowledge-base", str(medium_kb), 
            "--rdf-output-dir", str(rdf_output_dir)
        ]
        result = self.run_cli_command(args, timeout=180)
        assert result.returncode == 0
        return result
    
    # Pytest-benchmark tests
    
    def test_cli_startup_performance(self, benchmark):
        """Benchmark CLI startup time."""
        result = benchmark(self.cli_startup_benchmark)
        
        # Assertions about performance
        assert result.returncode == 0
        
        # Get benchmark stats
        stats = benchmark.stats
        assert stats.mean < 5.0, f"CLI startup too slow: {stats.mean:.3f}s"
        assert stats.max < 10.0, f"CLI startup max too slow: {stats.max:.3f}s"
    
    def test_small_kb_processing_performance(self, benchmark, small_kb, rdf_output_dir):
        """Benchmark small knowledge base processing."""
        result = benchmark(self.small_kb_processing_benchmark, small_kb, rdf_output_dir)
        
        assert result.returncode == 0
        
        stats = benchmark.stats
        assert stats.mean < 30.0, f"Small KB processing too slow: {stats.mean:.3f}s"
        
        # Check throughput (10 files)
        throughput = 10 / stats.mean
        assert throughput > 0.5, f"Throughput too low: {throughput:.2f} files/sec"
    
    def test_medium_kb_processing_performance(self, benchmark, medium_kb, rdf_output_dir):
        """Benchmark medium knowledge base processing."""
        result = benchmark(self.medium_kb_processing_benchmark, medium_kb, rdf_output_dir)
        
        assert result.returncode == 0
        
        stats = benchmark.stats 
        assert stats.mean < 120.0, f"Medium KB processing too slow: {stats.mean:.3f}s"
        
        # Check throughput (50 files)
        throughput = 50 / stats.mean
        assert throughput > 0.5, f"Throughput too low: {throughput:.2f} files/sec"
    
    @pytest.mark.parametrize("kb_size,expected_max_time", [
        ("small", 30.0),
        ("medium", 120.0),
    ])
    def test_processing_performance_scaling(self, benchmark, kb_size, expected_max_time, small_kb, medium_kb, rdf_output_dir):
        """Test that processing time scales reasonably with KB size."""
        if kb_size == "small":
            kb_path = small_kb
            file_count = 10
        else:
            kb_path = medium_kb
            file_count = 50
        
        def process_kb():
            args = [
                "process",
                "--knowledge-base", str(kb_path),
                "--rdf-output-dir", str(rdf_output_dir)
            ]
            return self.run_cli_command(args, timeout=int(expected_max_time * 2))
        
        result = benchmark(process_kb)
        
        assert result.returncode == 0
        
        stats = benchmark.stats
        assert stats.mean < expected_max_time, f"{kb_size} KB processing too slow: {stats.mean:.3f}s"
        
        # Calculate files per second
        fps = file_count / stats.mean
        print(f"{kb_size} KB: {fps:.2f} files/sec, {stats.mean:.3f}s total")


@pytest.mark.memory 
class TestCLIMemoryBenchmarks(CLIBenchmarkFixtures):
    """Memory-focused CLI benchmarks."""
    
    def run_cli_with_memory_tracking(self, args: List[str], timeout: int = 120) -> Dict:
        """Run CLI command with memory tracking."""
        base_command = ["poetry", "run", "python", "-m", "knowledgebase_processor.cli.main"]
        full_command = base_command + args
        
        # Get initial memory
        initial_memory = psutil.virtual_memory().used
        
        # Start process
        proc = subprocess.Popen(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=PROJECT_ROOT
        )
        
        # Track memory usage
        peak_memory = initial_memory
        memory_samples = []
        
        start_time = time.time()
        
        while proc.poll() is None:
            try:
                current_memory = psutil.virtual_memory().used
                memory_samples.append(current_memory)
                peak_memory = max(peak_memory, current_memory)
                
                # Check timeout
                if time.time() - start_time > timeout:
                    proc.kill()
                    break
                    
                time.sleep(0.1)
            except:
                break
        
        stdout, stderr = proc.communicate()
        end_time = time.time()
        final_memory = psutil.virtual_memory().used
        
        return {
            'returncode': proc.returncode,
            'stdout': stdout,
            'stderr': stderr,
            'duration': end_time - start_time,
            'initial_memory_mb': initial_memory / 1024 / 1024,
            'peak_memory_mb': peak_memory / 1024 / 1024,
            'final_memory_mb': final_memory / 1024 / 1024,
            'memory_delta_mb': (final_memory - initial_memory) / 1024 / 1024,
            'memory_samples': len(memory_samples)
        }
    
    def test_memory_usage_small_kb(self, small_kb, rdf_output_dir):
        """Test memory usage with small knowledge base."""
        args = [
            "process",
            "--knowledge-base", str(small_kb),
            "--rdf-output-dir", str(rdf_output_dir)
        ]
        
        result = self.run_cli_with_memory_tracking(args)
        
        assert result['returncode'] == 0
        assert result['memory_delta_mb'] < 100, f"Memory usage too high: {result['memory_delta_mb']:.1f}MB"
        assert result['duration'] < 60, f"Processing too slow: {result['duration']:.1f}s"
        
        print(f"Small KB memory: {result['memory_delta_mb']:.1f}MB, duration: {result['duration']:.1f}s")
    
    def test_memory_usage_medium_kb(self, medium_kb, rdf_output_dir):
        """Test memory usage with medium knowledge base.""" 
        args = [
            "process",
            "--knowledge-base", str(medium_kb),
            "--rdf-output-dir", str(rdf_output_dir)
        ]
        
        result = self.run_cli_with_memory_tracking(args)
        
        assert result['returncode'] == 0
        assert result['memory_delta_mb'] < 300, f"Memory usage too high: {result['memory_delta_mb']:.1f}MB"
        assert result['duration'] < 180, f"Processing too slow: {result['duration']:.1f}s"
        
        print(f"Medium KB memory: {result['memory_delta_mb']:.1f}MB, duration: {result['duration']:.1f}s")
    
    def test_memory_scaling(self, small_kb, medium_kb, rdf_output_dir):
        """Test that memory usage scales reasonably."""
        # Test small KB
        small_result = self.run_cli_with_memory_tracking([
            "process",
            "--knowledge-base", str(small_kb), 
            "--rdf-output-dir", str(rdf_output_dir)
        ])
        
        # Test medium KB
        medium_result = self.run_cli_with_memory_tracking([
            "process",
            "--knowledge-base", str(medium_kb),
            "--rdf-output-dir", str(rdf_output_dir)
        ])
        
        assert small_result['returncode'] == 0
        assert medium_result['returncode'] == 0
        
        # Medium KB has 5x more files, memory should not scale linearly
        if small_result['memory_delta_mb'] > 0:
            memory_ratio = medium_result['memory_delta_mb'] / small_result['memory_delta_mb']
            assert memory_ratio < 20, f"Memory scaling too aggressive: {memory_ratio:.1f}x"
        
        print(f"Memory scaling: small={small_result['memory_delta_mb']:.1f}MB, " + 
              f"medium={medium_result['memory_delta_mb']:.1f}MB")


@pytest.mark.stress
class TestCLIStressBenchmarks(CLIBenchmarkFixtures):
    """Stress testing benchmarks for the CLI."""
    
    def test_large_file_processing(self, benchmark, temp_workspace):
        """Benchmark processing of a single large file."""
        # Create large file (~1MB)
        large_kb = Path(temp_workspace) / "large_file_kb"
        large_kb.mkdir(exist_ok=True)
        
        # Generate large content
        sections = []
        for i in range(500):  # 500 sections ≈ 1MB
            sections.extend([
                f"## Section {i}",
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 20,
                "",
                f"### Subsection {i}.1", 
                "Detailed content with more text. " * 15,
                "",
                f"```python",
                f"def function_{i}():",
                f"    '''Function number {i}'''",
                f"    data = {{'key': {i}, 'value': 'data_{i}'}}", 
                f"    return process_data(data)",
                f"```",
                "",
                f"- Item {i}.1",
                f"- Item {i}.2", 
                f"- Item {i}.3",
                ""
            ])
        
        large_content = "# Large Document\n\n" + "\n".join(sections)
        large_file = large_kb / "large_document.md"
        large_file.write_text(large_content)
        
        rdf_dir = Path(temp_workspace) / "large_file_rdf"
        rdf_dir.mkdir(exist_ok=True)
        
        def process_large_file():
            args = [
                "process",
                "--knowledge-base", str(large_kb),
                "--rdf-output-dir", str(rdf_dir)
            ]
            result = subprocess.run(
                ["poetry", "run", "python", "-m", "knowledgebase_processor.cli.main"] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=PROJECT_ROOT,
                timeout=300
            )
            assert result.returncode == 0
            return result
        
        result = benchmark(process_large_file)
        
        stats = benchmark.stats
        assert stats.mean < 180, f"Large file processing too slow: {stats.mean:.3f}s"
        
        # Calculate throughput in MB/s
        file_size_mb = len(large_content) / 1024 / 1024
        throughput = file_size_mb / stats.mean
        print(f"Large file throughput: {throughput:.2f} MB/s")
    
    def test_concurrent_processing_simulation(self, small_kb, temp_workspace):
        """Simulate concurrent processing by running multiple instances."""
        import concurrent.futures
        import threading
        
        rdf_base_dir = Path(temp_workspace) / "concurrent_rdf"
        rdf_base_dir.mkdir(exist_ok=True)
        
        def run_single_process(instance_id):
            rdf_dir = rdf_base_dir / f"instance_{instance_id}"
            rdf_dir.mkdir(exist_ok=True)
            
            args = [
                "process",
                "--knowledge-base", str(small_kb),
                "--rdf-output-dir", str(rdf_dir)
            ]
            
            start_time = time.time()
            result = subprocess.run(
                ["poetry", "run", "python", "-m", "knowledgebase_processor.cli.main"] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, 
                text=True,
                cwd=PROJECT_ROOT,
                timeout=60
            )
            end_time = time.time()
            
            return {
                'instance_id': instance_id,
                'returncode': result.returncode,
                'duration': end_time - start_time,
                'success': result.returncode == 0
            }
        
        # Run 3 concurrent instances
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_single_process, i) for i in range(3)]
            results = [f.result() for f in concurrent.futures.as_completed(futures, timeout=90)]
        end_time = time.time()
        
        total_time = end_time - start_time
        successful_runs = [r for r in results if r['success']]
        
        assert len(successful_runs) >= 2, f"Not enough successful concurrent runs: {len(successful_runs)}/3"
        assert total_time < 90, f"Concurrent processing took too long: {total_time:.1f}s"
        
        avg_duration = sum(r['duration'] for r in successful_runs) / len(successful_runs)
        print(f"Concurrent processing: {len(successful_runs)}/3 successful, avg={avg_duration:.1f}s, total={total_time:.1f}s")


# Configuration for pytest-benchmark
def pytest_configure(config):
    """Configure pytest-benchmark settings."""
    config.option.benchmark_only = True
    config.option.benchmark_sort = 'mean'
    config.option.benchmark_columns = ['min', 'max', 'mean', 'stddev', 'median', 'ops', 'rounds']


if __name__ == "__main__":
    pytest.main([__file__, "--benchmark-only", "-v"])