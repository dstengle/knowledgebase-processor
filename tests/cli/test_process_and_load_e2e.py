import os
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock
from subprocess import run, PIPE, Popen, TimeoutExpired
import time
import json

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

    @patch("src.knowledgebase_processor.services.processing_service.ProcessingService.process_and_load")
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
        
        with patch("src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface.update") as mock_update:
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
        
        with patch("src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface.update"):
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

if __name__ == "__main__":
    unittest.main()