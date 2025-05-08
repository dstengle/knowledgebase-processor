"""Metadata store implementation."""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

from ..models.metadata import Metadata


class MetadataStore:
    """Store for document metadata.
    
    This is a simple implementation that stores metadata in JSON files.
    In a production system, this might use a database or other storage.
    """
    
    def __init__(self, store_path: str):
        """Initialize the MetadataStore.
        
        Args:
            store_path: Path to the directory where metadata will be stored
        """
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        self.metadata_cache = {}  # In-memory cache of metadata
    
    def save(self, metadata: Metadata) -> None:
        """Save metadata to the store.
        
        Args:
            metadata: The metadata to save
        """
        # Create a serializable representation of the metadata
        metadata_dict = metadata.model_dump()
        
        # Generate a filename based on the document ID
        filename = f"{metadata.document_id.replace('/', '_')}.json"
        file_path = self.store_path / filename
        
        # Write the metadata to a JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, indent=2, default=self._json_serializer)
        
        # Update the cache
        self.metadata_cache[metadata.document_id] = metadata
    
    def get(self, document_id: str) -> Optional[Metadata]:
        """Get metadata for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Metadata object if found, None otherwise
        """
        # Check the cache first
        if document_id in self.metadata_cache:
            return self.metadata_cache[document_id]
        
        # Generate the filename
        filename = f"{document_id.replace('/', '_')}.json"
        file_path = self.store_path / filename
        
        # Check if the file exists
        if not file_path.exists():
            return None
        
        # Read the metadata from the file
        with open(file_path, 'r', encoding='utf-8') as f:
            metadata_dict = json.load(f)
        
        # Create a Metadata object
        metadata = Metadata.model_validate(metadata_dict)
        
        # Update the cache
        self.metadata_cache[document_id] = metadata
        
        return metadata
    
    def list_all(self) -> List[str]:
        """List all document IDs in the store.
        
        Returns:
            List of document IDs
        """
        # List all JSON files in the store directory
        files = list(self.store_path.glob('*.json'))
        
        # Extract document IDs from filenames
        document_ids = [f.stem.replace('_', '/') for f in files]
        
        return document_ids
    
    def search(self, query: Dict[str, Any]) -> List[str]:
        """Search for documents matching the query.
        
        Args:
            query: Dictionary of search criteria
            
        Returns:
            List of matching document IDs
        """
        # This is a placeholder implementation
        # In a real system, this would use a more sophisticated search mechanism
        
        results = []
        
        # Load all metadata if not in cache
        for doc_id in self.list_all():
            if doc_id not in self.metadata_cache:
                self.get(doc_id)
        
        # Simple linear search through the cache
        for doc_id, metadata in self.metadata_cache.items():
            match = True
            
            # Check each query criterion
            for key, value in query.items():
                if key == 'tags' and isinstance(value, str):
                    # Check if the document has the specified tag
                    if value not in metadata.tags:
                        match = False
                        break
                # Add more search criteria as needed
            
            if match:
                results.append(doc_id)
        
        return results
        
    def _json_serializer(self, obj):
        """Custom JSON serializer for objects not serializable by default json code.
        
        Args:
            obj: The object to serialize
            
        Returns:
            A JSON serializable version of the object
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, set):
            return list(obj)
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")