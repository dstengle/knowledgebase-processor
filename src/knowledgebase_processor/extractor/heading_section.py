"""Heading and section extractor implementation."""

from typing import List, Dict, Optional, Tuple
import re
import uuid

from ..models.content import Document, ContentElement
from ..models.markdown import Heading, Section
from .base import BaseExtractor


class HeadingSectionExtractor(BaseExtractor):
    """Extractor for headings and sections from markdown documents.
    
    This extractor identifies all heading levels (H1-H6) and extracts
    the content sections between headings, preserving the hierarchical
    relationships between them.
    """
    
    def __init__(self):
        """Initialize the heading and section extractor."""
        # Regular expression to match markdown headings
        self.heading_regex = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    
    def extract(self, document: Document) -> List[ContentElement]:
        """Extract headings and sections from a document.
        
        Args:
            document: The document to extract from
            
        Returns:
            List of extracted Heading and Section elements
        """
        if not document.content:
            return []
        
        # Extract all headings with their positions
        headings = self._extract_headings(document.content)
        
        # Build the heading hierarchy
        heading_hierarchy = self._build_heading_hierarchy(headings)
        
        # Extract sections between headings
        sections = self._extract_sections(document.content, headings)
        
        # Combine headings and sections
        elements = []
        for heading in headings:
            elements.append(heading)
        for section in sections:
            elements.append(section)
        
        return elements
    
    def _extract_headings(self, content: str) -> List[Heading]:
        """Extract all headings from the content.
        
        Args:
            content: The document content
            
        Returns:
            List of Heading elements
        """
        headings = []
        lines = content.splitlines()
        
        for i, line in enumerate(lines):
            match = self.heading_regex.match(line)
            if match:
                level = len(match.group(1))  # Number of # characters
                text = match.group(2).strip()
                
                heading_id = str(uuid.uuid4())
                position = self.calculate_position(content, i, i)
                heading = Heading(
                    id=heading_id,
                    level=level,
                    text=text,
                    content=text,
                    position=position
                )
                headings.append(heading)
        
        return headings
    
    def _build_heading_hierarchy(self, headings: List[Heading]) -> List[Heading]:
        """Build the hierarchical relationships between headings.
        
        Args:
            headings: List of extracted headings
            
        Returns:
            List of headings with parent-child relationships set
        """
        if not headings:
            return []
        
        # Sort headings by position
        headings_sorted = sorted(headings, key=lambda h: h.position['start'])
        
        # Stack to keep track of parent headings at each level
        # Index 0 is for level 1, index 1 for level 2, etc.
        parent_stack = [None] * 6
        
        for heading in headings_sorted:
            level = heading.level
            
            # Set parent for this heading (parent is the most recent heading with lower level)
            parent_level = level - 1
            while parent_level > 0:
                if parent_stack[parent_level - 1] is not None:
                    heading.parent_id = parent_stack[parent_level - 1].id
                    break
                parent_level -= 1
            
            # Update the parent stack at this level
            parent_stack[level - 1] = heading
            
            # Clear all higher levels in the stack
            for i in range(level, 6):
                parent_stack[i] = None
        
        return headings_sorted
    
    def _extract_sections(self, content: str, headings: List[Heading]) -> List[Section]:
        """Extract sections between headings.
        
        Args:
            content: The document content
            headings: List of extracted headings
            
        Returns:
            List of Section elements
        """
        sections = []
        lines = content.splitlines()
        
        # Sort headings by position
        headings_sorted = sorted(headings, key=lambda h: h.position['start'])
        
        # Create sections between headings
        for i in range(len(headings_sorted)):
            start_line = headings_sorted[i].position['end'] + 1
            
            # End line is either the start of the next heading or the end of the document
            if i < len(headings_sorted) - 1:
                end_line = headings_sorted[i + 1].position['start'] - 1
            else:
                end_line = len(lines) - 1
            
            # Skip empty sections
            if start_line > end_line:
                continue
            
            # Extract section content
            section_content = '\n'.join(lines[start_line:end_line + 1]).strip()
            
            # Create section element
            section_id = str(uuid.uuid4())
            position = self.calculate_position(content, start_line, end_line)
            section = Section(
                id=section_id,
                content=section_content,
                position=position,
                heading_id=headings_sorted[i].id,
                parent_id=headings_sorted[i].id
            )
            sections.append(section)
        
        return sections