"""Base extractor implementation."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional

from ..models.content import Document, ContentElement


class BaseExtractor(ABC):
    """Base class for all extractors.
    
    Extractors are responsible for extracting specific types of content
    from documents, such as frontmatter, tags, headings, etc.
    """
    
    @abstractmethod
    def extract(self, document: Document) -> List[ContentElement]:
        """Extract content elements from a document.
        
        Args:
            document: The document to extract from
            
        Returns:
            List of extracted ContentElement objects
        """
        pass
    
    def calculate_position(self, content_or_document, start_line: int, end_line: int,
                          start_col: Optional[int] = None, end_col: Optional[int] = None) -> Dict[str, Any]:
        """Calculate position information for a content element.
        
        Args:
            content_or_document: The document or content string
            start_line: Starting line number (0-based)
            end_line: Ending line number (0-based)
            start_col: Starting column number (0-based, optional)
            end_col: Ending column number (0-based, optional)
            
        Returns:
            Dictionary with position information
        """
        # Handle both Document objects and string content
        if isinstance(content_or_document, Document):
            content = content_or_document.content
        else:
            content = content_or_document
            
        lines = content.splitlines()
        
        # Calculate character offsets
        start_offset = 0
        for i in range(start_line):
            start_offset += len(lines[i]) + 1  # +1 for newline
            
        end_offset = start_offset
        for i in range(start_line, end_line + 1):
            end_offset += len(lines[i]) + 1  # +1 for newline
        
        # Adjust for columns if provided
        if start_col is not None:
            start_offset += start_col
        
        if end_col is not None:
            # Subtract the length of the last line and add end_col
            end_offset = end_offset - len(lines[end_line]) - 1 + end_col
        else:
            # If no end_col, end at the end of the line
            end_offset -= 1  # Remove the last newline
            
        position = {
            'start': start_line,
            'end': end_line,
            'start_offset': start_offset,
            'end_offset': end_offset
        }
        
        if start_col is not None:
            position['start_col'] = start_col
        
        if end_col is not None:
            position['end_col'] = end_col
            
        return position