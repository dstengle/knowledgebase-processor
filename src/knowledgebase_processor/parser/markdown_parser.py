"""Markdown parser implementation."""

import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
from markdown_it import MarkdownIt
from markdown_it.token import Token

from ..models.content import Document, ContentElement
from ..models.markdown import (
    MarkdownElement, Heading, Section, MarkdownList,
    ListItem, TodoItem, Table, TableCell, CodeBlock, Blockquote
)
from .base import BaseParser


class MarkdownParser(BaseParser):
    """Parser for Markdown content.
    
    This parser uses markdown-it-py to parse markdown content into
    structured elements.
    """
    
    def __init__(self):
        """Initialize the Markdown parser."""
        self.md = MarkdownIt("commonmark", {"enable_tables": True})
        
    def parse(self, document: Document) -> List[ContentElement]:
        """Parse a document into markdown elements.
        
        Args:
            document: The document to parse
            
        Returns:
            List of parsed markdown elements
        """
        if not document.content:
            return []
        
        # Parse the markdown content
        tokens = self.md.parse(document.content)
        
        # Process the tokens into elements
        elements = self._process_tokens(tokens, document.content)
        
        return elements
    
    def _process_tokens(self, tokens: List[Token], content: str) -> List[MarkdownElement]:
        """Process markdown tokens into structured elements.
        
        Args:
            tokens: List of markdown tokens
            content: Original markdown content
            
        Returns:
            List of markdown elements
        """
        elements = []
        current_section = None
        current_list = None
        current_table = None
        current_blockquote_level = 0
        
        # Track parent-child relationships
        parent_stack = []
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # Process headings
            if token.type == 'heading_open':
                level = int(token.tag[1])  # h1, h2, etc.
                content_token = tokens[i + 1]
                heading_text = content_token.content
                
                # Get the position in the document
                position = {
                    'start': token.map[0] if token.map else 0,
                    'end': tokens[i + 2].map[1] if tokens[i + 2].map else 0
                }
                
                # Create heading element
                heading_id = str(uuid.uuid4())
                heading = Heading(
                    id=heading_id,
                    level=level,
                    text=heading_text,
                    content=heading_text,
                    position=position,
                    parent_id=parent_stack[-1].id if parent_stack else None
                )
                elements.append(heading)
                
                # Create a new section for this heading
                section_id = str(uuid.uuid4())
                current_section = Section(
                    id=section_id,
                    content="",
                    position={
                        'start': position['end'],
                        'end': 0  # Will be updated when the section ends
                    },
                    heading_id=heading_id,
                    parent_id=heading_id
                )
                elements.append(current_section)
                
                # Skip the content and closing tokens
                i += 3
                continue
            
            # Process lists
            elif token.type == 'bullet_list_open' or token.type == 'ordered_list_open':
                list_id = str(uuid.uuid4())
                
                # Determine the parent of this list
                parent_id = None
                if parent_stack and isinstance(parent_stack[-1], MarkdownList):
                    # This is a nested list, parent is the current list
                    parent_id = parent_stack[-1].id
                elif parent_stack:
                    # This might be a list inside a list item
                    parent_id = parent_stack[-1].id
                elif current_section:
                    # Top-level list in a section
                    parent_id = current_section.id
                
                new_list = MarkdownList(
                    id=list_id,
                    ordered=token.type == 'ordered_list_open',
                    content="",
                    position={
                        'start': token.map[0] if token.map else 0,
                        'end': 0  # Will be updated when the list ends
                    },
                    parent_id=parent_id
                )
                elements.append(new_list)
                parent_stack.append(new_list)
                current_list = new_list
                i += 1
                continue
                
            elif token.type == 'bullet_list_close' or token.type == 'ordered_list_close':
                if parent_stack and isinstance(parent_stack[-1], MarkdownList):
                    # Update the end position of the current list
                    parent_stack[-1].position['end'] = token.map[1] if token.map else 0
                    
                    # Pop the current list from the stack
                    popped = parent_stack.pop()
                    
                    # Update current_list to the parent list if there is one
                    if parent_stack and isinstance(parent_stack[-1], MarkdownList):
                        current_list = parent_stack[-1]
                    else:
                        current_list = None
                i += 1
                continue
                
            elif token.type == 'list_item_open':
                in_todo = False
                is_checked = False
                
                # Check if this is a todo item by looking ahead
                if i + 2 < len(tokens) and tokens[i + 2].type == 'inline':
                    inline_content = tokens[i + 2].content
                    todo_match = re.match(r'^\[([ xX])\]\s+(.+)$', inline_content)
                    if todo_match:
                        in_todo = True
                        is_checked = todo_match.group(1).lower() == 'x'
                        item_text = todo_match.group(2)
                    else:
                        item_text = inline_content
                else:
                    item_text = ""
                
                item_id = str(uuid.uuid4())
                if in_todo:
                    item = TodoItem(
                        id=item_id,
                        text=item_text,
                        is_checked=is_checked,
                        content=item_text,
                        position={
                            'start': token.map[0] if token.map else 0,
                            'end': 0  # Will be updated when the item ends
                        },
                        parent_id=current_list.id if current_list else None
                    )
                else:
                    item = ListItem(
                        id=item_id,
                        text=item_text,
                        content=item_text,
                        position={
                            'start': token.map[0] if token.map else 0,
                            'end': 0  # Will be updated when the item ends
                        },
                        parent_id=current_list.id if current_list else None
                    )
                
                elements.append(item)
                if current_list:
                    current_list.items.append(item)
                
                # Add this item to the parent stack to handle nested lists
                parent_stack.append(item)
                
                # Process the content of this list item
                j = i + 1
                nesting = 1
                while j < len(tokens) and nesting > 0:
                    # If we find a nested list, we'll process it in the next iteration
                    if tokens[j].type == 'bullet_list_open' or tokens[j].type == 'ordered_list_open':
                        break
                        
                    if tokens[j].type == 'list_item_open':
                        nesting += 1
                    elif tokens[j].type == 'list_item_close':
                        nesting -= 1
                        
                        # If this is the closing of our current item
                        if nesting == 0:
                            # Update the end position
                            item.position['end'] = tokens[j].map[1] if tokens[j].map else 0
                            
                            # Remove this item from the parent stack
                            if parent_stack and parent_stack[-1].id == item_id:
                                parent_stack.pop()
                    j += 1
                
                # If we didn't hit a nested list, move to the next token after this item
                if j < len(tokens) and tokens[j].type not in ['bullet_list_open', 'ordered_list_open']:
                    i = j
                else:
                    # We found a nested list, so just move past the list_item_open token
                    i += 1
                continue
            
            # Process code blocks
            elif token.type == 'fence':
                code_id = str(uuid.uuid4())
                code_block = CodeBlock(
                    id=code_id,
                    language=token.info,
                    code=token.content,
                    content=token.content,
                    position={
                        'start': token.map[0],
                        'end': token.map[1]
                    },
                    parent_id=current_section.id if current_section else None
                )
                elements.append(code_block)
                i += 1
                continue
            
            # Process tables
            elif token.type == 'table_open':
                table_id = str(uuid.uuid4())
                current_table = Table(
                    id=table_id,
                    content="",
                    position={
                        'start': token.map[0] if token.map else 0,
                        'end': 0  # Will be updated when the table ends
                    },
                    parent_id=current_section.id if current_section else None
                )
                elements.append(current_table)
                
                # Process table headers and rows
                row_index = 0
                j = i + 1
                while j < len(tokens) and tokens[j].type != 'table_close':
                    if tokens[j].type == 'thead_open':
                        # Process headers
                        header_row = []
                        k = j + 1
                        while k < len(tokens) and tokens[k].type != 'thead_close':
                            if tokens[k].type == 'th_open':
                                if k + 1 < len(tokens) and tokens[k + 1].type == 'inline':
                                    header_text = tokens[k + 1].content
                                    header_row.append(header_text)
                                    
                                    # Create a cell for this header
                                    cell_id = str(uuid.uuid4())
                                    cell = TableCell(
                                        id=cell_id,
                                        text=header_text,
                                        column=len(header_row) - 1,
                                        row=row_index,
                                        is_header=True,
                                        content=header_text,
                                        position={
                                            'start': tokens[k].map[0] if tokens[k].map else 0,
                                            'end': tokens[k + 2].map[1] if k + 2 < len(tokens) and tokens[k + 2].map else 0
                                        },
                                        parent_id=table_id
                                    )
                                    current_table.cells.append(cell)
                            k += 1
                        current_table.headers = header_row
                        row_index += 1
                    elif tokens[j].type == 'tbody_open':
                        # Process rows
                        k = j + 1
                        while k < len(tokens) and tokens[k].type != 'tbody_close':
                            if tokens[k].type == 'tr_open':
                                row = []
                                l = k + 1
                                col_index = 0
                                while l < len(tokens) and tokens[l].type != 'tr_close':
                                    if tokens[l].type == 'td_open':
                                        if l + 1 < len(tokens) and tokens[l + 1].type == 'inline':
                                            cell_text = tokens[l + 1].content
                                            row.append(cell_text)
                                            
                                            # Create a cell for this data
                                            cell_id = str(uuid.uuid4())
                                            cell = TableCell(
                                                id=cell_id,
                                                text=cell_text,
                                                column=col_index,
                                                row=row_index,
                                                is_header=False,
                                                content=cell_text,
                                                position={
                                                    'start': tokens[l].map[0] if tokens[l].map else 0,
                                                    'end': tokens[l + 2].map[1] if l + 2 < len(tokens) and tokens[l + 2].map else 0
                                                },
                                                parent_id=table_id
                                            )
                                            current_table.cells.append(cell)
                                            col_index += 1
                                    l += 1
                                current_table.rows.append(row)
                                row_index += 1
                            k += 1
                    j += 1
                
                if j < len(tokens) and tokens[j].type == 'table_close':
                    current_table.position['end'] = tokens[j].map[1] if tokens[j].map else 0
                    current_table = None
                
                i = j + 1
                continue
            
            # Process blockquotes
            elif token.type == 'blockquote_open':
                current_blockquote_level += 1
                blockquote_id = str(uuid.uuid4())
                
                # Find the content of this blockquote
                j = i + 1
                blockquote_content = ""
                while j < len(tokens) and tokens[j].type != 'blockquote_close':
                    if tokens[j].type == 'inline':
                        blockquote_content += tokens[j].content + "\n"
                    j += 1
                
                blockquote = Blockquote(
                    id=blockquote_id,
                    level=current_blockquote_level,
                    content=blockquote_content.strip(),
                    position={
                        'start': token.map[0] if token.map else 0,
                        'end': tokens[j].map[1] if j < len(tokens) and tokens[j].map else 0
                    },
                    parent_id=current_section.id if current_section else None
                )
                elements.append(blockquote)
                
                i = j + 1
                current_blockquote_level -= 1
                continue
            
            # Handle other tokens
            i += 1
        
        # Update any sections that didn't get an end position
        for element in elements:
            if isinstance(element, Section) and element.position and element.position.get('end') == 0:
                element.position['end'] = len(content.splitlines())
        
        return elements