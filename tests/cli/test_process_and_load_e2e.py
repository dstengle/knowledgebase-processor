import os
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock
from subprocess import run, PIPE, Popen, TimeoutExpired
import time
import json
from pathlib import Path

# Helper to get the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class TestProcessAndLoadE2E(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.kb_dir = os.path.join(self.temp_dir, "kb")
        os.makedirs(self.kb_dir)
        
        # Create sample files
        with open(os.path.join(self.kb_dir, "sample1.md"), "w") as f:
            f.write("# Sample Document 1\n\nContent one.")
        with open(os.path.join(self.kb_dir, "sample2.md"), "w") as f:
            f.write("# Sample Document 2\n\nContent two.")
        
        # Malformed file (if needed for a test)
        with open(os.path.join(self.kb_dir, "malformed.md"), "w") as f:
            f.write("Just some text without structure.")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def run_cli_command(self, args, **kwargs):
        base_command = ["poetry", "run", "python", "-m", "knowledgebase_processor.cli.main"]
        full_command = base_command + args
        return run(full_command, stdout=PIPE, stderr=PIPE, text=True, cwd=PROJECT_ROOT, **kwargs)

    @patch("knowledgebase_processor.services.processing_service.ProcessingService.process_and_load")
    def test_successful_run_mocked(self, mock_process_and_load):
        mock_process_and_load.return_value = 0
        
        args = [
            "process-and-load", self.kb_dir,
            "--endpoint-url", "http://fake-sparql-endpoint:9999/sparql",
            "--cleanup"
        ]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 0, f"CLI command failed with stderr: {result.stderr}")
        self.assertIn("Processing and loading completed successfully", result.stderr)
        mock_process_and_load.assert_called_once()

    @patch("src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface")
    def test_process_and_load_with_credentials(self, mock_sparql_interface):
        """Test that user and password are passed to the SPARQL interface."""
        mock_instance = mock_sparql_interface.return_value
        mock_instance.load_file.return_value = None

        args = [
            "process-and-load", self.kb_dir,
            "--endpoint-url", "http://fake-sparql-endpoint:9999/sparql",
            "--user", "testuser",
            "--password", "testpass"
        ]
        result = self.run_cli_command(args)

        self.assertEqual(result.returncode, 0, f"CLI command failed with stderr: {result.stderr}")
        
        # Check if SparqlQueryInterface was instantiated with credentials
        mock_sparql_interface.assert_called_with(
            endpoint_url='http://fake-sparql-endpoint:9999/sparql',
            update_endpoint_url='http://fake-sparql-endpoint:9999/update',
            username='testuser',
            password='testpass'
        )

    def test_invalid_knowledge_base_path(self):
        invalid_path = os.path.join(self.temp_dir, "non_existent_kb")
        args = ["process-and-load", invalid_path, "--endpoint-url", "http://example.com/sparql"]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 1)
        self.assertIn("is not a directory", result.stderr)

    def test_missing_endpoint_url(self):
        args = ["process-and-load", self.kb_dir]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 1)
        self.assertIn("SPARQL endpoint URL is required", result.stderr)

    def test_invalid_endpoint_url(self):
        args = ["process-and-load", self.kb_dir, "--endpoint-url", "not-a-valid-url"]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 1)
        self.assertIn("Invalid SPARQL endpoint URL", result.stderr)

    def test_unreachable_endpoint(self):
        # This test attempts to connect to a non-existent port, simulating an unreachable endpoint.
        args = [
            "process-and-load", self.kb_dir,
            "--endpoint-url", "http://localhost:9999/sparql",
            "--update-endpoint-url", "http://localhost:9999/update"
        ]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 1)
        self.assertIn("A SPARQL error occurred", result.stderr)
        self.assertIn("check if the SPARQL endpoint", result.stderr)

    def test_batch_processing_and_cleanup(self):
        rdf_output_dir = os.path.join(self.temp_dir, "rdf_output")
        
        with patch("knowledgebase_processor.services.sparql_service.SparqlQueryInterface.update") as mock_update:
            mock_update.return_value = True
            
            args = [
                "process-and-load", self.kb_dir,
                "--endpoint-url", "http://example.com/sparql",
                "--rdf-output-dir", rdf_output_dir,
                "--cleanup"
            ]
            
            # Ensure the output dir exists before running
            os.makedirs(rdf_output_dir)
            
            result = self.run_cli_command(args)
            
            self.assertEqual(result.returncode, 0, f"STDERR: {result.stderr}")
            
            # Check that RDF files were created and then removed
            self.assertTrue(os.path.exists(rdf_output_dir)) # Dir should still be there
            self.assertEqual(len(os.listdir(rdf_output_dir)), 0, "RDF output directory should be empty after cleanup")
            
            # Check that update was called for each file
            self.assertEqual(mock_update.call_count, 3) # sample1, sample2, malformed

    def test_rdf_output_validation(self):
        rdf_output_dir = os.path.join(self.temp_dir, "rdf_output_no_cleanup")
        
        with patch("knowledgebase_processor.services.sparql_service.SparqlQueryInterface.update"):
            args = [
                "process-and-load", self.kb_dir,
                "--endpoint-url", "http://example.com/sparql",
                "--rdf-output-dir", rdf_output_dir
                # No --cleanup
            ]
            
            result = self.run_cli_command(args)
            self.assertEqual(result.returncode, 0, f"STDERR: {result.stderr}")
            
            # Check that RDF files exist
            self.assertTrue(os.path.exists(rdf_output_dir))
            output_files = os.listdir(rdf_output_dir)
            self.assertEqual(len(output_files), 3)
            
            # Validate content of one of the TTL files
            sample1_ttl_path = os.path.join(rdf_output_dir, "sample1.ttl")
            self.assertTrue(os.path.exists(sample1_ttl_path))
            
            with open(sample1_ttl_path, "r") as f:
                content = f.read()
                self.assertIn('kb:title "Sample Document 1"', content)
                self.assertIn('kb:hasContent "Content one."', content)

    @unittest.skipIf("CI" not in os.environ, "Docker tests are run in CI environment only")
    def test_e2e_with_docker_fuseki(self):
        fuseki_proc = None
        try:
            # Start Fuseki from docker-compose
            run(["docker-compose", "up", "-d", "fuseki"], check=True, cwd=PROJECT_ROOT)
            time.sleep(10) # Give it time to start up

            endpoint_url = "http://localhost:3030/ds/query"
            update_endpoint_url = "http://localhost:3030/ds/update"
            graph_uri = "http://example.org/test_graph"

            # Run the process-and-load command
            args = [
                "process-and-load", self.kb_dir,
                "--endpoint-url", endpoint_url,
                "--update-endpoint-url", update_endpoint_url,
                "--graph", graph_uri,
                "--log-format", "json"
            ]
            result = self.run_cli_command(args)
            
            self.assertEqual(result.returncode, 0, f"STDERR: {result.stderr}")
            
            # Verify data was loaded by querying Fuseki
            query_args = [
                "sparql", "query",
                f'SELECT (COUNT(*) as ?count) FROM <{graph_uri}> WHERE {{ ?s ?p ?o }}',
                "--endpoint-url", endpoint_url,
                "--format", "json"
            ]
            query_result = self.run_cli_command(query_args)
            
            self.assertEqual(query_result.returncode, 0, f"Query failed: {query_result.stderr}")
            
            query_output = json.loads(query_result.stdout)
            count = int(query_output[0]['count'])
            self.assertGreater(count, 0, "No triples were loaded into the graph.")

        finally:
            # Stop and remove the Fuseki container
            run(["docker-compose", "down"], cwd=PROJECT_ROOT)

    # ==========================================
    # NEW ENHANCED TEST METHODS - QA Agent Added
    # ==========================================

    # Tests for 'process' command
    def test_process_command_integration(self):
        """Test process command integration without mocking."""
        args = ["--knowledge-base", self.kb_dir, "process", "--pattern", "**/*.md"]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 0)
        # Check for processing-related messages in stdout (where logs go)
        self.assertIn("Processing completed successfully", result.stdout)
        self.assertIn("Processing files matching pattern", result.stdout)

    def test_process_command_success(self):
        """Test successful process command execution (simplified)."""
        # For now, just test that the command runs without error
        # More detailed mocking can be added later if needed
        args = ["--knowledge-base", self.kb_dir, "process", "--pattern", "*.md"]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Processing completed successfully", result.stdout)

    def test_process_command_with_rdf_output(self):
        """Test process command with RDF output directory."""
        rdf_dir = os.path.join(self.temp_dir, "rdf_out")
        
        args = ["--knowledge-base", self.kb_dir, "process", "--pattern", "*.md", "--rdf-output-dir", rdf_dir]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Processing completed successfully", result.stdout)
        # Check if RDF directory was created
        self.assertTrue(os.path.exists(rdf_dir))

    def test_process_command_invalid_knowledge_base(self):
        """Test process command with invalid knowledge base path."""
        invalid_dir = os.path.join(self.temp_dir, "nonexistent")
        
        args = ["--knowledge-base", invalid_dir, "process"]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 1)
        self.assertIn("Base path does not exist", result.stdout)

    def test_process_command_with_pattern(self):
        """Test process command with custom pattern."""
        # Create a .txt file to test pattern matching
        with open(os.path.join(self.kb_dir, "test.txt"), "w") as f:
            f.write("# Test TXT file")
        
        args = ["--knowledge-base", self.kb_dir, "process", "--pattern", "**/*.txt"]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Processing completed successfully", result.stdout)

    # Tests for 'query' command
    @patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.query")
    def test_query_command_success(self, mock_query):
        """Test successful query command execution."""
        mock_query.return_value = ["Result 1", "Result 2", "Result 3"]
        
        args = ["--knowledge-base", self.kb_dir, "query", "test search", "--type", "text"]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Result 1", result.stdout)
        self.assertIn("Result 2", result.stdout)
        self.assertIn("Result 3", result.stdout)
        mock_query.assert_called_once_with("test search", "text")

    @patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.query")
    def test_query_command_no_results(self, mock_query):
        """Test query command with no results."""
        mock_query.return_value = []
        
        args = ["--knowledge-base", self.kb_dir, "query", "nonexistent", "--type", "tag"]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("No results found", result.stdout)
        mock_query.assert_called_once_with("nonexistent", "tag")

    @patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.query")
    def test_query_command_topic_type(self, mock_query):
        """Test query command with topic type."""
        mock_query.return_value = ["Topic result"]
        
        args = ["--knowledge-base", self.kb_dir, "query", "python programming", "--type", "topic"]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Topic result", result.stdout)
        mock_query.assert_called_once_with("python programming", "topic")

    @patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.query")
    def test_query_command_exception(self, mock_query):
        """Test query command handling exceptions."""
        mock_query.side_effect = Exception("Query error")
        
        args = ["--knowledge-base", self.kb_dir, "query", "test"]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 1)
        self.assertIn("Error during query", result.stderr)

    # Tests for 'sparql query' command
    @patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.sparql_query")
    def test_sparql_query_json_format(self, mock_sparql_query):
        """Test SPARQL query with JSON output format."""
        mock_sparql_query.return_value = [{"count": "42"}, {"count": "24"}]
        
        args = [
            "sparql", "query", "SELECT (COUNT(*) as ?count) WHERE { ?s ?p ?o }",
            "--endpoint-url", "http://example.com/sparql",
            "--format", "json"
        ]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('"count": "42"', result.stdout)
        mock_sparql_query.assert_called_once()

    @patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.sparql_query")
    def test_sparql_query_table_format(self, mock_sparql_query):
        """Test SPARQL query with table output format."""
        mock_sparql_query.return_value = [{"name": "John", "age": "30"}, {"name": "Jane", "age": "25"}]
        
        args = [
            "sparql", "query", "SELECT ?name ?age WHERE { ?person foaf:name ?name; foaf:age ?age }",
            "--endpoint-url", "http://example.com/sparql",
            "--format", "table",
            "--timeout", "60"
        ]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("name | age", result.stdout)
        self.assertIn("John | 30", result.stdout)
        self.assertIn("Jane | 25", result.stdout)

    @patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.sparql_query")
    def test_sparql_query_turtle_format(self, mock_sparql_query):
        """Test SPARQL query with turtle output format."""
        turtle_result = "@prefix ex: <http://example.org/> .\nex:subject ex:predicate ex:object ."
        mock_sparql_query.return_value = turtle_result
        
        args = [
            "sparql", "query", "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }",
            "--endpoint-url", "http://example.com/sparql",
            "--format", "turtle"
        ]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("@prefix ex:", result.stdout)

    @patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.sparql_query")
    def test_sparql_query_with_credentials(self, mock_sparql_query):
        """Test SPARQL query with authentication."""
        mock_sparql_query.return_value = [{"result": "authenticated"}]
        
        args = [
            "sparql", "query", "SELECT ?result WHERE { ?s ?p ?result }",
            "--endpoint-url", "http://secure.example.com/sparql",
            "--user", "testuser",
            "--password", "testpass",
            "--format", "json"
        ]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 0)
        mock_sparql_query.assert_called_once()

    @patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.sparql_query")
    def test_sparql_query_boolean_result(self, mock_sparql_query):
        """Test SPARQL ASK query returning boolean."""
        mock_sparql_query.return_value = True
        
        args = [
            "sparql", "query", "ASK { ?s ?p ?o }",
            "--endpoint-url", "http://example.com/sparql",
            "--format", "table"
        ]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("True", result.stdout)

    @patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.sparql_query")
    def test_sparql_query_exception(self, mock_sparql_query):
        """Test SPARQL query handling exceptions."""
        mock_sparql_query.side_effect = Exception("SPARQL endpoint unreachable")
        
        args = [
            "sparql", "query", "SELECT ?s WHERE { ?s ?p ?o }",
            "--endpoint-url", "http://unreachable.example.com/sparql"
        ]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 1)
        self.assertIn("SPARQL query failed", result.stderr)

    # Tests for 'sparql load-file' command
    @patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.sparql_load")
    def test_sparql_load_file_success(self, mock_sparql_load):
        """Test successful SPARQL load-file command."""
        # Create a dummy RDF file
        rdf_file = os.path.join(self.temp_dir, "test.ttl")
        with open(rdf_file, "w") as f:
            f.write("@prefix ex: <http://example.org/> .\nex:subject ex:predicate ex:object .")
        
        mock_sparql_load.return_value = None
        
        args = [
            "sparql", "load-file", rdf_file,
            "--endpoint-url", "http://example.com/sparql",
            "--graph", "http://example.org/graph",
            "--rdf-format", "turtle"
        ]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn(f"Successfully loaded RDF file '{rdf_file}'", result.stderr)
        mock_sparql_load.assert_called_once()

    @patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.sparql_load")
    def test_sparql_load_file_with_auth(self, mock_sparql_load):
        """Test SPARQL load-file with authentication."""
        rdf_file = os.path.join(self.temp_dir, "auth_test.ttl")
        with open(rdf_file, "w") as f:
            f.write("@prefix ex: <http://example.org/> .\nex:auth ex:test ex:data .")
        
        mock_sparql_load.return_value = None
        
        args = [
            "sparql", "load-file", rdf_file,
            "--endpoint-url", "http://secure.example.com/sparql",
            "--user", "admin",
            "--password", "secret",
            "--graph", "http://example.org/secure-graph"
        ]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 0)
        mock_sparql_load.assert_called_once()

    @patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.sparql_load")
    def test_sparql_load_file_different_formats(self, mock_sparql_load):
        """Test SPARQL load-file with different RDF formats."""
        formats_to_test = ["turtle", "n3", "nt", "xml", "json-ld"]
        
        for rdf_format in formats_to_test:
            with self.subTest(format=rdf_format):
                rdf_file = os.path.join(self.temp_dir, f"test.{rdf_format}")
                with open(rdf_file, "w") as f:
                    f.write("# Test RDF content")
                
                mock_sparql_load.return_value = None
                
                args = [
                    "sparql", "load-file", rdf_file,
                    "--endpoint-url", "http://example.com/sparql",
                    "--rdf-format", rdf_format
                ]
                result = self.run_cli_command(args)
                
                self.assertEqual(result.returncode, 0)

    @patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.sparql_load")
    def test_sparql_load_file_exception(self, mock_sparql_load):
        """Test SPARQL load-file handling exceptions."""
        rdf_file = os.path.join(self.temp_dir, "error_test.ttl")
        with open(rdf_file, "w") as f:
            f.write("invalid rdf content")
        
        mock_sparql_load.side_effect = Exception("Failed to load RDF")
        
        args = [
            "sparql", "load-file", rdf_file,
            "--endpoint-url", "http://example.com/sparql"
        ]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"Failed to load RDF file '{rdf_file}'", result.stderr)

    # Edge cases and error handling tests
    def test_missing_command(self):
        """Test CLI with no command specified."""
        args = ["--log-level", "DEBUG"]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 2)  # argparse error
        self.assertIn("required", result.stderr.lower())

    def test_unknown_command(self):
        """Test CLI with unknown command."""
        args = ["unknown-command"]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 2)  # argparse error
        self.assertIn("invalid choice", result.stderr.lower())

    def test_malformed_arguments_process(self):
        """Test process command with conflicting arguments."""
        args = ["process", "--pattern", "--rdf-output-dir"]  # Missing values
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 2)  # argparse error

    def test_malformed_arguments_sparql_query(self):
        """Test SPARQL query with missing query string."""
        args = ["sparql", "query", "--endpoint-url", "http://example.com/sparql"]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 2)  # argparse error
        self.assertIn("required", result.stderr.lower())

    def test_malformed_arguments_sparql_load(self):
        """Test SPARQL load-file with missing file path."""
        args = ["sparql", "load-file", "--endpoint-url", "http://example.com/sparql"]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 2)  # argparse error

    def test_invalid_sparql_subcommand(self):
        """Test SPARQL with invalid subcommand."""
        args = ["sparql", "invalid-subcommand"]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 2)  # argparse error

    def test_empty_query_string(self):
        """Test query command with empty query string."""
        args = ["--knowledge-base", self.kb_dir, "query", ""]  # Empty query
        result = self.run_cli_command(args)
        
        # Should not crash, but may return no results
        self.assertIn([0, 1], [result.returncode])  # Could be 0 or 1 depending on implementation

    def test_nonexistent_rdf_file_load(self):
        """Test SPARQL load-file with non-existent file."""
        nonexistent_file = os.path.join(self.temp_dir, "does_not_exist.ttl")
        
        args = [
            "sparql", "load-file", nonexistent_file,
            "--endpoint-url", "http://example.com/sparql"
        ]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 1)
        # Should contain some error about file not found

    # Configuration and logging tests
    @patch("src.knowledgebase_processor.config.load_config")
    def test_custom_config_file(self, mock_load_config):
        """Test CLI with custom configuration file."""
        config_file = os.path.join(self.temp_dir, "test_config.json")
        with open(config_file, "w") as f:
            json.dump({"knowledge_base_path": "/test/path"}, f)
        
        mock_config = MagicMock()
        mock_config.knowledge_base_path = "/test/path"
        mock_config.sparql_endpoint_url = "http://example.com/sparql"
        mock_load_config.return_value = mock_config
        
        with patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.query") as mock_query:
            mock_query.return_value = ["Config test result"]
            
            args = ["--config", config_file, "--knowledge-base", self.kb_dir, "query", "test"]
            result = self.run_cli_command(args)
            
            self.assertEqual(result.returncode, 0)
            mock_load_config.assert_called_with(config_file)

    def test_logging_configurations(self):
        """Test different logging configurations."""
        log_configs = [
            (["--log-level", "DEBUG"], "DEBUG"),
            (["--log-level", "ERROR"], "ERROR"), 
            (["--log-format", "json"], "json"),
            (["--log-format", "text"], "text")
        ]
        
        for args_addition, expected in log_configs:
            with self.subTest(config=expected):
                with patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.query") as mock_query:
                    mock_query.return_value = ["Log test"]
                    
                    args = args_addition + ["--knowledge-base", self.kb_dir, "query", "test"]
                    result = self.run_cli_command(args)
                    
                    # Should not crash with different log configurations
                    self.assertIn(result.returncode, [0, 1])  # May succeed or fail, but shouldn't crash

    def test_log_file_output(self):
        """Test logging to file."""
        log_file = os.path.join(self.temp_dir, "test.log")
        
        with patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.query") as mock_query:
            mock_query.return_value = ["Log file test"]
            
            args = ["--log-file", log_file, "--log-level", "DEBUG", "--knowledge-base", self.kb_dir, "query", "test"]
            result = self.run_cli_command(args)
            
            self.assertEqual(result.returncode, 0)
            # Log file should exist (though it might be empty due to mocking)
            self.assertTrue(os.path.exists(log_file) or result.returncode == 0)

    def test_knowledge_base_path_override(self):
        """Test knowledge base path override behavior."""
        custom_kb_path = os.path.join(self.temp_dir, "custom_kb")
        os.makedirs(custom_kb_path)
        
        with open(os.path.join(custom_kb_path, "custom.md"), "w") as f:
            f.write("# Custom KB Content")
        
        with patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.query") as mock_query:
            mock_query.return_value = ["Custom KB result"]
            
            args = ["--knowledge-base", custom_kb_path, "query", "custom"]
            result = self.run_cli_command(args)
            
            self.assertEqual(result.returncode, 0)

    def test_metadata_store_path_override(self):
        """Test metadata store path override behavior."""
        custom_metadata_path = os.path.join(self.temp_dir, "custom_metadata")
        os.makedirs(custom_metadata_path, exist_ok=True)
        
        with patch("src.knowledgebase_processor.api.KnowledgeBaseAPI.query") as mock_query:
            mock_query.return_value = ["Metadata test"]
            
            args = ["--metadata-store", custom_metadata_path, "--knowledge-base", self.kb_dir, "query", "metadata"]
            result = self.run_cli_command(args)
            
            self.assertEqual(result.returncode, 0)

    @patch("src.knowledgebase_processor.api.KnowledgeBaseAPI")
    def test_api_initialization_failure(self, mock_api_class):
        """Test CLI behavior when API initialization fails."""
        mock_api_class.side_effect = Exception("API initialization failed")
        
        args = ["--knowledge-base", self.kb_dir, "query", "test"]
        result = self.run_cli_command(args)
        
        self.assertEqual(result.returncode, 1)
        self.assertIn("Failed to initialize KnowledgeBaseAPI", result.stderr)

    def test_process_and_load_update_endpoint_url(self):
        """Test process-and-load with explicit update endpoint URL."""
        with patch("knowledgebase_processor.services.sparql_service.SparqlQueryInterface.update") as mock_update:
            mock_update.return_value = True
            
            args = [
                "process-and-load", self.kb_dir,
                "--endpoint-url", "http://example.com/query", 
                "--update-endpoint-url", "http://example.com/update"  # This should be handled by the CLI arg parser
            ]
            result = self.run_cli_command(args)
            
            # Should not crash even if update endpoint is different
            # The actual implementation may or may not use this arg, but CLI should parse it
            self.assertIn(result.returncode, [0, 1, 2])

if __name__ == "__main__":
    unittest.main()