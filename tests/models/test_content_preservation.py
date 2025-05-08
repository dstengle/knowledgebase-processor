"""Tests for content preservation functionality."""

import unittest
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.knowledgebase_processor.models.content import Document, ContentElement
from src.knowledgebase_processor.models.preservation import ContentPosition, PreservedContent
from src.knowledgebase_processor.models.markdown import Heading, Section
from src.knowledgebase_processor.extractor.base import BaseExtractor
from src.knowledgebase_processor.extractor.heading_section import HeadingSectionExtractor


class TestContentPreservation(unittest.TestCase):
    """Test cases for content preservation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.markdown_content = """# Heading 1
        
This is some content under heading 1.

## Heading 2

This is some content under heading 2.
It has multiple lines.

### Heading 3

Final paragraph.
"""
        self.document = Document(
            path="test.md",
            title="Test Document",
            content=self.markdown_content,
            elements=[]
        )
        
    def test_content_element_preservation(self):
        """Test that ContentElement can preserve original content."""
        element = ContentElement(
            element_type="test",
            content="Test content",
            position={
                'start': 0,
                'end': 0
            }
        )
        
        element.preserve_original_content("Line 1\nLine 2")
        
        self.assertIsNotNone(element.preserved_content)
        self.assertEqual(element.preserved_content.original_text, "Line 1")
        self.assertEqual(element.preserved_content.position.start_line, 0)
        self.assertEqual(element.preserved_content.position.end_line, 0)
        
    def test_document_content_preservation(self):
        """Test that Document preserves content for all elements."""
        # Extract headings and sections
        extractor = HeadingSectionExtractor()
        elements = extractor.extract(self.document)
        self.document.elements.extend(elements)
        
        # Preserve content
        self.document.preserve_content()
        
        # Check that all elements have preserved content
        for element in self.document.elements:
            self.assertIsNotNone(element.preserved_content)
            self.assertEqual(element.preserved_content.element_id, element.id)
            
            # Check that the preserved content matches the original
            original_lines = self.markdown_content.splitlines()
            start_line = element.position['start']
            end_line = element.position['end']
            expected_content = '\n'.join(original_lines[start_line:end_line + 1])
            
            self.assertEqual(element.preserved_content.original_text, expected_content)
            
    def test_position_calculation(self):
        """Test that position calculation works correctly."""
        # Create a concrete implementation of BaseExtractor for testing
        class TestExtractor(BaseExtractor):
            def extract(self, document):
                return []
                
        extractor = TestExtractor()
        
        content = "Line 1\nLine 2\nLine 3\nLine 4"
        doc = Document(path="test.md", title="Test", content=content, elements=[])
        
        # Test basic position calculation
        position = extractor.calculate_position(doc, 1, 2)
        self.assertEqual(position['start'], 1)
        self.assertEqual(position['end'], 2)
        self.assertEqual(position['start_offset'], 7)  # "Line 1\n" is 7 chars
        self.assertEqual(position['end_offset'], 20)  # "Line 1\nLine 2\nLine 3" is 20 chars
        
        # Test with columns
        position = extractor.calculate_position(doc, 1, 1, 2, 5)
        self.assertEqual(position['start'], 1)
        self.assertEqual(position['end'], 1)
        self.assertEqual(position['start_col'], 2)
        self.assertEqual(position['end_col'], 5)
        self.assertEqual(position['start_offset'], 9)  # "Line 1\nLi" is 9 chars
        self.assertEqual(position['end_offset'], 12)  # "Line 1\nLine " is 12 chars
        
    def test_get_content_at_position(self):
        """Test retrieving content at a specific position."""
        content = "Line 1\nLine 2\nLine 3\nLine 4"
        doc = Document(path="test.md", title="Test", content=content, elements=[])
        
        # Get content from line 1 to 2
        retrieved = doc.get_content_at_position(1, 2)
        self.assertEqual(retrieved, "Line 2\nLine 3")
        
        # Get single line
        retrieved = doc.get_content_at_position(0, 0)
        self.assertEqual(retrieved, "Line 1")
        
        # Test out of range
        with self.assertRaises(ValueError):
            doc.get_content_at_position(10, 20)


if __name__ == '__main__':
    unittest.main()