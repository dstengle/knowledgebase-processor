"""Entity processing orchestrator that coordinates specialized processors."""

from typing import List

from ..models.content import Document
from ..models.metadata import DocumentMetadata, ExtractedEntity as ModelExtractedEntity
from ..models.kb_entities import KbBaseEntity, KbDocument
from ..utils.document_registry import DocumentRegistry
from ..utils.id_generator import EntityIdGenerator
from ..utils.logging import get_logger

from .todo_processor import TodoProcessor
from .wikilink_processor import WikilinkProcessor
from .named_entity_processor import NamedEntityProcessor
from .element_extraction_processor import ElementExtractionProcessor
from .metadata_processor import MetadataProcessor


logger = get_logger("knowledgebase_processor.processor.entity")


class EntityProcessor:
    """Orchestrates entity extraction and conversion using specialized processors."""
    
    def __init__(
        self,
        document_registry: DocumentRegistry,
        id_generator: EntityIdGenerator
    ):
        """Initialize EntityProcessor with specialized processors."""
        self.document_registry = document_registry
        self.id_generator = id_generator
        
        # Initialize specialized processors
        self.todo_processor = TodoProcessor(id_generator)
        self.wikilink_processor = WikilinkProcessor(document_registry, id_generator)
        self.named_entity_processor = NamedEntityProcessor(document_registry, id_generator)
        self.element_processor = ElementExtractionProcessor()
        self.metadata_processor = MetadataProcessor()
    
    def register_extractor(self, extractor):
        """Register an extractor component."""
        self.element_processor.register_extractor(extractor)
    
    def register_analyzer(self, analyzer):
        """Register an analyzer component."""
        self.named_entity_processor.register_analyzer(analyzer)
    
    def extract_elements(
        self,
        document: Document,
        doc_metadata: DocumentMetadata
    ) -> List:
        """Extract elements from document using element processor.
        
        Args:
            document: Document to extract from
            doc_metadata: Document metadata to update
            
        Returns:
            List of extracted elements
        """
        return self.element_processor.extract_all_elements(document, doc_metadata)
    
    def extract_wikilinks(
        self,
        document: Document,
        document_id: str
    ) -> List:
        """Extract wikilinks using specialized processor.
        
        Args:
            document: Document to extract from
            document_id: ID of the source document
            
        Returns:
            List of KbWikiLink entities
        """
        return self.wikilink_processor.extract_wikilinks(document, document_id)
    
    def extract_todos_as_entities(
        self,
        document: Document,
        document_id: str
    ) -> List:
        """Extract todos using specialized processor.
        
        Args:
            document: Document to extract from
            document_id: ID of source document
            
        Returns:
            List of KbTodoItem entities
        """
        return self.todo_processor.extract_todos_from_elements(document.elements, document_id)
    
    def analyze_document(
        self,
        document: Document,
        doc_metadata: DocumentMetadata
    ) -> List[ModelExtractedEntity]:
        """Analyze document using named entity processor.
        
        Args:
            document: Document to analyze
            doc_metadata: Document metadata to update
            
        Returns:
            List of extracted entities from analyzers
        """
        return self.named_entity_processor.analyze_document_for_entities(document, doc_metadata)
    
    def convert_extracted_entity(
        self,
        extracted_entity: ModelExtractedEntity,
        source_doc_path: str
    ) -> KbBaseEntity:
        """Convert single extracted entity using named entity processor.
        
        Args:
            extracted_entity: Entity extracted by analyzers
            source_doc_path: Path to source document
            
        Returns:
            KbBaseEntity or None if conversion fails
        """
        converted_entities = self.named_entity_processor.convert_extracted_entities(
            [extracted_entity], 
            source_doc_path
        )
        return converted_entities[0] if converted_entities else None
    
    def process_document_entities(
        self,
        document: Document,
        kb_document: KbDocument,
        doc_metadata: DocumentMetadata
    ) -> List[KbBaseEntity]:
        """Process all entities from a document using specialized processors.
        
        Args:
            document: Document to process
            kb_document: KB document entity
            doc_metadata: Document metadata
            
        Returns:
            List of all extracted KB entities
        """
        all_entities: List[KbBaseEntity] = [kb_document]
        
        # Enhance metadata using metadata processor
        doc_metadata = self.metadata_processor.create_document_metadata(document, kb_document)
        
        # Extract elements using element processor
        self.extract_elements(document, doc_metadata)
        
        # Extract wikilinks using wikilink processor
        wikilinks = self.extract_wikilinks(document, kb_document.kb_id)
        all_entities.extend(wikilinks)
        
        # Extract todos using todo processor
        todos = self.extract_todos_as_entities(document, kb_document.kb_id)
        all_entities.extend(todos)
        
        # Analyze document for named entities using named entity processor
        extracted_entities = self.analyze_document(document, doc_metadata)
        kb_entities = self.named_entity_processor.convert_extracted_entities(
            extracted_entities,
            kb_document.original_path
        )
        all_entities.extend(kb_entities)
        
        logger.info(f"Processed {len(all_entities)} entities from document {kb_document.original_path}")
        return all_entities
    
    # Convenience methods to access specialized processor functionality
    
    def get_todo_statistics(self, todo_entities):
        """Get todo statistics using todo processor."""
        return self.todo_processor.get_todo_statistics(todo_entities)
    
    def get_wikilink_statistics(self, wikilink_entities):
        """Get wikilink statistics using wikilink processor."""
        return self.wikilink_processor.get_wikilink_statistics(wikilink_entities)
    
    def get_named_entity_statistics(self, named_entities):
        """Get named entity statistics using named entity processor."""
        return self.named_entity_processor.get_entity_statistics(named_entities)
    
    def validate_metadata(self, doc_metadata):
        """Validate metadata using metadata processor."""
        return self.metadata_processor.validate_metadata(doc_metadata)
    
    def get_extraction_summary(self, document):
        """Get extraction summary using element processor."""
        return self.element_processor.get_extraction_summary(document)