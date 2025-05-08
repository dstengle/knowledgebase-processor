"""Tag extractor implementation."""

import re
from typing import List, Set, Optional

from .base import BaseExtractor
from .frontmatter import FrontmatterExtractor
from ..models.content import Document, ContentElement
from ..models.metadata import Tag


class TagExtractor(BaseExtractor):
    """Extractor for tags in markdown documents.
    
    Extracts tags in various formats:
    - Hashtags: #tag
    - Inline tags: [tag]
    - YAML/TOML frontmatter tags (extracted from frontmatter)
    - Category tags: @category/tag
    """
    
    def __init__(self):
        """Initialize the TagExtractor."""
        # Regex patterns for different tag formats
        self.hashtag_pattern = re.compile(r'#([a-zA-Z0-9_-]+)')
        self.inline_tag_pattern = re.compile(r'\[([a-zA-Z0-9_-]+)\]')
        self.category_tag_pattern = re.compile(r'@([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)')
        
        # Initialize frontmatter extractor for extracting tags from frontmatter
        self.frontmatter_extractor = FrontmatterExtractor()
    
    def extract(self, document: Document) -> List[ContentElement]:
        """Extract tags from a document.
        
        Args:
            document: The document to extract from
            
        Returns:
            List of ContentElement objects representing tags
        """
        elements = []
        
        # Extract hashtags
        for match in self.hashtag_pattern.finditer(document.content):
            tag = match.group(1)
            element = ContentElement(
                element_type="tag",
                content=tag,
                position={"start": match.start(), "end": match.end()},
                metadata={"category": None}
            )
            elements.append(element)
        
        # Extract inline tags
        for match in self.inline_tag_pattern.finditer(document.content):
            tag = match.group(1)
            element = ContentElement(
                element_type="tag",
                content=tag,
                position={"start": match.start(), "end": match.end()},
                metadata={"category": None}
            )
            elements.append(element)
        
        # Extract category tags
        for match in self.category_tag_pattern.finditer(document.content):
            category = match.group(1)
            tag = match.group(2)
            element = ContentElement(
                element_type="tag",
                content=tag,
                position={"start": match.start(), "end": match.end()},
                metadata={"category": category}
            )
            elements.append(element)
        
        # Extract tags from frontmatter
        frontmatter_elements = self.frontmatter_extractor.extract(document)
        if frontmatter_elements:
            frontmatter_element = frontmatter_elements[0]
            frontmatter_format = frontmatter_element.metadata.get("format", "yaml")
            frontmatter_dict = self.frontmatter_extractor.parse_frontmatter(
                frontmatter_element.content,
                frontmatter_format
            )
            
            # Extract tags from frontmatter
            tags = self.frontmatter_extractor._extract_tags_from_frontmatter(frontmatter_dict)
            
            # Create ContentElement for each frontmatter tag
            for tag in tags:
                element = ContentElement(
                    element_type="tag",
                    content=tag,
                    position={
                        "start": frontmatter_element.position["start"],
                        "end": frontmatter_element.position["end"]
                    },
                    metadata={"source": "frontmatter"}
                )
                elements.append(element)
        
        return elements
    
    def get_all_tags(self, document: Document) -> Set[Tag]:
        """Get all unique tags from a document.
        
        Args:
            document: The document to extract tags from
            
        Returns:
            Set of Tag objects
        """
        tag_elements = self.extract(document)
        tags = set()
        
        for element in tag_elements:
            category = None
            if element.metadata and "category" in element.metadata:
                category = element.metadata["category"]
            
            tag = Tag(name=element.content, category=category)
            tags.add(tag)
        
        return tags