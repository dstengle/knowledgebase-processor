"""Markdown element data models for the Knowledge Base Processor."""

from pydantic import Field
from typing import Optional, List, Dict, Any
from .common import BaseKnowledgeModel
from .elements import ContentElement


class MarkdownElement(ContentElement):
    """Base class for all markdown elements."""
    
    parent_id: Optional[str] = Field(None, description="ID of the parent element")


class Heading(MarkdownElement):
    """Represents a markdown heading."""
    
    element_type: str = "heading"
    level: int = Field(..., description="Heading level (1-6)")
    text: str = Field(..., description="Heading text")


class Section(MarkdownElement):
    """Represents a section of content between headings."""
    
    element_type: str = "section"
    heading_id: Optional[str] = Field(None, description="ID of the associated heading")


class ListItem(MarkdownElement):
    """Represents a single item in a list."""
    
    element_type: str = "list_item"
    text: str = Field(..., description="Item text")
    is_checked: Optional[bool] = Field(None, description="Whether the item is checked (for todo items)")


class MarkdownList(MarkdownElement):
    """Represents a markdown list."""
    
    element_type: str = "list"
    ordered: bool = Field(False, description="Whether the list is ordered")
    items: List[ListItem] = Field(default_factory=list, description="List items")


class TodoItem(ListItem):
    """Represents a todo item in markdown."""
    
    element_type: str = "todo_item"
    is_checked: bool = Field(False, description="Whether the todo item is checked")


class TableCell(MarkdownElement):
    """Represents a cell in a markdown table."""
    
    element_type: str = "table_cell"
    text: str = Field(..., description="Cell text")
    column: int = Field(..., description="Column index")
    row: int = Field(..., description="Row index")
    is_header: bool = Field(False, description="Whether the cell is a header")


class Table(MarkdownElement):
    """Represents a markdown table."""
    
    element_type: str = "table"
    headers: List[str] = Field(default_factory=list, description="Table headers")
    rows: List[List[str]] = Field(default_factory=list, description="Table rows")
    cells: List[TableCell] = Field(default_factory=list, description="Table cells")


class CodeBlock(MarkdownElement):
    """Represents a markdown code block."""
    
    element_type: str = "code_block"
    language: Optional[str] = Field(None, description="Programming language")
    code: str = Field(..., description="Code content")


class Blockquote(MarkdownElement):
    """Represents a markdown blockquote."""
    
    element_type: str = "blockquote"
    level: int = Field(1, description="Nesting level")