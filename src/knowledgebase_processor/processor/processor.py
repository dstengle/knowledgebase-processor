"""Processor implementation for processing knowledge base content."""

from pathlib import Path
from typing import Optional

from rdflib import Graph

from ..analyzer.entity_recognizer import EntityRecognizer
from ..reader.reader import Reader
from ..metadata_store.interface import MetadataStoreInterface
from ..utils.document_registry import DocumentRegistry
from ..utils.id_generator import EntityIdGenerator
from ..utils.logging import get_logger

from .document_processor import DocumentProcessor
from .entity_processor import EntityProcessor
from .rdf_processor import RdfProcessor
from .pipeline_orchestrator import ProcessingPipeline


logger = get_logger("knowledgebase_processor.processor.main")


class Processor:
    """Main processor that orchestrates document processing using modular components."""

    def __init__(
        self,
        document_registry: DocumentRegistry,
        id_generator: EntityIdGenerator,
        config=None,
    ):
        """Initialize the Processor with modular components.
        
        Args:
            document_registry: Registry for document management
            id_generator: Generator for entity IDs
            config: Optional configuration object
        """
        self.config = config
        
        # Initialize component processors
        self.document_processor = DocumentProcessor(document_registry, id_generator)
        self.entity_processor = EntityProcessor(document_registry, id_generator)
        self.rdf_processor = RdfProcessor()
        
        # Create processing pipeline
        self.pipeline = ProcessingPipeline(
            self.document_processor,
            self.entity_processor,
            self.rdf_processor
        )
        
        # Initialize analyzers based on config
        analyze_entities = (
            config.analyze_entities 
            if config and hasattr(config, "analyze_entities") 
            else False
        )
        if analyze_entities:
            self.entity_processor.register_analyzer(EntityRecognizer(enabled=True))

    def register_extractor(self, extractor):
        """Register an extractor component."""
        self.entity_processor.register_extractor(extractor)

    def register_analyzer(self, analyzer):
        """Register an analyzer component."""
        self.entity_processor.register_analyzer(analyzer)

    def register_enricher(self, enricher):
        """Register an enricher component (for future use)."""
        # For now, just log that enrichers aren't fully implemented
        logger.debug(f"Enricher {type(enricher).__name__} registered but not yet integrated")

    def _create_and_register_document_entity(
        self,
        doc_path: str,
        knowledge_base_path: Path,
        document: Optional["Document"] = None
    ) -> Optional["KbDocument"]:
        """Creates a KbDocument entity and registers it.
        
        This method is kept for backward compatibility but delegates to DocumentProcessor.
        """
        kb_document = self.document_processor.create_document_entity(
            doc_path,
            knowledge_base_path,
            document
        )
        if kb_document:
            self.document_processor.register_document(kb_document)
        return kb_document

    def process_and_generate_rdf(
        self,
        reader: Reader,
        metadata_store: MetadataStoreInterface,
        pattern: str,
        knowledge_base_path: Path,
        rdf_output_dir_str: Optional[str] = None,
    ) -> int:
        """Processes all documents, builds a registry, extracts entities, and generates RDF.
        
        This method has been refactored to use the modular pipeline architecture.
        """
        logger.info(f"Starting processing with knowledge base path: {knowledge_base_path}")
        
        # Convert rdf_output_dir_str to Path if provided
        rdf_output_dir = Path(rdf_output_dir_str) if rdf_output_dir_str else None
        
        # Use the pipeline to process documents
        stats = self.pipeline.process_documents_batch(
            reader=reader,
            metadata_store=metadata_store,
            pattern=pattern,
            knowledge_base_path=knowledge_base_path,
            rdf_output_dir=rdf_output_dir
        )
        
        # Log final statistics
        logger.info(f"Processing completed: {stats}")
        
        # Return 0 for success (maintaining backward compatibility)
        return 0 if stats.processing_errors == 0 else 1

    def process_content_to_graph(
        self,
        content: str,
        document_id: Optional[str] = None
    ) -> Graph:
        """Processes markdown content string directly into an RDF graph.
        
        This method has been refactored to use the modular pipeline architecture.
        
        Args:
            content: The markdown content string to process
            document_id: Optional document ID (generates one if not provided)
            
        Returns:
            rdflib.Graph: The generated RDF graph containing entities from the content
        """
        return self.pipeline.process_content_to_graph(content, document_id)

    def _extracted_entity_to_kb_entity(
        self,
        extracted_entity: "ModelExtractedEntity",
        source_doc_path: str,
    ) -> Optional["KbBaseEntity"]:
        """Transforms an ExtractedEntity to a corresponding KbBaseEntity subclass instance.
        
        This method is kept for backward compatibility but delegates to EntityProcessor.
        """
        return self.entity_processor.convert_extracted_entity(
            extracted_entity,
            source_doc_path
        )
    
    def _update_document_title_from_frontmatter(self, document: "Document") -> None:
        """Update document title from frontmatter.
        
        This method is kept for backward compatibility with existing tests.
        In the refactored architecture, title handling is done during document creation.
        """
        from pathlib import Path
        
        # Look for frontmatter elements with title information
        for element in document.elements:
            if hasattr(element, 'element_type') and element.element_type == "frontmatter":
                # Try to parse frontmatter for title using element processor's extractors
                extractors = self.entity_processor.element_processor.extractors
                for extractor in extractors:
                    if hasattr(extractor, 'parse_frontmatter'):
                        frontmatter_dict = extractor.parse_frontmatter(element.content)
                        if frontmatter_dict and 'title' in frontmatter_dict:
                            document.title = frontmatter_dict['title']
                            return
        
        # Fallback to filename if no title found in frontmatter
        if not document.title:
            document.title = Path(document.path).stem.replace("_", " ").replace("-", " ")
