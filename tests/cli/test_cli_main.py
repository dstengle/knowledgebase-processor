"""Unit tests for CLI main functionality."""

import argparse
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from urllib.parse import urlparse

from knowledgebase_processor.cli.main import (
    main, parse_args, is_valid_url
)
from knowledgebase_processor.config import Config
from knowledgebase_processor.api import KnowledgeBaseAPI


class TestIsValidUrl:
    """Test URL validation function."""

    def test_valid_http_url(self):
        assert is_valid_url("http://example.com") is True

    def test_valid_https_url(self):
        assert is_valid_url("https://example.com") is True

    def test_valid_url_with_port(self):
        assert is_valid_url("http://localhost:3030") is True

    def test_valid_url_with_path(self):
        assert is_valid_url("https://example.com/sparql") is True

    def test_invalid_url_no_scheme(self):
        assert is_valid_url("example.com") is False

    def test_invalid_url_no_netloc(self):
        assert is_valid_url("http://") is False

    def test_invalid_url_empty_string(self):
        assert is_valid_url("") is False

    def test_invalid_url_none(self):
        assert is_valid_url(None) is False

    def test_invalid_url_malformed(self):
        assert is_valid_url("not-a-url") is False

    def test_url_with_query_params(self):
        assert is_valid_url("https://example.com/sparql?query=test") is True


class TestParseArgs:
    """Test CLI argument parsing."""

    def test_process_command_minimal(self):
        args = parse_args(["process"])
        assert args.command == "process"
        assert args.pattern == "**/*.md"
        assert args.rdf_output_dir is None

    def test_process_command_with_pattern(self):
        args = parse_args(["process", "--pattern", "*.txt"])
        assert args.command == "process"
        assert args.pattern == "*.txt"

    def test_process_command_with_rdf_output(self):
        args = parse_args(["process", "--rdf-output-dir", "/tmp/rdf"])
        assert args.command == "process"
        assert args.rdf_output_dir == "/tmp/rdf"

    def test_query_command_minimal(self):
        args = parse_args(["query", "test search"])
        assert args.command == "query"
        assert args.query_string == "test search"
        assert args.type == "text"

    def test_query_command_with_type(self):
        args = parse_args(["query", "test", "--type", "tag"])
        assert args.command == "query"
        assert args.query_string == "test"
        assert args.type == "tag"

    def test_sparql_query_command(self):
        args = parse_args(["sparql", "query", "SELECT * WHERE { ?s ?p ?o }"])
        assert args.command == "sparql"
        assert args.sparql_command == "query"
        assert args.sparql_query == "SELECT * WHERE { ?s ?p ?o }"
        assert args.timeout == 30
        assert args.format == "table"

    def test_sparql_query_with_options(self):
        args = parse_args([
            "sparql", "query", "SELECT * WHERE { ?s ?p ?o }",
            "--endpoint-url", "http://localhost:3030/sparql",
            "--timeout", "60",
            "--format", "json",
            "--user", "testuser",
            "--password", "testpass"
        ])
        assert args.endpoint_url == "http://localhost:3030/sparql"
        assert args.timeout == 60
        assert args.format == "json"
        assert args.user == "testuser"
        assert args.password == "testpass"

    def test_sparql_load_file_command(self):
        args = parse_args(["sparql", "load-file", "data.ttl"])
        assert args.command == "sparql"
        assert args.sparql_command == "load-file"
        assert args.file_path == "data.ttl"
        assert args.rdf_format == "turtle"

    def test_sparql_load_file_with_options(self):
        args = parse_args([
            "sparql", "load-file", "data.ttl",
            "--graph", "http://example.org/graph",
            "--endpoint-url", "http://localhost:3030/sparql",
            "--rdf-format", "n3"
        ])
        assert args.graph == "http://example.org/graph"
        assert args.endpoint_url == "http://localhost:3030/sparql"
        assert args.rdf_format == "n3"

    def test_process_and_load_command_minimal(self):
        args = parse_args(["process-and-load"])
        assert args.command == "process-and-load"
        assert args.knowledge_base_path is None
        assert args.pattern == "**/*.md"
        assert args.cleanup is False

    def test_process_and_load_command_with_path(self):
        args = parse_args(["process-and-load", "/path/to/kb"])
        assert args.command == "process-and-load"
        assert args.knowledge_base_path == "/path/to/kb"

    def test_process_and_load_command_with_options(self):
        args = parse_args([
            "process-and-load", "/path/to/kb",
            "--pattern", "*.md",
            "--graph", "http://example.org/graph",
            "--endpoint-url", "http://localhost:3030/sparql",
            "--cleanup",
            "--rdf-output-dir", "/tmp/rdf",
            "--user", "admin",
            "--password", "secret"
        ])
        assert args.knowledge_base_path == "/path/to/kb"
        assert args.pattern == "*.md"
        assert args.graph == "http://example.org/graph"
        assert args.endpoint_url == "http://localhost:3030/sparql"
        assert args.cleanup is True
        assert args.rdf_output_dir == "/tmp/rdf"
        assert args.user == "admin"
        assert args.password == "secret"

    def test_global_options(self):
        args = parse_args([
            "--config", "/path/to/config.yaml",
            "--knowledge-base", "/path/to/kb",
            "--metadata-store", "/path/to/metadata",
            "--log-level", "DEBUG",
            "--log-file", "/tmp/app.log",
            "--log-format", "json",
            "process"
        ])
        assert args.config == "/path/to/config.yaml"
        assert args.knowledge_base == "/path/to/kb"
        assert args.metadata_store == "/path/to/metadata"
        assert args.log_level == "DEBUG"
        assert args.log_file == "/tmp/app.log"
        assert args.log_format == "json"

    def test_missing_command_fails(self):
        with pytest.raises(SystemExit):
            parse_args([])

    def test_invalid_log_level_fails(self):
        with pytest.raises(SystemExit):
            parse_args(["--log-level", "INVALID", "process"])

    def test_invalid_query_type_fails(self):
        with pytest.raises(SystemExit):
            parse_args(["query", "test", "--type", "invalid"])

    def test_invalid_format_fails(self):
        with pytest.raises(SystemExit):
            parse_args(["sparql", "query", "SELECT * WHERE { ?s ?p ?o }", "--format", "invalid"])


class TestMain:
    """Test main function."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock KnowledgeBaseAPI."""
        api = Mock(spec=KnowledgeBaseAPI)
        api.config = Mock(spec=Config)
        api.config.knowledge_base_path = "/test/kb"
        api.config.metadata_store_path = "/test/.kbp/metadata/knowledgebase.db"
        return api

    @patch('knowledgebase_processor.cli.main.setup_logging')
    @patch('knowledgebase_processor.cli.main.load_config')
    @patch('knowledgebase_processor.cli.main.KnowledgeBaseAPI')
    @patch('knowledgebase_processor.cli.main.handle_process')
    def test_main_process_command_success(self, mock_handle_process, mock_api_class, mock_load_config, mock_setup_logging, mock_api):
        """Test main function with process command."""
        mock_load_config.return_value = mock_api.config
        mock_api_class.return_value = mock_api
        mock_handle_process.return_value = 0

        result = main(["process"])

        assert result == 0
        mock_setup_logging.assert_called_once()
        mock_load_config.assert_called_once_with(None)
        mock_api_class.assert_called_once_with(mock_api.config)
        # Check that handle_process was called with correct arguments
        mock_handle_process.assert_called_once()
        call_args = mock_handle_process.call_args
        assert call_args[0][0] == mock_api  # First argument is the API
        assert isinstance(call_args[0][1], argparse.Namespace)  # Second is Namespace
        assert call_args[0][1].command == "process"

    @patch('knowledgebase_processor.cli.main.setup_logging')
    @patch('knowledgebase_processor.cli.main.load_config')
    @patch('knowledgebase_processor.cli.main.KnowledgeBaseAPI')
    @patch('knowledgebase_processor.cli.main.handle_query')
    def test_main_query_command_success(self, mock_handle_query, mock_api_class, mock_load_config, mock_setup_logging, mock_api):
        """Test main function with query command."""
        mock_load_config.return_value = mock_api.config
        mock_api_class.return_value = mock_api
        mock_handle_query.return_value = 0

        result = main(["query", "test search"])

        assert result == 0
        mock_handle_query.assert_called_once()

    @patch('knowledgebase_processor.cli.main.setup_logging')
    @patch('knowledgebase_processor.cli.main.load_config')
    @patch('knowledgebase_processor.cli.main.KnowledgeBaseAPI')
    @patch('knowledgebase_processor.cli.main.handle_sparql')
    def test_main_sparql_command_success(self, mock_handle_sparql, mock_api_class, mock_load_config, mock_setup_logging, mock_api):
        """Test main function with sparql command."""
        mock_load_config.return_value = mock_api.config
        mock_api_class.return_value = mock_api
        mock_handle_sparql.return_value = 0

        result = main(["sparql", "query", "SELECT * WHERE { ?s ?p ?o }"])

        assert result == 0
        mock_handle_sparql.assert_called_once()

    @patch('knowledgebase_processor.cli.main.setup_logging')
    @patch('knowledgebase_processor.cli.main.load_config')
    @patch('knowledgebase_processor.cli.main.KnowledgeBaseAPI')
    @patch('knowledgebase_processor.cli.main.handle_process_and_load')
    def test_main_process_and_load_command_success(self, mock_handle_pal, mock_api_class, mock_load_config, mock_setup_logging, mock_api):
        """Test main function with process-and-load command."""
        mock_load_config.return_value = mock_api.config
        mock_api_class.return_value = mock_api
        mock_handle_pal.return_value = 0

        result = main(["process-and-load"])

        assert result == 0
        mock_handle_pal.assert_called_once()

    @patch('knowledgebase_processor.cli.main.setup_logging')
    @patch('knowledgebase_processor.cli.main.load_config')
    @patch('knowledgebase_processor.cli.main.KnowledgeBaseAPI')
    def test_main_api_initialization_failure(self, mock_api_class, mock_load_config, mock_setup_logging):
        """Test main function when API initialization fails."""
        mock_load_config.return_value = Mock(spec=Config)
        mock_api_class.side_effect = Exception("API init failed")

        result = main(["process"])

        assert result == 1
        mock_api_class.assert_called_once()

    @patch('knowledgebase_processor.cli.main.setup_logging')
    @patch('knowledgebase_processor.cli.main.load_config')
    @patch('knowledgebase_processor.cli.main.KnowledgeBaseAPI')
    def test_main_unknown_command(self, mock_api_class, mock_load_config, mock_setup_logging, mock_api):
        """Test main function with unknown command."""
        mock_load_config.return_value = mock_api.config
        mock_api_class.return_value = mock_api

        # This should not happen in practice due to argparse validation
        # but test the handler logic directly
        with patch('knowledgebase_processor.cli.main.parse_args') as mock_parse:
            # Mock the parsed args with all required attributes
            mock_parsed_args = Mock()
            mock_parsed_args.command = "unknown"
            mock_parsed_args.config = None
            mock_parsed_args.knowledge_base = None
            mock_parsed_args.metadata_store = None
            mock_parsed_args.log_level = "INFO"
            mock_parsed_args.log_file = None
            mock_parsed_args.log_format = "text"
            mock_parse.return_value = mock_parsed_args
            
            result = main([])

        assert result == 1

    @patch('knowledgebase_processor.cli.main.setup_logging')
    @patch('knowledgebase_processor.cli.main.load_config')
    @patch('knowledgebase_processor.cli.main.KnowledgeBaseAPI')
    def test_main_config_override_knowledge_base(self, mock_api_class, mock_load_config, mock_setup_logging, mock_api):
        """Test that command line knowledge base path overrides config."""
        mock_config = Mock(spec=Config)
        mock_config.knowledge_base_path = "/config/kb"
        mock_load_config.return_value = mock_config
        mock_api_class.return_value = mock_api

        with patch('knowledgebase_processor.cli.main.handle_process') as mock_handle:
            mock_handle.return_value = 0
            main(["--knowledge-base", "/cli/kb", "process"])

        assert mock_config.knowledge_base_path == "/cli/kb"

    @patch('knowledgebase_processor.cli.main.setup_logging')
    @patch('knowledgebase_processor.cli.main.load_config')
    @patch('knowledgebase_processor.cli.main.KnowledgeBaseAPI')
    @patch('pathlib.Path.cwd')
    def test_main_default_knowledge_base_path(self, mock_cwd, mock_api_class, mock_load_config, mock_setup_logging, mock_api):
        """Test that knowledge base path defaults to current directory."""
        mock_cwd.return_value = Path("/current/dir")
        mock_config = Mock(spec=Config)
        # Simulate no knowledge_base_path in config
        delattr(mock_config, 'knowledge_base_path')
        mock_load_config.return_value = mock_config
        mock_api_class.return_value = mock_api

        with patch('knowledgebase_processor.cli.main.handle_process') as mock_handle:
            mock_handle.return_value = 0
            main(["process"])

        assert mock_config.knowledge_base_path == "/current/dir"

    @patch('knowledgebase_processor.cli.main.setup_logging')
    @patch('knowledgebase_processor.cli.main.load_config')
    @patch('knowledgebase_processor.cli.main.KnowledgeBaseAPI')
    @patch('pathlib.Path.home')
    def test_main_metadata_store_path_handling(self, mock_home, mock_api_class, mock_load_config, mock_setup_logging, mock_api):
        """Test metadata store path handling with various scenarios."""
        mock_home.return_value = Path("/home/user")
        mock_config = Mock(spec=Config)
        mock_config.knowledge_base_path = "/test/kb"
        mock_load_config.return_value = mock_config
        mock_api_class.return_value = mock_api

        with patch('knowledgebase_processor.cli.main.handle_process') as mock_handle:
            mock_handle.return_value = 0
            
            # Test CLI override
            main(["--metadata-store", "/cli/metadata", "process"])
            assert mock_config.metadata_store_path == "/cli/metadata/knowledgebase.db"

            # Test config value
            mock_config.metadata_store_path = "/config/metadata"
            main(["process"])
            assert mock_config.metadata_store_path == "/config/metadata/knowledgebase.db"

            # Test default value
            delattr(mock_config, 'metadata_store_path')
            main(["process"])
            assert mock_config.metadata_store_path == "/home/user/.kbp/metadata/knowledgebase.db"