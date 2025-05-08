"""Tests for the list and table extractor."""

import unittest
from pathlib import Path

from knowledgebase_processor.models.content import Document
from knowledgebase_processor.extractor.list_table import ListTableExtractor


class TestListTableExtractor(unittest.TestCase):
    """Test cases for the list and table extractor."""
    
    def setUp(self):
        """Set up the test environment."""
        self.extractor = ListTableExtractor()
    
    def test_extract_unordered_list(self):
        """Test extracting an unordered list."""
        content = """
# Test Document

This is a test document with an unordered list:

- Item 1
- Item 2
- Item 3
"""
        document = Document(path="test.md", content=content)
        elements = self.extractor.extract(document)
        
        # Check that we extracted a list
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0].element_type, "list")
        self.assertFalse(elements[0].ordered)
        
        # Check the list items
        self.assertEqual(len(elements[0].items), 3)
        self.assertEqual(elements[0].items[0].text, "Item 1")
        self.assertEqual(elements[0].items[1].text, "Item 2")
        self.assertEqual(elements[0].items[2].text, "Item 3")
    
    def test_extract_ordered_list(self):
        """Test extracting an ordered list."""
        content = """
# Test Document

This is a test document with an ordered list:

1. First item
2. Second item
3. Third item
"""
        document = Document(path="test.md", content=content)
        elements = self.extractor.extract(document)
        
        # Check that we extracted a list
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0].element_type, "list")
        self.assertTrue(elements[0].ordered)
        
        # Check the list items
        self.assertEqual(len(elements[0].items), 3)
        self.assertEqual(elements[0].items[0].text, "First item")
        self.assertEqual(elements[0].items[1].text, "Second item")
        self.assertEqual(elements[0].items[2].text, "Third item")
    
    def test_extract_nested_list(self):
        """Test extracting a nested list."""
        content = """
# Test Document

This is a test document with a nested list:

- Item 1
  - Nested item 1.1
  - Nested item 1.2
- Item 2
  1. Nested ordered item 2.1
  2. Nested ordered item 2.2
- Item 3
"""
        document = Document(path="test.md", content=content)
        elements = self.extractor.extract(document)
        
        # We should have extracted at least one list
        lists = [e for e in elements if e.element_type == "list"]
        self.assertGreater(len(lists), 0, "No lists found")
        
        # Check that we have at least one list with "Item 1" in it
        has_item1 = False
        for l in lists:
            for item in l.items:
                if "Item 1" in item.text:
                    has_item1 = True
                    break
            if has_item1:
                break
        
        self.assertTrue(has_item1, "No list with 'Item 1' found")
        
        # Check that we have at least one list with a nested item
        has_nested_item = False
        for l in lists:
            for item in l.items:
                if "Nested" in item.text:
                    has_nested_item = True
                    break
            if has_nested_item:
                break
        
        self.assertTrue(has_nested_item, "No list with nested items found")
    
    def test_extract_table(self):
        """Test extracting a table."""
        content = """
# Test Document

This is a test document with a table:

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1,1 | Cell 1,2 | Cell 1,3 |
| Cell 2,1 | Cell 2,2 | Cell 2,3 |
"""
        document = Document(path="test.md", content=content)
        elements = self.extractor.extract(document)
        
        # Check that we extracted at least one element
        self.assertGreater(len(elements), 0, "No elements extracted")
        
        # Find the table element
        tables = [e for e in elements if e.element_type == "table"]
        self.assertGreater(len(tables), 0, "No table elements found")
        
        table = tables[0]
        
        # Check the table headers
        self.assertEqual(len(table.headers), 3, "Expected 3 headers")
        self.assertIn("Header 1", table.headers)
        self.assertIn("Header 2", table.headers)
        self.assertIn("Header 3", table.headers)
        
        # Check the table rows
        self.assertEqual(len(table.rows), 2, "Expected 2 rows")
        
        # Check for expected cell content
        cell_values = []
        for row in table.rows:
            cell_values.extend(row)
            
        self.assertIn("Cell 1,1", cell_values)
        self.assertIn("Cell 1,2", cell_values)
        self.assertIn("Cell 1,3", cell_values)
        self.assertIn("Cell 2,1", cell_values)
        self.assertIn("Cell 2,2", cell_values)
        self.assertIn("Cell 2,3", cell_values)
        
        # Check the table cells
        header_cells = [c for c in table.cells if c.is_header]
        data_cells = [c for c in table.cells if not c.is_header]
        
        self.assertEqual(len(header_cells), 3, "Expected 3 header cells")
        self.assertEqual(len(data_cells), 6, "Expected 6 data cells")


if __name__ == "__main__":
    unittest.main()