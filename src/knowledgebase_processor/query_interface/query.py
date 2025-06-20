"""Query interface implementation."""

from typing import List, Dict, Any, Optional, Set, Union

from ..metadata_store.interface import MetadataStoreInterface
from ..models.content import Document
from ..models.metadata import DocumentMetadata
from .sparql_interface import SparqlQueryInterface


class QueryInterface:
    """Interface for querying the knowledge base.
    
    This component provides methods for querying the knowledge base
    based on various criteria.
    """
    
    def __init__(self, metadata_store: MetadataStoreInterface, sparql_endpoint: Optional[str] = None):
        """Initialize the QueryInterface.
        
        Args:
            metadata_store: The metadata store to query
            sparql_endpoint: Optional SPARQL endpoint URL for advanced queries
        """
        self.metadata_store = metadata_store
        self.sparql_interface = SparqlQueryInterface(sparql_endpoint) if sparql_endpoint else None
    
    def find_by_tag(self, tag: str) -> List[str]:
        """Find documents with a specific tag.
        
        Args:
            tag: The tag to search for
            
        Returns:
            List of document IDs with the specified tag
        """
        return self.metadata_store.search({'tags': tag})
    
    def find_by_topic(self, topic: str) -> List[str]:
        """Find documents related to a specific topic.
        
        Args:
            topic: The topic to search for
            
        Returns:
            List of document IDs related to the specified topic
        """
        # This is a placeholder implementation
        # In a real system, this would use a more sophisticated search
        
        results = []
        
        # Get all document IDs
        all_docs = self.metadata_store.list_all()
        
        # Check each document for the topic
        for doc_id in all_docs:
            metadata = self.metadata_store.get(doc_id)
            if metadata:
                # Check if the document has elements with the topic
                # This is a simplified approach
                for element in metadata.structure.get('elements', []):
                    if element.get('element_type') == 'topic' and element.get('content') == topic:
                        results.append(doc_id)
                        break
        
        return results
    
    def find_related(self, document_id: str) -> List[Dict[str, Any]]:
        """Find documents related to a specific document.
        
        Args:
            document_id: ID of the document to find relations for
            
        Returns:
            List of dictionaries with related document information
        """
        # This is a placeholder implementation
        # In a real system, this would use relationship information
        
        results = []
        
        # Get the document's metadata
        metadata = self.metadata_store.get(document_id)
        if not metadata:
            return results
        
        # Get the document's tags
        tags = metadata.tags
        
        # Find documents with matching tags
        for tag in tags:
            related_docs = self.find_by_tag(tag)
            for related_id in related_docs:
                if related_id != document_id:  # Exclude the original document
                    results.append({
                        'document_id': related_id,
                        'relationship_type': 'shared_tag',
                        'shared_element': tag
                    })
        
        return results
    
    def search(self, query: str) -> List[str]: # Keep query as str for now, consistent with KnowledgeBaseProcessor.search
        """Search for documents matching a text query.
        
        Args:
            query: The search query (string)
            
        Returns:
            List of matching document IDs
        """
        # For a simple string query, we'll search in titles for now.
        # More complex query parsing can be added here or in MetadataStore.search
        if isinstance(query, str):
            return self.metadata_store.search({'title_contains': query})
        
        # If the query parameter were a Dict, we could pass it directly:
        # elif isinstance(query, dict):
        #     return self.metadata_store.search(query)
            
        return [] # Return empty list if query type is not supported
    
    def sparql_select(self, query: str, timeout: int = 30) -> List[Dict[str, Any]]:
        """Execute a SPARQL SELECT query.
        
        Args:
            query: The SPARQL SELECT query string
            timeout: Query timeout in seconds
            
        Returns:
            List of dictionaries representing the query results
            
        Raises:
            ValueError: If SPARQL interface is not configured
        """
        if not self.sparql_interface:
            raise ValueError("SPARQL endpoint not configured. Please provide sparql_endpoint in constructor.")
        
        return self.sparql_interface.select(query, timeout)
    
    def sparql_ask(self, query: str, timeout: int = 30) -> bool:
        """Execute a SPARQL ASK query.
        
        Args:
            query: The SPARQL ASK query string
            timeout: Query timeout in seconds
            
        Returns:
            Boolean result of the ASK query
            
        Raises:
            ValueError: If SPARQL interface is not configured
        """
        if not self.sparql_interface:
            raise ValueError("SPARQL endpoint not configured. Please provide sparql_endpoint in constructor.")
        
        return self.sparql_interface.ask(query, timeout)
    
    def sparql_construct(self, query: str, timeout: int = 30):
        """Execute a SPARQL CONSTRUCT query.
        
        Args:
            query: The SPARQL CONSTRUCT query string
            timeout: Query timeout in seconds
            
        Returns:
            RDFLib Graph containing the constructed triples
            
        Raises:
            ValueError: If SPARQL interface is not configured
        """
        if not self.sparql_interface:
            raise ValueError("SPARQL endpoint not configured. Please provide sparql_endpoint in constructor.")
        
        return self.sparql_interface.construct(query, timeout)
    
    def sparql_describe(self, query: str, timeout: int = 30):
        """Execute a SPARQL DESCRIBE query.
        
        Args:
            query: The SPARQL DESCRIBE query string
            timeout: Query timeout in seconds
            
        Returns:
            RDFLib Graph containing the described resources
            
        Raises:
            ValueError: If SPARQL interface is not configured
        """
        if not self.sparql_interface:
            raise ValueError("SPARQL endpoint not configured. Please provide sparql_endpoint in constructor.")
        
        return self.sparql_interface.describe(query, timeout)
    
    def sparql_update(self, query: str, timeout: int = 30) -> None:
        """Execute a SPARQL UPDATE query.
        
        Args:
            query: The SPARQL UPDATE query string
            timeout: Query timeout in seconds
            
        Raises:
            ValueError: If SPARQL interface is not configured
        """
        if not self.sparql_interface:
            raise ValueError("SPARQL endpoint not configured. Please provide sparql_endpoint in constructor.")
        
        self.sparql_interface.update(query, timeout)
    
    def load_rdf_data(self, graph, graph_uri: Optional[str] = None) -> None:
        """Load RDF data into the SPARQL store.
        
        Args:
            graph: RDFLib Graph containing the data to load
            graph_uri: Optional named graph URI to load data into
            
        Raises:
            ValueError: If SPARQL interface is not configured
        """
        if not self.sparql_interface:
            raise ValueError("SPARQL endpoint not configured. Please provide sparql_endpoint in constructor.")
        
        self.sparql_interface.load_data(graph, graph_uri)
    
    def load_rdf_file(self, file_path: str, graph_uri: Optional[str] = None, format: str = 'turtle') -> None:
        """Load RDF data from a file into the SPARQL store.
        
        Args:
            file_path: Path to the RDF file
            graph_uri: Optional named graph URI to load data into
            format: RDF format of the file (default: turtle)
            
        Raises:
            ValueError: If SPARQL interface is not configured
        """
        if not self.sparql_interface:
            raise ValueError("SPARQL endpoint not configured. Please provide sparql_endpoint in constructor.")
        
        self.sparql_interface.load_file(file_path, graph_uri, format)