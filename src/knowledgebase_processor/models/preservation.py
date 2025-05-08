"""Content preservation models for the Knowledge Base Processor."""

from pydantic import Field
from typing import Optional, Dict, Any, List, Tuple
from .common import BaseKnowledgeModel


class ContentPosition(BaseKnowledgeModel):
    """Represents the position of content within a document."""
    
    start_line: int = Field(..., description="Starting line number (0-based)")
    end_line: int = Field(..., description="Ending line number (0-based)")
    start_col: Optional[int] = Field(None, description="Starting column number (0-based)")
    end_col: Optional[int] = Field(None, description="Ending column number (0-based)")
    start_offset: Optional[int] = Field(None, description="Starting character offset from document start")
    end_offset: Optional[int] = Field(None, description="Ending character offset from document start")


class PreservedContent(BaseKnowledgeModel):
    """Represents preserved original content with position information."""
    
    original_text: str = Field(..., description="The original text content")
    position: ContentPosition = Field(..., description="Position information")
    element_id: str = Field(..., description="ID of the associated content element")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, 
                                             description="Additional context about the content")


class ContentPreservationMixin:
    """Mixin to add content preservation capabilities to content elements."""
    
    @property
    def preserved_content(self) -> Optional[PreservedContent]:
        """Get the preserved content for this element."""
        if not hasattr(self, '_preserved_content'):
            return None
        return self._preserved_content
    
    @preserved_content.setter
    def preserved_content(self, value: PreservedContent):
        """Set the preserved content for this element."""
        self._preserved_content = value
    
    def preserve_content(self, original_text: str, position: Dict[str, Any]):
        """Preserve the original content with position information."""
        content_position = ContentPosition(
            start_line=position.get('start', 0),
            end_line=position.get('end', 0),
            start_col=position.get('start_col'),
            end_col=position.get('end_col'),
            start_offset=position.get('start_offset'),
            end_offset=position.get('end_offset')
        )
        
        self._preserved_content = PreservedContent(
            original_text=original_text,
            position=content_position,
            element_id=self.id
        )