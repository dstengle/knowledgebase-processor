import unittest
from typing import List

from knowledgebase_processor.analyzer.entity_recognizer import EntityRecognizer
from knowledgebase_processor.models.metadata import DocumentMetadata, ExtractedEntity, BaseModel # Ensure BaseModel if needed

class TestEntityRecognizer(unittest.TestCase):
    def setUp(self):
        """
        Set up the test case by initializing the EntityRecognizer.
        """
        self.analyzer = EntityRecognizer()

    def _create_metadata(self) -> DocumentMetadata:
        """Helper to create a fresh DocumentMetadata instance."""
        # Assuming DocumentMetadata might require a path or other minimal setup
        # Adjust if DocumentMetadata has mandatory constructor arguments
        return DocumentMetadata(document_id="test.md", file_path="test.md")


    def test_extract_person_entity(self):
        metadata = self._create_metadata()
        content = "Apple is looking at buying U.K. startup for $1 billion. Steve Jobs was a visionary."
        self.analyzer.analyze(content, metadata)
        
        self.assertTrue(any(ent.text == "Steve Jobs" and ent.label == "PERSON" for ent in metadata.entities))

    def test_extract_org_entity(self):
        metadata = self._create_metadata()
        content = "Apple is a technology company based in Cupertino."
        self.analyzer.analyze(content, metadata)
        
        self.assertTrue(any(ent.text == "Apple" and ent.label == "ORG" for ent in metadata.entities))

    def test_extract_loc_gpe_entity(self):
        metadata = self._create_metadata()
        content = "London is the capital of the United Kingdom."
        self.analyzer.analyze(content, metadata)
        
        found_london = any(ent.text == "London" and (ent.label == "GPE" or ent.label == "LOC") for ent in metadata.entities)
        self.assertTrue(found_london, "London entity not found or mislabelled")

        # Check for United Kingdom if found, but don't fail if not,
        # acknowledging limitations of en_core_web_sm.
        uk_entity = next((ent for ent in metadata.entities if ent.text == "United Kingdom"), None)
        if uk_entity:
            self.assertIn(uk_entity.label, ["GPE", "LOC"], 
                          f"United Kingdom found with text '{uk_entity.text}' but label '{uk_entity.label}' is not GPE or LOC.")

    def test_extract_date_entity(self):
        metadata = self._create_metadata()
        content = "The event is scheduled for July 4th, 2024."
        self.analyzer.analyze(content, metadata)
        
        self.assertTrue(any(ent.text == "July 4th, 2024" and ent.label == "DATE" for ent in metadata.entities))

    def test_multiple_entities(self):
        metadata = self._create_metadata()
        content = "Alice went to Paris with Bob on January 1st."
        self.analyzer.analyze(content, metadata)
        
        entities_found = { (ent.text, ent.label) for ent in metadata.entities }
        expected_entities = {
            ("Alice", "PERSON"),
            ("Paris", "GPE"), # spaCy often labels cities as GPE
            ("Bob", "PERSON"),
            ("January 1st", "DATE")
        }
        # Check if all expected entities are a subset of what was found
        # This is more flexible than checking exact counts if spaCy finds more (e.g. "January 1st" as part of a larger date)
        self.assertTrue(expected_entities.issubset(entities_found), f"Expected {expected_entities}, but found {entities_found}")


    def test_no_entities(self):
        metadata = self._create_metadata()
        content = "This is a simple sentence without any special names."
        self.analyzer.analyze(content, metadata)
        self.assertEqual(len(metadata.entities), 0)

    def test_empty_content(self):
        metadata = self._create_metadata()
        content = ""
        self.analyzer.analyze(content, metadata)
        self.assertEqual(len(metadata.entities), 0)
        
    def test_unicode_content(self):
        metadata = self._create_metadata()
        content = "これは日本語のテキストです。東京は日本の首都です。" # "This is Japanese text. Tokyo is the capital of Japan."
        # Note: en_core_web_sm is primarily for English. For robust multilingual support,
        # a multilingual model or language-specific models would be needed.
        # This test primarily checks if it handles unicode without crashing.
        # We don't expect accurate entity recognition for Japanese with an English model.
        self.analyzer.analyze(content, metadata)
        # We are not asserting specific entities here, just that it runs.
        # Depending on the model, it might find "Tokyo" if it's in its English vocab.
        self.assertTrue(isinstance(metadata.entities, list))


if __name__ == '__main__':
    unittest.main()