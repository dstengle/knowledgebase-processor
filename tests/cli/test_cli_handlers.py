"""Unit tests for CLI command handlers."""

import argparse
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import pytest

from knowledgebase_processor.cli.main import (
    handle_process, handle_query, handle_sparql, 
    handle_sparql_query, handle_sparql_load, handle_process_and_load
)
from knowledgebase_processor.api import KnowledgeBaseAPI
from knowledgebase_processor.config import Config
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException


class TestHandleProcess:
    """Test handle_process function."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock KnowledgeBaseAPI."""
        api = Mock(spec=KnowledgeBaseAPI)
        api.process_documents.return_value = 0
        return api

    def test_handle_process_success(self, mock_api):
        """Test successful process command."""
        args = argparse.Namespace(
            pattern="**/*.md",
            rdf_output_dir=None
        )
        
        result = handle_process(mock_api, args)
        
        assert result == 0
        mock_api.process_documents.assert_called_once_with(
            pattern="**/*.md",
            rdf_output_dir=None
        )

    def test_handle_process_with_rdf_output(self, mock_api):
        """Test process command with RDF output directory."""
        args = argparse.Namespace(
            pattern="*.txt",
            rdf_output_dir="/tmp/rdf"
        )
        
        result = handle_process(mock_api, args)
        
        assert result == 0
        mock_api.process_documents.assert_called_once_with(
            pattern="*.txt",
            rdf_output_dir=Path("/tmp/rdf")
        )

    def test_handle_process_api_failure(self, mock_api):
        """Test process command when API returns failure."""
        mock_api.process_documents.return_value = 1
        args = argparse.Namespace(pattern="**/*.md", rdf_output_dir=None)
        
        result = handle_process(mock_api, args)
        
        assert result == 1

    def test_handle_process_exception(self, mock_api):
        """Test process command when exception occurs."""
        mock_api.process_documents.side_effect = Exception("Processing failed")
        args = argparse.Namespace(pattern="**/*.md", rdf_output_dir=None)
        
        result = handle_process(mock_api, args)
        
        assert result == 1


class TestHandleQuery:
    """Test handle_query function."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock KnowledgeBaseAPI."""
        api = Mock(spec=KnowledgeBaseAPI)
        return api

    def test_handle_query_success_with_results(self, mock_api, capsys):
        """Test successful query with results."""
        mock_api.query.return_value = ["Result 1", "Result 2", "Result 3"]
        args = argparse.Namespace(
            query_string="test query",
            type="text"
        )
        
        result = handle_query(mock_api, args)
        
        assert result == 0
        mock_api.query.assert_called_once_with("test query", "text")
        
        captured = capsys.readouterr()
        assert "Result 1" in captured.out
        assert "Result 2" in captured.out
        assert "Result 3" in captured.out

    def test_handle_query_success_no_results(self, mock_api, capsys):
        """Test successful query with no results."""
        mock_api.query.return_value = []
        args = argparse.Namespace(
            query_string="test query",
            type="tag"
        )
        
        result = handle_query(mock_api, args)
        
        assert result == 0
        mock_api.query.assert_called_once_with("test query", "tag")
        
        captured = capsys.readouterr()
        assert "No results found." in captured.out

    def test_handle_query_exception(self, mock_api):
        """Test query command when exception occurs."""
        mock_api.query.side_effect = Exception("Query failed")
        args = argparse.Namespace(
            query_string="test query",
            type="topic"
        )
        
        result = handle_query(mock_api, args)
        
        assert result == 1


class TestHandleSparqlQuery:
    """Test handle_sparql_query function."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock KnowledgeBaseAPI."""
        api = Mock(spec=KnowledgeBaseAPI)
        return api

    def test_handle_sparql_query_json_format(self, mock_api, capsys):
        """Test SPARQL query with JSON format."""
        mock_api.sparql_query.return_value = [
            {"subject": "http://example.org/1", "predicate": "http://example.org/title", "object": "Test 1"},
            {"subject": "http://example.org/2", "predicate": "http://example.org/title", "object": "Test 2"}
        ]
        args = argparse.Namespace(
            sparql_query="SELECT * WHERE { ?s ?p ?o }",
            endpoint_url="http://localhost:3030/sparql",
            timeout=30,
            format="json"
        )
        
        result = handle_sparql_query(mock_api, args)
        
        assert result == 0
        mock_api.sparql_query.assert_called_once_with(
            query="SELECT * WHERE { ?s ?p ?o }",
            endpoint_url="http://localhost:3030/sparql",
            timeout=30,
            format="json"
        )
        
        captured = capsys.readouterr()
        # Verify JSON output is properly formatted
        json.loads(captured.out)  # Should not raise exception

    def test_handle_sparql_query_table_format(self, mock_api, capsys):
        """Test SPARQL query with table format."""
        mock_api.sparql_query.return_value = [
            {"s": "subject1", "p": "predicate1", "o": "object1"},
            {"s": "subject2", "p": "predicate2", "o": "object2"}
        ]
        args = argparse.Namespace(
            sparql_query="SELECT * WHERE { ?s ?p ?o }",
            endpoint_url=None,
            timeout=60,
            format="table"
        )
        
        result = handle_sparql_query(mock_api, args)
        
        assert result == 0
        
        captured = capsys.readouterr()
        assert "s | p | o" in captured.out
        assert "subject1 | predicate1 | object1" in captured.out
        assert "subject2 | predicate2 | object2" in captured.out

    def test_handle_sparql_query_table_format_boolean_result(self, mock_api, capsys):
        """Test SPARQL query with table format returning boolean."""
        mock_api.sparql_query.return_value = True
        args = argparse.Namespace(
            sparql_query="ASK WHERE { ?s ?p ?o }",
            endpoint_url=None,
            timeout=30,
            format="table"
        )
        
        result = handle_sparql_query(mock_api, args)
        
        assert result == 0
        
        captured = capsys.readouterr()
        assert "True" in captured.out

    def test_handle_sparql_query_table_format_no_results(self, mock_api, capsys):
        """Test SPARQL query with table format returning no results."""
        mock_api.sparql_query.return_value = []
        args = argparse.Namespace(
            sparql_query="SELECT * WHERE { ?s ?p ?o }",
            endpoint_url=None,
            timeout=30,
            format="table"
        )
        
        result = handle_sparql_query(mock_api, args)
        
        assert result == 0
        
        captured = capsys.readouterr()
        assert "No results found." in captured.out

    def test_handle_sparql_query_turtle_format(self, mock_api, capsys):
        """Test SPARQL query with turtle format."""
        turtle_data = "@prefix ex: <http://example.org/> .\nex:subject ex:predicate ex:object ."
        mock_api.sparql_query.return_value = turtle_data
        args = argparse.Namespace(
            sparql_query="CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }",
            endpoint_url=None,
            timeout=30,
            format="turtle"
        )
        
        result = handle_sparql_query(mock_api, args)
        
        assert result == 0
        
        captured = capsys.readouterr()
        assert turtle_data in captured.out

    def test_handle_sparql_query_exception(self, mock_api):
        """Test SPARQL query when exception occurs."""
        mock_api.sparql_query.side_effect = Exception("SPARQL query failed")
        args = argparse.Namespace(
            sparql_query="SELECT * WHERE { ?s ?p ?o }",
            endpoint_url=None,
            timeout=30,
            format="json"
        )
        
        result = handle_sparql_query(mock_api, args)
        
        assert result == 1


class TestHandleSparqlLoad:
    """Test handle_sparql_load function."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock KnowledgeBaseAPI."""
        api = Mock(spec=KnowledgeBaseAPI)
        return api

    def test_handle_sparql_load_success(self, mock_api):
        """Test successful SPARQL load."""
        args = argparse.Namespace(
            file_path="/path/to/data.ttl",
            graph="http://example.org/graph",
            endpoint_url="http://localhost:3030/sparql",
            user="admin",
            password="secret",
            rdf_format="turtle"
        )
        
        result = handle_sparql_load(mock_api, args)
        
        assert result == 0
        mock_api.sparql_load.assert_called_once_with(
            file_path=Path("/path/to/data.ttl"),
            graph_uri="http://example.org/graph",
            endpoint_url="http://localhost:3030/sparql",
            username="admin",
            password="secret",
            rdf_format="turtle"
        )

    def test_handle_sparql_load_minimal_args(self, mock_api):
        """Test SPARQL load with minimal arguments."""
        args = argparse.Namespace(
            file_path="data.ttl",
            graph=None,
            endpoint_url=None,
            user=None,
            password=None,
            rdf_format="turtle"
        )
        
        result = handle_sparql_load(mock_api, args)
        
        assert result == 0
        mock_api.sparql_load.assert_called_once_with(
            file_path=Path("data.ttl"),
            graph_uri=None,
            endpoint_url=None,
            username=None,
            password=None,
            rdf_format="turtle"
        )

    def test_handle_sparql_load_exception(self, mock_api):
        """Test SPARQL load when exception occurs."""
        mock_api.sparql_load.side_effect = Exception("Load failed")
        args = argparse.Namespace(
            file_path="data.ttl",
            graph=None,
            endpoint_url=None,
            user=None,
            password=None,
            rdf_format="turtle"
        )
        
        result = handle_sparql_load(mock_api, args)
        
        assert result == 1


class TestHandleSparql:
    """Test handle_sparql routing function."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock KnowledgeBaseAPI."""
        return Mock(spec=KnowledgeBaseAPI)

    @patch('knowledgebase_processor.cli.main.handle_sparql_query')
    def test_handle_sparql_query_command(self, mock_handle_sparql_query, mock_api):
        """Test routing to SPARQL query handler."""
        mock_handle_sparql_query.return_value = 0
        args = argparse.Namespace(sparql_command="query")
        
        result = handle_sparql(mock_api, args)
        
        assert result == 0
        mock_handle_sparql_query.assert_called_once_with(mock_api, args)

    @patch('knowledgebase_processor.cli.main.handle_sparql_load')
    def test_handle_sparql_load_command(self, mock_handle_sparql_load, mock_api):
        """Test routing to SPARQL load handler."""
        mock_handle_sparql_load.return_value = 0
        args = argparse.Namespace(sparql_command="load-file")
        
        result = handle_sparql(mock_api, args)
        
        assert result == 0
        mock_handle_sparql_load.assert_called_once_with(mock_api, args)

    def test_handle_sparql_unknown_command(self, mock_api):
        """Test routing with unknown SPARQL command."""
        args = argparse.Namespace(sparql_command="unknown")
        
        result = handle_sparql(mock_api, args)
        
        assert result == 1


class TestHandleProcessAndLoad:
    """Test handle_process_and_load function."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock KnowledgeBaseAPI."""
        api = Mock(spec=KnowledgeBaseAPI)
        api.config = Mock(spec=Config)
        api.config.knowledge_base_path = "/test/kb"
        api.config.sparql_endpoint_url = "http://localhost:3030/sparql"
        api.processing_service = Mock()
        api.processing_service.process_and_load.return_value = 0
        return api

    @patch('knowledgebase_processor.cli.main.is_valid_url')
    @patch('pathlib.Path.is_dir')
    def test_handle_process_and_load_success(self, mock_is_dir, mock_is_valid_url, mock_api):
        """Test successful process-and-load command."""
        mock_is_dir.return_value = True
        mock_is_valid_url.return_value = True
        
        args = argparse.Namespace(
            knowledge_base_path="/custom/kb",
            pattern="**/*.md",
            endpoint_url="http://localhost:3030/sparql",
            graph="http://example.org/graph",
            cleanup=True,
            rdf_output_dir="/tmp/rdf",
            user="admin",
            password="secret"
        )
        
        result = handle_process_and_load(mock_api, args)
        
        assert result == 0
        mock_api.processing_service.process_and_load.assert_called_once_with(
            pattern="**/*.md",
            knowledge_base_path=Path("/custom/kb"),
            rdf_output_dir=Path("/tmp/rdf"),
            graph_uri="http://example.org/graph",
            endpoint_url="http://localhost:3030/sparql",
            cleanup=True,
            username="admin",
            password="secret"
        )

    @patch('knowledgebase_processor.cli.main.is_valid_url')
    @patch('pathlib.Path.is_dir')
    def test_handle_process_and_load_use_api_config_kb_path(self, mock_is_dir, mock_is_valid_url, mock_api):
        """Test process-and-load using API config knowledge base path."""
        mock_is_dir.return_value = True
        mock_is_valid_url.return_value = True
        
        args = argparse.Namespace(
            knowledge_base_path=None,  # Use API config
            pattern="**/*.md",
            endpoint_url=None,  # Use API config
            graph=None,
            cleanup=False,
            rdf_output_dir=None,
            user=None,
            password=None
        )
        
        result = handle_process_and_load(mock_api, args)
        
        assert result == 0
        mock_api.processing_service.process_and_load.assert_called_once_with(
            pattern="**/*.md",
            knowledge_base_path=Path("/test/kb"),
            rdf_output_dir=None,
            graph_uri=None,
            endpoint_url="http://localhost:3030/sparql",
            cleanup=False,
            username=None,
            password=None
        )

    @patch('pathlib.Path.is_dir')
    def test_handle_process_and_load_invalid_kb_path(self, mock_is_dir, mock_api):
        """Test process-and-load with invalid knowledge base path."""
        mock_is_dir.return_value = False
        
        args = argparse.Namespace(
            knowledge_base_path="/invalid/path",
            endpoint_url="http://localhost:3030/sparql"
        )
        
        result = handle_process_and_load(mock_api, args)
        
        assert result == 1

    @patch('knowledgebase_processor.cli.main.is_valid_url')
    @patch('pathlib.Path.is_dir')
    def test_handle_process_and_load_no_endpoint_url(self, mock_is_dir, mock_is_valid_url, mock_api):
        """Test process-and-load without endpoint URL."""
        mock_is_dir.return_value = True
        mock_api.config.sparql_endpoint_url = None
        
        args = argparse.Namespace(
            knowledge_base_path="/test/kb",
            endpoint_url=None
        )
        
        result = handle_process_and_load(mock_api, args)
        
        assert result == 1

    @patch('knowledgebase_processor.cli.main.is_valid_url')
    @patch('pathlib.Path.is_dir')
    def test_handle_process_and_load_invalid_endpoint_url(self, mock_is_dir, mock_is_valid_url, mock_api):
        """Test process-and-load with invalid endpoint URL."""
        mock_is_dir.return_value = True
        mock_is_valid_url.return_value = False
        
        args = argparse.Namespace(
            knowledge_base_path="/test/kb",
            endpoint_url="invalid-url"
        )
        
        result = handle_process_and_load(mock_api, args)
        
        assert result == 1

    @patch('knowledgebase_processor.cli.main.is_valid_url')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.mkdir')
    def test_handle_process_and_load_rdf_output_dir_creation_failure(self, mock_mkdir, mock_is_dir, mock_is_valid_url, mock_api):
        """Test process-and-load when RDF output directory creation fails."""
        mock_is_dir.return_value = True
        mock_is_valid_url.return_value = True
        mock_mkdir.side_effect = OSError("Permission denied")
        
        args = argparse.Namespace(
            knowledge_base_path="/test/kb",
            endpoint_url="http://localhost:3030/sparql",
            rdf_output_dir="/no/permission/rdf"
        )
        
        result = handle_process_and_load(mock_api, args)
        
        assert result == 1

    @patch('knowledgebase_processor.cli.main.is_valid_url')
    @patch('pathlib.Path.is_dir')
    def test_handle_process_and_load_sparql_exception(self, mock_is_dir, mock_is_valid_url, mock_api):
        """Test process-and-load with SPARQL exception."""
        mock_is_dir.return_value = True
        mock_is_valid_url.return_value = True
        mock_api.processing_service.process_and_load.side_effect = SPARQLWrapperException("SPARQL error")
        
        args = argparse.Namespace(
            knowledge_base_path="/test/kb",
            endpoint_url="http://localhost:3030/sparql",
            pattern="**/*.md",
            graph=None,
            cleanup=False,
            rdf_output_dir=None,
            user=None,
            password=None
        )
        
        result = handle_process_and_load(mock_api, args)
        
        assert result == 1

    @patch('knowledgebase_processor.cli.main.is_valid_url')
    @patch('pathlib.Path.is_dir')
    def test_handle_process_and_load_file_not_found_exception(self, mock_is_dir, mock_is_valid_url, mock_api):
        """Test process-and-load with FileNotFoundError exception."""
        mock_is_dir.return_value = True
        mock_is_valid_url.return_value = True
        mock_api.processing_service.process_and_load.side_effect = FileNotFoundError("File not found")
        
        args = argparse.Namespace(
            knowledge_base_path="/test/kb",
            endpoint_url="http://localhost:3030/sparql",
            pattern="**/*.md",
            graph=None,
            cleanup=False,
            rdf_output_dir=None,
            user=None,
            password=None
        )
        
        result = handle_process_and_load(mock_api, args)
        
        assert result == 1

    @patch('knowledgebase_processor.cli.main.is_valid_url')
    @patch('pathlib.Path.is_dir')
    def test_handle_process_and_load_general_exception(self, mock_is_dir, mock_is_valid_url, mock_api):
        """Test process-and-load with general exception."""
        mock_is_dir.return_value = True
        mock_is_valid_url.return_value = True
        mock_api.processing_service.process_and_load.side_effect = Exception("Unexpected error")
        
        args = argparse.Namespace(
            knowledge_base_path="/test/kb",
            endpoint_url="http://localhost:3030/sparql",
            pattern="**/*.md",
            graph=None,
            cleanup=False,
            rdf_output_dir=None,
            user=None,
            password=None
        )
        
        result = handle_process_and_load(mock_api, args)
        
        assert result == 1

    @patch('knowledgebase_processor.cli.main.is_valid_url')
    @patch('pathlib.Path.is_dir')
    def test_handle_process_and_load_api_failure(self, mock_is_dir, mock_is_valid_url, mock_api):
        """Test process-and-load when API returns failure code."""
        mock_is_dir.return_value = True
        mock_is_valid_url.return_value = True
        mock_api.processing_service.process_and_load.return_value = 1
        
        args = argparse.Namespace(
            knowledge_base_path="/test/kb",
            endpoint_url="http://localhost:3030/sparql",
            pattern="**/*.md",
            graph=None,
            cleanup=False,
            rdf_output_dir=None,
            user=None,
            password=None
        )
        
        result = handle_process_and_load(mock_api, args)
        
        assert result == 1