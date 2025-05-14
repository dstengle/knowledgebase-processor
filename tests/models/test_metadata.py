import unittest
from src.knowledgebase_processor.models.metadata import DocumentMetadata
from src.knowledgebase_processor.models.links import WikiLink # Added import

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

    # Correctly indented test method
    def test_wikilinks_field(self):
        wikilinks_data = [
            {"target_page": "Some Page", "display_text": "Some Page", "position": {"line": 1, "col": 5}},
            {"target_page": "Another Page", "display_text": "Another Page", "position": {"line": 2, "col": 10}}
        ]
        # Create Wikilink instances
        expected_wikilinks = [WikiLink(**data) for data in wikilinks_data]
        
        metadata = DocumentMetadata(
            document_id="doc1",
            title="Test Doc with Wikilinks", # Added title for completeness
            path="/test/doc.md", # Added path for completeness
            wikilinks=expected_wikilinks # Assign list of Wikilink objects
        )
        self.assertEqual(metadata.wikilinks, expected_wikilinks)