"""End-to-end tests for the Knowledge Base Processor CLI.

These tests use subprocess to run the actual CLI commands and verify the complete
user workflows from command line to output.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import List, Optional


class TestE2ECLI(unittest.TestCase):
    """End-to-end tests for CLI commands using subprocess."""
    
    def setUp(self):
        """Set up test environment with temporary directories and test files."""
        # Create temporary directory for test environment
        self.temp_dir = tempfile.mkdtemp()
        self.temp_dir_path = Path(self.temp_dir)
        
        # Create metadata store directory
        self.metadata_store_dir = self.temp_dir_path / "metadata"
        self.metadata_store_dir.mkdir(parents=True, exist_ok=True)
        
        # Create RDF output directory
        self.rdf_output_dir = self.temp_dir_path / "rdf_output"
        self.rdf_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test markdown files
        self.create_test_files()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def create_test_files(self):
        """Create test markdown files for E2E testing."""
        # Test file 1: Simple document with entities
        test_file_1 = self.temp_dir_path / "test_document.md"
        test_file_1.write_text("""---
title: "Test Document"
tags: [test, sample]
created: 2024-11-07T10:00:00-05:00
---

# Test Document

This is a test document for E2E testing.

## People
- [[John Doe]] is a software engineer
- [[Jane Smith]] works at [[Acme Corp]]

## Tasks
- [x] Complete project setup
- [ ] Write documentation
- [ ] Review code

## Topics
This document covers #testing and #automation topics.
""")
        
        # Test file 2: Another document for query testing
        test_file_2 = self.temp_dir_path / "second_document.md"
        test_file_2.write_text("""---
title: "Second Document"
tags: [example, demo]
---

# Second Document

This document mentions [[John Doe]] again and discusses #automation.

- [ ] Setup CI/CD pipeline
- [x] Configure testing framework
""")
    
    def run_cli_command(self, args: List[str], expect_success: bool = True) -> subprocess.CompletedProcess:
        """Run a CLI command and return the result.
        
        Args:
            args: Command arguments
            expect_success: Whether to expect the command to succeed
            
        Returns:
            CompletedProcess result
        """
        # Build command with poetry run prefix and metadata store
        cmd = [
            "poetry", "run", "python", "-m", "knowledgebase_processor.cli",
            "--metadata-store", str(self.metadata_store_dir),
            "--knowledge-base", str(self.temp_dir_path)
        ] + args
        
        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd()  # Run from project root
        )
        
        if expect_success and result.returncode != 0:
            self.fail(f"Command failed with exit code {result.returncode}.\n"
                     f"Command: {' '.join(cmd)}\n"
                     f"Stdout: {result.stdout}\n"
                     f"Stderr: {result.stderr}")
        
        return result
    
    def test_process_command_basic(self):
        """Test the process command processes files successfully."""
        # Run process command
        result = self.run_cli_command([
            "process",
            "--pattern", "*.md"
        ])
        
        # Verify success
        self.assertEqual(result.returncode, 0)
        
        # Check that output indicates success
        output = result.stdout + result.stderr
        self.assertIn("Processing completed successfully", output)
        
        # Verify metadata store was created
        metadata_files = list(self.metadata_store_dir.glob("*.db"))
        self.assertTrue(len(metadata_files) > 0, "Metadata database should be created")
    
    def test_process_command_with_rdf_output(self):
        """Test the process command with RDF output generation."""
        # Run process command with RDF output
        result = self.run_cli_command([
            "process",
            "--pattern", "*.md",
            "--rdf-output-dir", str(self.rdf_output_dir)
        ])
        
        # Verify success
        self.assertEqual(result.returncode, 0)
        
        # Check that output indicates success
        output = result.stdout + result.stderr
        self.assertIn("Processing completed successfully", output)
        
        # Verify RDF files were created
        rdf_files = list(self.rdf_output_dir.glob("*.ttl"))
        self.assertTrue(len(rdf_files) > 0, "RDF files should be generated")
        
        # Verify RDF files contain valid content
        for rdf_file in rdf_files:
            content = rdf_file.read_text()
            # Check for basic RDF structure
            self.assertIn("@prefix", content, f"RDF file {rdf_file} should contain prefix declarations")
    
    @unittest.skip("Query command is not implemented in this version.")
    def test_query_command_text_search(self):
        """Test the query command with text search."""
        # First process the files
        self.run_cli_command([
            "process",
            "--pattern", "*.md"
        ])
        
        # Run text query
        result = self.run_cli_command([
            "query",
            "--type", "text",
            "John Doe"
        ])
        
        # Verify success
        self.assertEqual(result.returncode, 0)
        
        # Check that results are returned
        output = result.stdout
        # Should find documents containing "John Doe"
        self.assertTrue(
            "Found" in output and "results" in output or "No results found" in output,
            "Query should return formatted results"
        )
    
    @unittest.skip("Query command is not implemented in this version.")
    def test_query_command_tag_search(self):
        """Test the query command with tag search."""
        # First process the files
        self.run_cli_command([
            "process",
            "--pattern", "*.md"
        ])
        
        # Run tag query
        result = self.run_cli_command([
            "query",
            "--type", "tag",
            "test"
        ])
        
        # Verify success
        self.assertEqual(result.returncode, 0)
        
        # Check that results are returned
        output = result.stdout
        self.assertTrue(
            "Found" in output and "results" in output or "No results found" in output,
            "Tag query should return formatted results"
        )
    
    def test_sparql_query_command_basic(self):
        """Test the SPARQL query command with a basic query."""
        # First process files and generate RDF
        self.run_cli_command([
            "process",
            "--pattern", "*.md",
            "--rdf-output-dir", str(self.rdf_output_dir)
        ])
        
        # Simple SPARQL query to test basic functionality
        sparql_query = """
        SELECT ?s ?p ?o
        WHERE {
            ?s ?p ?o .
        }
        LIMIT 5
        """
        
        # Run SPARQL query (this may fail if no SPARQL endpoint is configured)
        # We'll test that the command parsing works, even if the endpoint is not available
        result = subprocess.run([
            "poetry", "run", "python", "-m", "knowledgebase_processor.cli",
            "--metadata-store", str(self.metadata_store_dir),
            "--knowledge-base", str(self.temp_dir_path),
            "sparql", "query",
            "--format", "json",
            sparql_query
        ], capture_output=True, text=True)
        
        # The command should either succeed (if SPARQL endpoint available) 
        # or fail gracefully with a meaningful error message
        if result.returncode == 0:
            # If successful, output should be valid JSON or table format
            self.assertTrue(len(result.stdout) > 0, "SPARQL query should produce output")
        else:
            # If failed, should be due to connection issues, not parsing errors
            error_output = result.stderr + result.stdout
            # Should not be a Python traceback or argument parsing error
            self.assertNotIn("Traceback", error_output, "Should not have Python traceback")
            self.assertNotIn("unrecognized arguments", error_output, "Should not have argument parsing errors")
    
    def test_sparql_load_file_command(self):
        """Test the SPARQL load-file command."""
        # First process files and generate RDF
        self.run_cli_command([
            "process",
            "--pattern", "*.md",
            "--rdf-output-dir", str(self.rdf_output_dir)
        ])
        
        # Find an RDF file to load
        rdf_files = list(self.rdf_output_dir.glob("*.ttl"))
        self.assertTrue(len(rdf_files) > 0, "Need RDF files for load test")
        
        rdf_file = rdf_files[0]
        
        # Test SPARQL load command (may fail if no SPARQL endpoint available)
        result = subprocess.run([
            "poetry", "run", "python", "-m", "knowledgebase_processor.cli",
            "--metadata-store", str(self.metadata_store_dir),
            "--knowledge-base", str(self.temp_dir_path),
            "sparql", "load-file",
            "--rdf-format", "turtle",
            str(rdf_file)
        ], capture_output=True, text=True)
        
        # The command should either succeed or fail gracefully
        if result.returncode == 0:
            # If successful, should have success message
            output = result.stdout + result.stderr
            self.assertIn("Successfully loaded", output, "Should report successful load")
        else:
            # If failed, should be due to connection issues, not parsing errors
            error_output = result.stderr + result.stdout
            self.assertNotIn("Traceback", error_output, "Should not have Python traceback")
            self.assertNotIn("unrecognized arguments", error_output, "Should not have argument parsing errors")
    
    def test_invalid_command_handling(self):
        """Test that invalid commands are handled gracefully."""
        # Test invalid main command
        result = subprocess.run([
            "poetry", "run", "python", "-m", "knowledgebase_processor.cli",
            "invalid_command"
        ], capture_output=True, text=True)
        
        self.assertNotEqual(result.returncode, 0, "Invalid command should fail")
        
        # Should show help or error message, not crash
        error_output = result.stderr
        self.assertNotIn("Traceback", error_output, "Should not crash with traceback")
    
    def test_help_commands(self):
        """Test that help commands work properly."""
        # Test main help
        result = subprocess.run([
            "poetry", "run", "python", "-m", "knowledgebase_processor.cli",
            "--help"
        ], capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0, "Help command should succeed")
        self.assertIn("Knowledge Base Processor", result.stdout, "Should show main help")
        
        # Test process help
        result = subprocess.run([
            "poetry", "run", "python", "-m", "knowledgebase_processor.cli",
            "process", "--help"
        ], capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0, "Process help should succeed")
        self.assertIn("process", result.stdout, "Should show process help")
    
    def test_configuration_file_handling(self):
        """Test that configuration file handling works."""
        # Create a simple config file
        config_file = self.temp_dir_path / "test_config.json"
        config_file.write_text("""{
    "knowledge_base_path": ".",
    "metadata_store_path": "./metadata/test.db",
    "log_level": "INFO"
}""")
        
        # Run command with config file
        result = self.run_cli_command([
            "--config", str(config_file),
            "process",
            "--pattern", "*.md"
        ])
        
        # Should succeed (config parsing should work)
        self.assertEqual(result.returncode, 0)
    
    def test_log_level_configuration(self):
        """Test that log level configuration works."""
        # Test with DEBUG log level
        result = self.run_cli_command([
            "--log-level", "DEBUG",
            "process",
            "--pattern", "*.md"
        ])
        
        self.assertEqual(result.returncode, 0)
        
        # Debug output should contain more verbose logging
        output = result.stdout + result.stderr
        # At minimum, should not crash due to logging configuration
        self.assertNotIn("Traceback", output, "Should not crash due to logging config")


if __name__ == "__main__":
    unittest.main()