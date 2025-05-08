"""Base enricher implementation."""

from abc import ABC, abstractmethod

from ..models.content import Document


class BaseEnricher(ABC):
    """Base class for all enrichers.
    
    Enrichers are responsible for enriching documents with additional
    information derived from external sources or cross-document analysis.
    """
    
    @abstractmethod
    def enrich(self, document: Document) -> None:
        """Enrich a document with additional information.
        
        This method should modify the document in-place to add derived
        information or update existing elements.
        
        Args:
            document: The document to enrich
        """
        pass