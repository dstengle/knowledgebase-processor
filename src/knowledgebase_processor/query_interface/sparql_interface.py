"""SPARQL Query Interface for interacting with SPARQL endpoints."""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin

from SPARQLWrapper import SPARQLWrapper, JSON, XML, TURTLE, N3, RDFXML
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException
from rdflib import Graph

logger = logging.getLogger(__name__)


class SparqlQueryInterface:
    """Interface for executing SPARQL queries against a configurable SPARQL endpoint.
    
    This component provides methods for executing different types of SPARQL queries
    (SELECT, ASK, CONSTRUCT, DESCRIBE, UPDATE) against a SPARQL endpoint and handling
    different result formats.
    """
    
    def __init__(self, endpoint_url: str, update_endpoint_url: Optional[str] = None):
        """Initialize the SPARQL Query Interface.
        
        Args:
            endpoint_url: The SPARQL query endpoint URL
            update_endpoint_url: The SPARQL update endpoint URL (optional, defaults to endpoint_url + '/update')
        """
        self.endpoint_url = endpoint_url
        self.update_endpoint_url = update_endpoint_url or urljoin(endpoint_url.rstrip('/') + '/', 'update')
        
        # Initialize SPARQLWrapper instances
        self._query_wrapper = SPARQLWrapper(self.endpoint_url)
        self._update_wrapper = SPARQLWrapper(self.update_endpoint_url)
        
        logger.info(f"Initialized SPARQL interface with query endpoint: {self.endpoint_url}")
        logger.info(f"Update endpoint: {self.update_endpoint_url}")
    
    def select(self, query: str, timeout: int = 30) -> List[Dict[str, Any]]:
        """Execute a SPARQL SELECT query.
        
        Args:
            query: The SPARQL SELECT query string
            timeout: Query timeout in seconds
            
        Returns:
            List of dictionaries representing the query results
            
        Raises:
            SPARQLWrapperException: If the query fails
        """
        logger.debug(f"Executing SELECT query: {query}")
        
        self._query_wrapper.setQuery(query)
        self._query_wrapper.setReturnFormat(JSON)
        self._query_wrapper.setTimeout(timeout)
        
        try:
            results = self._query_wrapper.query().convert()
            bindings = results.get('results', {}).get('bindings', [])
            
            # Convert to more convenient format
            converted_results = []
            for binding in bindings:
                row = {}
                for var, value_info in binding.items():
                    row[var] = self._extract_value(value_info)
                converted_results.append(row)
            
            logger.debug(f"SELECT query returned {len(converted_results)} results")
            return converted_results
            
        except Exception as e:
            logger.error(f"Failed to execute SELECT query: {e}")
            raise SPARQLWrapperException(f"SELECT query failed: {e}") from e
    
    def ask(self, query: str, timeout: int = 30) -> bool:
        """Execute a SPARQL ASK query.
        
        Args:
            query: The SPARQL ASK query string
            timeout: Query timeout in seconds
            
        Returns:
            Boolean result of the ASK query
            
        Raises:
            SPARQLWrapperException: If the query fails
        """
        logger.debug(f"Executing ASK query: {query}")
        
        self._query_wrapper.setQuery(query)
        self._query_wrapper.setReturnFormat(JSON)
        self._query_wrapper.setTimeout(timeout)
        
        try:
            results = self._query_wrapper.query().convert()
            result = results.get('boolean', False)
            
            logger.debug(f"ASK query returned: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute ASK query: {e}")
            raise SPARQLWrapperException(f"ASK query failed: {e}") from e
    
    def construct(self, query: str, timeout: int = 30) -> Graph:
        """Execute a SPARQL CONSTRUCT query.
        
        Args:
            query: The SPARQL CONSTRUCT query string
            timeout: Query timeout in seconds
            
        Returns:
            RDFLib Graph containing the constructed triples
            
        Raises:
            SPARQLWrapperException: If the query fails
        """
        logger.debug(f"Executing CONSTRUCT query: {query}")
        
        self._query_wrapper.setQuery(query)
        self._query_wrapper.setReturnFormat(TURTLE)
        self._query_wrapper.setTimeout(timeout)
        
        try:
            results = self._query_wrapper.query().convert()
            
            # Parse the turtle result into an RDFLib graph
            graph = Graph()
            graph.parse(data=results, format='turtle')
            
            logger.debug(f"CONSTRUCT query returned graph with {len(graph)} triples")
            return graph
            
        except Exception as e:
            logger.error(f"Failed to execute CONSTRUCT query: {e}")
            raise SPARQLWrapperException(f"CONSTRUCT query failed: {e}") from e
    
    def describe(self, query: str, timeout: int = 30) -> Graph:
        """Execute a SPARQL DESCRIBE query.
        
        Args:
            query: The SPARQL DESCRIBE query string
            timeout: Query timeout in seconds
            
        Returns:
            RDFLib Graph containing the described resources
            
        Raises:
            SPARQLWrapperException: If the query fails
        """
        logger.debug(f"Executing DESCRIBE query: {query}")
        
        self._query_wrapper.setQuery(query)
        self._query_wrapper.setReturnFormat(TURTLE)
        self._query_wrapper.setTimeout(timeout)
        
        try:
            results = self._query_wrapper.query().convert()
            
            # Parse the turtle result into an RDFLib graph
            graph = Graph()
            graph.parse(data=results, format='turtle')
            
            logger.debug(f"DESCRIBE query returned graph with {len(graph)} triples")
            return graph
            
        except Exception as e:
            logger.error(f"Failed to execute DESCRIBE query: {e}")
            raise SPARQLWrapperException(f"DESCRIBE query failed: {e}") from e
    
    def update(self, query: str, timeout: int = 30) -> None:
        """Execute a SPARQL UPDATE query.
        
        Args:
            query: The SPARQL UPDATE query string
            timeout: Query timeout in seconds
            
        Raises:
            SPARQLWrapperException: If the update fails
        """
        logger.debug(f"Executing UPDATE query: {query}")
        
        self._update_wrapper.setQuery(query)
        self._update_wrapper.setTimeout(timeout)
        
        try:
            self._update_wrapper.query()
            logger.debug("UPDATE query executed successfully")
            
        except Exception as e:
            logger.error(f"Failed to execute UPDATE query: {e}")
            raise SPARQLWrapperException(f"UPDATE query failed: {e}") from e
    
    def load_data(self, graph: Graph, graph_uri: Optional[str] = None) -> None:
        """Load RDF data into the SPARQL store.
        
        Args:
            graph: RDFLib Graph containing the data to load
            graph_uri: Optional named graph URI to load data into
            
        Raises:
            SPARQLWrapperException: If the data loading fails
        """
        logger.info(f"Loading {len(graph)} triples into SPARQL store")
        
        # Serialize the graph to turtle format
        turtle_data = graph.serialize(format='turtle')
        
        # Build INSERT DATA query
        if graph_uri:
            query = f"""
            INSERT DATA {{
                GRAPH <{graph_uri}> {{
                    {turtle_data}
                }}
            }}
            """
        else:
            query = f"""
            INSERT DATA {{
                {turtle_data}
            }}
            """
        
        self.update(query)
        logger.info("Data loaded successfully")
    
    def load_file(self, file_path: str, graph_uri: Optional[str] = None, format: str = 'turtle') -> None:
        """Load RDF data from a file into the SPARQL store.
        
        Args:
            file_path: Path to the RDF file
            graph_uri: Optional named graph URI to load data into
            format: RDF format of the file (default: turtle)
            
        Raises:
            SPARQLWrapperException: If the file loading fails
        """
        logger.info(f"Loading RDF file: {file_path}")
        
        try:
            # Parse the file into a graph
            graph = Graph()
            graph.parse(file_path, format=format)
            
            # Load the graph data
            self.load_data(graph, graph_uri)
            
        except Exception as e:
            logger.error(f"Failed to load file {file_path}: {e}")
            raise SPARQLWrapperException(f"File loading failed: {e}") from e
    
    def clear_graph(self, graph_uri: Optional[str] = None) -> None:
        """Clear all data from a graph.
        
        Args:
            graph_uri: URI of the named graph to clear (if None, clears default graph)
            
        Raises:
            SPARQLWrapperException: If the clear operation fails
        """
        if graph_uri:
            query = f"CLEAR GRAPH <{graph_uri}>"
            logger.info(f"Clearing named graph: {graph_uri}")
        else:
            query = "CLEAR DEFAULT"
            logger.info("Clearing default graph")
        
        self.update(query)
        logger.info("Graph cleared successfully")
    
    def list_graphs(self) -> List[str]:
        """List all named graphs in the SPARQL store.
        
        Returns:
            List of named graph URIs
            
        Raises:
            SPARQLWrapperException: If the query fails
        """
        query = """
        SELECT DISTINCT ?graph
        WHERE {
            GRAPH ?graph { ?s ?p ?o }
        }
        ORDER BY ?graph
        """
        
        results = self.select(query)
        graphs = [result['graph'] for result in results]
        
        logger.debug(f"Found {len(graphs)} named graphs")
        return graphs
    
    def count_triples(self, graph_uri: Optional[str] = None) -> int:
        """Count the number of triples in a graph.
        
        Args:
            graph_uri: URI of the named graph to count (if None, counts default graph)
            
        Returns:
            Number of triples in the graph
            
        Raises:
            SPARQLWrapperException: If the query fails
        """
        if graph_uri:
            query = f"""
            SELECT (COUNT(*) as ?count)
            WHERE {{
                GRAPH <{graph_uri}> {{ ?s ?p ?o }}
            }}
            """
        else:
            query = """
            SELECT (COUNT(*) as ?count)
            WHERE { ?s ?p ?o }
            """
        
        results = self.select(query)
        count = int(results[0]['count']) if results else 0
        
        logger.debug(f"Graph contains {count} triples")
        return count
    
    def _extract_value(self, value_info: Dict[str, Any]) -> Union[str, int, float, bool]:
        """Extract and convert a value from SPARQL result binding.
        
        Args:
            value_info: Value information from SPARQL result binding
            
        Returns:
            Converted value with appropriate Python type
        """
        value = value_info.get('value', '')
        datatype = value_info.get('datatype', '')
        
        # Handle different datatypes
        if datatype == 'http://www.w3.org/2001/XMLSchema#integer':
            return int(value)
        elif datatype == 'http://www.w3.org/2001/XMLSchema#decimal' or \
             datatype == 'http://www.w3.org/2001/XMLSchema#double' or \
             datatype == 'http://www.w3.org/2001/XMLSchema#float':
            return float(value)
        elif datatype == 'http://www.w3.org/2001/XMLSchema#boolean':
            return value.lower() in ('true', '1')
        else:
            return value