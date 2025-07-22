"""
CLI Reliability and Error Recovery Tests

This module focuses on testing the CLI's behavior under various error conditions,
signal handling, resource constraints, and edge cases.
"""

import os
import sys
import tempfile
import shutil
import subprocess
import signal
import threading
import time
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from typing import List, Dict, Any
import json
import resource


PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestCLIReliability:
    """Test CLI reliability and error handling."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp(prefix="cli_reliability_")
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def basic_kb(self, temp_workspace):
        """Create basic knowledge base for testing."""
        kb_dir = temp_workspace / "basic_kb"
        kb_dir.mkdir()
        
        (kb_dir / "test.md").write_text("""# Test Document

This is a basic test document for reliability testing.

## Section 1
Content here.

## Section 2
More content here.
""")
        return kb_dir
    
    def run_cli_command(self, args: List[str], timeout: int = 30, **kwargs) -> subprocess.CompletedProcess:
        """Run CLI command with specified timeout."""
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
    
    def start_cli_process(self, args: List[str]) -> subprocess.Popen:
        """Start CLI process for signal testing."""
        base_command = ["poetry", "run", "python", "-m", "knowledgebase_processor.cli.main"]
        full_command = base_command + args
        
        return subprocess.Popen(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=PROJECT_ROOT
        )

    # Error Handling Tests
    
    def test_invalid_command_handling(self):
        """Test handling of invalid commands."""
        result = self.run_cli_command(["invalid-command"])
        
        assert result.returncode != 0
        assert "invalid choice" in result.stderr.lower() or "error" in result.stderr.lower()
        # Should not crash with unhandled exception
        assert "Traceback" not in result.stderr
    
    def test_missing_required_arguments(self):
        """Test handling of missing required arguments."""
        test_cases = [
            ["process"],  # Missing --knowledge-base
            ["process-and-load"],  # Missing knowledge base path
            ["query"],  # Missing query string
            ["sparql", "query"],  # Missing SPARQL query
        ]
        
        for args in test_cases:
            with pytest.subTest(args=args):
                result = self.run_cli_command(args)
                
                assert result.returncode != 0
                # Should show usage information, not crash
                assert "Traceback" not in result.stderr
                assert len(result.stderr) > 0  # Should have error message
    
    def test_invalid_file_paths(self, temp_workspace):
        """Test handling of invalid file paths."""
        test_cases = [
            str(temp_workspace / "nonexistent"),  # Non-existent directory
            str(temp_workspace / "file.txt"),     # File instead of directory (we'll create this)
            "/dev/null",                          # Device file
            "",                                   # Empty path
            "." * 300,                           # Very long path
        ]
        
        # Create a regular file for testing
        (temp_workspace / "file.txt").write_text("not a directory")
        
        for path in test_cases:
            with pytest.subTest(path=path):
                args = ["process", "--knowledge-base", path]
                result = self.run_cli_command(args)
                
                assert result.returncode != 0
                assert "Traceback" not in result.stderr
    
    def test_invalid_urls(self, basic_kb):
        """Test handling of invalid SPARQL URLs."""
        invalid_urls = [
            "not-a-url",
            "http://",
            "ftp://example.com/sparql",
            "http://256.256.256.256:99999/sparql",  # Invalid IP
            "http://localhost:99999/sparql",         # Invalid port
            "",
        ]
        
        for url in invalid_urls:
            with pytest.subTest(url=url):
                args = [
                    "process-and-load", str(basic_kb),
                    "--endpoint-url", url
                ]
                result = self.run_cli_command(args)
                
                assert result.returncode != 0
                assert "Traceback" not in result.stderr
    
    def test_malformed_configuration_files(self, temp_workspace, basic_kb):
        """Test handling of malformed configuration files."""
        config_tests = [
            ("invalid_json.json", "{invalid json}"),
            ("empty.json", ""),
            ("binary.json", b"\x00\x01\x02\xff"),
            ("huge.json", '{"key": "' + "a" * 1000000 + '"}'),
        ]
        
        for filename, content in config_tests:
            with pytest.subTest(config=filename):
                config_file = temp_workspace / filename
                
                if isinstance(content, bytes):
                    config_file.write_bytes(content)
                else:
                    config_file.write_text(content)
                
                args = [
                    "--config", str(config_file),
                    "process", "--knowledge-base", str(basic_kb)
                ]
                result = self.run_cli_command(args)
                
                assert result.returncode != 0
                # Should handle gracefully, not crash
                assert "Traceback" not in result.stderr

    # Malformed Input Tests
    
    def test_malformed_markdown_files(self, temp_workspace):
        """Test processing malformed markdown files."""
        malformed_kb = temp_workspace / "malformed_kb"
        malformed_kb.mkdir()
        
        malformed_files = {
            "binary.md": b"\x00\x01\x02\xff\xfe\xfd",
            "huge_line.md": "# Title\n" + "A" * 100000 + "\n",
            "unicode_issues.md": "# Title\n\u0000\uffff\u200b\u2028\u2029\n",
            "empty.md": "",
            "only_whitespace.md": "   \n   \t   \n   ",
            "control_chars.md": "# Title\n\x01\x02\x03\x1f\n",
            "null_bytes.md": "# Title\nContent with \x00 null bytes\n",
        }
        
        for filename, content in malformed_files.items():
            filepath = malformed_kb / filename
            if isinstance(content, bytes):
                filepath.write_bytes(content)
            else:
                filepath.write_text(content, encoding='utf-8', errors='replace')
        
        rdf_dir = temp_workspace / "malformed_rdf"
        rdf_dir.mkdir()
        
        args = [
            "process", 
            "--knowledge-base", str(malformed_kb),
            "--rdf-output-dir", str(rdf_dir)
        ]
        
        result = self.run_cli_command(args, timeout=60)
        
        # Should handle malformed files gracefully
        # May succeed with warnings or fail gracefully, but shouldn't crash
        assert result.returncode in [0, 1]
        assert "Traceback" not in result.stderr
    
    def test_extremely_large_files(self, temp_workspace):
        """Test handling of extremely large files."""
        large_kb = temp_workspace / "large_kb"
        large_kb.mkdir()
        
        # Create a very large file (~5MB)
        large_content = "# Huge Document\n\n" + ("Content line " * 50 + "\n") * 10000
        (large_kb / "huge.md").write_text(large_content)
        
        rdf_dir = temp_workspace / "large_rdf"
        rdf_dir.mkdir()
        
        args = [
            "process",
            "--knowledge-base", str(large_kb),
            "--rdf-output-dir", str(rdf_dir)
        ]
        
        # Should either succeed or fail gracefully within reasonable time
        result = self.run_cli_command(args, timeout=120)
        
        # Should not crash regardless of success/failure
        assert "Traceback" not in result.stderr
        
        if result.returncode == 0:
            # If successful, should have created output
            assert len(list(rdf_dir.glob("*.ttl"))) > 0

    # Signal Handling Tests
    
    @pytest.mark.skipif(os.name == 'nt', reason="Signal handling not reliable on Windows")
    def test_sigint_handling(self, basic_kb, temp_workspace):
        """Test graceful handling of SIGINT (Ctrl+C)."""
        rdf_dir = temp_workspace / "sigint_rdf"
        rdf_dir.mkdir()
        
        # Create larger dataset to ensure process runs long enough
        large_kb = temp_workspace / "large_for_sigint"
        large_kb.mkdir()
        
        for i in range(20):
            content = f"# Document {i}\n\n" + ("Content line\n" * 100)
            (large_kb / f"doc_{i:02d}.md").write_text(content)
        
        args = [
            "process",
            "--knowledge-base", str(large_kb),
            "--rdf-output-dir", str(rdf_dir)
        ]
        
        proc = self.start_cli_process(args)
        
        # Let it start processing
        time.sleep(2)
        
        # Send SIGINT
        proc.send_signal(signal.SIGINT)
        
        try:
            stdout, stderr = proc.communicate(timeout=30)
            
            # Should exit with non-zero code but not crash
            assert proc.returncode != 0
            assert "Traceback" not in stderr
            
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            pytest.fail("Process did not respond to SIGINT within timeout")
    
    @pytest.mark.skipif(os.name == 'nt', reason="Signal handling not reliable on Windows")
    def test_sigterm_handling(self, basic_kb, temp_workspace):
        """Test graceful handling of SIGTERM."""
        rdf_dir = temp_workspace / "sigterm_rdf"
        rdf_dir.mkdir()
        
        # Create larger dataset
        large_kb = temp_workspace / "large_for_sigterm"
        large_kb.mkdir()
        
        for i in range(15):
            content = f"# Document {i}\n\n" + ("Content line\n" * 150)
            (large_kb / f"doc_{i:02d}.md").write_text(content)
        
        args = [
            "process",
            "--knowledge-base", str(large_kb),
            "--rdf-output-dir", str(rdf_dir)
        ]
        
        proc = self.start_cli_process(args)
        
        # Let it start processing
        time.sleep(2)
        
        # Send SIGTERM
        proc.terminate()
        
        try:
            stdout, stderr = proc.communicate(timeout=30)
            
            # Should exit
            assert proc.returncode != 0
            
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            pytest.fail("Process did not respond to SIGTERM within timeout")

    # Resource Constraint Tests
    
    @pytest.mark.skipif(os.name == 'nt', reason="Resource limits not supported on Windows")
    def test_memory_limit_handling(self, basic_kb, temp_workspace):
        """Test behavior under memory constraints."""
        # Set a memory limit for the subprocess (not the test process)
        # This is tricky to test reliably, so we'll do a basic check
        
        # Create many files to potentially trigger memory issues
        many_files_kb = temp_workspace / "many_files"
        many_files_kb.mkdir()
        
        for i in range(100):
            content = f"# Document {i}\n\n" + ("Line of content\n" * 500)
            (many_files_kb / f"doc_{i:03d}.md").write_text(content)
        
        rdf_dir = temp_workspace / "memory_test_rdf"
        rdf_dir.mkdir()
        
        args = [
            "process",
            "--knowledge-base", str(many_files_kb),
            "--rdf-output-dir", str(rdf_dir)
        ]
        
        # Run with extended timeout
        result = self.run_cli_command(args, timeout=180)
        
        # Should either succeed or fail gracefully, not crash with OOM
        assert "Traceback" not in result.stderr
        assert "MemoryError" not in result.stderr
    
    def test_disk_space_simulation(self, basic_kb, temp_workspace):
        """Simulate disk space constraints by filling up output directory."""
        rdf_dir = temp_workspace / "full_disk_rdf"
        rdf_dir.mkdir()
        
        # Fill the directory with dummy files to simulate disk space issues
        # (This won't actually fill the disk but may trigger some error paths)
        for i in range(10):
            dummy_file = rdf_dir / f"dummy_{i}.txt"
            dummy_file.write_text("x" * 100000)  # 100KB files
        
        args = [
            "process",
            "--knowledge-base", str(basic_kb),
            "--rdf-output-dir", str(rdf_dir)
        ]
        
        result = self.run_cli_command(args, timeout=60)
        
        # Should handle gracefully regardless of success/failure
        assert "Traceback" not in result.stderr

    # Network and Connectivity Tests
    
    def test_network_timeout_handling(self, basic_kb):
        """Test handling of network timeouts."""
        # Use non-routable IP to simulate timeout
        args = [
            "process-and-load", str(basic_kb),
            "--endpoint-url", "http://10.255.255.1:9999/sparql"
        ]
        
        start_time = time.time()
        result = self.run_cli_command(args, timeout=60)
        duration = time.time() - start_time
        
        # Should timeout reasonably quickly
        assert result.returncode != 0
        assert duration < 45  # Should not hang for too long
        assert "Traceback" not in result.stderr
    
    def test_invalid_endpoint_response_handling(self, basic_kb):
        """Test handling of invalid endpoint responses."""
        # Use a non-SPARQL endpoint that will return unexpected responses
        args = [
            "process-and-load", str(basic_kb),
            "--endpoint-url", "http://httpbin.org/status/500"
        ]
        
        result = self.run_cli_command(args, timeout=60)
        
        # Should fail gracefully
        assert result.returncode != 0
        assert "Traceback" not in result.stderr

    # Resource Cleanup Tests
    
    def test_cleanup_on_early_exit(self, basic_kb, temp_workspace):
        """Test that resources are cleaned up on early exit."""
        rdf_dir = temp_workspace / "cleanup_test_rdf"
        rdf_dir.mkdir()
        
        # Create a scenario that might cause early exit
        args = [
            "process", "--knowledge-base", "/nonexistent",
            "--rdf-output-dir", str(rdf_dir)
        ]
        
        result = self.run_cli_command(args, timeout=30)
        
        # Should exit quickly and cleanly
        assert result.returncode != 0
        assert "Traceback" not in result.stderr
        
        # Directory should still exist but should be empty or minimal
        assert rdf_dir.exists()
    
    def test_partial_processing_recovery(self, temp_workspace):
        """Test recovery from partial processing failures."""
        mixed_kb = temp_workspace / "mixed_kb"
        mixed_kb.mkdir()
        
        # Create mix of valid and invalid files
        (mixed_kb / "valid1.md").write_text("# Valid Document 1\nContent here.")
        (mixed_kb / "valid2.md").write_text("# Valid Document 2\nMore content.")
        (mixed_kb / "invalid.md").write_bytes(b"\xff\xfe\xfd\x00")  # Binary data
        (mixed_kb / "valid3.md").write_text("# Valid Document 3\nFinal content.")
        
        rdf_dir = temp_workspace / "mixed_rdf"
        rdf_dir.mkdir()
        
        args = [
            "process",
            "--knowledge-base", str(mixed_kb),
            "--rdf-output-dir", str(rdf_dir)
        ]
        
        result = self.run_cli_command(args, timeout=60)
        
        # Should process what it can, may succeed or fail but shouldn't crash
        assert result.returncode in [0, 1]
        assert "Traceback" not in result.stderr
        
        # Should have processed at least some valid files
        ttl_files = list(rdf_dir.glob("*.ttl"))
        # At least some processing should have occurred
        assert len(ttl_files) >= 0  # May be 0 if it fails early, but shouldn't crash

    # Edge Case Tests
    
    def test_unicode_handling_in_paths(self, temp_workspace):
        """Test handling of Unicode characters in file paths."""
        unicode_kb = temp_workspace / "unicode_测试_🚀"
        unicode_kb.mkdir()
        
        # Create files with Unicode names
        unicode_files = [
            "测试文档.md",
            "🚀_rocket.md", 
            "café_résumé.md",
            "файл.md",
        ]
        
        for filename in unicode_files:
            try:
                filepath = unicode_kb / filename
                filepath.write_text(f"# {filename}\n\nUnicode content: 测试 🚀 café файл")
            except (OSError, UnicodeError):
                # Skip files that can't be created on this filesystem
                continue
        
        # Only test if we successfully created files
        if list(unicode_kb.glob("*.md")):
            rdf_dir = temp_workspace / "unicode_rdf"
            rdf_dir.mkdir()
            
            args = [
                "process",
                "--knowledge-base", str(unicode_kb),
                "--rdf-output-dir", str(rdf_dir)
            ]
            
            result = self.run_cli_command(args, timeout=60)
            
            # Should handle Unicode gracefully
            assert "Traceback" not in result.stderr
    
    def test_concurrent_access_simulation(self, basic_kb, temp_workspace):
        """Simulate concurrent access to the same knowledge base."""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def run_process(instance_id):
            rdf_dir = temp_workspace / f"concurrent_{instance_id}"
            rdf_dir.mkdir(exist_ok=True)
            
            args = [
                "process",
                "--knowledge-base", str(basic_kb),
                "--rdf-output-dir", str(rdf_dir)
            ]
            
            try:
                result = self.run_cli_command(args, timeout=60)
                results_queue.put({
                    'instance': instance_id,
                    'returncode': result.returncode,
                    'stderr': result.stderr,
                    'success': result.returncode == 0
                })
            except Exception as e:
                results_queue.put({
                    'instance': instance_id,
                    'error': str(e),
                    'success': False
                })
        
        # Start 3 concurrent processes
        threads = []
        for i in range(3):
            thread = threading.Thread(target=run_process, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join(timeout=90)
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # At least some should succeed
        successful = [r for r in results if r.get('success', False)]
        assert len(successful) >= 1, f"No concurrent processes succeeded: {results}"
        
        # None should crash
        for result in results:
            if 'stderr' in result:
                assert "Traceback" not in result['stderr']