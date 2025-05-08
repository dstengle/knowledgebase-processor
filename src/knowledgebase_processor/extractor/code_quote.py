"""Code block and blockquote extractor implementation."""

from typing import List, Dict, Optional, Tuple
import re
import uuid

from ..models.content import Document, ContentElement
from ..models.markdown import CodeBlock, Blockquote
from .base import BaseExtractor


class CodeQuoteExtractor(BaseExtractor):
    """Extractor for code blocks and blockquotes from markdown documents.
    
    This extractor identifies:
    - Code blocks with language specification (```language\n...\n```)
    - Blockquotes with proper nesting (> text)
    
    It preserves the content within these blocks and their structure.
    """
    
    def __init__(self):
        """Initialize the code block and blockquote extractor."""
        # Regular expression to match code blocks
        # Group 1: language (optional)
        # Group 2: code content
        self.code_block_regex = re.compile(
            r'```([\w+-]*)?\s*\n(.*?)\n\s*```',
            re.DOTALL
        )
        
        # Regular expression to match blockquotes
        # We'll handle nesting separately by counting '>' characters
        self.blockquote_regex = re.compile(
            r'^[ \t]*(>+)[ ]?(.*?)$',
            re.MULTILINE
        )
    
    def extract(self, document: Document) -> List[ContentElement]:
        """Extract code blocks and blockquotes from a document.
        
        Args:
            document: The document to extract from
            
        Returns:
            List of extracted CodeBlock and Blockquote elements
        """
        if not document.content:
            return []
        
        elements = []
        
        # Extract code blocks
        code_blocks = self._extract_code_blocks(document.content)
        elements.extend(code_blocks)
        
        # Extract blockquotes
        blockquotes = self._extract_blockquotes(document.content)
        elements.extend(blockquotes)
        
        return elements
    
    def _extract_code_blocks(self, content: str) -> List[CodeBlock]:
        """Extract code blocks from the content.
        
        Args:
            content: The document content
            
        Returns:
            List of CodeBlock elements
        """
        code_blocks = []
        
        # Find all code blocks in the content
        for match in self.code_block_regex.finditer(content):
            language = match.group(1).strip() if match.group(1) else None
            code_content = match.group(2)
            
            # Normalize indentation - find common indentation and remove it
            lines = code_content.splitlines()
            if lines:
                # Find minimum indentation (excluding empty lines)
                non_empty_lines = [line for line in lines if line.strip()]
                if non_empty_lines:
                    min_indent = min(len(line) - len(line.lstrip()) for line in non_empty_lines)
                    # Remove common indentation
                    normalized_lines = []
                    for line in lines:
                        if line.strip():  # Non-empty line
                            normalized_lines.append(line[min_indent:] if len(line) >= min_indent else line)
                        else:  # Empty line
                            normalized_lines.append(line)
                    code_content = '\n'.join(normalized_lines)
            
            # Calculate position
            start_pos = content[:match.start()].count('\n')
            end_pos = start_pos + code_content.count('\n') + 2  # +2 for the ``` lines
            
            # Create code block element
            code_block_id = str(uuid.uuid4())
            code_block = CodeBlock(
                id=code_block_id,
                language=language,
                code=code_content,
                content=code_content,
                position={
                    'start': start_pos,
                    'end': end_pos
                }
            )
            code_blocks.append(code_block)
        
        return code_blocks
    
    def _extract_blockquotes(self, content: str) -> List[Blockquote]:
        """Extract blockquotes from the content.
        
        Args:
            content: The document content
            
        Returns:
            List of Blockquote elements
        """
        blockquotes = []
        lines = content.splitlines()
        
        # Track consecutive blockquote lines
        current_blockquote = {
            'level': 0,
            'content': [],
            'start': -1,
            'end': -1
        }
        
        for i, line in enumerate(lines):
            match = self.blockquote_regex.match(line)
            
            if match:
                level = len(match.group(1))  # Number of > characters
                text = match.group(2)
                
                # If this is the start of a new blockquote or a different level
                if current_blockquote['start'] == -1 or current_blockquote['level'] != level:
                    # Save the previous blockquote if it exists
                    if current_blockquote['start'] != -1:
                        self._save_blockquote(current_blockquote, blockquotes)
                    
                    # Start a new blockquote
                    current_blockquote = {
                        'level': level,
                        'content': [text],
                        'start': i,
                        'end': i
                    }
                else:
                    # Continue the current blockquote
                    current_blockquote['content'].append(text)
                    current_blockquote['end'] = i
            else:
                # If we were tracking a blockquote and hit a non-blockquote line
                if current_blockquote['start'] != -1:
                    self._save_blockquote(current_blockquote, blockquotes)
                    current_blockquote = {
                        'level': 0,
                        'content': [],
                        'start': -1,
                        'end': -1
                    }
        
        # Save the last blockquote if it exists
        if current_blockquote['start'] != -1:
            self._save_blockquote(current_blockquote, blockquotes)
        
        return blockquotes
    
    def _save_blockquote(self, blockquote_data: Dict, blockquotes: List[Blockquote]):
        """Save a blockquote to the list.
        
        Args:
            blockquote_data: Dictionary with blockquote data
            blockquotes: List to append the blockquote to
        """
        blockquote_id = str(uuid.uuid4())
        blockquote_content = '\n'.join(blockquote_data['content'])
        
        blockquote = Blockquote(
            id=blockquote_id,
            level=blockquote_data['level'],
            content=blockquote_content,
            position={
                'start': blockquote_data['start'],
                'end': blockquote_data['end']
            }
        )
        blockquotes.append(blockquote)