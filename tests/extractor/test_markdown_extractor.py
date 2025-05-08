"""Tests for the markdown extractor."""

import unittest
from pathlib import Path

from knowledgebase_processor.models.content import Document
from knowledgebase_processor.models.markdown import (
    Heading, Section, MarkdownList, ListItem, TodoItem, Table, CodeBlock, Blockquote
)
from knowledgebase_processor.extractor.markdown import MarkdownExtractor


class TestMarkdownExtractor(unittest.TestCase):
    """Test cases for the markdown extractor."""
    
    def setUp(self):
        """Set up the test environment."""
        self.extractor = MarkdownExtractor()
    
    def test_extract_empty_document(self):
        """Test extracting from an empty document."""
        document = Document(path="test.md", content="", title="Test")
        elements = self.extractor.extract(document)
        self.assertEqual(len(elements), 0)
    
    def test_extract_headings(self):
        """Test extracting headings."""
        content = """# Heading 1
        
## Heading 2

### Heading 3
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # We should have 3 headings and 3 sections
        headings = [e for e in elements if e.element_type == "heading"]
        sections = [e for e in elements if e.element_type == "section"]
        
        self.assertEqual(len(headings), 3)
        self.assertEqual(len(sections), 3)
    
    def test_extract_lists_and_todos(self):
        """Test extracting lists and todo items."""
        content = """
- Item 1
- [ ] Todo item 1
- [x] Completed todo item
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # We should have lists and todo items
        lists = [e for e in elements if e.element_type == "list"]
        list_items = [e for e in elements if e.element_type == "list_item"]
        todo_items = [e for e in elements if e.element_type == "todo_item"]
        
        self.assertGreaterEqual(len(lists), 1)
        self.assertGreaterEqual(len(list_items) + len(todo_items), 3)
    
    def test_extract_code_blocks(self):
        """Test extracting code blocks."""
        content = """
```python
def hello_world():
    print("Hello, world!")
```
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # We should have a code block
        code_blocks = [e for e in elements if e.element_type == "code_block"]
        self.assertEqual(len(code_blocks), 1)
        self.assertEqual(code_blocks[0].language, "python")
    
    @unittest.skip("Table parsing not yet fully implemented")
    def test_extract_tables(self):
        """Test extracting tables."""
        content = """
Header 1 | Header 2
-------- | --------
Cell 1   | Cell 2
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # We should have a table
        tables = [e for e in elements if e.element_type == "table"]
        self.assertEqual(len(tables), 1)
    
    def test_extract_blockquotes(self):
        """Test extracting blockquotes."""
        content = """
> This is a blockquote
> With multiple lines
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # We should have a blockquote
        blockquotes = [e for e in elements if e.element_type == "blockquote"]
        self.assertGreaterEqual(len(blockquotes), 1)
    
    def test_integration_with_processor(self):
        """Test integration with the processor."""
        from knowledgebase_processor.processor.processor import Processor
        
        processor = Processor()
        processor.register_extractor(self.extractor)
        
        content = """# Test Document
        
## Section 1

- List item 1
- [ ] Todo item

## Section 2

```python
def test():
    pass
```
"""
        document = Document(path="test.md", content=content, title="Test")
        processed_doc = processor.process_document(document)
        
        # Check that elements were added to the document
        self.assertGreater(len(processed_doc.elements), 0)
        
        # Check that we have different element types
        element_types = set(e.element_type for e in processed_doc.elements)
        self.assertGreaterEqual(len(element_types), 4)  # At least heading, section, list, code_block


if __name__ == "__main__":
    unittest.main()