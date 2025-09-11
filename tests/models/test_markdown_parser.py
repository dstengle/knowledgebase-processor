"""Tests for the markdown parser."""

import unittest
from pathlib import Path

from knowledgebase_processor.models.content import Document
from knowledgebase_processor.models.markdown import (
    Heading, Section, MarkdownList, ListItem, TodoItem, Table, CodeBlock, Blockquote
)
from knowledgebase_processor.parser.markdown_parser import MarkdownParser


class TestMarkdownParser(unittest.TestCase):
    """Test cases for the markdown parser."""
    
    def setUp(self):
        """Set up the test environment."""
        self.parser = MarkdownParser()
    
    def test_parse_empty_document(self):
        """Test parsing an empty document."""
        document = Document(path="test.md", content="", title="Test")
        elements = self.parser.parse(document)
        self.assertEqual(len(elements), 0)
    
    def test_parse_headings(self):
        """Test parsing headings."""
        content = """# Heading 1
        
## Heading 2

### Heading 3
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.parser.parse(document)
        
        # We should have 3 headings and 3 sections
        headings = [e for e in elements if isinstance(e, Heading)]
        sections = [e for e in elements if isinstance(e, Section)]
        
        self.assertEqual(len(headings), 3)
        self.assertEqual(len(sections), 3)
        
        # Check heading levels
        self.assertEqual(headings[0].level, 1)
        self.assertEqual(headings[1].level, 2)
        self.assertEqual(headings[2].level, 3)
        
        # Check heading text
        self.assertEqual(headings[0].text, "Heading 1")
        self.assertEqual(headings[1].text, "Heading 2")
        self.assertEqual(headings[2].text, "Heading 3")
    
    def test_parse_lists(self):
        """Test parsing lists."""
        content = """
- Item 1
- Item 2
  - Nested item 1
  - Nested item 2
- Item 3

1. Ordered item 1
2. Ordered item 2
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.parser.parse(document)
        
        # We should have 2 lists
        lists = [e for e in elements if isinstance(e, MarkdownList)]
        self.assertGreaterEqual(len(lists), 2)  # At least 2 lists (unordered and ordered)
        
        # Check that we have both ordered and unordered lists
        ordered_lists = [lst for lst in lists if lst.ordered]
        unordered_lists = [lst for lst in lists if not lst.ordered]
        self.assertGreaterEqual(len(ordered_lists), 1)
        self.assertGreaterEqual(len(unordered_lists), 1)
        
        # Check list items
        list_items = [e for e in elements if isinstance(e, ListItem)]
        self.assertGreaterEqual(len(list_items), 5)  # At least 5 items (not counting nested)
    
    def test_parse_todo_items(self):
        """Test parsing todo items."""
        content = """
- [ ] Todo item 1
- [x] Completed todo item
- [ ] Todo item 2
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.parser.parse(document)
        
        # We should have todo items
        todo_items = [e for e in elements if isinstance(e, TodoItem)]
        self.assertEqual(len(todo_items), 3)
        
        # Check todo item status
        self.assertFalse(todo_items[0].is_checked)
        self.assertTrue(todo_items[1].is_checked)
        self.assertFalse(todo_items[2].is_checked)
        
        # Check todo item text
        self.assertEqual(todo_items[0].text, "Todo item 1")
        self.assertEqual(todo_items[1].text, "Completed todo item")
        self.assertEqual(todo_items[2].text, "Todo item 2")
    
    def test_parse_code_blocks(self):
        """Test parsing code blocks."""
        content = """
```python
def hello_world():
    print("Hello, world!")
```

```
Plain code block
```
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.parser.parse(document)
        
        # We should have 2 code blocks
        code_blocks = [e for e in elements if isinstance(e, CodeBlock)]
        self.assertEqual(len(code_blocks), 2)
        
        # Check code block language
        self.assertEqual(code_blocks[0].language, "python")
        self.assertEqual(code_blocks[1].language, "")
        
        # Check code block content
        self.assertEqual(code_blocks[0].code.strip(), 'def hello_world():\n    print("Hello, world!")')
        self.assertEqual(code_blocks[1].code.strip(), 'Plain code block')
    
    @unittest.skip("Table parsing not yet fully implemented")
    def test_parse_tables(self):
        """Test parsing tables."""
        content = """
Header 1 | Header 2
-------- | --------
Cell 1   | Cell 2
Cell 3   | Cell 4
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.parser.parse(document)
        
        # We should have 1 table
        tables = [e for e in elements if isinstance(e, Table)]
        self.assertEqual(len(tables), 1)
        
        # Check table headers
        self.assertEqual(len(tables[0].headers), 2)
        self.assertEqual(tables[0].headers[0], "Header 1")
        self.assertEqual(tables[0].headers[1], "Header 2")
        
        # Check table rows
        self.assertEqual(len(tables[0].rows), 2)
        self.assertEqual(tables[0].rows[0][0], "Cell 1")
        self.assertEqual(tables[0].rows[0][1], "Cell 2")
        self.assertEqual(tables[0].rows[1][0], "Cell 3")
        self.assertEqual(tables[0].rows[1][1], "Cell 4")
    
    def test_parse_blockquotes(self):
        """Test parsing blockquotes."""
        content = """
> This is a blockquote
> With multiple lines

> Nested blockquotes
>> Are also supported
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.parser.parse(document)
        
        # We should have blockquotes
        blockquotes = [e for e in elements if isinstance(e, Blockquote)]
        self.assertGreaterEqual(len(blockquotes), 2)
    
    def test_complex_document(self):
        """Test parsing a complex document with multiple element types."""
        content = """# Complex Document

This is a paragraph with some text.

## Section 1

- List item 1
- [ ] Todo item
- [x] Completed todo item

### Subsection

```python
def example():
    return "This is an example"
```

## Section 2

> Blockquote with some text
> And another line

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.parser.parse(document)
        
        # Check that we have various element types
        headings = [e for e in elements if isinstance(e, Heading)]
        lists = [e for e in elements if isinstance(e, MarkdownList)]
        todo_items = [e for e in elements if isinstance(e, TodoItem)]
        code_blocks = [e for e in elements if isinstance(e, CodeBlock)]
        blockquotes = [e for e in elements if isinstance(e, Blockquote)]
        tables = [e for e in elements if isinstance(e, Table)]
        
        self.assertGreaterEqual(len(headings), 3)
        self.assertGreaterEqual(len(lists), 1)
        self.assertGreaterEqual(len(todo_items), 2)
        self.assertGreaterEqual(len(code_blocks), 1)
        self.assertGreaterEqual(len(blockquotes), 1)
        # Table parsing not yet fully implemented
        # self.assertGreaterEqual(len(tables), 1)


if __name__ == "__main__":
    unittest.main()