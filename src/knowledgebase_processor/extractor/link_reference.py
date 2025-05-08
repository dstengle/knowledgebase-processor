"""Link and reference extractor implementation."""

from typing import List, Dict, Optional, Tuple
import re
import uuid

from ..models.content import Document, ContentElement
from ..models.links import Link, Reference, Citation
from .base import BaseExtractor


class LinkReferenceExtractor(BaseExtractor):
    """Extractor for links and references from markdown documents.
    
    This extractor identifies inline links, reference-style links,
    link reference definitions, and citations in markdown content.
    """
    
    def __init__(self):
        """Initialize the link and reference extractor."""
        # Regular expressions for different link types
        
        # Inline links: [text](url "optional title")
        self.inline_link_regex = re.compile(r'\[([^\]]+)\]\(([^)"]+)(?:\s+"([^"]+)")?\)')
        
        # Reference-style links: [text][reference]
        # Make sure it's a complete reference link pattern
        self.ref_link_regex = re.compile(r'\[([^\]]+)\]\[([^\]]*)\](?!\()')
        
        # Shorthand reference links: [reference]
        # Make sure it's not followed by () or [] and not preceded by ]
        self.shorthand_ref_link_regex = re.compile(r'(?<!\])\[([^\]]+)\](?!\(|\[)')
        
        # Link reference definitions: [reference]: url "optional title"
        self.link_ref_def_regex = re.compile(r'^\[([^\]]+)\]:\s+(\S+)(?:\s+"([^"]+)")?$', re.MULTILINE)
        
        # Citations: (Author, Year) or [@citation]
        self.citation_regex = re.compile(r'(?:\(([^)]+,\s*\d{4}[^)]*)\)|\[@([^\]]+)\])')
    
    def extract(self, document: Document) -> List[ContentElement]:
        """Extract links and references from a document.
        
        Args:
            document: The document to extract from
            
        Returns:
            List of extracted Link, Reference, and Citation elements
        """
        if not document.content:
            return []
        
        elements = []
        
        # Extract link reference definitions first
        references = self._extract_references(document.content)
        elements.extend(references)
        
        # Create a mapping of reference keys to their URLs for resolving reference-style links
        ref_map = {ref.key: ref.url for ref in references}
        
        # Extract inline links
        inline_links = self._extract_inline_links(document.content)
        elements.extend(inline_links)
        
        # Extract reference-style links
        ref_links = self._extract_reference_links(document.content, ref_map)
        elements.extend(ref_links)
        
        # Extract citations
        citations = self._extract_citations(document.content)
        elements.extend(citations)
        
        return elements
    
    def _extract_inline_links(self, content: str) -> List[Link]:
        """Extract inline links from the content.
        
        Args:
            content: The document content
            
        Returns:
            List of Link elements
        """
        links = []
        lines = content.splitlines()
        
        for i, line in enumerate(lines):
            for match in self.inline_link_regex.finditer(line):
                text = match.group(1)
                url = match.group(2)
                
                # Determine if the link is internal (relative path or anchor)
                is_internal = not (url.startswith('http://') or 
                                  url.startswith('https://') or 
                                  url.startswith('ftp://') or
                                  url.startswith('mailto:'))
                
                link_id = str(uuid.uuid4())
                link = Link(
                    id=link_id,
                    text=text,
                    url=url,
                    is_internal=is_internal,
                    content=match.group(0),
                    position={
                        'start': i,
                        'end': i,
                        'start_char': match.start(),
                        'end_char': match.end()
                    }
                )
                links.append(link)
        
        return links
    
    def _extract_reference_links(self, content: str, ref_map: Dict[str, str]) -> List[Link]:
        """Extract reference-style links from the content.
        
        Args:
            content: The document content
            ref_map: Mapping of reference keys to URLs
            
        Returns:
            List of Link elements
        """
        links = []
        lines = content.splitlines()
        
        # Only extract explicit reference links: [text][reference]
        # We're not handling shorthand references to avoid regex conflicts
        for i, line in enumerate(lines):
            # Find all potential reference links
            matches = list(self.ref_link_regex.finditer(line))
            
            for match in matches:
                text = match.group(1)
                ref_key = match.group(2) or text  # If reference is empty, use text as reference
                
                if ref_key in ref_map:
                    url = ref_map[ref_key]
                    
                    # Determine if the link is internal
                    is_internal = not (url.startswith('http://') or
                                      url.startswith('https://') or
                                      url.startswith('ftp://') or
                                      url.startswith('mailto:'))
                    
                    link_id = str(uuid.uuid4())
                    link = Link(
                        id=link_id,
                        text=text,
                        url=url,
                        is_internal=is_internal,
                        content=match.group(0),
                        position={
                            'start': i,
                            'end': i,
                            'start_char': match.start(),
                            'end_char': match.end()
                        },
                        metadata={
                            'reference_key': ref_key
                        }
                    )
                    links.append(link)
        
        return links
    
    def _extract_references(self, content: str) -> List[Reference]:
        """Extract link reference definitions from the content.
        
        Args:
            content: The document content
            
        Returns:
            List of Reference elements
        """
        references = []
        lines = content.splitlines()
        
        for i, line in enumerate(lines):
            match = self.link_ref_def_regex.match(line)
            if match:
                key = match.group(1)
                url = match.group(2)
                title = match.group(3)
                
                ref_id = str(uuid.uuid4())
                reference = Reference(
                    id=ref_id,
                    key=key,
                    url=url,
                    title=title,
                    content=line,
                    position={
                        'start': i,
                        'end': i
                    }
                )
                references.append(reference)
        
        return references
    
    def _extract_citations(self, content: str) -> List[Citation]:
        """Extract citations from the content.
        
        Args:
            content: The document content
            
        Returns:
            List of Citation elements
        """
        citations = []
        lines = content.splitlines()
        
        for i, line in enumerate(lines):
            for match in self.citation_regex.finditer(line):
                # Either (Author, Year) or [@citation] format
                citation_text = match.group(1) or match.group(2)
                
                citation_id = str(uuid.uuid4())
                citation = Citation(
                    id=citation_id,
                    text=citation_text,
                    content=match.group(0),
                    position={
                        'start': i,
                        'end': i,
                        'start_char': match.start(),
                        'end_char': match.end()
                    }
                )
                citations.append(citation)
        
        return citations