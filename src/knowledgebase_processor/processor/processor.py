"""Processor implementation for processing knowledge base content."""

import uuid
from pathlib import Path
from urllib.parse import quote
from typing import List, Dict, Any, Optional, cast

from rdflib import Graph
from rdflib.namespace import SDO as SCHEMA, RDFS, XSD

from ..models.content import Document, ContentElement
from ..models.markdown import TodoItem # Added this import
from ..models.metadata import DocumentMetadata, ExtractedEntity as ModelExtractedEntity # Renamed to avoid clash
from ..models.links import WikiLink, Link
from ..analyzer.entity_recognizer import EntityRecognizer
from ..models.kb_entities import KbBaseEntity, KbPerson, KbOrganization, KbLocation, KbDateEntity, KbTodoItem, KB
# from ..models.entities import ExtractedEntity # This is now ModelExtractedEntity
from ..rdf_converter import RdfConverter
from ..reader.reader import Reader
from ..metadata_store.interface import MetadataStoreInterface
from ..utils.logging import get_logger

logger_processor_rdf = get_logger("knowledgebase_processor.processor.rdf")


class Processor:
    """Processor component for processing knowledge base content.
    
    The Processor is responsible for coordinating the extraction and analysis
    of content from the knowledge base documents.
    """
    
    def __init__(self, config=None):
        """Initialize the Processor.
        
        Args:
            config: Configuration object to control processor behavior.
        """
        self.config = config
        self.extractors = []
        self.analyzers = []
        self.enrichers = []
        
        # Conditionally initialize entity recognizers based on config
        analyze_entities = False  # Default value - spacy is disabled by default
        if config and hasattr(config, 'analyze_entities'):
            analyze_entities = config.analyze_entities
            
        if analyze_entities:
            self.analyzers.append(EntityRecognizer(enabled=True)) # Default EntityRecognizer for general analysis
            self.entity_recognizer = EntityRecognizer(enabled=True) # Dedicated instance for wikilink entity extraction
        else:
            self.entity_recognizer = EntityRecognizer(enabled=False) # Disabled instance for wikilink entity extraction
    
    def register_extractor(self, extractor):
        """Register an extractor component.
        
        Args:
            extractor: An extractor component
        """
        self.extractors.append(extractor)
    
    def register_analyzer(self, analyzer):
        """Register an analyzer component.
        
        Args:
            analyzer: An analyzer component
        """
        self.analyzers.append(analyzer)
    
    def register_enricher(self, enricher):
        """Register an enricher component.
        
        Args:
            enricher: An enricher component
        """
        self.enrichers.append(enricher)
    
    def process_document(self, document: Document) -> Document:
        """Process a document using registered components and attach its metadata.
        
        Args:
            document: The document to process
            
        Returns:
            The processed document with extracted elements and populated metadata.
        """
        # 1. Run Extractors
        for extractor in self.extractors:
            elements = extractor.extract(document)
            document.elements.extend(elements)
        
        # 2. Update Document Title
        self._update_document_title_from_frontmatter(document)
        
        # 3. Preserve Content
        document.preserve_content()
        
        # 4. Initialize DocumentMetadata
        doc_metadata = DocumentMetadata(
            document_id=document.id or document.path, # Use document.id if available, else path
            title=document.title, # Title is now set
            path=document.path
        )
        
        # 5. Populate doc_metadata from document.elements
        for element in document.elements:
            if element.element_type == "frontmatter":
                format_type = element.metadata.get("format", "yaml")
                frontmatter_extractor = None
                for extractor_instance in self.extractors: # Renamed to avoid conflict
                    if hasattr(extractor_instance, "parse_frontmatter"):
                        frontmatter_extractor = extractor_instance
                        break
                if frontmatter_extractor:
                    frontmatter_dict = frontmatter_extractor.parse_frontmatter(
                        element.content, format_type
                    )
                    if "tags" in frontmatter_dict:
                        tags = frontmatter_extractor._extract_tags_from_frontmatter(frontmatter_dict)
                        for tag in tags:
                            doc_metadata.tags.add(tag)
                    frontmatter_model = frontmatter_extractor.create_frontmatter_model(frontmatter_dict)
                    doc_metadata.frontmatter = frontmatter_model
            elif element.element_type == "tag":
                doc_metadata.tags.add(element.content)
            elif element.element_type == "link":
                if isinstance(element, Link): # Element should be a Link instance
                    doc_metadata.links.append(element)
            elif element.element_type == "wikilink":
                wikilink_obj = cast(WikiLink, element) # Element should be a WikiLink instance
                text_for_analysis = wikilink_obj.display_text
                # Use the Processor's dedicated entity_recognizer instance for wikilink text
                raw_entities = self.entity_recognizer.analyze_text_for_entities(text_for_analysis)
                wikilink_obj.entities = raw_entities # entities are List[ModelExtractedEntity]
                doc_metadata.wikilinks.append(wikilink_obj)
        
        # Populate doc_metadata.structure
        doc_metadata.structure = {
            "content": document.content,
            "title": document.title,
            "elements": [
                {
                    "element_type": e.element_type,
                    "content": e.content,
                    "position": e.position # Assuming ContentElement has position
                }
                for e in document.elements
            ]
        }

        # 6. Run Analyzers (populates doc_metadata.entities for document-wide entities)
        for analyzer in self.analyzers:
            if isinstance(analyzer, EntityRecognizer): # This refers to the general analyzers list
                if document.content: # Ensure content exists
                    # This analyze method should populate doc_metadata.entities
                    analyzer.analyze(document.content, doc_metadata)
            else:
                analyzer.analyze(document) # Or pass doc_metadata if they are adapted
        
        # 7. Run Enrichers
        for enricher in self.enrichers:
            enricher.enrich(document) # Or pass doc_metadata if they are adapted
        
        # 8. Attach Metadata to Document
        document.metadata = doc_metadata
        
        # 9. Return Document
        return document
    
    def _update_document_title_from_frontmatter(self, document: Document) -> None:
        """Update document title from frontmatter if available, otherwise use filename.
        
        This method implements a fallback mechanism for document titles:
        1. Use frontmatter title if available
        2. If frontmatter title is not available, use the filename (minus extension)
        
        Args:
            document: The document to update
        """
        # Find frontmatter elements
        frontmatter_elements = [e for e in document.elements if e.element_type == "frontmatter"]
        
        # Check if we have frontmatter
        if frontmatter_elements:
            # Get the first frontmatter element
            frontmatter_element = frontmatter_elements[0]
            
            # Parse the frontmatter
            format_type = frontmatter_element.metadata.get("format", "yaml")
            
            # Find the FrontmatterExtractor to use its parsing methods
            frontmatter_extractor = None
            for extractor in self.extractors: # This 'extractor' is fine, it's a local loop var
                if hasattr(extractor, "parse_frontmatter"):
                    frontmatter_extractor = extractor
                    break
            
            if frontmatter_extractor:
                # Parse the frontmatter content
                frontmatter_dict = frontmatter_extractor.parse_frontmatter(
                    frontmatter_element.content, format_type
                )
                
                # Update document title if available in frontmatter
                if "title" in frontmatter_dict and frontmatter_dict["title"]:
                    document.title = frontmatter_dict["title"]
                    return
        
        # Fallback: If no frontmatter title was found, use the filename (minus extension)
        if document.path:
            import os
            # Extract filename without extension
            filename = os.path.basename(document.path)
            name_without_ext = os.path.splitext(filename)[0]
            
            # Convert filename to title format (replace underscores/hyphens with spaces)
            title_from_filename = name_without_ext.replace('_', ' ').replace('-', ' ')
            
            document.title = title_from_filename

    def _generate_kb_id(self, entity_type_str: str, text: str) -> str:
        """Generates a unique knowledge base ID (URI) for an entity."""
        slug = "".join(c if c.isalnum() else "_" for c in text.lower())
        slug = slug[:50].strip('_')
        return str(KB[f"{entity_type_str}/{slug}_{uuid.uuid4().hex[:8]}"])

    def _extracted_entity_to_kb_entity(
        self,
        extracted_entity: ModelExtractedEntity, # Use the renamed import
        source_doc_relative_path: str
    ) -> Optional[KbBaseEntity]:
        """Transforms an ExtractedEntity to a corresponding KbBaseEntity subclass instance."""
        kb_id_text = extracted_entity.text
        entity_label_upper = extracted_entity.label.upper()
        logger_processor_rdf.info(f"Processing entity: {kb_id_text} of type {entity_label_upper}")

        normalized_path = source_doc_relative_path.replace("\\", "/")
        safe_path_segment = quote(normalized_path.replace(" ", "_"))
        full_document_uri = str(KB[f"Document/{safe_path_segment}"])

        common_args = {
            "label": extracted_entity.text,
            "source_document_uri": full_document_uri,
            "extracted_from_text_span": (extracted_entity.start_char, extracted_entity.end_char),
        }

        if entity_label_upper == "PERSON":
            kb_id = self._generate_kb_id("Person", kb_id_text)
            return KbPerson(kb_id=kb_id, full_name=extracted_entity.text, **common_args)
        elif entity_label_upper == "ORG":
            kb_id = self._generate_kb_id("Organization", kb_id_text)
            return KbOrganization(kb_id=kb_id, name=extracted_entity.text, **common_args)
        elif entity_label_upper in ["LOC", "GPE"]:
            kb_id = self._generate_kb_id("Location", kb_id_text)
            return KbLocation(kb_id=kb_id, name=extracted_entity.text, **common_args)
        elif entity_label_upper == "DATE":
            kb_id = self._generate_kb_id("DateEntity", kb_id_text)
            return KbDateEntity(kb_id=kb_id, date_value=extracted_entity.text, **common_args)
        else:
            logger_processor_rdf.debug(f"Unhandled entity type: {extracted_entity.label} for text: '{extracted_entity.text}'")
            return None

    def process_and_generate_rdf(
        self,
        reader: Reader,
        metadata_store: MetadataStoreInterface,
        pattern: str,
        knowledge_base_path: Path, # For context, e.g. making doc paths relative if needed
        rdf_output_dir_str: Optional[str] = None,
    ) -> int:
        """
        Processes all documents matching a pattern, saves their metadata,
        and optionally generates RDF/TTL files.
        This method consolidates logic previously in cli/main.py process_command.
        """
        logger_proc_rdf = get_logger("knowledgebase_processor.processor.rdf_process") # Specific logger
        logger_proc_rdf.info(f"Processing files matching pattern: {pattern}")
        logger_proc_rdf.info(f"Knowledge base path: {knowledge_base_path}")

        rdf_converter: Optional[RdfConverter] = None
        rdf_output_path: Optional[Path] = None

        if rdf_output_dir_str:
            rdf_output_path = Path(rdf_output_dir_str)
            try:
                rdf_output_path.mkdir(parents=True, exist_ok=True)
                logger_proc_rdf.info(f"RDF output will be saved to: {rdf_output_path.resolve()}")
                rdf_converter = RdfConverter()
            except OSError as e:
                logger_proc_rdf.error(f"Could not create RDF output directory {rdf_output_path}: {e}", exc_info=True)
                return 1

        processed_documents: List[Document] = []
        try:
            # Iterate through documents provided by the reader
            for doc_from_reader in reader.read_all(pattern):
                # Process the document using the existing process_document method
                processed_doc = self.process_document(doc_from_reader)
                
                # Save metadata using the provided metadata_store
                if processed_doc.metadata:
                    metadata_store.save(processed_doc.metadata)
                
                processed_documents.append(processed_doc)
            
            count = len(processed_documents)
            logger_proc_rdf.info(f"Processed and stored metadata for {count} documents.")

            if rdf_converter and rdf_output_path and processed_documents:
                logger_proc_rdf.info(f"Starting RDF generation for {count} documents...")
                for doc_idx, doc in enumerate(processed_documents):
                    if not doc.path: # doc.path should be relative string path from Document model
                        logger_proc_rdf.warning(f"Document at index {doc_idx} missing source_path, skipping RDF generation.")
                        continue

                    if not doc.metadata or not doc.metadata.entities:
                        logger_proc_rdf.debug(f"No entities to convert for document: {doc.path}")
                        continue

                    doc_graph = Graph()
                    doc_graph.bind("kb", KB)
                    doc_graph.bind("schema", SCHEMA)
                    doc_graph.bind("rdfs", RDFS)
                    doc_graph.bind("xsd", XSD)

                    logger_proc_rdf.debug(f"Generating RDF for document: {doc.path}")
                    entities_converted_count = 0
                    # Convert extracted entities (PERSON, ORG, etc.)
                    for extracted_entity in doc.metadata.entities:
                        # doc.path is already the relative path string
                        kb_entity = self._extracted_entity_to_kb_entity(extracted_entity, str(doc.path))
                        if kb_entity:
                            try:
                                entity_graph = rdf_converter.kb_entity_to_graph(kb_entity, base_uri_str=str(KB))
                                for triple in entity_graph:
                                    doc_graph.add(triple)
                                entities_converted_count += 1
                                logger_proc_rdf.debug(f"Converted entity '{kb_entity.label}' ({kb_entity.kb_id}) to RDF.")
                            except Exception as e_conv:
                                logger_proc_rdf.error(f"Error converting entity '{kb_entity.label}' to RDF: {e_conv}", exc_info=True)
                    
                    # Convert TodoItems from document elements
                    for element in doc.elements:
                        if element.element_type == "todo_item":
                            # Assuming element is a models.markdown.TodoItem
                            markdown_todo = cast("TodoItem", element) # Add import: from ..models.markdown import TodoItem
                            
                            # Create KbTodoItem from markdown.TodoItem
                            # Ensure kb_id is unique and well-formed
                            todo_kb_id_text = f"todo_{markdown_todo.text[:30]}" # Simple ID generation
                            kb_todo_id = self._generate_kb_id("TodoItem", todo_kb_id_text)
                            
                            normalized_path = str(doc.path).replace("\\", "/")
                            safe_path_segment = quote(normalized_path.replace(" ", "_"))
                            full_document_uri = str(KB[f"Document/{safe_path_segment}"])

                            kb_todo_item = KbTodoItem(
                                kb_id=kb_todo_id,
                                description=markdown_todo.text,
                                is_completed=markdown_todo.is_checked,
                                label=markdown_todo.text, # Use description as label
                                source_document_uri=full_document_uri,
                                # extracted_from_text_span can be set if position is available and needed
                                # extracted_from_text_span=(markdown_todo.position['start'], markdown_todo.position['end']) if markdown_todo.position else None
                            )
                            try:
                                todo_entity_graph = rdf_converter.kb_entity_to_graph(kb_todo_item, base_uri_str=str(KB))
                                for triple in todo_entity_graph:
                                    doc_graph.add(triple)
                                entities_converted_count +=1
                                logger_proc_rdf.debug(f"Converted TodoItem '{kb_todo_item.description}' to RDF.")
                            except Exception as e_conv_todo:
                                logger_proc_rdf.error(f"Error converting TodoItem '{kb_todo_item.description}' to RDF: {e_conv_todo}", exc_info=True)

                    logger_proc_rdf.debug(f"Converted {entities_converted_count} total entities (including ToDos) for {doc.path}.")

                    if len(doc_graph) > 0:
                        # doc.path is like "folder/file.md". We want "file.ttl"
                        output_filename = Path(Path(doc.path).name).with_suffix(".ttl")
                        output_file_path = rdf_output_path / output_filename
                        try:
                            doc_graph.serialize(destination=str(output_file_path), format="turtle")
                            logger_proc_rdf.info(f"Saved RDF for {Path(doc.path).name} to {output_file_path}")
                        except Exception as e_ser:
                            logger_proc_rdf.error(f"Error serializing RDF for {Path(doc.path).name} to {output_file_path}: {e_ser}", exc_info=True)
                    else:
                        logger_proc_rdf.info(f"No RDF triples generated for document: {doc.path}")
            return 0
        except Exception as e:
            logger_proc_rdf.error(f"An error occurred during processing or RDF generation: {e}", exc_info=True)
            return 1
