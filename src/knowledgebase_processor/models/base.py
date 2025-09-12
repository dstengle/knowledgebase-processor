"""Base models for the Knowledge Base Processor.

This module provides the unified base classes that consolidate
BaseKnowledgeModel and KbBaseEntity into a single inheritance hierarchy.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from rdflib.namespace import SDO as SCHEMA, RDFS, XSD

# Import KB namespace from centralized configuration
from knowledgebase_processor.config.vocabulary import KB


class KnowledgeBaseEntity(BaseModel):
    """Universal base for all knowledge base models.
    
    Consolidates BaseKnowledgeModel and KbBaseEntity into a single base class
    that provides both basic model functionality and RDF support.
    """
    
    # Core Identity
    id: str = Field(
        ..., 
        description="Universal unique identifier",
        json_schema_extra={
            "rdf_property": RDFS.seeAlso,
            "is_object_property": True,
            "rdf_datatype": XSD.anyURI
        }
    )
    kb_id: Optional[str] = Field(
        None, 
        description="Knowledge base specific identifier (URI)",
        json_schema_extra={
            "rdf_property": KB.identifier,
            "rdf_datatype": XSD.anyURI
        }
    )
    
    # Labels and Descriptions
    label: Optional[str] = Field(
        None,
        description="Human-readable label for the entity",
        json_schema_extra={
            "rdf_property": RDFS.label,
            "rdf_datatype": XSD.string
        }
    )
    
    # Timestamps (UTC)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp",
        json_schema_extra={
            "rdf_property": SCHEMA.dateCreated,
            "rdf_datatype": XSD.dateTime
        }
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
        json_schema_extra={
            "rdf_property": SCHEMA.dateModified,
            "rdf_datatype": XSD.dateTime
        }
    )
    
    # Provenance
    source_document_uri: Optional[str] = Field(
        None,
        description="URI of the source document",
        json_schema_extra={
            "rdf_property": KB.sourceDocument,
            "is_object_property": True,
            "rdf_datatype": XSD.anyURI
        }
    )
    extraction_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Context about how this entity was extracted"
    )
    
    class Config:
        json_schema_extra = {
            "rdf_types": [KB.Entity]
        }


class ContentEntity(KnowledgeBaseEntity):
    """Base for extracted content entities.
    
    Consolidates ExtractedEntity with richer entity models.
    """
    
    # Content Identity
    text: str = Field(
        ..., 
        description="Extracted text",
        json_schema_extra={
            "rdf_property": SCHEMA.text,
            "rdf_datatype": XSD.string
        }
    )
    entity_type: str = Field(
        ..., 
        description="Type of entity (e.g., person, organization, location)",
        json_schema_extra={
            "rdf_property": KB.entityType,
            "rdf_datatype": XSD.string
        }
    )
    
    # Position Information (consolidating extracted_from_text_span)
    start_char: Optional[int] = Field(
        None,
        description="Starting character offset in source text",
        json_schema_extra={
            "rdf_property": KB.startOffset,
            "rdf_datatype": XSD.integer
        }
    )
    end_char: Optional[int] = Field(
        None,
        description="Ending character offset in source text",
        json_schema_extra={
            "rdf_property": KB.endOffset,
            "rdf_datatype": XSD.integer
        }
    )
    position_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional position context (line numbers, etc.)"
    )
    
    # Confidence and Quality
    confidence_score: Optional[float] = Field(
        None,
        description="Confidence score from extraction",
        json_schema_extra={
            "rdf_property": KB.confidence,
            "rdf_datatype": XSD.float
        }
    )
    extraction_method: Optional[str] = Field(
        None,
        description="Method used for extraction",
        json_schema_extra={
            "rdf_property": KB.extractionMethod,
            "rdf_datatype": XSD.string
        }
    )
    
    @property
    def extracted_from_text_span(self) -> Optional[Tuple[int, int]]:
        """Backward compatibility for kb_entities text span."""
        if self.start_char is not None and self.end_char is not None:
            return (self.start_char, self.end_char)
        return None
    
    class Config:
        json_schema_extra = {
            "rdf_types": [KB.ExtractedEntity]
        }


class MarkdownEntity(ContentEntity):
    """Base for markdown-specific elements."""
    
    element_type: str = Field(
        "markdown",
        description="Type of markdown element",
        json_schema_extra={
            "rdf_property": KB.elementType,
            "rdf_datatype": XSD.string
        }
    )
    parent_id: Optional[str] = Field(
        None,
        description="ID of parent element",
        json_schema_extra={
            "rdf_property": KB.parentElement,
            "is_object_property": True,
            "rdf_datatype": XSD.anyURI
        }
    )
    
    class Config:
        json_schema_extra = {
            "rdf_types": [KB.MarkdownElement]
        }


class DocumentEntity(KnowledgeBaseEntity):
    """Base for all document-related entities."""
    
    # Document Identity
    path: str = Field(
        ..., 
        description="Document path",
        json_schema_extra={
            "rdf_property": KB.path,
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
    
    # Content
    content: str = Field(
        ..., 
        description="Raw content of the document",
        json_schema_extra={
            "rdf_property": SCHEMA.text,
            "rdf_datatype": XSD.string
        }
    )
    content_hash: Optional[str] = Field(
        None,
        description="Hash for change detection",
        json_schema_extra={
            "rdf_property": KB.contentHash,
            "rdf_datatype": XSD.string
        }
    )
    
    class Config:
        json_schema_extra = {
            "rdf_types": [KB.Document, SCHEMA.CreativeWork]
        }