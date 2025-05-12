import unittest
from knowledgebase_processor.analyzer.entities import EntityRecognizer
from knowledgebase_processor.models.metadata import Entity

class TestEntityRecognizer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recognizer = EntityRecognizer()

    def test_extract_person_org_gpe(self):
        text = "Barack Obama was the president of the United States and worked with Microsoft."
        entities = self.recognizer.extract_entities(text)
        labels = {e.label for e in entities} if entities else set()
        self.assertIn("PERSON", labels)
        self.assertIn("ORG", labels)
        self.assertIn("GPE", labels)

    def test_no_entities(self):
        text = "This is a sentence without any named entities."
        entities = self.recognizer.extract_entities(text)
        self.assertIsNone(entities)

    def test_multiple_entities(self):
        text = "Apple is looking at buying U.K. startup for $1 billion."
        entities = self.recognizer.extract_entities(text)
        self.assertIsNotNone(entities)
        self.assertGreaterEqual(len(entities), 2)

    def test_entity_fields(self):
        text = "Google was founded in California."
        entities = self.recognizer.extract_entities(text)
        self.assertIsNotNone(entities)
        for ent in entities:
            self.assertIsInstance(ent.text, str)
            self.assertIsInstance(ent.label, str)
            self.assertIsInstance(ent.start_char, int)
            self.assertIsInstance(ent.end_char, int)
            self.assertGreaterEqual(ent.end_char, ent.start_char)

    def test_model_not_available(self):
        recognizer = EntityRecognizer(model_name="nonexistent_model_123")
        text = "Barack Obama"
        entities = recognizer.extract_entities(text)
        self.assertIsNone(entities)

if __name__ == "__main__":
    unittest.main()