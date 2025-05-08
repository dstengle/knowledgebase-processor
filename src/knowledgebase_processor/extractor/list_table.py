"""List and table extractor implementation."""

from typing import List, Dict, Any, Optional, Tuple
import re
import uuid

from ..models.content import Document, ContentElement
from ..models.markdown import (
    MarkdownList, ListItem, TodoItem, Table, TableCell
)
from .base import BaseExtractor
from ..parser.markdown_parser import MarkdownParser


class ListTableExtractor(BaseExtractor):
    """Extractor for lists and tables in markdown content.
    
    This extractor identifies and extracts both ordered and unordered lists,
    including nested lists, as well as tables with headers and data cells.
    """
    
    def __init__(self):
        """Initialize the List and Table extractor."""
        self.parser = MarkdownParser()
    
    def extract(self, document: Document) -> List[ContentElement]:
        """Extract lists and tables from a document.
        
        Args:
            document: The document to extract from
            
        Returns:
            List of extracted list and table elements
        """
        result_elements = []
        
        # Use the markdown parser to get all elements (for lists)
        all_elements = self.parser.parse(document)
        
        # Filter for list elements
        list_elements = [
            element for element in all_elements
            if element.element_type == 'list'
        ]
        
        # Add all list elements to the result
        result_elements.extend(list_elements)
        
        # Custom parsing for tables
        tables = self._extract_tables(document.content)
        result_elements.extend(tables)
        
        return result_elements
    
    def _extract_tables(self, content: str) -> List[Table]:
        """Extract tables from markdown content.
        
        Args:
            content: The markdown content to extract tables from
            
        Returns:
            List of extracted Table objects
        """
        tables = []
        
        # Regular expression to match markdown tables
        # This matches the header row, separator row, and data rows
        table_pattern = r'(\|[^\n]+\|\n\|[-:| ]+\|\n(?:\|[^\n]+\|\n)+)'
        
        # Find all tables in the content
        for match in re.finditer(table_pattern, content):
            table_text = match.group(1)
            table_lines = table_text.strip().split('\n')
            
            # Create a new table
            table_id = str(uuid.uuid4())
            table = Table(
                id=table_id,
                content=table_text,
                position={
                    'start': match.start(),
                    'end': match.end()
                }
            )
            
            # Process the header row
            if table_lines:
                header_row = table_lines[0]
                headers = self._parse_table_row(header_row)
                table.headers = headers
                
                # Process data rows (skip the header and separator rows)
                for row_idx, row_text in enumerate(table_lines[2:]):
                    cells = self._parse_table_row(row_text)
                    table.rows.append(cells)
                    
                    # Create cell objects
                    for col_idx, cell_text in enumerate(cells):
                        cell_id = str(uuid.uuid4())
                        cell = TableCell(
                            id=cell_id,
                            text=cell_text,
                            column=col_idx,
                            row=row_idx,
                            is_header=False,
                            content=cell_text,
                            parent_id=table_id
                        )
                        table.cells.append(cell)
                
                # Create header cell objects
                for col_idx, header_text in enumerate(headers):
                    cell_id = str(uuid.uuid4())
                    cell = TableCell(
                        id=cell_id,
                        text=header_text,
                        column=col_idx,
                        row=0,
                        is_header=True,
                        content=header_text,
                        parent_id=table_id
                    )
                    table.cells.append(cell)
                
                tables.append(table)
        
        return tables
    
    def _parse_table_row(self, row_text: str) -> List[str]:
        """Parse a table row into cells.
        
        Args:
            row_text: The text of the table row
            
        Returns:
            List of cell values
        """
        # Remove leading and trailing | and split by |
        cells = row_text.strip('|').split('|')
        
        # Trim whitespace from each cell
        return [cell.strip() for cell in cells]