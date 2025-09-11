"""Metadata processing module for handling document metadata operations."""

from typing import Optional, Dict, Any
from pathlib import Path

from ..models.content import Document
from ..models.metadata import DocumentMetadata
from ..models.kb_entities import KbDocument
from ..utils.logging import get_logger


logger = get_logger("knowledgebase_processor.processor.metadata")


class MetadataProcessor:
    """Handles document metadata creation, validation, and management."""
    
    def __init__(self):
        """Initialize MetadataProcessor."""
        pass
    
    def create_document_metadata(
        self,
        document: Document,
        kb_document: KbDocument
    ) -> DocumentMetadata:
        """Create or enhance document metadata.
        
        Args:
            document: Source document
            kb_document: KB document entity
            
        Returns:
            DocumentMetadata with proper fields set
        """
        # Use existing metadata as base or create new
        if document.metadata:
            doc_metadata = document.metadata
            # Update key fields to ensure consistency
            doc_metadata.document_id = kb_document.kb_id
            doc_metadata.path = kb_document.original_path
            if not doc_metadata.title:
                doc_metadata.title = kb_document.label
        else:
            doc_metadata = DocumentMetadata(
                document_id=kb_document.kb_id,
                path=kb_document.original_path,
                title=kb_document.label
            )
        
        # Enhance metadata with additional information
        doc_metadata = self._enhance_metadata(doc_metadata, document, kb_document)
        
        logger.debug(f"Created metadata for document: {kb_document.original_path}")
        return doc_metadata
    
    def _enhance_metadata(
        self,
        doc_metadata: DocumentMetadata,
        document: Document,
        kb_document: KbDocument
    ) -> DocumentMetadata:
        """Enhance metadata with additional computed information.
        
        Args:
            doc_metadata: Base metadata to enhance
            document: Source document
            kb_document: KB document entity
            
        Returns:
            Enhanced metadata
        """
        # Add file information
        try:
            file_path = Path(kb_document.original_path)
            if not hasattr(doc_metadata, 'file_extension'):
                doc_metadata.file_extension = file_path.suffix
            if not hasattr(doc_metadata, 'filename'):
                doc_metadata.filename = file_path.name
            if not hasattr(doc_metadata, 'parent_directory'):
                doc_metadata.parent_directory = str(file_path.parent)
        except Exception as e:
            logger.debug(f"Could not enhance file metadata: {e}")
        
        # Add content statistics
        if document.content:
            try:
                content_stats = self._calculate_content_statistics(document.content)
                if not hasattr(doc_metadata, 'content_stats'):
                    doc_metadata.content_stats = content_stats
            except Exception as e:
                logger.debug(f"Could not calculate content statistics: {e}")
        
        # Add element count
        if document.elements:
            if not hasattr(doc_metadata, 'element_count'):
                doc_metadata.element_count = len(document.elements)
        
        return doc_metadata
    
    def _calculate_content_statistics(self, content: str) -> Dict[str, Any]:
        """Calculate basic statistics about document content.
        
        Args:
            content: Document content string
            
        Returns:
            Dictionary with content statistics
        """
        lines = content.split('\n')
        words = content.split()
        
        return {
            'character_count': len(content),
            'line_count': len(lines),
            'word_count': len(words),
            'paragraph_count': len([line for line in lines if line.strip()]),
            'empty_line_count': len([line for line in lines if not line.strip()])
        }
    
    def extract_frontmatter_metadata(
        self,
        document: Document,
        extractors: list
    ) -> Dict[str, Any]:
        """Extract metadata from frontmatter using available extractors.
        
        Args:
            document: Document to extract frontmatter from
            extractors: List of extractors that might handle frontmatter
            
        Returns:
            Dictionary with frontmatter metadata
        """
        frontmatter_data = {}
        
        # Look for frontmatter elements
        for element in document.elements:
            if (hasattr(element, 'element_type') and 
                element.element_type == "frontmatter"):
                
                # Try each extractor to parse frontmatter
                for extractor in extractors:
                    if hasattr(extractor, 'parse_frontmatter'):
                        try:
                            parsed = extractor.parse_frontmatter(element.content)
                            if parsed and isinstance(parsed, dict):
                                frontmatter_data.update(parsed)
                                logger.debug(f"Extracted frontmatter: {list(parsed.keys())}")
                        except Exception as e:
                            logger.debug(f"Failed to parse frontmatter with {type(extractor).__name__}: {e}")
        
        return frontmatter_data
    
    def update_metadata_from_frontmatter(
        self,
        doc_metadata: DocumentMetadata,
        frontmatter_data: Dict[str, Any]
    ) -> DocumentMetadata:
        """Update document metadata with frontmatter information.
        
        Args:
            doc_metadata: Metadata to update
            frontmatter_data: Frontmatter data to incorporate
            
        Returns:
            Updated metadata
        """
        # Map common frontmatter fields to metadata attributes
        field_mapping = {
            'title': 'title',
            'author': 'author',
            'date': 'date_created',
            'created': 'date_created',
            'modified': 'date_modified',
            'updated': 'date_modified',
            'tags': 'tags',
            'categories': 'categories',
            'description': 'description',
            'summary': 'summary'
        }
        
        for fm_key, fm_value in frontmatter_data.items():
            if fm_key.lower() in field_mapping:
                metadata_attr = field_mapping[fm_key.lower()]
                try:
                    setattr(doc_metadata, metadata_attr, fm_value)
                    logger.debug(f"Updated metadata.{metadata_attr} from frontmatter.{fm_key}")
                except Exception as e:
                    logger.debug(f"Could not set metadata.{metadata_attr}: {e}")
            else:
                # Store unknown frontmatter fields in a custom dict
                if not hasattr(doc_metadata, 'custom_frontmatter'):
                    doc_metadata.custom_frontmatter = {}
                doc_metadata.custom_frontmatter[fm_key] = fm_value
        
        return doc_metadata
    
    def validate_metadata(
        self,
        doc_metadata: DocumentMetadata
    ) -> Dict[str, Any]:
        """Validate document metadata for completeness and correctness.
        
        Args:
            doc_metadata: Metadata to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'required_fields_present': True,
            'field_types_correct': True
        }
        
        # Check required fields
        required_fields = ['document_id', 'path']
        for field in required_fields:
            if not hasattr(doc_metadata, field) or not getattr(doc_metadata, field):
                validation_results['errors'].append(f"Missing required field: {field}")
                validation_results['required_fields_present'] = False
                validation_results['is_valid'] = False
        
        # Check field types
        expected_types = {
            'document_id': str,
            'path': str,
            'title': (str, type(None))
        }
        
        for field, expected_type in expected_types.items():
            if hasattr(doc_metadata, field):
                field_value = getattr(doc_metadata, field)
                if field_value is not None and not isinstance(field_value, expected_type):
                    validation_results['warnings'].append(
                        f"Field {field} has unexpected type: {type(field_value)}"
                    )
                    validation_results['field_types_correct'] = False
        
        # Check for common issues
        if hasattr(doc_metadata, 'path'):
            path = doc_metadata.path
            if '\\' in path and '/' in path:
                validation_results['warnings'].append(
                    "Path contains mixed path separators"
                )
        
        if hasattr(doc_metadata, 'title'):
            title = doc_metadata.title
            if title and len(title) > 200:
                validation_results['warnings'].append(
                    f"Title is very long ({len(title)} characters)"
                )
        
        return validation_results
    
    def merge_metadata(
        self,
        primary_metadata: DocumentMetadata,
        secondary_metadata: DocumentMetadata
    ) -> DocumentMetadata:
        """Merge two metadata objects, with primary taking precedence.
        
        Args:
            primary_metadata: Primary metadata (takes precedence)
            secondary_metadata: Secondary metadata (used for missing fields)
            
        Returns:
            Merged metadata
        """
        # Start with a copy of primary metadata
        merged = DocumentMetadata(
            document_id=primary_metadata.document_id,
            path=primary_metadata.path,
            title=primary_metadata.title or (
                secondary_metadata.title if hasattr(secondary_metadata, 'title') else None
            )
        )
        
        # Copy all attributes from primary
        for attr_name in dir(primary_metadata):
            if not attr_name.startswith('_') and hasattr(primary_metadata, attr_name):
                try:
                    attr_value = getattr(primary_metadata, attr_name)
                    if not callable(attr_value):
                        setattr(merged, attr_name, attr_value)
                except (AttributeError, TypeError):
                    continue
        
        # Fill in missing attributes from secondary
        for attr_name in dir(secondary_metadata):
            if (not attr_name.startswith('_') and 
                hasattr(secondary_metadata, attr_name) and
                not hasattr(merged, attr_name)):
                try:
                    attr_value = getattr(secondary_metadata, attr_name)
                    if not callable(attr_value):
                        setattr(merged, attr_name, attr_value)
                except (AttributeError, TypeError):
                    continue
        
        logger.debug("Merged metadata from two sources")
        return merged