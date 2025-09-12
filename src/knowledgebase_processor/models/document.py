"""Document models for the Knowledge Base Processor.

This module provides the unified document models that consolidate
Document and KbDocument into a single model with integrated metadata.
"""

from typing import Optional, List, Set, Dict, Any
from pydantic import Field
from rdflib.namespace import SDO as SCHEMA, XSD

# Import KB namespace from centralized configuration
from knowledgebase_processor.config.vocabulary import KB
from .base import DocumentEntity, KnowledgeBaseEntity


class UnifiedDocumentMetadata(KnowledgeBaseEntity):
    """Unified document metadata model.
    
    Consolidates DocumentMetadata with enhanced entity support.
    """
    
    document_id: str = Field(
        ...,
        description="ID of the associated document",
        json_schema_extra={
            "rdf_property": KB.documentId,
            "rdf_datatype": XSD.string
        }
    )
    title: Optional[str] = Field(
        None,
        description="Document title",
        json_schema_extra={
            "rdf_property": SCHEMA.name,
            "rdf_datatype": XSD.string
        }
    )
    path: Optional[str] = Field(
        None,
        description="Document path",
        json_schema_extra={
            "rdf_property": KB.path,
            "rdf_datatype": XSD.string
        }
    )
    
    # Frontmatter
    frontmatter: Optional[Dict[str, Any]] = Field(
        None,
        description="Frontmatter metadata"
    )
    
    # Collections
    tags: Set[str] = Field(
        default_factory=set,
        description="All tags in the document",
        json_schema_extra={
            "rdf_property": SCHEMA.keywords,
            "rdf_datatype": XSD.string
        }
    )
    
    # Document structure
    structure: Dict[str, Any] = Field(
        default_factory=dict,
        description="Document structure metadata"
    )
    references: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="References in the document"
    )
    
    class Config:
        json_schema_extra = {
            "rdf_types": [KB.DocumentMetadata]
        }


class UnifiedDocument(DocumentEntity):
    """Complete unified document model.
    
    Consolidates Document and KbDocument with full metadata integration.
    """
    
    # Path variants (from KbDocument)
    original_path: Optional[str] = Field(
        None,
        description="Original unmodified file path",
        json_schema_extra={
            "rdf_property": KB.originalPath,
            "rdf_datatype": XSD.string
        }
    )
    path_without_extension: Optional[str] = Field(
        None,
        description="Path without extension for linking",
        json_schema_extra={
            "rdf_property": KB.pathWithoutExtension,
            "rdf_datatype": XSD.string
        }
    )
    
    # Metadata (integrated directly)
    metadata: Optional[UnifiedDocumentMetadata] = Field(
        None,
        description="Complete document metadata"
    )
    
    # Structured content elements (forward reference to avoid circular imports)
    elements: List[Any] = Field(
        default_factory=list,
        description="Structured elements of the document"
    )
    
    def preserve_content(self) -> None:
        """Preserve original content for all elements."""
        for element in self.elements:
            if hasattr(element, 'preserve_original_content'):
                element.preserve_original_content(self.content)
    
    def get_content_at_position(self, start_line: int, end_line: int) -> str:
        """Get the original content at the specified position.
        
        Args:
            start_line: Starting line number (0-based)
            end_line: Ending line number (0-based)
            
        Returns:
            The content at the specified position
        """
        lines = self.content.splitlines()
        if start_line < 0 or end_line >= len(lines):
            raise ValueError(
                f"Position out of range: {start_line}-{end_line}, "
                f"document has {len(lines)} lines"
            )
        
        return '\n'.join(lines[start_line:end_line + 1])
    
    class Config:
        json_schema_extra = {
            "rdf_types": [KB.Document, SCHEMA.CreativeWork],
            "rdfs_label_fallback_fields": ["title", "label", "original_path"]
        }


class PlaceholderDocument(KnowledgeBaseEntity):
    """Placeholder document entity for forward references.
    
    Maintains existing KbPlaceholderDocument functionality.
    """
    
    title: str = Field(
        ...,
        description="Title extracted from wiki link that references this placeholder",
        json_schema_extra={
            "rdf_property": SCHEMA.name,
            "rdf_datatype": XSD.string
        }
    )
    normalized_name: str = Field(
        ...,
        description="Normalized name used to generate deterministic ID",
        json_schema_extra={
            "rdf_property": KB.normalizedName,
            "rdf_datatype": XSD.string
        }
    )
    referenced_by: List[str] = Field(
        default_factory=list,
        description="List of document URIs that reference this placeholder",
        json_schema_extra={
            "rdf_property": KB.referencedBy,
            "is_object_property": True,
            "rdf_datatype": XSD.anyURI
        }
    )
    expected_path: Optional[str] = Field(
        None,
        description="Expected file path where this document should be created",
        json_schema_extra={
            "rdf_property": KB.expectedPath,
            "rdf_datatype": XSD.string
        }
    )
    
    class Config:
        json_schema_extra = {
            "rdf_types": [KB.PlaceholderDocument, SCHEMA.CreativeWork],
            "rdfs_label_fallback_fields": ["title", "normalized_name"]
        }


# Backward compatibility aliases
Document = UnifiedDocument
DocumentMetadata = UnifiedDocumentMetadata
KbDocument = UnifiedDocument  # Direct alias for kb_entities usage
KbPlaceholderDocument = PlaceholderDocument