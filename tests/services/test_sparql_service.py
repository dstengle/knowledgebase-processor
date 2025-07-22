"""Unit tests for SparqlService."""

import json
import unittest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile

from rdflib import Graph
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException

from knowledgebase_processor.services.sparql_service import SparqlService


class TestSparqlService(unittest.TestCase):
    """Test cases for SparqlService."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = Mock()
        self.mock_config.sparql_endpoint_url = "http://localhost:3030/test/query"
        self.mock_config.sparql_update_endpoint_url = "http://localhost:3030/test/update"

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_initialization_with_config(self, mock_sparql_interface_class):
        """Test SparqlService initialization with config."""
        service = SparqlService(config=self.mock_config)
        self.assertEqual(service.config, self.mock_config)
        self.assertIsNotNone(service.logger)
        mock_sparql_interface_class.assert_called_with(
            endpoint_url=self.mock_config.sparql_endpoint_url,
            update_endpoint_url=self.mock_config.sparql_update_endpoint_url
        )

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_initialization_without_config(self, mock_sparql_interface_class):
        """Test SparqlService initialization without config."""
        service = SparqlService()
        self.assertIsNone(service.config)
        self.assertIsNotNone(service.logger)
        mock_sparql_interface_class.assert_called_with(
            endpoint_url=None,
            update_endpoint_url=None
        )

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_select_json_format(self, mock_sparql_interface_class):
        """Test executing a SELECT query with JSON format."""
        mock_interface = mock_sparql_interface_class.return_value
        mock_results = [
            {"name": "John", "age": "30"},
            {"name": "Jane", "age": "25"}
        ]
        mock_interface.select.return_value = mock_results
        
        sparql_service = SparqlService(self.mock_config)
        query = "SELECT ?name ?age WHERE { ?person :name ?name ; :age ?age }"
        
        result = sparql_service.execute_query(query, format="json")
        
        mock_interface.select.assert_called_once_with(query, timeout=30)
        self.assertIsInstance(result, str)
        parsed_result = json.loads(result)
        self.assertEqual(parsed_result, mock_results)

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_select_table_format(self, mock_sparql_interface_class):
        """Test executing a SELECT query with table format."""
        mock_interface = mock_sparql_interface_class.return_value
        mock_results = [
            {"name": "John", "age": "30"},
            {"name": "Jane", "age": "25"}
        ]
        mock_interface.select.return_value = mock_results
        
        sparql_service = SparqlService(self.mock_config)
        query = "SELECT ?name ?age WHERE { ?person :name ?name ; :age ?age }"
        
        result = sparql_service.execute_query(query, format="table")
        
        self.assertIsInstance(result, str)
        self.assertIn("name | age", result)
        self.assertIn("John | 30", result)
        self.assertIn("Jane | 25", result)

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_select_empty_results(self, mock_sparql_interface_class):
        """Test executing a SELECT query with empty results."""
        mock_interface = mock_sparql_interface_class.return_value
        mock_interface.select.return_value = []
        
        sparql_service = SparqlService(self.mock_config)
        query = "SELECT ?name WHERE { ?person :name ?name }"
        
        result = sparql_service.execute_query(query, format="table")
        
        self.assertEqual(result, "No results found.")

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_ask(self, mock_sparql_interface_class):
        """Test executing an ASK query."""
        mock_interface = mock_sparql_interface_class.return_value
        mock_interface.ask.return_value = True
        
        sparql_service = SparqlService(self.mock_config)
        query = "ASK { ?person :name 'John' }"
        
        result = sparql_service.execute_query(query, format="json")
        
        mock_interface.ask.assert_called_once_with(query, timeout=30)
        parsed_result = json.loads(result)
        self.assertEqual(parsed_result, {"boolean": True})

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_construct(self, mock_sparql_interface_class):
        """Test executing a CONSTRUCT query."""
        mock_interface = mock_sparql_interface_class.return_value
        mock_graph = Mock(spec=Graph)
        mock_graph.serialize.return_value = "@prefix : <http://example.org/> .\n:person1 :name 'John' ."
        mock_interface.construct.return_value = mock_graph
        
        sparql_service = SparqlService(self.mock_config)
        query = "CONSTRUCT { ?person :name ?name } WHERE { ?person :name ?name }"
        
        result = sparql_service.execute_query(query, format="turtle")
        
        mock_interface.construct.assert_called_once_with(query, timeout=30)
        self.assertIn("John", result)

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_describe(self, mock_sparql_interface_class):
        """Test executing a DESCRIBE query."""
        mock_interface = mock_sparql_interface_class.return_value
        mock_graph = Mock(spec=Graph)
        mock_graph.serialize.return_value = "@prefix : <http://example.org/> .\n:person1 :name 'John' ."
        mock_interface.describe.return_value = mock_graph
        
        sparql_service = SparqlService(self.mock_config)
        query = "DESCRIBE :person1"
        
        result = sparql_service.execute_query(query, format="turtle")
        
        mock_interface.describe.assert_called_once_with(query, timeout=30)
        self.assertIn("John", result)

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_update(self, mock_sparql_interface_class):
        """Test executing an UPDATE query."""
        mock_interface = mock_sparql_interface_class.return_value
        sparql_service = SparqlService(self.mock_config)
        query = "INSERT DATA { :person1 :name 'John' }"
        
        result = sparql_service.execute_query(query)
        
        mock_interface.update.assert_called_once_with(query, timeout=30)
        self.assertEqual(result, "Update query executed successfully.")

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_no_endpoint_configured(self, mock_sparql_interface_class):
        """Test executing query without configured endpoint raises error."""
        service = SparqlService()
        
        with self.assertRaises(ValueError) as context:
            service.execute_query("SELECT * WHERE { ?s ?p ?o }")
        
        self.assertIn("SPARQL query endpoint not specified", str(context.exception))

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_with_endpoint_override(self, mock_sparql_interface_class):
        """Test executing query with endpoint URL override."""
        service = SparqlService()
        custom_endpoint = "http://custom:3030/test/query"
        
        mock_interface = mock_sparql_interface_class.return_value
        mock_interface.select.return_value = []
        
        service.execute_query("SELECT * WHERE { ?s ?p ?o }", endpoint_url=custom_endpoint)
        
        mock_sparql_interface_class.assert_called_with(endpoint_url=custom_endpoint, update_endpoint_url=None)

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_unsupported_query_type(self, mock_sparql_interface_class):
        """Test executing unsupported query type raises error."""
        sparql_service = SparqlService(self.mock_config)
        with self.assertRaises(ValueError) as context:
            sparql_service.execute_query("EXPLAIN SELECT * WHERE { ?s ?p ?o }")
        
        self.assertIn("Could not determine query type", str(context.exception))

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_sparql_wrapper_exception(self, mock_sparql_interface_class):
        """Test handling of SPARQLWrapper exceptions."""
        mock_interface = mock_sparql_interface_class.return_value
        mock_interface.select.side_effect = SPARQLWrapperException("Test error")
        
        sparql_service = SparqlService(self.mock_config)
        with self.assertRaises(SPARQLWrapperException):
            sparql_service.execute_query("SELECT * WHERE { ?s ?p ?o }")

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_unexpected_exception(self, mock_sparql_interface_class):
        """Test handling of unexpected exceptions."""
        mock_interface = mock_sparql_interface_class.return_value
        mock_interface.select.side_effect = Exception("Unexpected error")
        
        sparql_service = SparqlService(self.mock_config)
        with self.assertRaises(Exception):
            sparql_service.execute_query("SELECT * WHERE { ?s ?p ?o }")

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_load_rdf_file_success(self, mock_sparql_interface_class):
        """Test successful RDF file loading."""
        mock_interface = mock_sparql_interface_class.return_value
        sparql_service = SparqlService(self.mock_config)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as tmp_file:
            tmp_file.write("@prefix : <http://example.org/> .\n:person1 :name 'John' .")
            tmp_file_path = Path(tmp_file.name)
        
        try:
            sparql_service.load_rdf_file(
                file_path=tmp_file_path,
                graph_uri="http://example.org/graph1"
            )
            
            mock_interface.load_file.assert_called_once_with(
                file_path=str(tmp_file_path),
                graph_uri="http://example.org/graph1",
                format="turtle"
            )
        finally:
            tmp_file_path.unlink()

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_load_rdf_file_no_update_endpoint(self, mock_sparql_interface_class):
        """Test RDF file loading without update endpoint raises error."""
        config = Mock()
        config.sparql_endpoint_url = "http://localhost:3030/test/query"
        config.sparql_update_endpoint_url = None
        service = SparqlService(config)
        
        with self.assertRaises(ValueError) as context:
            service.load_rdf_file(Path("test.ttl"))
        
        self.assertIn("SPARQL update endpoint not specified", str(context.exception))

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_load_rdf_file_with_auth(self, mock_sparql_interface_class):
        """Test RDF file loading with authentication."""
        mock_interface = mock_sparql_interface_class.return_value
        sparql_service = SparqlService(self.mock_config)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as tmp_file:
            tmp_file.write("@prefix : <http://example.org/> .\n:person1 :name 'John' .")
            tmp_file_path = Path(tmp_file.name)
        
        try:
            sparql_service.load_rdf_file(
                file_path=tmp_file_path,
                username="testuser",
                password="testpass",
                rdf_format="n3"
            )
            
            mock_interface.load_file.assert_called_once_with(
                file_path=str(tmp_file_path),
                graph_uri=None,
                format="n3"
            )
        finally:
            tmp_file_path.unlink()

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_load_rdf_file_inferred_query_endpoint(self, mock_sparql_interface_class):
        """Test RDF file loading with inferred query endpoint."""
        config = Mock()
        config.sparql_update_endpoint_url = "http://localhost:3030/test/update"
        config.sparql_endpoint_url = None
        
        service = SparqlService(config)
        
        mock_sparql_interface_class.assert_called_with(
            endpoint_url="http://localhost:3030/test/query",
            update_endpoint_url="http://localhost:3030/test/update"
        )

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_load_rdf_file_sparql_exception(self, mock_sparql_interface_class):
        """Test handling of SPARQL exceptions during file loading."""
        mock_interface = mock_sparql_interface_class.return_value
        sparql_service = SparqlService(self.mock_config)
        mock_interface.load_file.side_effect = SPARQLWrapperException("Load failed")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as tmp_file:
            tmp_file.write("@prefix : <http://example.org/> .")
            tmp_file_path = Path(tmp_file.name)
        
        try:
            with self.assertRaises(SPARQLWrapperException):
                sparql_service.load_rdf_file(file_path=tmp_file_path)
        finally:
            tmp_file_path.unlink()

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_load_rdf_file_nonexistent_file(self, mock_sparql_interface_class):
        """Test loading non-existent RDF file raises FileNotFoundError."""
        mock_interface = mock_sparql_interface_class.return_value
        sparql_service = SparqlService(self.mock_config)
        nonexistent_path = Path("/path/to/nonexistent/file.ttl")
        
        mock_interface.load_file.side_effect = FileNotFoundError("File not found")
        
        with self.assertRaises(FileNotFoundError):
            sparql_service.load_rdf_file(file_path=nonexistent_path)

    @patch('knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_execute_query_custom_timeout(self, mock_sparql_interface_class):
        """Test executing query with custom timeout."""
        mock_interface = mock_sparql_interface_class.return_value
        sparql_service = SparqlService(self.mock_config)
        mock_interface.select.return_value = []
        
        sparql_service.execute_query("SELECT * WHERE { ?s ?p ?o }", timeout=60)
        
        mock_interface.select.assert_called_once_with("SELECT * WHERE { ?s ?p ?o }", timeout=60)


if __name__ == '__main__':
    unittest.main()