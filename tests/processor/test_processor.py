"""Tests for the Processor component."""

import unittest
from unittest.mock import MagicMock, patch

from knowledgebase_processor.processor.processor import Processor
from knowledgebase_processor.models.content import Document, ContentElement


class TestProcessor(unittest.TestCase):
    """Test cases for the Processor component."""
    
    def setUp(self):
        """Set up the test environment."""
        self.processor = Processor()
        
        # Create a mock extractor with parse_frontmatter method
        self.mock_extractor = MagicMock()
        self.mock_extractor.parse_frontmatter = MagicMock(return_value={})
        
        # Register the mock extractor
        self.processor.register_extractor(self.mock_extractor)
    
    def test_update_document_title_from_frontmatter(self):
        """Test updating document title from frontmatter."""
        # Create a document with frontmatter
        document = Document(
            path="test_doc.md",
            title="Original Title",
            content="---\ntitle: Frontmatter Title\n---\nContent",
            elements=[]
        )
        
        # Create a frontmatter element
        frontmatter_element = ContentElement(
            element_type="frontmatter",
            content="title: Frontmatter Title",
            position={"start": 0, "end": 2},
            metadata={"format": "yaml"}
        )
        
        # Add the frontmatter element to the document
        document.elements.append(frontmatter_element)
        
        # Configure the mock extractor to return a frontmatter dict with a title
        self.mock_extractor.parse_frontmatter.return_value = {"title": "Frontmatter Title"}
        
        # Update the document title
        self.processor._update_document_title_from_frontmatter(document)
        
        # Check that the title was updated from frontmatter
        self.assertEqual(document.title, "Frontmatter Title")
    
    def test_update_document_title_fallback_to_filename(self):
        """Test fallback to filename when frontmatter title is not available."""
        # Create a document without frontmatter title
        document = Document(
            path="test_document_name.md",
            title=None,
            content="Content without frontmatter",
            elements=[]
        )
        
        # Update the document title
        self.processor._update_document_title_from_frontmatter(document)
        
        # Check that the title was updated from filename
        self.assertEqual(document.title, "test document name")
    
    def test_update_document_title_with_empty_frontmatter(self):
        """Test fallback to filename when frontmatter exists but has no title."""
        # Create a document with frontmatter but no title
        document = Document(
            path="another_test_doc.md",
            title=None,
            content="---\nauthor: Test Author\n---\nContent",
            elements=[]
        )
        
        # Create a frontmatter element without title
        frontmatter_element = ContentElement(
            element_type="frontmatter",
            content="author: Test Author",
            position={"start": 0, "end": 2},
            metadata={"format": "yaml"}
        )
        
        # Add the frontmatter element to the document
        document.elements.append(frontmatter_element)
        
        # Configure the mock extractor to return a frontmatter dict without a title
        self.mock_extractor.parse_frontmatter.return_value = {"author": "Test Author"}
        
        # Update the document title
        self.processor._update_document_title_from_frontmatter(document)
        
        # Check that the title was updated from filename
        self.assertEqual(document.title, "another test doc")
    
    def test_update_document_title_with_hyphens_and_underscores(self):
        """Test that hyphens and underscores in filenames are converted to spaces."""
        # Create a document with hyphens and underscores in filename
        document = Document(
            path="test-file_with-special_chars.md",
            title=None,
            content="Content",
            elements=[]
        )
        
        # Update the document title
        self.processor._update_document_title_from_frontmatter(document)
        
        # Check that the title was updated from filename with hyphens/underscores converted to spaces
        self.assertEqual(document.title, "test file with special chars")


if __name__ == "__main__":
    unittest.main()