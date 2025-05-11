"""Link and reference data models for the Knowledge Base Processor."""

from pydantic import Field
from typing import Optional, List
from .markdown import MarkdownElement


class Link(MarkdownElement):
    """Represents a markdown link."""
    
    element_type: str = "link"
    text: str = Field(..., description="Link text/label")
    url: str = Field(..., description="Link URL/target")
    is_internal: bool = Field(False, description="Whether the link is internal to the knowledge base")


class Reference(MarkdownElement):
    """Represents a markdown reference-style link definition."""
    
    element_type: str = "reference"
    key: str = Field(..., description="Reference key/identifier")
    url: str = Field(..., description="Reference URL/target")
    title: Optional[str] = Field(None, description="Optional reference title")


class Citation(MarkdownElement):
    """Represents a citation in markdown."""
    
    element_type: str = "citation"
    text: str = Field(..., description="Citation text")
    reference_key: Optional[str] = Field(None, description="Key to a reference if available")
class WikiLink(MarkdownElement):
    """Represents a wikilink ([[Page Name]] or [[Page Name|Display Text]])."""

    element_type: str = "wikilink"
    target_page: str = Field(..., description="Target page name")
    display_text: str = Field(..., description="Display text for the link (may be same as target_page)")