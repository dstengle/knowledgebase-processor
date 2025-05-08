"""Todo item extractor implementation."""

import re
from typing import List, Optional, Dict, Any

from .base import BaseExtractor
from ..models.content import Document, ContentElement
from ..models.markdown import TodoItem, Section


class TodoItemExtractor(BaseExtractor):
    """Extractor for todo items in markdown documents.
    
    Extracts todo items in the format:
    - [ ] Unchecked todo item
    - [x] Checked todo item
    
    Also captures the context (section/list) containing the todo item.
    """
    
    def __init__(self):
        """Initialize the TodoItemExtractor."""
        # Regex pattern for todo items
        self.todo_pattern = re.compile(r'^-\s+\[([ xX])\]\s+(.+)$', re.MULTILINE)
    
    def extract(self, document: Document) -> List[ContentElement]:
        """Extract todo items from a document.
        
        Args:
            document: The document to extract from
            
        Returns:
            List of TodoItem objects
        """
        elements = []
        
        # Find all todo items in the document
        for match in self.todo_pattern.finditer(document.content):
            is_checked = match.group(1).lower() == 'x'
            text = match.group(2)
            
            # Get the position in the document
            start = match.start()
            end = match.end()
            
            # Find the context (section) containing this todo item
            context = self._find_context(document, start)
            
            # Create the todo item
            todo_item = TodoItem(
                element_type="todo_item",
                text=text,
                is_checked=is_checked,
                content=match.group(0),
                position={"start": start, "end": end},
                parent_id=context.get("id") if context else None
            )
            
            elements.append(todo_item)
        
        return elements
    
    def _find_context(self, document: Document, position: int) -> Optional[Dict[str, Any]]:
        """Find the context (section) containing a position in the document.
        
        Args:
            document: The document to search in
            position: The position to find context for
            
        Returns:
            Dictionary with context information or None if not found
        """
        # For simplicity, if there's only one section in the document,
        # use it as the context for all todo items
        sections = [e for e in document.elements if getattr(e, 'element_type', '') == 'section']
        if len(sections) == 1:
            return {
                "id": sections[0].id,
                "type": "section"
            }
        
        # Otherwise, look for a section that contains this position
        for element in document.elements:
            if hasattr(element, 'id') and element.position:
                # Check if the position is within this element's range
                start = element.position.get("start", 0)
                end = element.position.get("end", float('inf'))
                
                if start <= position and end >= position:
                    return {
                        "id": element.id,
                        "type": element.element_type
                    }
        
        # If no context found, return None
        return None