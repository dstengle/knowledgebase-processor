"""Content data models for the Knowledge Base Processor."""

from pydantic import Field
from typing import Optional, List, Dict, Any, TYPE_CHECKING
import uuid
from .common import BaseKnowledgeModel
from .preservation import ContentPreservationMixin
from .elements import ContentElement
# Import ExtractedEntity directly, DocumentMetadata under TYPE_CHECKING
from .entities import ExtractedEntity

if TYPE_CHECKING:
    from .metadata import DocumentMetadata

if TYPE_CHECKING:
    from .metadata import Entity
class Document(BaseKnowledgeModel):
    """Represents a document in the knowledge base."""
    
    path: str = Field(..., description="Path to the document")
    title: Optional[str] = Field(None, description="Document title")
    content: str = Field(..., description="Raw content of the document")
    elements: List[ContentElement] = Field(default_factory=list, description="Structured elements of the document")
    
    entities: Optional[List[ExtractedEntity]] = None # Changed to ExtractedEntity
    metadata: Optional["DocumentMetadata"] = Field(None, description="Full metadata of the document") # Added metadata field
    
    def preserve_content(self) -> None:
        """Preserve the original content for all elements in the document."""
        for element in self.elements:
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
            raise ValueError(f"Position out of range: {start_line}-{end_line}, document has {len(lines)} lines")
        
        return '\n'.join(lines[start_line:end_line + 1])