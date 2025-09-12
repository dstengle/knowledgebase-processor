"""Link models for the Knowledge Base Processor.

This module consolidates WikiLink from links.py and KbWikiLink 
from kb_entities.py into a single unified LinkEntity model.
"""

from typing import Optional, List
from pydantic import Field
from rdflib.namespace import SDO as SCHEMA, RDFS, XSD

# Import KB namespace from centralized configuration
from knowledgebase_processor.config.vocabulary import KB
from .base import MarkdownEntity
from .entity_types import ContentEntity


class LinkEntity(MarkdownEntity):
    """Unified link model supporting wikilinks and regular links.
    
    Consolidates WikiLink from links.py and KbWikiLink from kb_entities.py.
    Supports both simple markdown links and rich wikilinks.
    """
    
    entity_type: str = "link"
    element_type: str = "link"  # Can be "link" or "wikilink" for markdown
    
    # Core Link Attributes
    target: str = Field(
        ...,
        description="Link target (URL or page name)",
        json_schema_extra={
            "rdf_property": KB.target,
            "rdf_datatype": XSD.string
        }
    )
    display_text: str = Field(
        ...,
        description="Display text for the link",
        json_schema_extra={
            "rdf_property": RDFS.label,
            "rdf_datatype": XSD.string
        }
    )
    link_type: str = Field(
        ...,
        description="Type: wikilink, markdown, url",
        json_schema_extra={
            "rdf_property": KB.linkType,
            "rdf_datatype": XSD.string
        }
    )
    
    # WikiLink specific (from KbWikiLink)
    original_text: Optional[str] = Field(
        None,
        description="Original wikilink text (e.g., '[[Page Name|Alias]]')",
        json_schema_extra={
            "rdf_property": KB.originalText,
            "rdf_datatype": XSD.string
        }
    )
    target_path: Optional[str] = Field(
        None,
        description="Target path extracted from wikilink",
        json_schema_extra={
            "rdf_property": KB.targetPath,
            "rdf_datatype": XSD.string
        }
    )
    alias: Optional[str] = Field(
        None,
        description="Alias text from wikilink",
        json_schema_extra={
            "rdf_property": KB.alias,
            "rdf_datatype": XSD.string
        }
    )
    resolved_document_uri: Optional[str] = Field(
        None,
        description="URI of resolved document entity",
        json_schema_extra={
            "rdf_property": KB.resolvedDocument,
            "is_object_property": True,
            "rdf_datatype": XSD.anyURI
        }
    )
    
    # Regular link specific
    url: Optional[str] = Field(
        None,
        description="URL for regular markdown links",
        json_schema_extra={
            "rdf_property": SCHEMA.url,
            "rdf_datatype": XSD.anyURI
        }
    )
    is_internal: bool = Field(
        False,
        description="Whether the link is internal to the knowledge base",
        json_schema_extra={
            "rdf_property": KB.isInternal,
            "rdf_datatype": XSD.boolean
        }
    )
    
    # Extracted entities from link text
    entities: List[ContentEntity] = Field(
        default_factory=list,
        description="Entities extracted from link text or target"
    )
    
    # Backward compatibility properties
    @property
    def target_page(self) -> str:
        """Backward compatibility for WikiLink model."""
        return self.target_path or self.target
    
    @property
    def text(self) -> str:
        """Backward compatibility for basic Link model."""
        return self.display_text
    
    class Config:
        json_schema_extra = {
            "rdf_types": [KB.Link, KB.WikiLink],
            "rdfs_label_fallback_fields": ["display_text", "alias", "target"]
        }


class Reference(MarkdownEntity):
    """Represents a markdown reference-style link definition.
    
    Maintains existing Reference model for markdown processing.
    """
    
    element_type: str = "reference"
    entity_type: str = "reference"
    
    key: str = Field(
        ..., 
        description="Reference key/identifier",
        json_schema_extra={
            "rdf_property": KB.referenceKey,
            "rdf_datatype": XSD.string
        }
    )
    url: str = Field(
        ..., 
        description="Reference URL/target",
        json_schema_extra={
            "rdf_property": SCHEMA.url,
            "rdf_datatype": XSD.anyURI
        }
    )
    title: Optional[str] = Field(
        None, 
        description="Optional reference title",
        json_schema_extra={
            "rdf_property": SCHEMA.name,
            "rdf_datatype": XSD.string
        }
    )
    
    class Config:
        json_schema_extra = {
            "rdf_types": [KB.Reference]
        }


class Citation(MarkdownEntity):
    """Represents a citation in markdown.
    
    Maintains existing Citation model for academic content.
    """
    
    element_type: str = "citation"
    entity_type: str = "citation"
    
    citation_text: str = Field(
        ..., 
        description="Citation text",
        json_schema_extra={
            "rdf_property": SCHEMA.citation,
            "rdf_datatype": XSD.string
        }
    )
    reference_key: Optional[str] = Field(
        None, 
        description="Key to a reference if available",
        json_schema_extra={
            "rdf_property": KB.referenceKey,
            "rdf_datatype": XSD.string
        }
    )
    
    # Backward compatibility
    @property
    def text(self) -> str:
        """Backward compatibility for citation text."""
        return self.citation_text
    
    class Config:
        json_schema_extra = {
            "rdf_types": [KB.Citation, SCHEMA.CreativeWork]
        }


# Backward compatibility aliases
WikiLink = LinkEntity
Link = LinkEntity