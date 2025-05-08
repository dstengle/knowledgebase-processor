"*""Markdown extractor implementation."""


from typing import List

from ..models.content import Document, ContentElement
from ..parser.markdown_parser import MarkdownParser
from .base import BaseExtractor


class MarkdownExtractor(BaseExtractor):
    """Extractor for markdown elements.
    
    This extractor uses the MarkdownParser to extract structured
    elements from markdown documents.
    """
    
    def __init__(self):
        """Initialize the Markdown extractor."""
        self.parser = MarkdownParser()
    
    def extract(self, document: Document) -> List[ContentElement]:
        """Extract markdown elements from a document.
        
        Args:
            document: The document to extract from
            
        Returns:
            List of extracted markdown elements
        """
        return self.parser.parse(document)