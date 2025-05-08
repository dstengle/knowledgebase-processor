"""Tests for the link and reference extractor."""

import unittest
from pathlib import Path

from knowledgebase_processor.models.content import Document
from knowledgebase_processor.models.links import Link, Reference, Citation
from knowledgebase_processor.extractor.link_reference import LinkReferenceExtractor


class TestLinkReferenceExtractor(unittest.TestCase):
    """Test cases for the link and reference extractor."""
    
    def setUp(self):
        """Set up the test environment."""
        self.extractor = LinkReferenceExtractor()
    
    def test_extract_empty_document(self):
        """Test extracting from an empty document."""
        document = Document(path="test.md", content="", title="Test")
        elements = self.extractor.extract(document)
        self.assertEqual(len(elements), 0)
    
    def test_extract_inline_links(self):
        """Test extracting inline links."""
        content = """
# Test Document

This is a [link to Google](https://www.google.com) in a paragraph.
Here's [another link](https://example.com "Example Site") with a title.
And here's an [internal link](../path/to/file.md) to a local file.
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # Filter out only Link elements
        links = [e for e in elements if isinstance(e, Link)]
        
        # We should have 3 links
        self.assertEqual(len(links), 3)
        
        # Check the first link (Google)
        self.assertEqual(links[0].text, "link to Google")
        self.assertEqual(links[0].url, "https://www.google.com")
        self.assertFalse(links[0].is_internal)
        
        # Check the second link (Example with title)
        self.assertEqual(links[1].text, "another link")
        self.assertEqual(links[1].url, "https://example.com")
        self.assertFalse(links[1].is_internal)
        
        # Check the third link (internal)
        self.assertEqual(links[2].text, "internal link")
        self.assertEqual(links[2].url, "../path/to/file.md")
        self.assertTrue(links[2].is_internal)
    
    def test_extract_reference_links(self):
        """Test extracting reference-style links."""
        content = """
# Reference Links

This is a [reference link][ref1] in a paragraph.
Here's [another reference][ref2] in the same paragraph.

You can also use [shorthand][] references.
Or even just use the [text itself].

[ref1]: https://www.example.com
[ref2]: https://www.example.org "Example.org"
[shorthand]: https://shorthand.example.com
[text itself]: https://text.example.com
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # Filter out Link and Reference elements
        links = [e for e in elements if isinstance(e, Link)]
        references = [e for e in elements if isinstance(e, Reference)]
        
        # We should have links and references
        self.assertGreater(len(links), 0)
        self.assertEqual(len(references), 4)
        
        # Check reference definitions
        ref_keys = [r.key for r in references]
        self.assertIn("ref1", ref_keys)
        self.assertIn("ref2", ref_keys)
        self.assertIn("shorthand", ref_keys)
        self.assertIn("text itself", ref_keys)
        
        # Find ref2 and check its title
        ref2 = next(r for r in references if r.key == "ref2")
        self.assertEqual(ref2.url, "https://www.example.org")
        self.assertEqual(ref2.title, "Example.org")
        
        # Check that links have correct URLs from references
        ref1_link = next(l for l in links if l.text == "reference link")
        self.assertEqual(ref1_link.url, "https://www.example.com")
        
        # Check reference links
        ref1_link = next(l for l in links if l.text == "reference link")
        self.assertEqual(ref1_link.url, "https://www.example.com")
        
        ref2_link = next(l for l in links if l.text == "another reference")
        self.assertEqual(ref2_link.url, "https://www.example.org")
    
    def test_extract_citations(self):
        """Test extracting citations."""
        content = """
# Citations

According to (Smith, 2020), this is an important finding.
Another study [@johnson2019] showed similar results.
Multiple citations (Smith, 2020; Johnson, 2019) support this claim.
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # Filter out Citation elements
        citations = [e for e in elements if isinstance(e, Citation)]
        
        # We should have 3 citations
        self.assertEqual(len(citations), 3)
        
        # Check citation texts
        citation_texts = [c.text for c in citations]
        self.assertIn("Smith, 2020", citation_texts)
        self.assertIn("johnson2019", citation_texts)
        self.assertIn("Smith, 2020; Johnson, 2019", citation_texts)
    
    def test_mixed_link_types(self):
        """Test extracting a mix of link types in the same document."""
        content = """
# Mixed Link Types

This document has [inline links](https://example.com) and [reference links][ref1].
It also has citations (Author, 2023) and [@citation-key].

[ref1]: https://reference.example.com "Reference Example"
"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # Count each type of element
        links = [e for e in elements if isinstance(e, Link)]
        references = [e for e in elements if isinstance(e, Reference)]
        citations = [e for e in elements if isinstance(e, Citation)]
        
        self.assertGreater(len(links), 0)  # At least one link
        self.assertEqual(len(references), 1)
        self.assertEqual(len(citations), 2)
        
        # Check that we have links
        self.assertGreater(len(links), 0)
    
    def test_integration_with_processor(self):
        """Test integration with the processor."""
        from knowledgebase_processor.processor.processor import Processor
        
        processor = Processor()
        processor.register_extractor(self.extractor)
        
        content = """
# Test Document

This is a [link to Google](https://www.google.com) in a paragraph.
Here's a [reference link][ref1] in the same paragraph.

[ref1]: https://www.example.com "Example Site"
"""
        document = Document(path="test.md", content=content, title="Test")
        processed_doc = processor.process_document(document)
        
        # Check that elements were added to the document
        self.assertGreater(len(processed_doc.elements), 0)
        
        # Check that we have links and references
        links = [e for e in processed_doc.elements if isinstance(e, Link)]
        references = [e for e in processed_doc.elements if isinstance(e, Reference)]
        
        self.assertGreater(len(links), 0)  # At least one link
        self.assertEqual(len(references), 1)


if __name__ == "__main__":
    unittest.main()