"""Tests for the heading and section extractor."""

import unittest
from pathlib import Path
from unittest.mock import Mock

from knowledgebase_processor.models.content import Document
from knowledgebase_processor.models.markdown import Heading, Section
from knowledgebase_processor.extractor.heading_section import HeadingSectionExtractor


class TestHeadingSectionExtractor(unittest.TestCase):
    """Test cases for the heading and section extractor."""
    
    def setUp(self):
        """Set up the test environment."""
        self.extractor = HeadingSectionExtractor()
    
    def test_extract_empty_document(self):
        """Test extracting from an empty document."""
        document = Document(path="test.md", content="", title="Test")
        elements = self.extractor.extract(document)
        self.assertEqual(len(elements), 0)
    
    def test_extract_single_heading(self):
        """Test extracting a single heading."""
        content = "# Heading 1\n\nSome content."
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # We should have 1 heading and 1 section
        headings = [e for e in elements if isinstance(e, Heading)]
        sections = [e for e in elements if isinstance(e, Section)]
        
        self.assertEqual(len(headings), 1)
        self.assertEqual(len(sections), 1)
        self.assertEqual(headings[0].level, 1)
        self.assertEqual(headings[0].text, "Heading 1")
        self.assertEqual(sections[0].content, "Some content.")
        self.assertEqual(sections[0].heading_id, headings[0].id)
        self.assertEqual(sections[0].parent_id, headings[0].id)
    
    def test_extract_multiple_headings(self):
        """Test extracting multiple headings."""
        content = """# Heading 1
        
Some content for heading 1.

## Heading 2

Content for heading 2.

### Heading 3

Content for heading 3.

## Another Heading 2

Content for another heading 2.
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # We should have 4 headings and 4 sections
        headings = [e for e in elements if isinstance(e, Heading)]
        sections = [e for e in elements if isinstance(e, Section)]
        
        self.assertEqual(len(headings), 4)
        self.assertEqual(len(sections), 4)
        
        # Check heading levels
        self.assertEqual(headings[0].level, 1)
        self.assertEqual(headings[1].level, 2)
        self.assertEqual(headings[2].level, 3)
        self.assertEqual(headings[3].level, 2)
        
        # Check heading text
        self.assertEqual(headings[0].text, "Heading 1")
        self.assertEqual(headings[1].text, "Heading 2")
        self.assertEqual(headings[2].text, "Heading 3")
        self.assertEqual(headings[3].text, "Another Heading 2")
        
        # Check hierarchical relationships
        self.assertIsNone(headings[0].parent_id)  # H1 has no parent
        self.assertEqual(headings[1].parent_id, headings[0].id)  # H2 is child of H1
        self.assertEqual(headings[2].parent_id, headings[1].id)  # H3 is child of H2
        self.assertEqual(headings[3].parent_id, headings[0].id)  # Another H2 is child of H1
        
        # Check sections are linked to their headings
        for i, section in enumerate(sections):
            self.assertEqual(section.heading_id, headings[i].id)
            self.assertEqual(section.parent_id, headings[i].id)
    
    def test_extract_complex_hierarchy(self):
        """Test extracting a complex heading hierarchy."""
        content = """# H1
Content 1

## H2-A
Content 2A

### H3-A
Content 3A

#### H4
Content 4

### H3-B
Content 3B

## H2-B
Content 2B

# Another H1
Content for another H1
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # We should have 7 headings and 7 sections
        headings = [e for e in elements if isinstance(e, Heading)]
        sections = [e for e in elements if isinstance(e, Section)]
        
        self.assertEqual(len(headings), 7)
        self.assertEqual(len(sections), 7)
        
        # Check heading levels
        heading_levels = [h.level for h in headings]
        self.assertEqual(heading_levels, [1, 2, 3, 4, 3, 2, 1])
        
        # Check parent-child relationships
        # H1 (index 0) has no parent
        self.assertIsNone(headings[0].parent_id)
        
        # H2-A (index 1) is child of first H1
        self.assertEqual(headings[1].parent_id, headings[0].id)
        
        # H3-A (index 2) is child of H2-A
        self.assertEqual(headings[2].parent_id, headings[1].id)
        
        # H4 (index 3) is child of H3-A
        self.assertEqual(headings[3].parent_id, headings[2].id)
        
        # H3-B (index 4) is child of H2-A
        self.assertEqual(headings[4].parent_id, headings[1].id)
        
        # H2-B (index 5) is child of first H1
        self.assertEqual(headings[5].parent_id, headings[0].id)
        
        # Another H1 (index 6) has no parent
        self.assertIsNone(headings[6].parent_id)
    
    def test_extract_non_sequential_headings(self):
        """Test extracting headings that skip levels (e.g., H1 to H3)."""
        content = """# H1
Content 1

### H3 (skipping H2)
Content 3

##### H5 (skipping H4)
Content 5
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # We should have 3 headings and 3 sections
        headings = [e for e in elements if isinstance(e, Heading)]
        
        self.assertEqual(len(headings), 3)
        
        # Check heading levels
        self.assertEqual(headings[0].level, 1)
        self.assertEqual(headings[1].level, 3)
        self.assertEqual(headings[2].level, 5)
        
        # Check parent-child relationships
        self.assertIsNone(headings[0].parent_id)  # H1 has no parent
        self.assertEqual(headings[1].parent_id, headings[0].id)  # H3 is child of H1 (skipping H2)
        self.assertEqual(headings[2].parent_id, headings[1].id)  # H5 is child of H3 (skipping H4)
    
    @unittest.skip("Processor now requires arguments")
    def test_integration_with_processor(self):
        """Test integration with the processor."""
        from knowledgebase_processor.processor.processor import Processor
        
        processor = Processor(Mock(), Mock())
        processor.register_extractor(self.extractor)
        
        content = """# Test Document
        
## Section 1

Content for section 1.

## Section 2

Content for section 2.

### Subsection 2.1

Content for subsection 2.1.
"""
        document = Document(path="test.md", content=content, title="Test")
        processed_doc = processor.process_document(document)
        
        # Check that elements were added to the document
        self.assertGreater(len(processed_doc.elements), 0)
        
        # Check that we have headings and sections
        headings = [e for e in processed_doc.elements if isinstance(e, Heading)]
        sections = [e for e in processed_doc.elements if isinstance(e, Section)]
        
        self.assertEqual(len(headings), 4)  # H1, H2, H2, H3
        self.assertEqual(len(sections), 4)  # One section for each heading


if __name__ == "__main__":
    unittest.main()