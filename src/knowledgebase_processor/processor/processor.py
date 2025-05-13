"""Processor implementation for processing knowledge base content."""

from typing import List, Dict, Any, Optional

from ..models.content import Document, ContentElement
from ..models.metadata import DocumentMetadata
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
        """Process a document using registered components.
        
        Args:
            document: The document to process
            
        Returns:
            The processed document with extracted elements
        """
        # Extract content elements
        for extractor in self.extractors:
            elements = extractor.extract(document)
            document.elements.extend(elements)
        
        # Update document title from frontmatter if available
        self._update_document_title_from_frontmatter(document)
        
        # Preserve original content for all elements
        document.preserve_content()
        
        # Analyze content
        # Create/retrieve metadata for the document
        # This metadata object will be passed to analyzers that require it.
        doc_metadata = self.extract_metadata(document)

        for analyzer in self.analyzers:
            if isinstance(analyzer, EntityRecognizer):
                if document.content: # Ensure content exists
                    analyzer.analyze(document.content, doc_metadata) # Pass the created doc_metadata
            else:
                # Assuming other analyzers expect the Document object directly
                # or handle metadata internally if needed.
                analyzer.analyze(document)
        
        # Enrich content
        for enricher in self.enrichers:
            enricher.enrich(document)
        
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
            for extractor in self.extractors:
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
    
    def extract_metadata(self, document: Document) -> DocumentMetadata:
        """Extract metadata from a document.
        
        Args:
            document: The document to extract metadata from
            
        Returns:
            Metadata object containing the extracted metadata
        """
        metadata = DocumentMetadata(
            document_id=document.id or document.path,
            title=getattr(document, "title", None),
            path=getattr(document, "path", None)
        )
        
        # Extract metadata from document elements
        for element in document.elements:
            # Process different element types
            if element.element_type == "frontmatter":
                # Process frontmatter
                format_type = element.metadata.get("format", "yaml")
                
                # Find the FrontmatterExtractor to use its parsing methods
                frontmatter_extractor = None
                for extractor in self.extractors:
                    if hasattr(extractor, "parse_frontmatter"):
                        frontmatter_extractor = extractor
                        break
                
                if frontmatter_extractor:
                    # Parse the frontmatter content
                    frontmatter_dict = frontmatter_extractor.parse_frontmatter(
                        element.content, format_type
                    )
                    
                    # Extract tags from frontmatter
                    if "tags" in frontmatter_dict:
                        tags = frontmatter_extractor._extract_tags_from_frontmatter(frontmatter_dict)
                        for tag in tags:
                            metadata.tags.add(tag)
                    
                    # Create frontmatter model
                    frontmatter_model = frontmatter_extractor.create_frontmatter_model(frontmatter_dict)
                    metadata.frontmatter = frontmatter_model
            elif element.element_type == "tag":
                # Process tag
                metadata.tags.add(element.content)
            elif element.element_type == "link":
                # Process link
                metadata.links.append({
                    "text": element.content,
                    "position": element.position
                })
        
            elif element.element_type == "wikilink":
                # Process wikilink
                metadata.wikilinks.append({
                    "text": element.content,
                    "position": element.position
                })
        
        # Store document content and structure in metadata
        metadata.structure = {
            "content": document.content,
            "title": document.title,
            "elements": [
                {
                    "element_type": e.element_type,
                    "content": e.content,
                    "position": e.position
                }
                for e in document.elements
            ]
        }
        # Entity extraction is now handled by the EntityRecognizer's analyze method
        # called in the main processing loop.
        # The metadata.entities field will be populated there.
        return metadata