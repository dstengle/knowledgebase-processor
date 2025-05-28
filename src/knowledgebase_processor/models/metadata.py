"""Metadata data models for the Knowledge Base Processor."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Set, TYPE_CHECKING
from datetime import datetime
from .common import BaseKnowledgeModel
from .links import Link, WikiLink
from .entities import ExtractedEntity
if TYPE_CHECKING:
    from .markdown import TodoItem # Forward reference for TodoItem


class Tag(BaseKnowledgeModel):
    """Represents a tag in the knowledge base."""

    name: str = Field(..., description="Tag name")
    category: Optional[str] = Field(None, description="Tag category")

    def __hash__(self):
        """Make Tag hashable for use in sets."""
        return hash((self.name, self.category))

    def __eq__(self, other):
        """Define equality for Tag objects."""
        if not isinstance(other, Tag):
            return False
        return self.name == other.name and self.category == other.category


class Frontmatter(BaseKnowledgeModel):
    """Represents frontmatter metadata in a document."""

    title: Optional[str] = Field(None, description="Document title")
    date: Optional[datetime] = Field(None, description="Document date")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom frontmatter fields")



class DocumentMetadata(BaseKnowledgeModel):
    """Represents the complete metadata for a document."""

    document_id: str = Field(..., description="ID of the associated document")
    title: Optional[str] = Field(None, description="Document title")
    path: Optional[str] = Field(None, description="Document path")
    frontmatter: Optional[Frontmatter] = Field(None, description="Frontmatter metadata")
    tags: Set[str] = Field(default_factory=set, description="All tags in the document")
    links: List["Link"] = Field(default_factory=list, description="Links in the document")
    references: List[Dict[str, Any]] = Field(default_factory=list, description="References in the document")
    structure: Dict[str, Any] = Field(default_factory=dict, description="Document structure metadata")
    wikilinks: List[WikiLink] = Field(default_factory=list, description="WikiLinks in the document")
    entities: List[ExtractedEntity] = Field(default_factory=list, description="Extracted entities from the content, including text, label, and character offsets.")
    todo_items: List["TodoItem"] = Field(default_factory=list, description="Extracted ToDo items from the document.")