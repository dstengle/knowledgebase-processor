"""
Test SPARQL query functionality against Fuseki.

This test module validates the SPARQL query interface by testing
various query patterns against a running Fuseki server.
"""

import unittest
import logging
import requests
import unittest
import logging
import requests

logger = logging.getLogger(__name__)


class TestSparqlQueries(unittest.TestCase):
    """Test SPARQL query execution against Fuseki."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class - skip if Fuseki is not accessible."""
        # Check if existing Fuseki server is accessible
        try:
            response = requests.get("http://localhost:3030/$/ping", timeout=5)
            if response.status_code == 200:
                # Use existing server
                cls.fuseki_wrapper = type('MockWrapper', (), {
                    'dataset_url': 'http://localhost:3030/test',
                    'base_url': 'http://localhost:3030',
                    'is_running': lambda: True,
                    'clear_data': lambda: None,
                    'stop': lambda: None
                })()
                logger.info("Using existing Fuseki server")
                return
        except Exception:
            pass
        
        # Skip if no Fuseki available
        raise unittest.SkipTest("Fuseki server not available")
    
    def load_rdf_data(self, rdf_data: str, content_type: str = "text/turtle") -> None:
        """Load RDF data into the Fuseki dataset."""
        try:
            data_url = f"{self.fuseki_wrapper.dataset_url}/data"
            
            response = requests.post(
                data_url,
                data=rdf_data,
                headers={"Content-Type": content_type},
                timeout=30
            )
            response.raise_for_status()
            logger.info("RDF data loaded successfully")
            
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to load RDF data: {e}")
    
    def execute_sparql_query(self, query: str, query_type: str = "SELECT"):
        """Execute a SPARQL query against the Fuseki dataset."""
        try:
            query_url = f"{self.fuseki_wrapper.dataset_url}/sparql"
            
            accept_headers = {
                "SELECT": "application/sparql-results+json",
                "ASK": "application/sparql-results+json",
                "CONSTRUCT": "text/turtle",
                "DESCRIBE": "text/turtle"
            }
            
            accept_header = accept_headers.get(query_type.upper(), "application/sparql-results+json")
            
            response = requests.post(
                query_url,
                data={"query": query},
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": accept_header
                },
                timeout=30
            )
            response.raise_for_status()
            
            if "application/json" in response.headers.get("content-type", ""):
                return response.json()
            else:
                return {"text": response.text}
            
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to execute SPARQL query: {e}")
    
    def execute_sparql_update(self, update: str) -> None:
        """Execute a SPARQL UPDATE against the Fuseki dataset."""
        try:
            update_url = f"{self.fuseki_wrapper.dataset_url}/update"
            
            response = requests.post(
                update_url,
                data={"update": update},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            response.raise_for_status()
            logger.info("SPARQL update executed successfully")
            
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to execute SPARQL update: {e}")
    
    def count_triples(self) -> int:
        """Count the total number of triples in the dataset."""
        query = "SELECT (COUNT(*) AS ?count) WHERE { ?s ?p ?o }"
        result = self.execute_sparql_query(query, "SELECT")
        
        bindings = result.get("results", {}).get("bindings", [])
        if bindings:
            return int(bindings[0]["count"]["value"])
        return 0
    
    def test_simple_select_query(self):
        """Test a simple SELECT query."""
        # Load some test data
        test_data = """
        @prefix ex: <http://example.org/> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        
        ex:John rdfs:label "John Doe" .
        ex:Jane rdfs:label "Jane Smith" .
        """
        
        self.load_rdf_data(test_data)
        
        # Execute query
        query = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?person ?label WHERE {
            ?person rdfs:label ?label .
        }
        """
        
        result = self.execute_sparql_query(query)
        bindings = result.get("results", {}).get("bindings", [])
        
        # Should find 2 people
        self.assertEqual(len(bindings), 2)
    
    def test_ask_query(self):
        """Test an ASK query."""
        # Load test data
        test_data = """
        @prefix ex: <http://example.org/> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        
        ex:John rdfs:label "John Doe" .
        """
        
        self.load_rdf_data(test_data)
        
        # Test positive case
        ask_query_positive = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX ex: <http://example.org/>
        ASK {
            ex:John rdfs:label "John Doe" .
        }
        """
        
        result = self.execute_sparql_query(ask_query_positive, "ASK")
        self.assertTrue(result.get("boolean", False))
        
        # Test negative case
        ask_query_negative = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX ex: <http://example.org/>
        ASK {
            ex:John rdfs:label "Jane Doe" .
        }
        """
        
        result = self.execute_sparql_query(ask_query_negative, "ASK")
        self.assertFalse(result.get("boolean", True))
    
    def test_count_query(self):
        """Test counting triples."""
        # Load test data
        test_data = """
        @prefix ex: <http://example.org/> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        
        ex:John rdfs:label "John Doe" .
        ex:Jane rdfs:label "Jane Smith" .
        ex:Bob rdfs:label "Bob Johnson" .
        """
        
        self.load_rdf_data(test_data)
        
        # Count all triples
        count = self.count_triples()
        self.assertEqual(count, 3)
    
    def test_sparql_update(self):
        """Test SPARQL UPDATE operations."""
        # Insert data using UPDATE
        update_query = """
        PREFIX ex: <http://example.org/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        INSERT DATA {
            ex:Alice rdfs:label "Alice Wilson" .
            ex:Charlie rdfs:label "Charlie Brown" .
        }
        """
        
        self.execute_sparql_update(update_query)
        
        # Verify data was inserted
        count = self.count_triples()
        self.assertEqual(count, 2)
        
        # Query for specific person
        query = """
        PREFIX ex: <http://example.org/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?label WHERE {
            ex:Alice rdfs:label ?label .
        }
        """
        
        result = self.execute_sparql_query(query)
        bindings = result.get("results", {}).get("bindings", [])
        self.assertEqual(len(bindings), 1)
        self.assertEqual(bindings[0]["label"]["value"], "Alice Wilson")


if __name__ == '__main__':
    unittest.main()