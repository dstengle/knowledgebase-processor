import unittest
from src.knowledgebase_processor.models.metadata import DocumentMetadata

class TestDocumentMetadata(unittest.TestCase): # Renamed class for clarity
    def test_title_and_path(self):
        meta = DocumentMetadata(
            document_id="doc-1",
            title="Sample Title",
            path="/docs/sample.md"
        )
        self.assertEqual(meta.title, "Sample Title")
        self.assertEqual(meta.path, "/docs/sample.md")

if __name__ == "__main__":
    unittest.main()
    def test_wikilinks_field(self): # Indented to be part of the class
        # from src.knowledgebase_processor.models.metadata import DocumentMetadata # Import already at top
        wikilinks = [
            {"text": "Some Page", "position": {"line": 1, "col": 5}},
            {"text": "Another Page", "position": {"line": 2, "col": 10}}
        ]
        metadata = DocumentMetadata(
            document_id="doc1",
            wikilinks=wikilinks
        )
        self.assertEqual(metadata.wikilinks, wikilinks)