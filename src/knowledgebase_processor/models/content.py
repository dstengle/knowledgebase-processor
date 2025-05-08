"""Content data models for the Knowledge Base Processor."""

from pydantic import Field
from typing import Optional, List, Dict, Any, TYPE_CHECKING
import uuid
from .common import BaseKnowledgeModel
from .preservation import ContentPreservationMixin


class ContentElement(BaseKnowledgeModel, ContentPreservationMixin):
    """Base class for all content elements."""
    
    element_type: str = Field(..., description="Type of content element")
    content: str = Field(..., description="Raw content of the element")
    position: Optional[Dict[str, Any]] = Field(None, description="Position in the document")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata for the element")
    
    def preserve_original_content(self, document_content: str) -> None:
        """Preserve the original content from the document.
        
        Args:
            document_content: The full document content
        """
        if not self.position:
            return
        
        start_line = self.position.get('start', 0)
        end_line = self.position.get('end', 0)
        
        if start_line is None or end_line is None:
            return
            
        lines = document_content.splitlines()
        if start_line < 0 or end_line >= len(lines):
            return
            
        original_text = '\n'.join(lines[start_line:end_line + 1])
        
        # Ensure we have an ID
        if not hasattr(self, 'id') or self.id is None:
            self.id = str(uuid.uuid4())
            
        self.preserve_content(original_text, self.position)


class Document(BaseKnowledgeModel):
    """Represents a document in the knowledge base."""
    
    path: str = Field(..., description="Path to the document")
    title: Optional[str] = Field(None, description="Document title")
    content: str = Field(..., description="Raw content of the document")
    elements: List[ContentElement] = Field(default_factory=list, description="Structured elements of the document")
    
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