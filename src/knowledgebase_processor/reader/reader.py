"""Reader implementation for accessing the knowledge base."""

import os
from pathlib import Path
from typing import List, Optional, Iterator

from ..models.content import Document


class Reader:
    """Reader component for accessing the knowledge base.
    
    The Reader is responsible for reading files from the knowledge base
    and providing them to the Processor component.
    """
    
    def __init__(self, base_path: str):
        """Initialize the Reader with the base path of the knowledge base.
        
        Args:
            base_path: The base path of the knowledge base
        """
        self.base_path = Path(base_path)
        if not self.base_path.exists():
            raise ValueError(f"Base path does not exist: {base_path}")
        if not self.base_path.is_dir():
            raise ValueError(f"Base path is not a directory: {base_path}")
    
    def list_files(self, pattern: str = "**/*.md") -> List[Path]:
        """List all files in the knowledge base matching the pattern.
        
        Args:
            pattern: Glob pattern to match files (default: "**/*.md")
            
        Returns:
            List of Path objects for matching files
        """
        return list(self.base_path.glob(pattern))
    
    def read_file(self, path: Path) -> Document:
        """Read a file and return it as a Document.
        
        Args:
            path: Path to the file
            
        Returns:
            Document object containing the file content
        """
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        relative_path = path.relative_to(self.base_path) if path.is_absolute() else path
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title from filename or first heading
        title = path.stem
        
        return Document(
            path=str(relative_path),
            title=title,
            content=content,
            elements=[]  # Elements will be populated by the Processor
        )
    
    def read_all(self, pattern: str = "**/*.md") -> Iterator[Document]:
        """Read all files matching the pattern and yield Documents.
        
        Args:
            pattern: Glob pattern to match files (default: "**/*.md")
            
        Yields:
            Document objects for each matching file
        """
        for path in self.list_files(pattern):
            yield self.read_file(path)