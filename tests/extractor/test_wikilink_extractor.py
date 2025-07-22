import unittest
from unittest.mock import Mock
from knowledgebase_processor.extractor.wikilink_extractor import WikiLinkExtractor
from knowledgebase_processor.models.content import Document

class TestWikiLinkExtractor(unittest.TestCase):
    def setUp(self):
        # Create mocks for document_registry and id_generator
        self.mock_registry = Mock()
        self.mock_registry.find_document_by_path.return_value = None
        
        self.mock_id_generator = Mock()
        self.mock_id_generator.generate_wikilink_id.return_value = "wikilink_123"
        
        self.extractor = WikiLinkExtractor(self.mock_registry, self.mock_id_generator)

    def test_basic_wikilink(self):
        doc = Document(path="test.md", content="This is a link to [[Page One]].")
        result = self.extractor.extract(doc, "doc_id")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].target_path, "Page One")
        self.assertEqual(result[0].label, "Page One")
        self.assertIsNone(result[0].alias)

    def test_wikilink_with_display_text(self):
        doc = Document(path="test.md", content="See [[Page Two|Custom Text]].")
        result = self.extractor.extract(doc, "doc_id")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].target_path, "Page Two")
        self.assertEqual(result[0].alias, "Custom Text")
        self.assertEqual(result[0].label, "Custom Text")

    def test_multiple_wikilinks(self):
        doc = Document(path="test.md", content="[[A]] and [[B|Bee]] are both links.")
        result = self.extractor.extract(doc, "doc_id")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].target_path, "A")
        self.assertEqual(result[0].label, "A")
        self.assertEqual(result[1].target_path, "B")
        self.assertEqual(result[1].alias, "Bee")
        self.assertEqual(result[1].label, "Bee")

    def test_wikilink_at_line_edges(self):
        doc = Document(path="test.md", content="[[Start]] middle [[End|Finish]]")
        result = self.extractor.extract(doc, "doc_id")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].target_path, "Start")
        self.assertEqual(result[1].target_path, "End")
        self.assertEqual(result[1].alias, "Finish")

    def test_no_wikilinks(self):
        doc = Document(path="test.md", content="No links here.")
        result = self.extractor.extract(doc, "doc_id")
        self.assertEqual(result, [])

    def test_nested_or_broken_wikilinks(self):
        doc = Document(path="test.md", content="[[Not closed or [[Nested|Display]]]]")
        result = self.extractor.extract(doc, "doc_id")
        # Should extract only the valid [[Nested|Display]]
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].target_path, "Nested")
        self.assertEqual(result[0].alias, "Display")

    def test_original_text_preservation(self):
        doc = Document(path="test.md", content="Link: [[Some Page|Custom Display]]")
        result = self.extractor.extract(doc, "doc_id")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].original_text, "[[Some Page|Custom Display]]")

    def test_document_resolution(self):
        # Mock a resolved document
        mock_resolved_doc = Mock()
        mock_resolved_doc.kb_id = "doc_456"
        self.mock_registry.find_document_by_path.return_value = mock_resolved_doc
        
        doc = Document(path="test.md", content="[[Existing Page]]")
        result = self.extractor.extract(doc, "doc_id")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].resolved_document_uri, "doc_456")

if __name__ == "__main__":
    unittest.main()