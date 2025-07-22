"""Reader implementation for accessing the knowledge base."""

import os
import re
import yaml
from pathlib import Path
from typing import List, Optional, Iterator, Dict, Any

from ..models.content import Document
from ..models.metadata import DocumentMetadata, Frontmatter
from ..utils.logging import get_logger

logger = get_logger(__name__)


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
        if not pattern:
            logger.warning("Empty pattern provided to list_files, defaulting to '**/*.md'")
            pattern = "**/*.md"
        return list(self.base_path.glob(pattern))

    def read_all_paths(self, pattern: str = "**/*.md") -> Iterator[Path]:
        """Read all file paths matching the pattern.
        
        Args:
            pattern: Glob pattern to match files (default: "**/*.md")
            
        Yields:
            Path objects for each matching file
        """
        if not pattern:
            logger.warning("Empty pattern provided to read_all_paths, defaulting to '**/*.md'")
            pattern = "**/*.md"
        for path in self.list_files(pattern):
            yield path

    def read_content(self, path: str) -> str:
        """Reads the content of a file.

        Args:
            path: The absolute path to the file.

        Returns:
            The content of the file as a string.
        """
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def parse_frontmatter(self, content: str) -> tuple[Optional[Dict[str, Any]], str]:
        """Parse YAML frontmatter from markdown content.
        
        Args:
            content: Raw markdown content
            
        Returns:
            Tuple of (frontmatter_dict, content_without_frontmatter)
        """
        # Check for YAML frontmatter pattern
        frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL | re.MULTILINE)
        match = frontmatter_pattern.match(content)
        
        if not match:
            return None, content
            
        try:
            # Parse the YAML frontmatter
            yaml_content = match.group(1)
            frontmatter_data = yaml.safe_load(yaml_content) or {}
            
            # Remove frontmatter from content
            content_without_frontmatter = content[match.end():]
            
            return frontmatter_data, content_without_frontmatter
            
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse YAML frontmatter: {e}")
            return None, content
    
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
        
        content = self.read_content(str(path))
        
        # Parse frontmatter
        frontmatter_data, content_without_frontmatter = self.parse_frontmatter(content)
        
        # Determine title: frontmatter title > processed filename > first heading
        if frontmatter_data and 'title' in frontmatter_data:
            title = frontmatter_data['title']
        else:
            # Fall back to processed filename first (convert underscores/hyphens to spaces)
            title = path.stem.replace("_", " ").replace("-", " ")
            
            # If filename processing results in something generic, try first heading
            if not title or title.lower() in ['readme', 'index', 'untitled']:
                heading_match = re.search(r'^#\s+(.+)$', content_without_frontmatter, re.MULTILINE)
                if heading_match:
                    title = heading_match.group(1).strip()
        
        # Create Frontmatter object if we have frontmatter data
        frontmatter_obj = None
        if frontmatter_data:
            # Handle tags - they might be a list or a string
            tags = frontmatter_data.get('tags', [])
            if isinstance(tags, str):
                tags = [tags]
            elif tags is None:
                tags = []
                
            # Handle date
            date_val = frontmatter_data.get('date')
            if isinstance(date_val, str):
                try:
                    from datetime import datetime
                    date_val = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                except ValueError:
                    logger.warning(f"Could not parse date from frontmatter: {date_val}")
                    date_val = None
            
            frontmatter_obj = Frontmatter(
                title=frontmatter_data.get('title'),
                date=date_val,
                tags=tags,
                custom_fields={k: v for k, v in frontmatter_data.items() 
                             if k not in ['title', 'date', 'tags']}
            )
        
        # Create metadata
        doc_metadata = DocumentMetadata(
            document_id=str(relative_path),  # Will be replaced by proper ID generation later
            path=str(relative_path),
            title=title,
            frontmatter=frontmatter_obj,
            tags=set(frontmatter_obj.tags) if frontmatter_obj else set(),
            links=[],  # Will be populated by extractors
            wikilinks=[],  # Will be populated by extractors
            entities=[],  # Will be populated by extractors
            references=[],
            structure={}
        )
        
        return Document(
            path=str(relative_path),
            title=title,
            content=content,
            elements=[],  # Elements will be populated by the Processor
            metadata=doc_metadata
        )
    
    def read_all(self, pattern: str = "**/*.md") -> Iterator[Document]:
        """Read all files matching the pattern and yield Documents.
        
        Args:
            pattern: Glob pattern to match files (default: "**/*.md")
            
        Yields:
            Document objects for each matching file
        """
        if not pattern:
            logger.warning("Empty pattern provided to read_all, defaulting to '**/*.md'")
            pattern = "**/*.md"
        for path in self.list_files(pattern):
            yield self.read_file(path)