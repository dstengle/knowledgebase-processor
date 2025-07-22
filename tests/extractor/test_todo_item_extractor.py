"""Tests for the todo item extractor."""

import unittest
from pathlib import Path
from unittest.mock import Mock

from knowledgebase_processor.models.content import Document
from knowledgebase_processor.models.markdown import TodoItem
from knowledgebase_processor.extractor.todo_item import TodoItemExtractor


class TestTodoItemExtractor(unittest.TestCase):
    """Test cases for the todo item extractor."""
    
    def setUp(self):
        """Set up the test environment."""
        self.extractor = TodoItemExtractor()
    
    def test_extract_empty_document(self):
        """Test extracting from an empty document."""
        document = Document(path="test.md", content="", title="Test")
        elements = self.extractor.extract(document)
        self.assertEqual(len(elements), 0)
    
    def test_extract_no_todos(self):
        """Test extracting from a document with no todo items."""
        content = """# Test Document
        
This is a test document with no todo items.

- Regular list item
- Another regular item
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        self.assertEqual(len(elements), 0)
    
    def test_extract_unchecked_todos(self):
        """Test extracting unchecked todo items."""
        content = """# Test Document
        
- [ ] Todo item 1
- [ ] Todo item 2
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # We should have 2 todo items
        self.assertEqual(len(elements), 2)
        
        # All should be unchecked
        for element in elements:
            self.assertIsInstance(element, TodoItem)
            self.assertEqual(element.element_type, "todo_item")
            self.assertFalse(element.is_checked)
    
    def test_extract_checked_todos(self):
        """Test extracting checked todo items."""
        content = """# Test Document
        
- [x] Completed todo item 1
- [X] Completed todo item 2
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # We should have 2 todo items
        self.assertEqual(len(elements), 2)
        
        # All should be checked
        for element in elements:
            self.assertIsInstance(element, TodoItem)
            self.assertEqual(element.element_type, "todo_item")
            self.assertTrue(element.is_checked)
    
    def test_extract_mixed_todos(self):
        """Test extracting a mix of checked and unchecked todo items."""
        content = """# Test Document
        
- [ ] Todo item 1
- [x] Completed todo item
- [ ] Todo item 2
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # We should have 3 todo items
        self.assertEqual(len(elements), 3)
        
        # Check the completion status
        self.assertFalse(elements[0].is_checked)
        self.assertTrue(elements[1].is_checked)
        self.assertFalse(elements[2].is_checked)
    
    def test_extract_todo_text(self):
        """Test extracting the text content of todo items."""
        content = """# Test Document
        
- [ ] Buy milk
- [x] Write code
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # Check the text content
        self.assertEqual(elements[0].text, "Buy milk")
        self.assertEqual(elements[1].text, "Write code")
    
    def test_extract_todo_with_context(self):
        """Test extracting todo items with their context."""
        # Create a document with a section
        document = Document(
            path="test.md",
            content="# Shopping List\n\n- [ ] Buy milk\n- [x] Buy eggs",
            title="Test"
        )
        
        # Add a section element to the document
        from knowledgebase_processor.models.markdown import Section
        import uuid
        
        section_id = str(uuid.uuid4())
        section = Section(
            id=section_id,
            element_type="section",
            content="# Shopping List\n\n- [ ] Buy milk\n- [x] Buy eggs",
            position={"start": 0, "end": 4},
            heading_id=None
        )
        document.elements.append(section)
        
        # Extract todo items
        elements = self.extractor.extract(document)
        
        # Check that the todo items have the section as parent
        self.assertEqual(len(elements), 2)
        self.assertEqual(elements[0].parent_id, section_id)
        self.assertEqual(elements[1].parent_id, section_id)
    
    def test_extract_todos_with_leading_whitespace(self):
        """Test extracting todo items with leading whitespace."""
        content = """# Test Document
        
 - [ ] Single space indent
  - [x] Two space indent
    - [ ] Four space indent
	- [x] Tab indent
- [ ] No indent
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # We should have 5 todo items
        self.assertEqual(len(elements), 5)
        
        # Check all are TodoItem instances
        for element in elements:
            self.assertIsInstance(element, TodoItem)
            self.assertEqual(element.element_type, "todo_item")
        
        # Check specific items
        self.assertEqual(elements[0].text, "Single space indent")
        self.assertFalse(elements[0].is_checked)
        
        self.assertEqual(elements[1].text, "Two space indent")
        self.assertTrue(elements[1].is_checked)
        
        self.assertEqual(elements[2].text, "Four space indent")
        self.assertFalse(elements[2].is_checked)
        
        self.assertEqual(elements[3].text, "Tab indent")
        self.assertTrue(elements[3].is_checked)
        
        self.assertEqual(elements[4].text, "No indent")
        self.assertFalse(elements[4].is_checked)
    
    @unittest.skip("Processor now requires arguments")
    def test_integration_with_processor(self):
        """Test integration with the processor."""
        from knowledgebase_processor.processor.processor import Processor
        
        processor = Processor(Mock(), Mock())
        processor.register_extractor(self.extractor)
        
        content = """# Test Document
        
## Tasks
- [ ] Task 1
- [x] Task 2
- [ ] Task 3
"""
        document = Document(path="test.md", content=content, title="Test")
        processed_doc = processor.process_document(document)
        
        # Check that todo items were added to the document
        todo_items = [e for e in processed_doc.elements if e.element_type == "todo_item"]
        self.assertEqual(len(todo_items), 3)
        
        # Check completion status
        self.assertFalse(todo_items[0].is_checked)
        self.assertTrue(todo_items[1].is_checked)
        self.assertFalse(todo_items[2].is_checked)


if __name__ == "__main__":
    unittest.main()