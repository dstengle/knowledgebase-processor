import unittest
from knowledgebase_processor.extractor.wikilink_extractor import WikiLinkExtractor
from knowledgebase_processor.models.content import Document

class TestWikiLinkExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = WikiLinkExtractor()

    def test_basic_wikilink(self):
        doc = Document(path="test.md", content="This is a link to [[Page One]].")
        result = self.extractor.extract(doc)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].target_page, "Page One")
        self.assertEqual(result[0].display_text, "Page One")

    def test_wikilink_with_display_text(self):
        doc = Document(path="test.md", content="See [[Page Two|Custom Text]].")
        result = self.extractor.extract(doc)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].target_page, "Page Two")
        self.assertEqual(result[0].display_text, "Custom Text")

    def test_multiple_wikilinks(self):
        doc = Document(path="test.md", content="[[A]] and [[B|Bee]] are both links.")
        result = self.extractor.extract(doc)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].target_page, "A")
        self.assertEqual(result[0].display_text, "A")
        self.assertEqual(result[1].target_page, "B")
        self.assertEqual(result[1].display_text, "Bee")

    def test_wikilink_at_line_edges(self):
        doc = Document(path="test.md", content="[[Start]] middle [[End|Finish]]")
        result = self.extractor.extract(doc)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].target_page, "Start")
        self.assertEqual(result[1].target_page, "End")
        self.assertEqual(result[1].display_text, "Finish")

    def test_no_wikilinks(self):
        doc = Document(path="test.md", content="No links here.")
        result = self.extractor.extract(doc)
        self.assertEqual(result, [])

    def test_nested_or_broken_wikilinks(self):
        doc = Document(path="test.md", content="[[Not closed or [[Nested|Display]]]]")
        result = self.extractor.extract(doc)
        # Should extract only the valid [[Nested|Display]]
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].target_page, "Nested")
        self.assertEqual(result[0].display_text, "Display")

if __name__ == "__main__":
    unittest.main()