"""Base parser implementation."""

from abc import ABC, abstractmethod
from typing import List

from ..models.content import Document, ContentElement


class BaseParser(ABC):
    """Base class for all parsers.
    
    Parsers are responsible for parsing document content into structured
    elements, such as markdown elements, code elements, etc.
    """
    
    @abstractmethod
    def parse(self, document: Document) -> List[ContentElement]:
        """Parse a document into content elements.
        
        Args:
            document: The document to parse
            
        Returns:
            List of parsed ContentElement objects
        """
        pass