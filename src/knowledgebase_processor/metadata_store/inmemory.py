from typing import List, Dict, Any, Optional
from .interface import MetadataStoreInterface
from ..models.metadata import DocumentMetadata

class InMemoryMetadataStore(MetadataStoreInterface):
    def __init__(self):
        self._store: Dict[str, DocumentMetadata] = {}

    def save(self, metadata: DocumentMetadata) -> None:
        self._store[metadata.document_id] = metadata

    def get(self, document_id: str) -> Optional[DocumentMetadata]:
        return self._store.get(document_id)

    def list_all(self) -> List[str]:
        return list(self._store.keys())

    def search(self, query: Dict[str, Any]) -> List[str]:
        results = []
        for doc_id, metadata in self._store.items():
            if 'tags' in query and hasattr(metadata, 'tags'):
                if query['tags'] in getattr(metadata, 'tags', []):
                    results.append(doc_id)
            elif 'title_contains' in query and hasattr(metadata, 'title'):
                if query['title_contains'].lower() in (metadata.title or '').lower():
                    results.append(doc_id)
        return results

    def close(self) -> None:
        pass