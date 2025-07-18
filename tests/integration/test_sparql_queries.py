"""
Test SPARQL query functionality against Fuseki.

This test module validates the SPARQL query interface by testing
various query patterns against a running Fuseki server.
"""

import unittest
import logging
import requests

from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException

logger = logging.getLogger(__name__)

class TestSparqlQueries(unittest.TestCase):
    """Test SPARQL query execution against Fuseki."""
    
    FUSEKI_URL = "http://fuseki:3030"
    DATASET_NAME = "test"
    SPARQL_ENDPOINT = f"{FUSEKI_URL}/{DATASET_NAME}/sparql"
    UPDATE_ENDPOINT = f"{FUSEKI_URL}/{DATASET_NAME}/update"
    DATA_ENDPOINT = f"{FUSEKI_URL}/{DATASET_NAME}/data"

    # Test data fixture
    TEST_DATA = """
    @prefix ex: <http://example.org/> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    
    ex:John a ex:Person ;
             rdfs:label "John Doe" .
    ex:Jane a ex:Person ;
             rdfs:label "Jane Smith" .
    """

    # SPARQL queries
    QUERIES = {
        "count_triples": "SELECT (COUNT(*) AS ?count) WHERE { ?s ?p ?o }",
        "select_persons": """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?person ?label WHERE {
                ?person a <http://example.org/Person> ;
                        rdfs:label ?label .
            }
        """,
        "ask_person_exists": """
            PREFIX ex: <http://example.org/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            ASK { ex:John rdfs:label "John Doe" . }
        """,
        "insert_person": """
            PREFIX ex: <http://example.org/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            INSERT DATA { ex:Alice rdfs:label "Alice" . }
        """
    }

    @classmethod
    def setUpClass(cls):
        """Set up the test class - skip if Fuseki is not accessible."""
        try:
            response = requests.get(f"{cls.FUSEKI_URL}/$/ping", timeout=5)
            if response.status_code != 200:
                raise unittest.SkipTest("Fuseki server not available")
        except requests.RequestException:
            raise unittest.SkipTest("Fuseki server not available")

    def setUp(self):
        """Set up each test case."""
        self.clear_data()
        self.load_rdf_data(self.TEST_DATA)

    def tearDown(self):
        """Clean up after each test."""
        self.clear_data()

    def execute_sparql_query(self, query: str, query_type: str = "SELECT"):
        """Execute a SPARQL query against the Fuseki dataset."""
        accept_headers = {
            "SELECT": "application/sparql-results+json",
            "ASK": "application/sparql-results+json",
        }
        accept_header = accept_headers.get(query_type.upper(), "application/sparql-results+json")
        
        try:
            response = requests.post(
                self.SPARQL_ENDPOINT,
                data={"query": query},
                headers={"Accept": accept_header},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to execute SPARQL query: {e}")

    def execute_sparql_update(self, update: str):
        """Execute a SPARQL UPDATE against the Fuseki dataset."""
        try:
            response = requests.post(
                self.UPDATE_ENDPOINT,
                data={"update": update},
                auth=("admin", "admin"),
                timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to execute SPARQL update: {e}")

    def load_rdf_data(self, rdf_data: str, content_type: str = "text/turtle"):
        """Load RDF data into the Fuseki dataset."""
        try:
            response = requests.post(
                self.DATA_ENDPOINT,
                data=rdf_data,
                headers={"Content-Type": content_type},
                auth=("admin", "admin"),
                timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to load RDF data: {e}")

    def clear_data(self):
        """Clear all data from the dataset."""
        self.execute_sparql_update("CLEAR DEFAULT")

    def test_simple_select_query(self):
        """Test a simple SELECT query."""
        result = self.execute_sparql_query(self.QUERIES["select_persons"])
        bindings = result.get("results", {}).get("bindings", [])
        self.assertEqual(len(bindings), 2)

    def test_ask_query(self):
        """Test an ASK query."""
        result = self.execute_sparql_query(self.QUERIES["ask_person_exists"], "ASK")
        self.assertTrue(result.get("boolean", False))

    def test_count_query(self):
        """Test counting triples."""
        result = self.execute_sparql_query(self.QUERIES["count_triples"])
        count = int(result["results"]["bindings"][0]["count"]["value"])
        self.assertEqual(count, 4)

    def test_sparql_update(self):
        """Test SPARQL UPDATE operations."""
        self.execute_sparql_update(self.QUERIES["insert_person"])
        
        # Verify data was inserted
        result = self.execute_sparql_query("PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT (COUNT(*) as ?count) WHERE { ?s rdfs:label ?o }")
        count = int(result["results"]["bindings"][0]["count"]["value"])
        self.assertEqual(count, 3)

    def test_insert_with_quotes_fails(self):
        """Test inserting data with quotes that should fail."""
        failing_query = """
        PREFIX ex: <http://example.org/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        INSERT DATA { ex:Bob rdfs:label "Bob's data with \\"quotes\\" and backslash \\" . }
        """
        with self.assertRaises(RuntimeError):
            self.execute_sparql_update(failing_query)

    def test_insert_with_quotes_fixed(self):
        """Test inserting data with quotes that should succeed."""
        fixed_query = """
        PREFIX ex: <http://example.org/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        INSERT DATA { ex:Bob rdfs:label "Bob's data with \\"quotes\\" and backslash \\\\" . }
        """
        self.execute_sparql_update(fixed_query)
        result = self.execute_sparql_query("PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX ex: <http://example.org/> SELECT ?label WHERE { ex:Bob rdfs:label ?label }")
        label = result["results"]["bindings"][0]["label"]["value"]
        self.assertEqual(label, "Bob's data with \\\"quotes\\\" and backslash \\\\")

if __name__ == '__main__':
    unittest.main()