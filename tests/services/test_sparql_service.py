"""Unit tests for SparqlService."""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

from rdflib import Graph
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException

from src.knowledgebase_processor.services.sparql_service import SparqlService


class TestSparqlService(unittest.TestCase):
    """Test cases for SparqlService."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = Mock()
        self.mock_config.sparql_endpoint = "http://localhost:3030/test/query"
        self.mock_config.sparql_update_endpoint = "http://localhost:3030/test/update"
        
        self.sparql_service = SparqlService(self.mock_config)

    def test_initialization_with_config(self):
        """Test SparqlService initialization with config."""
        service = SparqlService(self.mock_config)
        self.assertEqual(service.config, self.mock_config)
        self.assertIsNotNone(service.logger)

    def test_initialization_without_config(self):
        """Test SparqlService initialization without config."""
        service = SparqlService()
        self.assertIsNone(service.config)
        self.assertIsNotNone(service.logger)

    @patch('src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_select_json_format(self, mock_sparql_interface_class):
        """Test executing a SELECT query with JSON format."""
        # Setup mock
        mock_interface = Mock()
        mock_sparql_interface_class.return_value = mock_interface
        mock_results = [
            {"name": "John", "age": "30"},
            {"name": "Jane", "age": "25"}
        ]
        mock_interface.select.return_value = mock_results
        
        query = "SELECT ?name ?age WHERE { ?person :name ?name ; :age ?age }"
        
        result = self.sparql_service.execute_query(query, format="json")
        
        # Verify interface was created correctly
        mock_sparql_interface_class.assert_called_once_with(
            endpoint_url=self.mock_config.sparql_endpoint
        )
        # Verify select was called
        mock_interface.select.assert_called_once_with(query, timeout=30)
        # Verify result is JSON
        self.assertIsInstance(result, str)
        parsed_result = json.loads(result)
        self.assertEqual(parsed_result, mock_results)

    @patch('src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_select_table_format(self, mock_sparql_interface_class):
        """Test executing a SELECT query with table format."""
        # Setup mock
        mock_interface = Mock()
        mock_sparql_interface_class.return_value = mock_interface
        mock_results = [
            {"name": "John", "age": "30"},
            {"name": "Jane", "age": "25"}
        ]
        mock_interface.select.return_value = mock_results
        
        query = "SELECT ?name ?age WHERE { ?person :name ?name ; :age ?age }"
        
        result = self.sparql_service.execute_query(query, format="table")
        
        # Verify result is formatted as table
        self.assertIsInstance(result, str)
        self.assertIn("name | age", result)
        self.assertIn("John | 30", result)
        self.assertIn("Jane | 25", result)

    @patch('src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_select_empty_results(self, mock_sparql_interface_class):
        """Test executing a SELECT query with empty results."""
        # Setup mock
        mock_interface = Mock()
        mock_sparql_interface_class.return_value = mock_interface
        mock_interface.select.return_value = []
        
        query = "SELECT ?name WHERE { ?person :name ?name }"
        
        result = self.sparql_service.execute_query(query, format="table")
        
        self.assertEqual(result, "No results found.")

    @patch('src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_ask(self, mock_sparql_interface_class):
        """Test executing an ASK query."""
        # Setup mock
        mock_interface = Mock()
        mock_sparql_interface_class.return_value = mock_interface
        mock_interface.ask.return_value = True
        
        query = "ASK { ?person :name 'John' }"
        
        result = self.sparql_service.execute_query(query, format="json")
        
        # Verify ask was called
        mock_interface.ask.assert_called_once_with(query, timeout=30)
        # Verify result
        parsed_result = json.loads(result)
        self.assertEqual(parsed_result, {"boolean": True})

    @patch('src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_construct(self, mock_sparql_interface_class):
        """Test executing a CONSTRUCT query."""
        # Setup mock
        mock_interface = Mock()
        mock_sparql_interface_class.return_value = mock_interface
        mock_graph = Mock(spec=Graph)
        mock_graph.serialize.return_value = "@prefix : <http://example.org/> .\n:person1 :name 'John' ."
        mock_interface.construct.return_value = mock_graph
        
        query = "CONSTRUCT { ?person :name ?name } WHERE { ?person :name ?name }"
        
        result = self.sparql_service.execute_query(query, format="turtle")
        
        # Verify construct was called
        mock_interface.construct.assert_called_once_with(query, timeout=30)
        # Verify result
        self.assertIn("John", result)

    @patch('src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_describe(self, mock_sparql_interface_class):
        """Test executing a DESCRIBE query."""
        # Setup mock
        mock_interface = Mock()
        mock_sparql_interface_class.return_value = mock_interface
        mock_graph = Mock(spec=Graph)
        mock_graph.serialize.return_value = "@prefix : <http://example.org/> .\n:person1 :name 'John' ."
        mock_interface.describe.return_value = mock_graph
        
        query = "DESCRIBE :person1"
        
        result = self.sparql_service.execute_query(query, format="turtle")
        
        # Verify describe was called
        mock_interface.describe.assert_called_once_with(query, timeout=30)
        # Verify result
        self.assertIn("John", result)

    @patch('src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_update(self, mock_sparql_interface_class):
        """Test executing an UPDATE query."""
        # Setup mock
        mock_interface = Mock()
        mock_sparql_interface_class.return_value = mock_interface
        
        query = "INSERT DATA { :person1 :name 'John' }"
        
        result = self.sparql_service.execute_query(query)
        
        # Verify update was called
        mock_interface.update.assert_called_once_with(query, timeout=30)
        # Verify result
        self.assertEqual(result, "Update query executed successfully.")

    def test_execute_query_no_endpoint_configured(self):
        """Test executing query without configured endpoint raises error."""
        service = SparqlService()  # No config
        
        with self.assertRaises(ValueError) as context:
            service.execute_query("SELECT * WHERE { ?s ?p ?o }")
        
        self.assertIn("SPARQL query endpoint not specified", str(context.exception))

    def test_execute_query_with_endpoint_override(self):
        """Test executing query with endpoint URL override."""
        service = SparqlService()  # No config
        custom_endpoint = "http://custom:3030/test/query"
        
        with patch('src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface') as mock_interface_class:
            mock_interface = Mock()
            mock_interface_class.return_value = mock_interface
            mock_interface.select.return_value = []
            
            service.execute_query("SELECT * WHERE { ?s ?p ?o }", endpoint_url=custom_endpoint)
            
            # Verify interface was created with custom endpoint
            mock_interface_class.assert_called_once_with(endpoint_url=custom_endpoint)

    def test_execute_query_unsupported_query_type(self):
        """Test executing unsupported query type raises error."""
        with self.assertRaises(ValueError) as context:
            self.sparql_service.execute_query("EXPLAIN SELECT * WHERE { ?s ?p ?o }")
        
        self.assertIn("Could not determine query type", str(context.exception))

    @patch('src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_sparql_wrapper_exception(self, mock_sparql_interface_class):
        """Test handling of SPARQLWrapper exceptions."""
        # Setup mock to raise exception
        mock_interface = Mock()
        mock_sparql_interface_class.return_value = mock_interface
        mock_interface.select.side_effect = SPARQLWrapperException("Test error")
        
        with self.assertRaises(SPARQLWrapperException):
            self.sparql_service.execute_query("SELECT * WHERE { ?s ?p ?o }")

    @patch('src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_unexpected_exception(self, mock_sparql_interface_class):
        """Test handling of unexpected exceptions."""
        # Setup mock to raise exception
        mock_interface = Mock()
        mock_sparql_interface_class.return_value = mock_interface
        mock_interface.select.side_effect = Exception("Unexpected error")
        
        with self.assertRaises(Exception):
            self.sparql_service.execute_query("SELECT * WHERE { ?s ?p ?o }")

    @patch('src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_load_rdf_file_success(self, mock_sparql_interface_class):
        """Test successful RDF file loading."""
        # Setup mock
        mock_interface = Mock()
        mock_sparql_interface_class.return_value = mock_interface
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as tmp_file:
            tmp_file.write("@prefix : <http://example.org/> .\n:person1 :name 'John' .")
            tmp_file_path = Path(tmp_file.name)
        
        try:
            self.sparql_service.load_rdf_file(
                file_path=tmp_file_path,
                graph_uri="http://example.org/graph1"
            )
            
            # Verify interface was created correctly
            mock_sparql_interface_class.assert_called_once_with(
                endpoint_url=self.mock_config.sparql_endpoint,
                update_endpoint_url=self.mock_config.sparql_update_endpoint,
                username=None,
                password=None
            )
            # Verify load_file was called
            mock_interface.load_file.assert_called_once_with(
                file_path=str(tmp_file_path),
                graph_uri="http://example.org/graph1",
                format="turtle"
            )
        finally:
            tmp_file_path.unlink()

    def test_load_rdf_file_no_update_endpoint(self):
        """Test RDF file loading without update endpoint raises error."""
        service = SparqlService()  # No config
        
        with self.assertRaises(ValueError) as context:
            service.load_rdf_file(Path("test.ttl"))
        
        self.assertIn("SPARQL update endpoint not specified", str(context.exception))

    @patch('src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_load_rdf_file_with_auth(self, mock_sparql_interface_class):
        """Test RDF file loading with authentication."""
        # Setup mock
        mock_interface = Mock()
        mock_sparql_interface_class.return_value = mock_interface
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as tmp_file:
            tmp_file.write("@prefix : <http://example.org/> .\n:person1 :name 'John' .")
            tmp_file_path = Path(tmp_file.name)
        
        try:
            self.sparql_service.load_rdf_file(
                file_path=tmp_file_path,
                username="testuser",
                password="testpass",
                rdf_format="n3"
            )
            
            # Verify interface was created with auth
            mock_sparql_interface_class.assert_called_once_with(
                endpoint_url=self.mock_config.sparql_endpoint,
                update_endpoint_url=self.mock_config.sparql_update_endpoint,
                username="testuser",
                password="testpass"
            )
            # Verify load_file was called with correct format
            mock_interface.load_file.assert_called_once_with(
                file_path=str(tmp_file_path),
                graph_uri=None,
                format="n3"
            )
        finally:
            tmp_file_path.unlink()

    @patch('src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_load_rdf_file_inferred_query_endpoint(self, mock_sparql_interface_class):
        """Test RDF file loading with inferred query endpoint."""
        # Setup config with only update endpoint
        config = Mock()
        config.sparql_update_endpoint = "http://localhost:3030/test/update"
        config.sparql_endpoint = None
        
        service = SparqlService(config)
        mock_interface = Mock()
        mock_sparql_interface_class.return_value = mock_interface
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as tmp_file:
            tmp_file.write("@prefix : <http://example.org/> .")
            tmp_file_path = Path(tmp_file.name)
        
        try:
            service.load_rdf_file(file_path=tmp_file_path)
            
            # Verify interface was created with inferred query endpoint
            mock_sparql_interface_class.assert_called_once_with(
                endpoint_url="http://localhost:3030/test/query",  # /update replaced with /query
                update_endpoint_url="http://localhost:3030/test/update",
                username=None,
                password=None
            )
        finally:
            tmp_file_path.unlink()

    @patch('src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_load_rdf_file_sparql_exception(self, mock_sparql_interface_class):
        """Test handling of SPARQL exceptions during file loading."""
        # Setup mock to raise exception
        mock_interface = Mock()
        mock_sparql_interface_class.return_value = mock_interface
        mock_interface.load_file.side_effect = SPARQLWrapperException("Load failed")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as tmp_file:
            tmp_file.write("@prefix : <http://example.org/> .")
            tmp_file_path = Path(tmp_file.name)
        
        try:
            with self.assertRaises(SPARQLWrapperException):
                self.sparql_service.load_rdf_file(file_path=tmp_file_path)
        finally:
            tmp_file_path.unlink()

    def test_load_rdf_file_nonexistent_file(self):
        """Test loading non-existent RDF file raises FileNotFoundError."""
        nonexistent_path = Path("/path/to/nonexistent/file.ttl")
        
        with patch('src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface') as mock_interface_class:
            mock_interface = Mock()
            mock_interface_class.return_value = mock_interface
            mock_interface.load_file.side_effect = FileNotFoundError("File not found")
            
            with self.assertRaises(FileNotFoundError):
                self.sparql_service.load_rdf_file(file_path=nonexistent_path)

    def test_execute_query_custom_timeout(self):
        """Test executing query with custom timeout."""
        with patch('src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface') as mock_interface_class:
            mock_interface = Mock()
            mock_interface_class.return_value = mock_interface
            mock_interface.select.return_value = []
            
            self.sparql_service.execute_query("SELECT * WHERE { ?s ?p ?o }", timeout=60)
            
            # Verify timeout was passed through
            mock_interface.select.assert_called_once_with("SELECT * WHERE { ?s ?p ?o }", timeout=60)


if __name__ == '__main__':
    unittest.main()