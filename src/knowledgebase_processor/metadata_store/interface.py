from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..models.metadata import DocumentMetadata

class MetadataStoreInterface(ABC):
    @abstractmethod
    def save(self, metadata: DocumentMetadata) -> None:
        """Save metadata to the store."""
        pass

    @abstractmethod
    def get(self, document_id: str) -> Optional[DocumentMetadata]:
        """Retrieve metadata for a document."""
        pass

    @abstractmethod
    def list_all(self) -> List[str]:
        """List all document IDs."""
        pass

    @abstractmethod
    def search(self, query: Dict[str, Any]) -> List[str]:
        """Search for documents matching the query."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the store and release resources."""
        pass