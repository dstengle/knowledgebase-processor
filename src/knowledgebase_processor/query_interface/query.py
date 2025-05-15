"""Query interface implementation."""

from typing import List, Dict, Any, Optional, Set

from ..metadata_store.interface import MetadataStoreInterface
from ..models.content import Document
from ..models.metadata import DocumentMetadata


class QueryInterface:
    """Interface for querying the knowledge base.
    
    This component provides methods for querying the knowledge base
    based on various criteria.
    """
    
    def __init__(self, metadata_store: MetadataStoreInterface):
        """Initialize the QueryInterface.
        
        Args:
            metadata_store: The metadata store to query
        """
        self.metadata_store = metadata_store
    
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