"""Named entity processing module for handling NER entity extraction and conversion."""

from typing import List, Optional, Dict, Type

from ..models.content import Document
from ..models.metadata import DocumentMetadata, ExtractedEntity as ModelExtractedEntity
from ..models.kb_entities import (
    KbBaseEntity,
    KbPerson,
    KbOrganization,
    KbLocation,
    KbDateEntity,
)
from ..utils.document_registry import DocumentRegistry
from ..utils.id_generator import EntityIdGenerator
from ..utils.logging import get_logger


logger = get_logger("knowledgebase_processor.processor.named_entity")


class NamedEntityProcessor:
    """Handles named entity recognition (NER) and conversion to KB entities."""
    
    # Mapping from NER labels to KB entity classes
    ENTITY_TYPE_MAPPING: Dict[str, Type[KbBaseEntity]] = {
        'PERSON': KbPerson,
        'ORG': KbOrganization,
        'LOC': KbLocation,
        'GPE': KbLocation,  # Geopolitical entities treated as locations
        'DATE': KbDateEntity,
    }
    
    def __init__(
        self,
        document_registry: DocumentRegistry,
        id_generator: EntityIdGenerator
    ):
        """Initialize NamedEntityProcessor with required dependencies.
        
        Args:
            document_registry: Registry for document management
            id_generator: Generator for entity IDs
        """
        self.document_registry = document_registry
        self.id_generator = id_generator
        self.analyzers = []
    
    def register_analyzer(self, analyzer):
        """Register a named entity analyzer.
        
        Args:
            analyzer: NER analyzer to register
        """
        self.analyzers.append(analyzer)
        logger.debug(f"Registered NER analyzer: {type(analyzer).__name__}")
    
    def analyze_document_for_entities(
        self,
        document: Document,
        doc_metadata: DocumentMetadata
    ) -> List[ModelExtractedEntity]:
        """Analyze document content for named entities.
        
        Args:
            document: Document to analyze
            doc_metadata: Document metadata to update with entities
            
        Returns:
            List of extracted entities from analyzers
        """
        extracted_entities = []
        
        for analyzer in self.analyzers:
            if hasattr(analyzer, 'analyze'):
                try:
                    # Clear existing entities to avoid duplicates
                    original_entities = doc_metadata.entities.copy()
                    doc_metadata.entities.clear()
                    
                    # Run analysis
                    analyzer.analyze(document.content, doc_metadata)
                    
                    # Collect new entities
                    new_entities = doc_metadata.entities.copy()
                    extracted_entities.extend(new_entities)
                    
                    # Restore original entities plus new ones
                    doc_metadata.entities = original_entities + new_entities
                    
                    logger.debug(
                        f"Analyzer {type(analyzer).__name__} found {len(new_entities)} entities"
                    )
                    
                except Exception as e:
                    logger.error(f"Error during entity analysis: {e}", exc_info=True)
        
        logger.info(f"Found {len(extracted_entities)} named entities in document")
        return extracted_entities
    
    def convert_extracted_entities(
        self,
        extracted_entities: List[ModelExtractedEntity],
        source_doc_path: str
    ) -> List[KbBaseEntity]:
        """Convert extracted entities to KB entities.
        
        Args:
            extracted_entities: Entities extracted by NER analyzers
            source_doc_path: Path to source document
            
        Returns:
            List of KB entities
        """
        kb_entities = []
        
        for extracted_entity in extracted_entities:
            kb_entity = self._convert_single_entity(extracted_entity, source_doc_path)
            if kb_entity:
                kb_entities.append(kb_entity)
        
        logger.debug(f"Converted {len(kb_entities)} extracted entities to KB entities")
        return kb_entities
    
    def _convert_single_entity(
        self,
        extracted_entity: ModelExtractedEntity,
        source_doc_path: str
    ) -> Optional[KbBaseEntity]:
        """Convert a single extracted entity to a KB entity.
        
        Args:
            extracted_entity: Entity extracted by NER analyzer
            source_doc_path: Path to source document
            
        Returns:
            Appropriate KbBaseEntity subclass or None if conversion fails
        """
        # Find source document
        kb_document = self.document_registry.find_document_by_path(source_doc_path)
        if not kb_document:
            logger.warning(f"Could not find document for path: {source_doc_path}")
            return None
        
        # Prepare common arguments
        common_args = {
            "label": extracted_entity.text,
            "source_document_uri": kb_document.kb_id,
            "extracted_from_text_span": (
                extracted_entity.start_char,
                extracted_entity.end_char,
            ),
        }
        
        # Determine entity type and create appropriate KB entity
        entity_label_upper = extracted_entity.label.upper()
        text = extracted_entity.text
        
        # Generate ID for the entity
        entity_id = self.id_generator.generate_wikilink_id(
            kb_document.kb_id,
            f"{entity_label_upper}-{text}"
        )
        
        # Get entity class from mapping
        entity_class = self.ENTITY_TYPE_MAPPING.get(entity_label_upper)
        if not entity_class:
            logger.debug(f"Unhandled entity type: {extracted_entity.label} for text: '{text}'")
            return None
        
        # Create entity with type-specific arguments
        try:
            if entity_class == KbPerson:
                return entity_class(kb_id=entity_id, full_name=text, **common_args)
            elif entity_class == KbOrganization:
                return entity_class(kb_id=entity_id, name=text, **common_args)
            elif entity_class == KbLocation:
                return entity_class(kb_id=entity_id, name=text, **common_args)
            elif entity_class == KbDateEntity:
                return entity_class(kb_id=entity_id, date_value=text, **common_args)
            else:
                # Fallback for other entity types
                return entity_class(kb_id=entity_id, **common_args)
                
        except Exception as e:
            logger.error(f"Failed to create KB entity for {extracted_entity.label}: {e}")
            return None
    
    def group_entities_by_type(
        self,
        entities: List[KbBaseEntity]
    ) -> Dict[str, List[KbBaseEntity]]:
        """Group entities by their type.
        
        Args:
            entities: List of KB entities to group
            
        Returns:
            Dictionary mapping entity type names to lists of entities
        """
        grouped = {}
        
        for entity in entities:
            entity_type = type(entity).__name__
            if entity_type not in grouped:
                grouped[entity_type] = []
            grouped[entity_type].append(entity)
        
        return grouped
    
    def get_entity_statistics(
        self,
        entities: List[KbBaseEntity]
    ) -> Dict[str, int]:
        """Get statistics about named entities by type.
        
        Args:
            entities: List of entities to analyze
            
        Returns:
            Dictionary with counts by entity type
        """
        stats = {}
        grouped = self.group_entities_by_type(entities)
        
        for entity_type, entity_list in grouped.items():
            stats[entity_type] = len(entity_list)
        
        stats['total'] = len(entities)
        return stats
    
    def filter_entities_by_confidence(
        self,
        entities: List[KbBaseEntity],
        min_confidence: float = 0.8
    ) -> List[KbBaseEntity]:
        """Filter entities by confidence score if available.
        
        Args:
            entities: List of entities to filter
            min_confidence: Minimum confidence threshold
            
        Returns:
            Filtered list of high-confidence entities
        """
        # Note: This method assumes entities have a confidence attribute
        # In the current implementation, confidence is not stored in KB entities
        # This is a placeholder for future enhancement
        
        filtered = []
        for entity in entities:
            if hasattr(entity, 'confidence'):
                if entity.confidence >= min_confidence:
                    filtered.append(entity)
            else:
                # If no confidence available, include all entities
                filtered.append(entity)
        
        logger.debug(f"Filtered {len(entities)} entities to {len(filtered)} high-confidence entities")
        return filtered