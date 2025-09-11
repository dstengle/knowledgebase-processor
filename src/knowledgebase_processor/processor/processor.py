"""Processor implementation for processing knowledge base content."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, cast

from rdflib import Graph
from rdflib.namespace import SDO as SCHEMA, RDFS, XSD

from ..models.content import Document
from ..models.markdown import TodoItem
from ..models.metadata import DocumentMetadata, ExtractedEntity as ModelExtractedEntity
from ..models.kb_entities import (
    KbBaseEntity,
    KbPerson,
    KbOrganization,
    KbLocation,
    KbDateEntity,
    KbTodoItem,
    KbDocument,
    KbWikiLink,
    KB,
)
from ..analyzer.entity_recognizer import EntityRecognizer
from ..rdf_converter import RdfConverter
from ..reader.reader import Reader
from ..metadata_store.interface import MetadataStoreInterface
from ..utils.document_registry import DocumentRegistry
from ..utils.id_generator import EntityIdGenerator
from ..utils.logging import get_logger


logger_processor_rdf = get_logger("knowledgebase_processor.processor.rdf")


class Processor:
    """Processor component for processing knowledge base content."""

    def __init__(
        self,
        document_registry: DocumentRegistry,
        id_generator: EntityIdGenerator,
        config=None,
    ):
        """Initialize the Processor."""
        self.config = config
        self.document_registry = document_registry
        self.id_generator = id_generator
        self.extractors = []
        self.analyzers = []
        self.enrichers = []

        analyze_entities = config.analyze_entities if config and hasattr(config, "analyze_entities") else False
        if analyze_entities:
            self.analyzers.append(EntityRecognizer(enabled=True))

    def register_extractor(self, extractor):
        """Register an extractor component."""
        self.extractors.append(extractor)

    def register_analyzer(self, analyzer):
        """Register an analyzer component."""
        self.analyzers.append(analyzer)

    def register_enricher(self, enricher):
        """Register an enricher component."""
        self.enrichers.append(enricher)

    def _create_and_register_document_entity(self, doc_path: str, knowledge_base_path: Path, document: Optional[Document] = None) -> Optional[KbDocument]:
        """Creates a KbDocument entity and registers it."""
        try:
            original_path = os.path.relpath(doc_path, knowledge_base_path)
            normalized_path = original_path.replace("\\", "/")
            path_without_extension, _ = os.path.splitext(normalized_path)

            doc_id = self.id_generator.generate_document_id(normalized_path)
            
            # Use title from document metadata if available, otherwise fall back to filename
            if document and document.title:
                label = document.title
            else:
                label = Path(original_path).stem.replace("_", " ").replace("-", " ")

            document_entity = KbDocument(
                kb_id=doc_id,
                label=label,
                original_path=original_path,
                path_without_extension=path_without_extension,
                source_document_uri=doc_id,
            )
            self.document_registry.register_document(document_entity)
            return document_entity
        except Exception as e:
            logger_processor_rdf.error(f"Failed to create document entity for {doc_path}: {e}", exc_info=True)
            return None

    def process_and_generate_rdf(
        self,
        reader: Reader,
        metadata_store: MetadataStoreInterface,
        pattern: str,
        knowledge_base_path: Path,
        rdf_output_dir_str: Optional[str] = None,
    ) -> int:
        """Processes all documents, builds a registry, extracts entities, and generates RDF."""
        from ..extractor.wikilink_extractor import WikiLinkExtractor
        logger_proc_rdf = get_logger("knowledgebase_processor.processor.rdf_process")
        logger_proc_rdf.info(f"Starting processing with knowledge base path: {knowledge_base_path}")

        # --- Phase 1: Read all documents with frontmatter parsing and build the registry ---
        documents = []
        for file_path in reader.read_all_paths(pattern):
            document = reader.read_file(file_path)  # This parses frontmatter
            documents.append((str(file_path), document))
            # Create and register document entity with proper title
            self._create_and_register_document_entity(str(file_path), knowledge_base_path, document)
        logger_proc_rdf.info(f"Registered {len(self.document_registry.get_all_documents())} documents.")

        # --- Phase 2: Process each document for entities and RDF generation ---
        rdf_converter = RdfConverter() if rdf_output_dir_str else None
        rdf_output_path = Path(rdf_output_dir_str) if rdf_output_dir_str else None
        if rdf_output_path:
            rdf_output_path.mkdir(parents=True, exist_ok=True)

        processed_docs_count = 0
        for doc_path_str, document in documents:
            try:
                
                kb_document = self.document_registry.find_document_by_path(
                    os.path.relpath(doc_path_str, knowledge_base_path).replace("\\", "/")
                )
                if not kb_document:
                    logger_proc_rdf.warning(f"Could not find registered document for path: {doc_path_str}. Skipping.")
                    continue

                # Run extractors to get elements
                all_entities: List[KbBaseEntity] = [kb_document]
                
                # Initialize WikiLinkExtractor here, as it needs the populated registry
                wikilink_extractor = WikiLinkExtractor(self.document_registry, self.id_generator)

                # Use metadata from document with updated document ID
                doc_metadata = document.metadata or DocumentMetadata(
                    document_id=kb_document.kb_id, 
                    path=kb_document.original_path, 
                    title=kb_document.label
                )
                # Update the document ID to use the proper KB ID
                doc_metadata.document_id = kb_document.kb_id
                doc_metadata.path = kb_document.original_path

                for extractor in self.extractors:
                    elements = extractor.extract(document)
                    if elements:
                        document.elements.extend(elements)
                        if hasattr(extractor, "update_metadata"):
                            extractor.update_metadata(elements, doc_metadata)

                # Extract and resolve wikilinks
                wikilinks = wikilink_extractor.extract(document, kb_document.kb_id)
                all_entities.extend(wikilinks)

                # Extract and convert todo items to KB entities
                for element in document.elements:
                    if isinstance(element, TodoItem):
                        # Generate a stable, human-readable IRI for the todo
                        todo_id = self.id_generator.generate_todo_id(kb_document.kb_id, element.text)
                        
                        # Create KbTodoItem entity
                        kb_todo = KbTodoItem(
                            kb_id=todo_id,
                            label=element.text,
                            description=element.text,
                            is_completed=element.is_checked,
                            source_document_uri=kb_document.kb_id,
                            extracted_from_text_span=(
                                element.position.get("start", 0),
                                element.position.get("end", 0)
                            ) if element.position else None
                        )
                        all_entities.append(kb_todo)

                # Run analyzers for NER
                if self.analyzers:
                    for analyzer in self.analyzers:
                        if isinstance(analyzer, EntityRecognizer):
                            analyzer.analyze(document.content, doc_metadata)
                            for extracted_entity in doc_metadata.entities:
                                kb_entity = self._extracted_entity_to_kb_entity(extracted_entity, kb_document.original_path)
                                if kb_entity:
                                    all_entities.append(kb_entity)
                
                # Save metadata
                metadata_store.save(doc_metadata)

                # Generate RDF for all collected entities for this document
                if rdf_converter and rdf_output_path:
                    doc_graph = Graph()
                    doc_graph.bind("kb", KB)
                    doc_graph.bind("schema", SCHEMA)
                    doc_graph.bind("rdfs", RDFS)
                    doc_graph.bind("xsd", XSD)

                    for entity in all_entities:
                        entity_graph = rdf_converter.kb_entity_to_graph(entity, base_uri_str=str(KB))
                        doc_graph += entity_graph

                    if len(doc_graph) > 0:
                        output_filename = Path(kb_document.original_path).with_suffix(".ttl").name
                        output_file_path = rdf_output_path / output_filename
                        doc_graph.serialize(destination=str(output_file_path), format="turtle")
                        logger_proc_rdf.info(f"Saved RDF for {kb_document.original_path} to {output_file_path}")

                processed_docs_count += 1
            except Exception as e:
                logger_proc_rdf.error(f"Failed to process document {doc_path_str}: {e}", exc_info=True)

        logger_proc_rdf.info(f"Successfully processed {processed_docs_count} documents.")
        return 0

    def process_content_to_graph(self, content: str, document_id: Optional[str] = None) -> Graph:
        """Processes markdown content string directly into an RDF graph.
        
        This method provides a simplified interface for processing markdown content
        without requiring file I/O or external metadata stores.
        
        Args:
            content: The markdown content string to process
            document_id: Optional document ID (generates one if not provided)
            
        Returns:
            rdflib.Graph: The generated RDF graph containing entities from the content
        """
        logger_proc_content = get_logger("knowledgebase_processor.processor.content_to_graph")
        
        # Generate document ID if not provided
        if not document_id:
            document_id = self.id_generator.generate_document_id("temp_document.md")
        
        # Create a temporary Document object
        document = Document(
            path="temp_document.md",
            title="Temporary Document",
            content=content
        )
        
        # Create a temporary KbDocument entity for processing
        temp_kb_document = KbDocument(
            kb_id=document_id,
            label="Temporary Document",
            original_path="temp_document.md",
            path_without_extension="temp_document",
            source_document_uri=document_id,
        )
        
        # Temporarily register the document (will be cleaned up)
        original_documents = self.document_registry.get_all_documents().copy()
        self.document_registry.register_document(temp_kb_document)
        
        try:
            # Initialize RDF converter and graph
            rdf_converter = RdfConverter()
            graph = Graph()
            graph.bind("kb", KB)
            graph.bind("schema", SCHEMA)
            graph.bind("rdfs", RDFS)
            graph.bind("xsd", XSD)
            
            # Collect all entities for this document
            all_entities: List[KbBaseEntity] = [temp_kb_document]
            
            # Create metadata for the document
            doc_metadata = DocumentMetadata(
                document_id=document_id,
                path="temp_document.md",
                title="Temporary Document"
            )
            
            # Run extractors to get elements
            for extractor in self.extractors:
                elements = extractor.extract(document)
                if elements:
                    document.elements.extend(elements)
                    if hasattr(extractor, "update_metadata"):
                        extractor.update_metadata(elements, doc_metadata)
            
            # Extract and resolve wikilinks (if WikiLinkExtractor is available)
            try:
                from ..extractor.wikilink_extractor import WikiLinkExtractor
                wikilink_extractor = WikiLinkExtractor(self.document_registry, self.id_generator)
                wikilinks = wikilink_extractor.extract(document, document_id)
                all_entities.extend(wikilinks)
            except ImportError:
                logger_proc_content.debug("WikiLinkExtractor not available, skipping wikilink extraction")
            
            # Extract and convert todo items to KB entities
            for element in document.elements:
                if isinstance(element, TodoItem):
                    # Generate a stable ID for the todo
                    todo_id = self.id_generator.generate_todo_id(document_id, element.text)
                    
                    # Create KbTodoItem entity
                    kb_todo = KbTodoItem(
                        kb_id=todo_id,
                        label=element.text,
                        description=element.text,
                        is_completed=element.is_checked,
                        source_document_uri=document_id,
                        extracted_from_text_span=(
                            element.position.get("start", 0),
                            element.position.get("end", 0)
                        ) if element.position else None
                    )
                    all_entities.append(kb_todo)
            
            # Run analyzers for NER (if enabled)
            for analyzer in self.analyzers:
                if isinstance(analyzer, EntityRecognizer):
                    analyzer.analyze(document.content, doc_metadata)
                    for extracted_entity in doc_metadata.entities:
                        kb_entity = self._extracted_entity_to_kb_entity(extracted_entity, "temp_document.md")
                        if kb_entity:
                            all_entities.append(kb_entity)
            
            # Convert all entities to RDF and add to graph
            for entity in all_entities:
                entity_graph = rdf_converter.kb_entity_to_graph(entity, base_uri_str=str(KB))
                graph += entity_graph
            
            logger_proc_content.info(f"Generated RDF graph with {len(graph)} triples from content")
            return graph
            
        finally:
            # Clean up: restore original document registry state
            self.document_registry._documents_by_id.clear()
            self.document_registry._id_by_original_path.clear()
            self.document_registry._id_by_path_without_extension.clear()
            self.document_registry._id_by_basename_without_extension.clear()
            for original_doc in original_documents:
                self.document_registry.register_document(original_doc)

    def _extracted_entity_to_kb_entity(
        self,
        extracted_entity: ModelExtractedEntity,
        source_doc_path: str,
    ) -> Optional[KbBaseEntity]:
        """Transforms an ExtractedEntity to a corresponding KbBaseEntity subclass instance."""
        kb_document = self.document_registry.find_document_by_path(source_doc_path)
        if not kb_document:
            return None

        common_args = {
            "label": extracted_entity.text,
            "source_document_uri": kb_document.kb_id,
            "extracted_from_text_span": (
                extracted_entity.start_char,
                extracted_entity.end_char,
            ),
        }

        entity_label_upper = extracted_entity.label.upper()
        text = extracted_entity.text
        
        # This is a placeholder for a more robust ID generation for other entities
        temp_id = self.id_generator.generate_wikilink_id(kb_document.kb_id, f"{entity_label_upper}-{text}")

        if entity_label_upper == "PERSON":
            return KbPerson(kb_id=temp_id, full_name=text, **common_args)
        elif entity_label_upper == "ORG":
            return KbOrganization(kb_id=temp_id, name=text, **common_args)
        elif entity_label_upper in ["LOC", "GPE"]:
            return KbLocation(kb_id=temp_id, name=text, **common_args)
        elif entity_label_upper == "DATE":
            return KbDateEntity(kb_id=temp_id, date_value=text, **common_args)
        else:
            logger_processor_rdf.debug(f"Unhandled entity type: {extracted_entity.label} for text: '{text}'")
            return None
