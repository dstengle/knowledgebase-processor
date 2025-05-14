"""Processor implementation for processing knowledge base content."""

from typing import List, Dict, Any, Optional, cast # Added cast

from ..models.content import Document, ContentElement
from ..models.metadata import DocumentMetadata, ExtractedEntity
from ..models.links import WikiLink, Link
from knowledgebase_processor.analyzer.entity_recognizer import EntityRecognizer


class Processor:
    """Processor component for processing knowledge base content.
    
    The Processor is responsible for coordinating the extraction and analysis
    of content from the knowledge base documents.
    """
    
    def __init__(self):
        """Initialize the Processor."""
        self.extractors = []
        self.analyzers = []
        self.analyzers.append(EntityRecognizer())
        self.enrichers = []
        self.entity_recognizer = EntityRecognizer()
    
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
                wikilink_obj.entities = raw_entities # entities are List[ExtractedEntity]
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
            if isinstance(analyzer, EntityRecognizer):
                if document.content: # Ensure content exists
                    analyzer.analyze(document.content, doc_metadata) # Modifies doc_metadata.entities
            else:
                # Assuming other analyzers expect the Document object directly
                # or handle metadata internally if needed.
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
    
    # The extract_metadata method is now removed as its logic is integrated into process_document.