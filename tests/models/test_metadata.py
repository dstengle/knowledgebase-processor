import unittest
from src.knowledgebase_processor.models.metadata import Metadata

class TestMetadata(unittest.TestCase):
    def test_title_and_path(self):
        meta = Metadata(
            document_id="doc-1",
            title="Sample Title",
            path="/docs/sample.md"
        )
        self.assertEqual(meta.title, "Sample Title")
        self.assertEqual(meta.path, "/docs/sample.md")

if __name__ == "__main__":
    unittest.main()
def test_wikilinks_field(self):
        from src.knowledgebase_processor.models.metadata import Metadata
        wikilinks = [
            {"text": "Some Page", "position": {"line": 1, "col": 5}},
            {"text": "Another Page", "position": {"line": 2, "col": 10}}
        ]
        metadata = Metadata(
            document_id="doc1",
            wikilinks=wikilinks
        )
        self.assertEqual(metadata.wikilinks, wikilinks)