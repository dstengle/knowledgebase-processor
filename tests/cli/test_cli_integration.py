"""Integration tests for CLI argument combinations and edge cases."""

import argparse
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from knowledgebase_processor.cli.main import main, parse_args
from knowledgebase_processor.config import Config
from knowledgebase_processor.api import KnowledgeBaseAPI


class TestCliIntegration:
    """Test CLI integration scenarios with various argument combinations."""

    @pytest.fixture
    def temp_directory(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_api(self):
        """Create a mock KnowledgeBaseAPI with typical configuration."""
        api = Mock(spec=KnowledgeBaseAPI)
        api.config = Mock(spec=Config)
        api.config.knowledge_base_path = "/test/kb"
        api.config.sparql_endpoint_url = "http://localhost:3030/sparql"
        api.config.metadata_store_path = "/test/.kbp/metadata/knowledgebase.db"
        
        # Mock service methods
        api.process_documents = Mock(return_value=0)
        api.query = Mock(return_value=["result1", "result2"])
        api.sparql_query = Mock(return_value=[{"subject": "s1", "predicate": "p1", "object": "o1"}])
        api.sparql_load = Mock()
        
        api.processing_service = Mock()
        api.processing_service.process_and_load = Mock(return_value=0)
        
        return api

    def setup_common_mocks(self, mock_api):
        """Setup common mocks for CLI testing."""
        with patch('knowledgebase_processor.cli.main.setup_logging'), \
             patch('knowledgebase_processor.cli.main.load_config') as mock_load_config, \
             patch('knowledgebase_processor.cli.main.KnowledgeBaseAPI') as mock_api_class:
            
            mock_load_config.return_value = mock_api.config
            mock_api_class.return_value = mock_api
            
            return mock_load_config, mock_api_class


class TestProcessCommandIntegration(TestCliIntegration):
    """Test process command with various configurations."""

    def test_process_command_minimal_arguments(self, mock_api):
        """Test process command with minimal arguments."""
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        result = main(["process"])
        
        assert result == 0
        mock_api.process_documents.assert_called_once_with(
            pattern="**/*.md",
            rdf_output_dir=None
        )

    def test_process_command_with_custom_pattern(self, mock_api):
        """Test process command with custom file pattern."""
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        result = main(["process", "--pattern", "*.txt"])
        
        assert result == 0
        mock_api.process_documents.assert_called_once_with(
            pattern="*.txt",
            rdf_output_dir=None
        )

    def test_process_command_with_rdf_output(self, mock_api, temp_directory):
        """Test process command with RDF output directory."""
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        rdf_dir = str(Path(temp_directory) / "rdf_output")
        
        result = main(["process", "--rdf-output-dir", rdf_dir])
        
        assert result == 0
        mock_api.process_documents.assert_called_once_with(
            pattern="**/*.md",
            rdf_output_dir=Path(rdf_dir)
        )

    def test_process_command_with_global_options(self, mock_api, temp_directory):
        """Test process command with global options."""
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        config_file = str(Path(temp_directory) / "config.yaml")
        kb_path = str(Path(temp_directory) / "kb")
        
        result = main([
            "--config", config_file,
            "--knowledge-base", kb_path,
            "--log-level", "DEBUG",
            "process",
            "--pattern", "docs/**/*.md"
        ])
        
        assert result == 0
        # Verify config override
        assert mock_api.config.knowledge_base_path == kb_path


class TestQueryCommandIntegration(TestCliIntegration):
    """Test query command with various configurations."""

    def test_query_command_text_search(self, mock_api, capsys):
        """Test text query command."""
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        result = main(["query", "test search"])
        
        assert result == 0
        mock_api.query.assert_called_once_with("test search", "text")
        
        captured = capsys.readouterr()
        assert "result1" in captured.out
        assert "result2" in captured.out

    def test_query_command_tag_search(self, mock_api, capsys):
        """Test tag query command."""
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        result = main(["query", "important", "--type", "tag"])
        
        assert result == 0
        mock_api.query.assert_called_once_with("important", "tag")

    def test_query_command_no_results(self, mock_api, capsys):
        """Test query command with no results."""
        mock_api.query.return_value = []
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        result = main(["query", "nonexistent"])
        
        assert result == 0
        captured = capsys.readouterr()
        assert "No results found." in captured.out


class TestSparqlCommandIntegration(TestCliIntegration):
    """Test SPARQL command with various configurations."""

    def test_sparql_query_json_format(self, mock_api, capsys):
        """Test SPARQL query with JSON format."""
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        result = main([
            "sparql", "query", "SELECT * WHERE { ?s ?p ?o }",
            "--format", "json"
        ])
        
        assert result == 0
        mock_api.sparql_query.assert_called_once_with(
            query="SELECT * WHERE { ?s ?p ?o }",
            endpoint_url=None,
            timeout=30,
            format="json"
        )
        
        captured = capsys.readouterr()
        # Should be valid JSON
        json.loads(captured.out)

    def test_sparql_query_table_format(self, mock_api, capsys):
        """Test SPARQL query with table format."""
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        result = main([
            "sparql", "query", "SELECT * WHERE { ?s ?p ?o }",
            "--format", "table",
            "--timeout", "60"
        ])
        
        assert result == 0
        mock_api.sparql_query.assert_called_once_with(
            query="SELECT * WHERE { ?s ?p ?o }",
            endpoint_url=None,
            timeout=60,
            format="table"
        )
        
        captured = capsys.readouterr()
        assert "subject | predicate | object" in captured.out

    def test_sparql_query_with_endpoint_and_credentials(self, mock_api):
        """Test SPARQL query with custom endpoint and credentials."""
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        result = main([
            "sparql", "query", "SELECT * WHERE { ?s ?p ?o }",
            "--endpoint-url", "http://custom:3030/sparql",
            "--user", "admin",
            "--password", "secret",
            "--format", "json"
        ])
        
        assert result == 0
        mock_api.sparql_query.assert_called_once_with(
            query="SELECT * WHERE { ?s ?p ?o }",
            endpoint_url="http://custom:3030/sparql",
            timeout=30,
            format="json"
        )

    def test_sparql_load_file_minimal(self, mock_api, temp_directory):
        """Test SPARQL load-file with minimal arguments."""
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        test_file = str(Path(temp_directory) / "test.ttl")
        Path(test_file).touch()  # Create empty file
        
        result = main(["sparql", "load-file", test_file])
        
        assert result == 0
        mock_api.sparql_load.assert_called_once_with(
            file_path=Path(test_file),
            graph_uri=None,
            endpoint_url=None,
            username=None,
            password=None,
            rdf_format="turtle"
        )

    def test_sparql_load_file_with_all_options(self, mock_api, temp_directory):
        """Test SPARQL load-file with all options."""
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        test_file = str(Path(temp_directory) / "test.n3")
        Path(test_file).touch()  # Create empty file
        
        result = main([
            "sparql", "load-file", test_file,
            "--graph", "http://example.org/graph",
            "--endpoint-url", "http://localhost:3030/sparql",
            "--user", "admin",
            "--password", "secret",
            "--rdf-format", "n3"
        ])
        
        assert result == 0
        mock_api.sparql_load.assert_called_once_with(
            file_path=Path(test_file),
            graph_uri="http://example.org/graph",
            endpoint_url="http://localhost:3030/sparql",
            username="admin",
            password="secret",
            rdf_format="n3"
        )


class TestProcessAndLoadIntegration(TestCliIntegration):
    """Test process-and-load command integration."""

    @patch('knowledgebase_processor.cli.main.is_valid_url')
    @patch('pathlib.Path.is_dir')
    def test_process_and_load_minimal(self, mock_is_dir, mock_is_valid_url, mock_api):
        """Test process-and-load with minimal arguments."""
        mock_is_dir.return_value = True
        mock_is_valid_url.return_value = True
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        result = main([
            "process-and-load",
            "--endpoint-url", "http://localhost:3030/sparql"
        ])
        
        assert result == 0
        mock_api.processing_service.process_and_load.assert_called_once()

    @patch('knowledgebase_processor.cli.main.is_valid_url')
    @patch('pathlib.Path.is_dir')
    def test_process_and_load_with_knowledge_base_path(self, mock_is_dir, mock_is_valid_url, mock_api, temp_directory):
        """Test process-and-load with explicit knowledge base path."""
        mock_is_dir.return_value = True
        mock_is_valid_url.return_value = True
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        kb_path = str(Path(temp_directory) / "kb")
        Path(kb_path).mkdir()
        
        result = main([
            "process-and-load", kb_path,
            "--endpoint-url", "http://localhost:3030/sparql",
            "--pattern", "*.md",
            "--cleanup"
        ])
        
        assert result == 0
        call_args = mock_api.processing_service.process_and_load.call_args
        assert call_args[1]['knowledge_base_path'] == Path(kb_path)
        assert call_args[1]['pattern'] == "*.md"
        assert call_args[1]['cleanup'] is True

    @patch('knowledgebase_processor.cli.main.is_valid_url')
    @patch('pathlib.Path.is_dir')
    def test_process_and_load_with_all_options(self, mock_is_dir, mock_is_valid_url, mock_api, temp_directory):
        """Test process-and-load with all options."""
        mock_is_dir.return_value = True
        mock_is_valid_url.return_value = True
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        kb_path = str(Path(temp_directory) / "kb")
        rdf_path = str(Path(temp_directory) / "rdf")
        Path(kb_path).mkdir()
        
        result = main([
            "process-and-load", kb_path,
            "--pattern", "docs/**/*.md",
            "--graph", "http://example.org/graph",
            "--endpoint-url", "http://localhost:3030/sparql",
            "--cleanup",
            "--rdf-output-dir", rdf_path,
            "--user", "admin",
            "--password", "secret"
        ])
        
        assert result == 0
        call_args = mock_api.processing_service.process_and_load.call_args
        assert call_args[1]['knowledge_base_path'] == Path(kb_path)
        assert call_args[1]['pattern'] == "docs/**/*.md"
        assert call_args[1]['graph_uri'] == "http://example.org/graph"
        assert call_args[1]['endpoint_url'] == "http://localhost:3030/sparql"
        assert call_args[1]['cleanup'] is True
        assert call_args[1]['rdf_output_dir'] == Path(rdf_path)
        assert call_args[1]['username'] == "admin"
        assert call_args[1]['password'] == "secret"


class TestConfigurationOverrides(TestCliIntegration):
    """Test configuration override scenarios."""

    def test_knowledge_base_path_precedence(self, mock_api, temp_directory):
        """Test knowledge base path precedence: CLI > config > default."""
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        # Test CLI override
        cli_kb_path = str(Path(temp_directory) / "cli_kb")
        result = main(["--knowledge-base", cli_kb_path, "process"])
        assert result == 0
        assert mock_api.config.knowledge_base_path == cli_kb_path

    @patch('pathlib.Path.cwd')
    def test_knowledge_base_path_default_to_cwd(self, mock_cwd, mock_api):
        """Test knowledge base path defaults to current working directory."""
        mock_cwd.return_value = Path("/current/working/dir")
        
        # Remove knowledge_base_path from config to test default
        delattr(mock_api.config, 'knowledge_base_path')
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        result = main(["process"])
        assert result == 0
        assert mock_api.config.knowledge_base_path == "/current/working/dir"

    @patch('pathlib.Path.home')
    def test_metadata_store_path_precedence(self, mock_home, mock_api, temp_directory):
        """Test metadata store path precedence: CLI > config > default."""
        mock_home.return_value = Path("/home/user")
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        # Test CLI override
        cli_metadata_path = str(Path(temp_directory) / "cli_metadata")
        result = main(["--metadata-store", cli_metadata_path, "process"])
        assert result == 0
        assert mock_api.config.metadata_store_path == f"{cli_metadata_path}/knowledgebase.db"

    @patch('pathlib.Path.home')
    def test_metadata_store_path_default(self, mock_home, mock_api):
        """Test metadata store path defaults to ~/.kbp/metadata."""
        mock_home.return_value = Path("/home/user")
        
        # Remove metadata_store_path from config to test default
        delattr(mock_api.config, 'metadata_store_path')
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        result = main(["process"])
        assert result == 0
        assert mock_api.config.metadata_store_path == "/home/user/.kbp/metadata/knowledgebase.db"


class TestErrorHandlingIntegration(TestCliIntegration):
    """Test error handling in integration scenarios."""

    def test_api_initialization_failure_integration(self, mock_api):
        """Test complete flow when API initialization fails."""
        with patch('knowledgebase_processor.cli.main.setup_logging'), \
             patch('knowledgebase_processor.cli.main.load_config') as mock_load_config, \
             patch('knowledgebase_processor.cli.main.KnowledgeBaseAPI') as mock_api_class:
            
            mock_load_config.return_value = mock_api.config
            mock_api_class.side_effect = Exception("API initialization failed")
            
            result = main(["process"])
            
            assert result == 1

    def test_command_handler_failure_integration(self, mock_api):
        """Test complete flow when command handler fails."""
        mock_api.process_documents.return_value = 1  # Failure code
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        result = main(["process"])
        
        assert result == 1

    def test_command_handler_exception_integration(self, mock_api):
        """Test complete flow when command handler raises exception."""
        mock_api.process_documents.side_effect = Exception("Processing failed")
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        result = main(["process"])
        
        assert result == 1

    @patch('knowledgebase_processor.cli.main.is_valid_url')
    @patch('pathlib.Path.is_dir')
    def test_process_and_load_validation_failures(self, mock_is_dir, mock_is_valid_url, mock_api):
        """Test process-and-load validation failure scenarios."""
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        # Test invalid knowledge base path
        mock_is_dir.return_value = False
        result = main([
            "process-and-load", "/invalid/path",
            "--endpoint-url", "http://localhost:3030/sparql"
        ])
        assert result == 1
        
        # Test invalid endpoint URL
        mock_is_dir.return_value = True
        mock_is_valid_url.return_value = False
        result = main([
            "process-and-load", "/valid/path",
            "--endpoint-url", "invalid-url"
        ])
        assert result == 1

    def test_missing_endpoint_url_integration(self, mock_api):
        """Test process-and-load without endpoint URL."""
        mock_api.config.sparql_endpoint_url = None
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        with patch('pathlib.Path.is_dir', return_value=True):
            result = main(["process-and-load", "/valid/path"])
            
        assert result == 1


class TestComplexArgumentCombinations(TestCliIntegration):
    """Test complex argument combinations and edge cases."""

    def test_all_global_options_with_process_and_load(self, mock_api, temp_directory):
        """Test all global options with process-and-load command."""
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        config_file = str(Path(temp_directory) / "config.yaml")
        kb_path = str(Path(temp_directory) / "kb")
        metadata_path = str(Path(temp_directory) / "metadata")
        log_file = str(Path(temp_directory) / "app.log")
        rdf_path = str(Path(temp_directory) / "rdf")
        Path(kb_path).mkdir()
        
        with patch('knowledgebase_processor.cli.main.is_valid_url', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=True):
            
            result = main([
                "--config", config_file,
                "--knowledge-base", kb_path,
                "--metadata-store", metadata_path,
                "--log-level", "DEBUG",
                "--log-file", log_file,
                "--log-format", "json",
                "process-and-load", kb_path,
                "--pattern", "docs/**/*.md",
                "--graph", "http://example.org/graph",
                "--endpoint-url", "http://localhost:3030/sparql",
                "--cleanup",
                "--rdf-output-dir", rdf_path,
                "--user", "admin",
                "--password", "secret"
            ])
        
        assert result == 0
        # Verify configuration overrides
        assert mock_api.config.knowledge_base_path == kb_path
        assert mock_api.config.metadata_store_path == f"{metadata_path}/knowledgebase.db"

    def test_sparql_query_with_all_options(self, mock_api, capsys):
        """Test SPARQL query with all available options."""
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        result = main([
            "--log-level", "INFO",
            "--log-format", "json",
            "sparql", "query", "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10",
            "--endpoint-url", "https://dbpedia.org/sparql",
            "--timeout", "120",
            "--format", "json",
            "--user", "dbuser",
            "--password", "dbpass"
        ])
        
        assert result == 0
        mock_api.sparql_query.assert_called_once_with(
            query="SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10",
            endpoint_url="https://dbpedia.org/sparql",
            timeout=120,
            format="json"
        )

    def test_query_with_special_characters(self, mock_api, capsys):
        """Test query command with special characters and spaces."""
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        query_with_spaces = "search term with spaces and 'quotes'"
        result = main(["query", query_with_spaces, "--type", "text"])
        
        assert result == 0
        mock_api.query.assert_called_once_with(query_with_spaces, "text")

    def test_file_paths_with_spaces_and_special_chars(self, mock_api, temp_directory):
        """Test file paths containing spaces and special characters."""
        mock_load_config, mock_api_class = self.setup_common_mocks(mock_api)
        
        # Create paths with spaces
        kb_path = str(Path(temp_directory) / "knowledge base with spaces")
        rdf_path = str(Path(temp_directory) / "rdf output")
        test_file = str(Path(temp_directory) / "test file.ttl")
        
        Path(kb_path).mkdir()
        Path(test_file).touch()
        
        # Test process command with spaces in paths
        result = main([
            "--knowledge-base", kb_path,
            "process",
            "--rdf-output-dir", rdf_path
        ])
        
        assert result == 0
        assert mock_api.config.knowledge_base_path == kb_path
        mock_api.process_documents.assert_called_once_with(
            pattern="**/*.md",
            rdf_output_dir=Path(rdf_path)
        )

        # Test SPARQL load with file containing spaces
        result = main(["sparql", "load-file", test_file])
        
        assert result == 0
        mock_api.sparql_load.assert_called_once_with(
            file_path=Path(test_file),
            graph_uri=None,
            endpoint_url=None,
            username=None,
            password=None,
            rdf_format="turtle"
        )