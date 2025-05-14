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


    def test_analyze_text_for_entities_john_doe_acme_new_york(self):
        """Test analyze_text_for_entities with a sentence containing multiple entities."""
        text_to_analyze = "John Doe works at Acme Corp in New York."
        entities: List[ExtractedEntity] = self.analyzer.analyze_text_for_entities(text_to_analyze)

        expected_entities_data = [
            {"text": "John Doe", "label": "PERSON", "start_char": 0, "end_char": 8},
            {"text": "Acme Corp", "label": "ORG", "start_char": 18, "end_char": 27},
            {"text": "New York", "label": "GPE", "start_char": 31, "end_char": 39},
        ]

        # Convert to a set of tuples for easier comparison if order doesn't matter
        # or if spaCy might find them in a different order.
        # For this specific case, order is likely preserved but comparing sets is robust.
        
        actual_entities_set = {(e.text, e.label, e.start_char, e.end_char) for e in entities}
        expected_entities_set = {(d["text"], d["label"], d["start_char"], d["end_char"]) for d in expected_entities_data}

        self.assertEqual(actual_entities_set, expected_entities_set,
                         f"Expected entities {expected_entities_set} but got {actual_entities_set}")

    def test_analyze_text_for_entities_jane_smith_wikilink_alias(self):
        """Test analyze_text_for_entities with a wikilink alias."""
        text_to_analyze = "Dr. Smith" # Simulating the text part of "[[Jane Smith|Dr. Smith]]"
        entities: List[ExtractedEntity] = self.analyzer.analyze_text_for_entities(text_to_analyze)
        
        self.assertEqual(len(entities), 1, f"Expected 1 entity, got {len(entities)}")
        entity = entities[0]
        self.assertEqual(entity.text, "Smith") # spaCy model 'en_core_web_sm' extracts "Smith"
        self.assertEqual(entity.label, "PERSON")
        self.assertEqual(entity.start_char, 4) # "Smith" in "Dr. Smith" (D=0,r=1,.=2, =3,S=4)
        self.assertEqual(entity.end_char, 9)   # "Smith"

    def test_analyze_text_for_entities_simple_phrase_no_entities(self):
        """Test analyze_text_for_entities with a phrase containing no entities."""
        text_to_analyze = "A simple phrase"
        entities: List[ExtractedEntity] = self.analyzer.analyze_text_for_entities(text_to_analyze)
        self.assertEqual(len(entities), 0)

    def test_analyze_text_for_entities_london_wikilink(self):
        """Test analyze_text_for_entities with a GPE from a wikilink."""
        text_to_analyze = "London" # Simulating the text part of "[[London]]"
        entities: List[ExtractedEntity] = self.analyzer.analyze_text_for_entities(text_to_analyze)
        
        self.assertEqual(len(entities), 1, f"Expected 1 entity, got {len(entities)}")
        entity = entities[0]
        self.assertEqual(entity.text, "London")
        self.assertIn(entity.label, ["GPE", "LOC"], f"Expected GPE or LOC, got {entity.label}") # spaCy usually labels cities as GPE
        self.assertEqual(entity.start_char, 0)
        self.assertEqual(entity.end_char, 6)


if __name__ == '__main__':
    unittest.main()