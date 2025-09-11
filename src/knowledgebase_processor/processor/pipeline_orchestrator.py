"""Pipeline orchestrator for coordinating document processing pipeline."""

from pathlib import Path
from typing import Optional, List, Tuple
import os

from rdflib import Graph

from ..models.content import Document
from ..models.metadata import DocumentMetadata
from ..models.kb_entities import KbDocument
from ..reader.reader import Reader
from ..metadata_store.interface import MetadataStoreInterface
from ..utils.logging import get_logger

from .document_processor import DocumentProcessor
from .entity_processor import EntityProcessor
from .rdf_processor import RdfProcessor


logger = get_logger("knowledgebase_processor.processor.pipeline")


class ProcessingStats:
    """Statistics for document processing operations."""
    
    def __init__(self):
        """Initialize processing statistics."""
        self.total_documents = 0
        self.processed_successfully = 0
        self.processing_errors = 0
        self.rdf_generated = 0
    
    def __str__(self) -> str:
        """String representation of statistics."""
        return (
            f"Processing Statistics:\n"
            f"  Total documents: {self.total_documents}\n"
            f"  Processed successfully: {self.processed_successfully}\n"
            f"  Processing errors: {self.processing_errors}\n"
            f"  RDF files generated: {self.rdf_generated}"
        )


class ProcessingPipeline:
    """Orchestrates the document processing pipeline."""
    
    def __init__(
        self,
        document_processor: DocumentProcessor,
        entity_processor: EntityProcessor,
        rdf_processor: Optional[RdfProcessor] = None
    ):
        """Initialize ProcessingPipeline with component processors.
        
        Args:
            document_processor: Handles document operations
            entity_processor: Handles entity extraction
            rdf_processor: Handles RDF generation (optional)
        """
        self.document_processor = document_processor
        self.entity_processor = entity_processor
        self.rdf_processor = rdf_processor
    
    def process_single_document(
        self,
        document: Document,
        kb_document: KbDocument,
        metadata_store: Optional[MetadataStoreInterface] = None
    ) -> Tuple[List, DocumentMetadata]:
        """Process a single document through the pipeline.
        
        Args:
            document: Document to process
            kb_document: KB document entity
            metadata_store: Optional metadata store for saving
            
        Returns:
            Tuple of (entities list, document metadata)
        """
        # Create or use existing metadata
        doc_metadata = document.metadata or DocumentMetadata(
            document_id=kb_document.kb_id,
            path=kb_document.original_path,
            title=kb_document.label
        )
        
        # Update metadata with KB document info
        doc_metadata.document_id = kb_document.kb_id
        doc_metadata.path = kb_document.original_path
        
        # Process entities
        all_entities = self.entity_processor.process_document_entities(
            document,
            kb_document,
            doc_metadata
        )
        
        # Save metadata if store provided
        if metadata_store:
            metadata_store.save(doc_metadata)
        
        return all_entities, doc_metadata
    
    def process_documents_batch(
        self,
        reader: Reader,
        metadata_store: MetadataStoreInterface,
        pattern: str,
        knowledge_base_path: Path,
        rdf_output_dir: Optional[Path] = None
    ) -> ProcessingStats:
        """Process a batch of documents matching pattern.
        
        Args:
            reader: Reader for file operations
            metadata_store: Store for document metadata
            pattern: File pattern to match
            knowledge_base_path: Base path of knowledge base
            rdf_output_dir: Optional directory for RDF output
            
        Returns:
            ProcessingStats with results
        """
        stats = ProcessingStats()
        
        # Phase 1: Read and register all documents
        logger.info("Phase 1: Reading and registering documents")
        documents_data = self.document_processor.read_and_register_documents(
            reader,
            pattern,
            knowledge_base_path
        )
        stats.total_documents = len(documents_data)
        
        # Setup RDF output if specified
        if rdf_output_dir and self.rdf_processor:
            rdf_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Phase 2: Process each document
        logger.info("Phase 2: Processing documents for entities and RDF")
        for doc_path, document, kb_document in documents_data:
            try:
                # Process document
                entities, doc_metadata = self.process_single_document(
                    document,
                    kb_document,
                    metadata_store
                )
                
                # Generate RDF if configured
                if rdf_output_dir and self.rdf_processor:
                    success = self.rdf_processor.process_document_to_rdf(
                        entities,
                        rdf_output_dir,
                        kb_document.original_path
                    )
                    if success:
                        stats.rdf_generated += 1
                
                stats.processed_successfully += 1
                
            except Exception as e:
                logger.error(f"Failed to process document {doc_path}: {e}", exc_info=True)
                stats.processing_errors += 1
        
        return stats
    
    def process_content_to_graph(
        self,
        content: str,
        document_id: Optional[str] = None
    ) -> Graph:
        """Process markdown content directly into an RDF graph.
        
        Args:
            content: Markdown content string
            document_id: Optional document ID
            
        Returns:
            RDF graph containing entities from content
        """
        # Generate document ID if not provided
        if not document_id:
            doc_id = self.document_processor.id_generator.generate_document_id("temp_document.md")
        else:
            doc_id = document_id
        
        # Create temporary document
        document = Document(
            path="temp_document.md",
            title="Temporary Document",
            content=content
        )
        
        # Create temporary KB document
        temp_kb_document = KbDocument(
            kb_id=doc_id,
            label="Temporary Document",
            original_path="temp_document.md",
            path_without_extension="temp_document",
            source_document_uri=doc_id,
        )
        
        # Save current registry state
        original_documents = self.document_processor.get_all_documents().copy()
        
        try:
            # Temporarily register the document
            self.document_processor.register_document(temp_kb_document)
            
            # Process document
            entities, _ = self.process_single_document(
                document,
                temp_kb_document
            )
            
            # Convert to RDF graph
            if self.rdf_processor:
                graph = self.rdf_processor.entities_to_graph(entities)
            else:
                # Create minimal RDF processor if not provided
                from .rdf_processor import RdfProcessor
                temp_rdf = RdfProcessor()
                graph = temp_rdf.entities_to_graph(entities)
            
            logger.info(f"Generated RDF graph with {len(graph)} triples from content")
            return graph
            
        finally:
            # Restore original registry state
            self._restore_registry(original_documents)
    
    def _restore_registry(self, original_documents: List[KbDocument]) -> None:
        """Restore document registry to original state.
        
        Args:
            original_documents: Original list of documents to restore
        """
        # Clear current state
        registry = self.document_processor.document_registry
        registry._documents_by_id.clear()
        registry._id_by_original_path.clear()
        registry._id_by_path_without_extension.clear()
        registry._id_by_basename_without_extension.clear()
        
        # Restore original documents
        for doc in original_documents:
            self.document_processor.register_document(doc)