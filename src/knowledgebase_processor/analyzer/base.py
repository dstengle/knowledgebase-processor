"""Base analyzer implementation."""

from abc import ABC, abstractmethod

from ..models.content import Document


class BaseAnalyzer(ABC):
    """Base class for all analyzers.
    
    Analyzers are responsible for analyzing document content and elements
    to derive additional insights and metadata.
    """
    
    @abstractmethod
    def analyze(self, document: Document) -> None:
        """Analyze a document and update it with derived insights.
        
        This method should modify the document in-place to add derived
        information or update existing elements.
        
        Args:
            document: The document to analyze
        """
        pass