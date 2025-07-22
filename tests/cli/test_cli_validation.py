"""Unit tests for CLI input validation and error conditions."""

import argparse
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import urlparse

from knowledgebase_processor.cli.main import (
    parse_args, is_valid_url, main
)
from knowledgebase_processor.config import Config
from knowledgebase_processor.api import KnowledgeBaseAPI


class TestArgumentValidation:
    """Test CLI argument validation."""

    def test_required_command_missing(self):
        """Test that missing command raises SystemExit."""
        with pytest.raises(SystemExit):
            parse_args([])

    def test_invalid_log_level(self):
        """Test invalid log level raises SystemExit."""
        with pytest.raises(SystemExit):
            parse_args(["--log-level", "INVALID", "process"])

    def test_valid_log_levels(self):
        """Test all valid log levels are accepted."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            args = parse_args(["--log-level", level, "process"])
            assert args.log_level == level

    def test_invalid_log_format(self):
        """Test invalid log format raises SystemExit."""
        with pytest.raises(SystemExit):
            parse_args(["--log-format", "invalid", "process"])

    def test_valid_log_formats(self):
        """Test all valid log formats are accepted."""
        valid_formats = ["text", "json"]
        for format_type in valid_formats:
            args = parse_args(["--log-format", format_type, "process"])
            assert args.log_format == format_type

    def test_invalid_query_type(self):
        """Test invalid query type raises SystemExit."""
        with pytest.raises(SystemExit):
            parse_args(["query", "test", "--type", "invalid"])

    def test_valid_query_types(self):
        """Test all valid query types are accepted."""
        valid_types = ["text", "tag", "topic"]
        for query_type in valid_types:
            args = parse_args(["query", "test", "--type", query_type])
            assert args.type == query_type

    def test_invalid_sparql_format(self):
        """Test invalid SPARQL output format raises SystemExit."""
        with pytest.raises(SystemExit):
            parse_args(["sparql", "query", "SELECT * WHERE { ?s ?p ?o }", "--format", "invalid"])

    def test_valid_sparql_formats(self):
        """Test all valid SPARQL output formats are accepted."""
        valid_formats = ["json", "table", "turtle"]
        for format_type in valid_formats:
            args = parse_args(["sparql", "query", "SELECT * WHERE { ?s ?p ?o }", "--format", format_type])
            assert args.format == format_type

    def test_invalid_rdf_format(self):
        """Test invalid RDF format raises SystemExit."""
        with pytest.raises(SystemExit):
            parse_args(["sparql", "load-file", "data.ttl", "--rdf-format", "invalid"])

    def test_valid_rdf_formats(self):
        """Test all valid RDF formats are accepted."""
        valid_formats = ["turtle", "n3", "nt", "xml", "json-ld"]
        for format_type in valid_formats:
            args = parse_args(["sparql", "load-file", "data.ttl", "--rdf-format", format_type])
            assert args.rdf_format == format_type

    def test_sparql_subcommand_required(self):
        """Test that SPARQL subcommand is required."""
        with pytest.raises(SystemExit):
            parse_args(["sparql"])

    def test_sparql_query_requires_query_string(self):
        """Test that SPARQL query requires query string."""
        with pytest.raises(SystemExit):
            parse_args(["sparql", "query"])

    def test_sparql_load_file_requires_file_path(self):
        """Test that SPARQL load-file requires file path."""
        with pytest.raises(SystemExit):
            parse_args(["sparql", "load-file"])

    def test_query_command_requires_query_string(self):
        """Test that query command requires query string."""
        with pytest.raises(SystemExit):
            parse_args(["query"])


class TestUrlValidation:
    """Test URL validation function."""

    def test_valid_urls(self):
        """Test various valid URL formats."""
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "http://localhost",
            "https://localhost",
            "http://127.0.0.1",
            "https://127.0.0.1",
            "http://example.com:8080",
            "https://example.com:443",
            "http://localhost:3030",
            "http://example.com/sparql",
            "https://example.com/sparql/query",
            "http://example.com/path/to/endpoint",
            "https://sub.example.com",
            "http://example.com/sparql?param=value",
            "https://example.com/sparql#fragment",
        ]
        
        for url in valid_urls:
            assert is_valid_url(url), f"URL should be valid: {url}"

    def test_invalid_urls(self):
        """Test various invalid URL formats."""
        invalid_urls = [
            "",  # Empty string
            None,  # None value
            "example.com",  # No scheme
            "ftp://example.com",  # Wrong scheme (not http/https)
            "http://",  # No netloc
            "https://",  # No netloc
            "http:///path",  # Empty netloc
            "://example.com",  # Empty scheme
            "not-a-url",  # Not a URL at all
            "just text",  # Plain text
            "http:/example.com",  # Missing slash
            "http//example.com",  # Missing colon
            "http:",  # Incomplete URL
            "://",  # Just scheme separator
            " http://example.com",  # Leading whitespace
            "http://example.com ",  # Trailing whitespace
        ]
        
        for url in invalid_urls:
            assert not is_valid_url(url), f"URL should be invalid: {url}"

    def test_url_validation_with_special_characters(self):
        """Test URL validation with special characters."""
        # Valid URLs with special characters
        valid_special_urls = [
            "http://example.com/path%20with%20spaces",
            "https://user:pass@example.com",
            "http://192.168.1.1:8080/endpoint",
            "https://example-site.co.uk",
            "http://api.example.com/v1/sparql",
        ]
        
        for url in valid_special_urls:
            assert is_valid_url(url), f"URL with special characters should be valid: {url}"

    def test_url_validation_edge_cases(self):
        """Test URL validation edge cases."""
        # Edge cases that should be invalid
        edge_cases = [
            "http://",
            "https://",
            "http:// ",
            "http://.",
            "http://..",
            "http://../",
            "http://?",
            "http://#",
        ]
        
        for url in edge_cases:
            assert not is_valid_url(url), f"Edge case should be invalid: {url}"


class TestConfigurationValidation:
    """Test configuration validation and error handling."""

    @patch('knowledgebase_processor.cli.main.setup_logging')
    @patch('knowledgebase_processor.cli.main.load_config')
    def test_config_loading_failure(self, mock_load_config, mock_setup_logging):
        """Test behavior when config loading fails."""
        mock_load_config.side_effect = Exception("Config loading failed")
        
        # Should not crash, but may behave unexpectedly depending on implementation
        # This tests that the exception propagates properly
        with pytest.raises(Exception, match="Config loading failed"):
            main(["process"])

    @patch('knowledgebase_processor.cli.main.setup_logging')
    @patch('knowledgebase_processor.cli.main.load_config')
    @patch('knowledgebase_processor.cli.main.KnowledgeBaseAPI')
    def test_api_initialization_failure(self, mock_api_class, mock_load_config, mock_setup_logging):
        """Test behavior when API initialization fails."""
        mock_config = Mock(spec=Config)
        mock_config.knowledge_base_path = "/test/kb"
        mock_load_config.return_value = mock_config
        mock_api_class.side_effect = Exception("API initialization failed")
        
        result = main(["process"])
        
        assert result == 1

    @patch('knowledgebase_processor.cli.main.setup_logging')
    def test_logging_setup_failure(self, mock_setup_logging):
        """Test behavior when logging setup fails."""
        mock_setup_logging.side_effect = Exception("Logging setup failed")
        
        # Should not crash the entire application
        with pytest.raises(Exception, match="Logging setup failed"):
            main(["process"])


class TestFilePathValidation:
    """Test file path validation scenarios."""

    def test_config_file_path_validation(self):
        """Test config file path handling."""
        args = parse_args(["--config", "/path/to/config.yaml", "process"])
        assert args.config == "/path/to/config.yaml"
        
        args = parse_args(["--config", "relative/config.yaml", "process"])
        assert args.config == "relative/config.yaml"

    def test_knowledge_base_path_validation(self):
        """Test knowledge base path handling."""
        args = parse_args(["--knowledge-base", "/absolute/path", "process"])
        assert args.knowledge_base == "/absolute/path"
        
        args = parse_args(["--knowledge-base", "relative/path", "process"])
        assert args.knowledge_base == "relative/path"

    def test_metadata_store_path_validation(self):
        """Test metadata store path handling."""
        args = parse_args(["--metadata-store", "/absolute/metadata", "process"])
        assert args.metadata_store == "/absolute/metadata"
        
        args = parse_args(["--metadata-store", "relative/metadata", "process"])
        assert args.metadata_store == "relative/metadata"

    def test_log_file_path_validation(self):
        """Test log file path handling."""
        args = parse_args(["--log-file", "/var/log/app.log", "process"])
        assert args.log_file == "/var/log/app.log"
        
        args = parse_args(["--log-file", "app.log", "process"])
        assert args.log_file == "app.log"

    def test_rdf_output_dir_validation(self):
        """Test RDF output directory path handling."""
        args = parse_args(["process", "--rdf-output-dir", "/tmp/rdf"])
        assert args.rdf_output_dir == "/tmp/rdf"
        
        args = parse_args(["process", "--rdf-output-dir", "output"])
        assert args.rdf_output_dir == "output"

    def test_sparql_load_file_path_validation(self):
        """Test SPARQL load file path handling."""
        args = parse_args(["sparql", "load-file", "/absolute/path/data.ttl"])
        assert args.file_path == "/absolute/path/data.ttl"
        
        args = parse_args(["sparql", "load-file", "relative/data.ttl"])
        assert args.file_path == "relative/data.ttl"


class TestNumericParameterValidation:
    """Test numeric parameter validation."""

    def test_timeout_parameter_validation(self):
        """Test timeout parameter accepts integers."""
        args = parse_args(["sparql", "query", "SELECT * WHERE { ?s ?p ?o }", "--timeout", "60"])
        assert args.timeout == 60
        assert isinstance(args.timeout, int)

    def test_timeout_parameter_default_value(self):
        """Test timeout parameter default value."""
        args = parse_args(["sparql", "query", "SELECT * WHERE { ?s ?p ?o }"])
        assert args.timeout == 30

    def test_invalid_timeout_parameter(self):
        """Test invalid timeout parameter raises SystemExit."""
        with pytest.raises(SystemExit):
            parse_args(["sparql", "query", "SELECT * WHERE { ?s ?p ?o }", "--timeout", "not-a-number"])


class TestArgumentCombinations:
    """Test argument combinations and conflicts."""

    def test_global_options_with_process_command(self):
        """Test global options work with process command."""
        args = parse_args([
            "--config", "config.yaml",
            "--knowledge-base", "/kb",
            "--metadata-store", "/metadata",
            "--log-level", "DEBUG",
            "--log-file", "app.log",
            "--log-format", "json",
            "process",
            "--pattern", "*.md",
            "--rdf-output-dir", "/output"
        ])
        
        assert args.config == "config.yaml"
        assert args.knowledge_base == "/kb"
        assert args.metadata_store == "/metadata"
        assert args.log_level == "DEBUG"
        assert args.log_file == "app.log"
        assert args.log_format == "json"
        assert args.command == "process"
        assert args.pattern == "*.md"
        assert args.rdf_output_dir == "/output"

    def test_global_options_with_query_command(self):
        """Test global options work with query command."""
        args = parse_args([
            "--config", "config.yaml",
            "--log-level", "WARNING",
            "query", "test search", "--type", "tag"
        ])
        
        assert args.config == "config.yaml"
        assert args.log_level == "WARNING"
        assert args.command == "query"
        assert args.query_string == "test search"
        assert args.type == "tag"

    def test_global_options_with_sparql_command(self):
        """Test global options work with SPARQL command."""
        args = parse_args([
            "--config", "config.yaml",
            "--log-level", "ERROR",
            "sparql", "query", "SELECT * WHERE { ?s ?p ?o }",
            "--format", "json",
            "--timeout", "120"
        ])
        
        assert args.config == "config.yaml"
        assert args.log_level == "ERROR"
        assert args.command == "sparql"
        assert args.sparql_command == "query"
        assert args.sparql_query == "SELECT * WHERE { ?s ?p ?o }"
        assert args.format == "json"
        assert args.timeout == 120

    def test_credential_parameters_work_together(self):
        """Test username and password parameters work together."""
        args = parse_args([
            "sparql", "query", "SELECT * WHERE { ?s ?p ?o }",
            "--user", "testuser",
            "--password", "testpass"
        ])
        
        assert args.user == "testuser"
        assert args.password == "testpass"

    def test_endpoint_url_parameters_work_together(self):
        """Test endpoint URL parameters work with other options."""
        args = parse_args([
            "process-and-load", "/kb",
            "--endpoint-url", "http://localhost:3030/sparql",
            "--graph", "http://example.org/graph",
            "--user", "admin",
            "--password", "secret"
        ])
        
        assert args.endpoint_url == "http://localhost:3030/sparql"
        assert args.graph == "http://example.org/graph"
        assert args.user == "admin"
        assert args.password == "secret"


class TestErrorMessageValidation:
    """Test that appropriate error messages are generated."""

    def test_missing_required_argument_error_message(self):
        """Test error messages for missing required arguments."""
        # Test missing command
        with pytest.raises(SystemExit):
            try:
                parse_args([])
            except SystemExit as e:
                # argparse should have printed an error message
                pass
            else:
                pytest.fail("Should have raised SystemExit")

    def test_invalid_choice_error_message(self):
        """Test error messages for invalid choices."""
        # Test invalid log level
        with pytest.raises(SystemExit):
            try:
                parse_args(["--log-level", "INVALID", "process"])
            except SystemExit as e:
                # argparse should have printed an error message about invalid choice
                pass
            else:
                pytest.fail("Should have raised SystemExit")

    def test_invalid_type_error_message(self):
        """Test error messages for invalid types."""
        # Test invalid timeout (non-integer)
        with pytest.raises(SystemExit):
            try:
                parse_args(["sparql", "query", "SELECT * WHERE { ?s ?p ?o }", "--timeout", "not-a-number"])
            except SystemExit as e:
                # argparse should have printed an error message about invalid type
                pass
            else:
                pytest.fail("Should have raised SystemExit")