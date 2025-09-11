import unittest
from knowledgebase_processor.analyzer.entity_recognizer import EntityRecognizer # Updated import
from knowledgebase_processor.models.entities import ExtractedEntity # Updated import

@unittest.skip("Spacy entity recognition disabled - tests skipped")
class TestEntityRecognizer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recognizer = EntityRecognizer()

    def test_extract_person_org_gpe(self):
        text = "Barack Obama was the president of the United States and worked with Microsoft."
        entities = self.recognizer.analyze_text_for_entities(text) # Changed method call
        labels = {e.label for e in entities} # entities is now List[ExtractedEntity], never None
        self.assertIn("PERSON", labels)
        self.assertIn("ORG", labels)
        self.assertIn("GPE", labels)

    def test_no_entities(self):
        text = "This is a sentence without any named entities."
        entities = self.recognizer.analyze_text_for_entities(text) # Changed method call
        self.assertEqual(len(entities), 0) # analyze_text_for_entities returns [] for no entities

    def test_multiple_entities(self):
        text = "Apple is looking at buying U.K. startup for $1 billion."
        entities = self.recognizer.analyze_text_for_entities(text) # Changed method call
        self.assertIsNotNone(entities) # Should be a list
        self.assertGreaterEqual(len(entities), 2)

    def test_entity_fields(self):
        text = "Google was founded in California."
        entities = self.recognizer.analyze_text_for_entities(text) # Changed method call
        self.assertIsNotNone(entities) # Should be a list
        for ent in entities: # ent is now ExtractedEntity
            self.assertIsInstance(ent.text, str)
            self.assertIsInstance(ent.label, str)
            self.assertIsInstance(ent.start_char, int)
            self.assertIsInstance(ent.end_char, int)
            self.assertGreaterEqual(ent.end_char, ent.start_char)

    # def test_model_not_available(self):
    #     # The current EntityRecognizer constructor does not take model_name
    #     # and loads "en_core_web_sm" by default. If it fails, it raises an OSError.
    #     # This test needs to be re-evaluated or adapted if we want to test model loading failure.
    #     # For now, we assume the default model is available for other tests.
    #     # If we want to test this specific scenario, we'd need to mock spacy.load.
    #     # Let's skip this test for now as it's not compatible with the current EntityRecognizer.
    #     # Alternatively, we can try to catch the OSError if spacy.load is called with a bad model name.
    #     # The current EntityRecognizer loads the model in __init__.
    #     # with self.assertRaises(OSError): # Or potentially another specific spaCy error
    #     #      EntityRecognizer(model_name="nonexistent_model_123") # This will fail if model_name is not a param

    #     # Re-evaluating: The EntityRecognizer in analyzer.entity_recognizer.py does not accept model_name
    #     # It loads "en_core_web_sm" in its __init__.
    #     # This test as written is incompatible.
    #     # To test a model loading failure, one would typically mock spacy.load.
    #     # For now, I will comment out this test as it's not directly applicable to the refactored class.
    #     pass # Commenting out the original test logic.

#    def test_model_not_available(self):
#        # This test was for the old EntityRecognizer that accepted a model_name.
#        # The current one in entity_recognizer.py loads "en_core_web_sm" by default.
#        # To test failure, one would mock spacy.load() within that class.
#        # For now, this specific test case is not directly applicable.
#        pass


if __name__ == "__main__":
    unittest.main()