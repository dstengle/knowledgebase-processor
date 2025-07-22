"""Unified API for all knowledge base operations.

This module provides a facade pattern implementation that acts as a single entry point
for all knowledge base operations, delegating to the appropriate service classes.
"""

from pathlib import Path
from typing import Any, List, Optional, Dict

from .config.config import Config
from .main import KnowledgeBaseProcessor
from .services.entity_service import EntityService
from .services.sparql_service import SparqlService
from .services.processing_service import ProcessingService
from .models.entities import ExtractedEntity
from .models.kb_entities import KbBaseEntity
from .models.content import Document
from .models.metadata import DocumentMetadata
from .utils.logging import get_logger


class KnowledgeBaseAPI:
    """Unified API for all knowledge base operations.
    
    This class acts as a facade that provides a simplified interface to all
    knowledge base functionality by coordinating between service classes.
    """
    
    def __init__(self, config: Config):
        """Initialize the KnowledgeBaseAPI.
        
        Args:
            config: Configuration object containing settings for all services
        """
        self.config = config
        self.logger = get_logger("knowledgebase_processor.api")
        
        # Initialize the main knowledge base processor
        self.kb_processor = KnowledgeBaseProcessor(
            knowledge_base_dir=config.knowledge_base_path,
            metadata_store_path=config.metadata_store_path,
            metadata_store_backend="sqlite",
            config=config
        )
        
        # Initialize service classes
        self.entity_service = EntityService()
        self.sparql_service = SparqlService(config)
        self.processing_service = ProcessingService(
            processor=self.kb_processor.processor,
            reader=self.kb_processor.reader,
            metadata_store=self.kb_processor.metadata_store,
            config=config,
        )
        
        self.logger.info("KnowledgeBaseAPI initialized successfully")
    
    # Processing operations
    def process_documents(self, pattern: str, rdf_output_dir: Optional[Path] = None) -> int:
        """Process documents matching the given pattern.
        
        Args:
            pattern: File pattern to match (e.g., "**/*.md")
            rdf_output_dir: Optional directory to save RDF output files
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        return self.processing_service.process_documents(
            pattern=pattern,
            knowledge_base_path=Path(self.config.knowledge_base_path),
            rdf_output_dir=rdf_output_dir,
        )
    
    def process_single_document(self, file_path: Path) -> Document:
        """Process a single document.
        
        Args:
            file_path: Path to the document to process
            
        Returns:
            Processed document
        """
        # This method is no longer directly supported by the refactored processor.
        # It would require a different processing flow.
        # For now, we can raise a NotImplementedError.
        raise NotImplementedError("Processing a single document is not supported in this version.")
    
    # Query operations
    def query(self, query_string: str, query_type: str = "text") -> List[Any]:
        """Execute a query against the knowledge base.
        
        Args:
            query_string: The query string to search for
            query_type: Type of query ("text", "tag", "topic")
            
        Returns:
            List of matching results
        """
        # This method is also affected by the refactoring.
        # The query logic needs to be re-evaluated.
        raise NotImplementedError("Querying is not supported in this version.")
    
    def search(self, query: str) -> List[str]:
        """Search for documents matching a text query.
        
        Args:
            query: The search query
            
        Returns:
            List of matching document IDs
        """
        return self.kb_processor.search(query)
    
    def find_by_tag(self, tag: str) -> List[str]:
        """Find documents with a specific tag.
        
        Args:
            tag: The tag to search for
            
        Returns:
            List of document IDs with the specified tag
        """
        return self.kb_processor.find_by_tag(tag)
    
    def find_by_topic(self, topic: str) -> List[str]:
        """Find documents related to a specific topic.
        
        Args:
            topic: The topic to search for
            
        Returns:
            List of document IDs related to the specified topic
        """
        return self.kb_processor.find_by_topic(topic)
    
    def find_related(self, document_id: str) -> List[Dict[str, Any]]:
        """Find documents related to a specific document.
        
        Args:
            document_id: ID of the document to find relations for
            
        Returns:
            List of dictionaries with related document information
        """
        return self.kb_processor.find_related(document_id)
    
    # SPARQL operations
    def sparql_query(self, query: str, endpoint_url: Optional[str] = None,
                    timeout: int = 30, format: str = "json") -> Any:
        """Execute a SPARQL query.
        
        Args:
            query: SPARQL query string
            endpoint_url: SPARQL endpoint URL (overrides config if provided)
            timeout: Query timeout in seconds
            format: Output format ("json", "table", "turtle")
            
        Returns:
            Query results in the requested format
        """
        return self.sparql_service.execute_query(
            query=query,
            endpoint_url=endpoint_url,
            timeout=timeout,
            format=format
        )
    
    def sparql_load(self, file_path: Path, graph_uri: Optional[str] = None,
                   endpoint_url: Optional[str] = None, update_endpoint_url: Optional[str] = None,
                   username: Optional[str] = None, password: Optional[str] = None,
                   rdf_format: str = "turtle") -> None:
        """Load RDF file into SPARQL store.
        
        Args:
            file_path: Path to the RDF file to load
            graph_uri: Named graph URI to load data into
            endpoint_url: SPARQL endpoint URL (overrides config if provided)
            update_endpoint_url: SPARQL update endpoint URL (overrides config if provided)
            username: Username for authentication
            password: Password for authentication
            rdf_format: Format of the RDF file
        """
        self.sparql_service.load_rdf_file(
            file_path=file_path,
            graph_uri=graph_uri,
            endpoint_url=endpoint_url,
            update_endpoint_url=update_endpoint_url,
            username=username,
            password=password,
            rdf_format=rdf_format
        )
    
    # Entity operations
    def generate_kb_id(self, entity_type: str, text: str) -> str:
        """Generate a unique knowledge base ID for an entity.
        
        Args:
            entity_type: The type of entity (e.g., "Person", "Organization")
            text: The text content of the entity
            
        Returns:
            A unique URI for the entity
        """
        return self.entity_service.generate_kb_id(entity_type, text)
    
    def transform_to_kb_entity(self, extracted_entity: ExtractedEntity,
                              source_doc_relative_path: str) -> Optional[KbBaseEntity]:
        """Transform an ExtractedEntity to a KbBaseEntity.
        
        Args:
            extracted_entity: The extracted entity to transform
            source_doc_relative_path: Relative path to the source document
            
        Returns:
            A KbBaseEntity instance or None if the entity type is not handled
        """
        return self.entity_service.transform_to_kb_entity(
            extracted_entity=extracted_entity,
            source_doc_relative_path=source_doc_relative_path
        )
    
    # Metadata operations
    def get_metadata(self, document_id: str) -> Optional[DocumentMetadata]:
        """Get metadata for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Metadata object if found, None otherwise
        """
        return self.kb_processor.get_metadata(document_id)
    
    # Convenience methods for common operations
    def process_all(self, pattern: str = "**/*.md") -> int:
        """Process all files matching the pattern."""
        return self.kb_processor.process_all(pattern)
    
    def process_file(self, file_path: str) -> Document:
        """Process a single file using the main processor.
        
        Args:
            file_path: Path to the file to process (relative to base_path)
            
        Returns:
            Processed document
        """
        raise NotImplementedError("process_file is no longer supported, use process_all.")