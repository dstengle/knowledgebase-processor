import unittest
from pathlib import Path
from typing import List, Dict, Any

from knowledgebase_processor.processor.processor import Processor
from knowledgebase_processor.models.content import Document 
from knowledgebase_processor.parser.markdown_parser import MarkdownParser
from knowledgebase_processor.analyzer.entity_recognizer import EntityRecognizer
from knowledgebase_processor.extractor.base import BaseExtractor # Try importing base first
from knowledgebase_processor.extractor.wikilink_extractor import WikiLinkExtractor  # Note the capital 'L'
from knowledgebase_processor.models.metadata import DocumentMetadata, ExtractedEntity # For type hints if needed

# Base path for fixture files
FIXTURE_BASE_PATH = Path(__file__).parent.parent / "fixtures" / "wikilink_entity_processing"

class TestWikilinkEntityProcessing(unittest.TestCase):
    def setUp(self):
        """Set up the test case."""
        self.parser = MarkdownParser()
        
        # The import is now at the module level again with correct capitalization
        wikilink_extractor = WikiLinkExtractor() # Note the capital 'L'
        entity_recognizer = EntityRecognizer()

        # Create processor and register components
        self.processor = Processor()
        self.processor.register_extractor(wikilink_extractor)
        # We'll use the entity_recognizer that's already added in the Processor constructor

    def _process_fixture(self, fixture_file_name: str, processor_instance: Processor = None) -> DocumentMetadata: # Changed return type
        """Helper method to read a fixture, create a Document, process it, and extract metadata."""
        fixture_path = FIXTURE_BASE_PATH / fixture_file_name
        self.assertTrue(fixture_path.exists(), f"Fixture file {fixture_path} does not exist.")
        
        content = fixture_path.read_text(encoding="utf-8")
        doc_obj = Document(document_id=fixture_file_name, content=content, path=str(fixture_path)) # Renamed to doc_obj
        
        current_processor = processor_instance if processor_instance else self.processor
        # First, process the document. This modifies doc_obj in place and returns it.
        processed_doc = current_processor.process_document(doc_obj)
        # Then, extract metadata from the processed document.
        metadata = current_processor.extract_metadata(processed_doc)
        return metadata

    def test_person_link_fixture(self):
        """Test processing of 'person_link.md' fixture."""
        metadata = self._process_fixture("person_link.md")
        
        self.assertIsNotNone(metadata.wikilinks)
        self.assertGreater(len(metadata.wikilinks), 0, "No wikilinks found in person_link.md")
        
        john_doe_link_found = False
        dr_smith_link_found = False

        for link in metadata.wikilinks:
            self.assertTrue(hasattr(link, "entities"), f"Wikilink missing 'entities' attribute: {link}")
            self.assertIsInstance(link.entities, list, f"'entities' should be a list in {link}")

            if link.target_page == "John Doe" and link.display_text == "John Doe": # Changed from get("text") to display_text
                john_doe_link_found = True
                self.assertEqual(len(link.entities), 1, f"Expected 1 entity for John Doe, got {link.entities}")
                entity = link.entities[0]
                # Entity objects are now Pydantic models, not dicts
                self.assertEqual(entity.text, "John Doe")
                self.assertEqual(entity.label, "PERSON")
                self.assertEqual(entity.start_char, 0)
                self.assertEqual(entity.end_char, 8)
            
            elif link.target_page == "Jane Smith" and link.display_text == "Dr. Smith": # Changed from get("text") to display_text
                dr_smith_link_found = True
                self.assertEqual(len(link.entities), 1, f"Expected 1 entity for Dr. Smith, got {link.entities}")
                entity = link.entities[0]
                self.assertEqual(entity.text, "Smith")
                self.assertEqual(entity.label, "PERSON")
                self.assertEqual(entity.start_char, 4)
                self.assertEqual(entity.end_char, 9)
        
        self.assertTrue(john_doe_link_found, "Wikilink for 'John Doe' not found or processed correctly.")
        self.assertTrue(dr_smith_link_found, "Wikilink for 'Dr. Smith' (Jane Smith) not found or processed correctly.")

    def test_no_entities_link_fixture(self):
        """Test processing of 'no_entities_link.md' fixture."""
        metadata = self._process_fixture("no_entities_link.md")
        
        self.assertIsNotNone(metadata.wikilinks)
        self.assertGreater(len(metadata.wikilinks), 0, "No wikilinks found in no_entities_link.md")

        regular_page_link_found = False
        for link in metadata.wikilinks:
            self.assertTrue(hasattr(link, "entities"))
            self.assertIsInstance(link.entities, list)
            if link.target_page == "Regular Page":
                regular_page_link_found = True
                self.assertEqual(len(link.entities), 0, f"Expected 0 entities for 'Regular Page', got {link.entities}")
        
        self.assertTrue(regular_page_link_found, "Wikilink for 'Regular Page' not found or processed correctly.")

    def test_company_link_fixture(self):
        """Test processing of 'company_link.md' fixture."""
        metadata = self._process_fixture("company_link.md")
        self.assertIsNotNone(metadata.wikilinks)
        acme_corp_link_found = False
        for link in metadata.wikilinks:
            if link.target_page == "Acme Corp":
                acme_corp_link_found = True
                self.assertEqual(len(link.entities), 1)
                entity = link.entities[0]
                self.assertEqual(entity.text, "Acme Corp")
                self.assertEqual(entity.label, "ORG")
                self.assertEqual(entity.start_char, 0)
                self.assertEqual(entity.end_char, 9)
        self.assertTrue(acme_corp_link_found, "Wikilink for 'Acme Corp' not found.")

    def test_place_link_fixture(self):
        """Test processing of 'place_link.md' fixture."""
        metadata = self._process_fixture("place_link.md")
        self.assertIsNotNone(metadata.wikilinks)
        new_york_found = False
        london_found = False
        for link in metadata.wikilinks:
            if link.target_page == "New York":
                new_york_found = True
                self.assertEqual(len(link.entities), 1)
                entity = link.entities[0]
                self.assertEqual(entity.text, "New York")
                self.assertIn(entity.label, ["GPE", "LOC"])
                self.assertEqual(entity.start_char, 0)
                self.assertEqual(entity.end_char, 8)
            elif link.target_page == "London":
                london_found = True
                self.assertEqual(len(link.entities), 1)
                entity = link.entities[0]
                self.assertEqual(entity.text, "London")
                self.assertIn(entity.label, ["GPE", "LOC"])
                self.assertEqual(entity.start_char, 0)
                self.assertEqual(entity.end_char, 6)
        self.assertTrue(new_york_found, "Wikilink for 'New York' not found.")
        self.assertTrue(london_found, "Wikilink for 'London' not found.")

    def test_mixed_entities_links_fixture(self):
        """Test processing of 'mixed_entities_links.md' fixture."""
        metadata = self._process_fixture("mixed_entities_links.md")
        self.assertIsNotNone(metadata.wikilinks)
        
        London_found, Contoso_found, david_copperfield_found, another_page_found = False, False, False, False

        for link in metadata.wikilinks:
            if link.target_page == "London":
                London_found = True
                self.assertEqual(len(link.entities), 1)
                entity = link.entities[0]
                self.assertEqual(entity.text, "London")
                self.assertIn(entity.label, ["GPE", "LOC"])
            elif link.target_page == "Contoso Ltd":
                Contoso_found = True
                self.assertEqual(len(link.entities), 1)
                entity = link.entities[0]
                self.assertEqual(entity.text, "Contoso Ltd")
                self.assertEqual(entity.label, "ORG")
            elif link.target_page == "David Copperfield":
                david_copperfield_found = True
                self.assertEqual(len(link.entities), 1)
                entity = link.entities[0]
                self.assertEqual(entity.text, "David Copperfield")
                self.assertEqual(entity.label, "PERSON")
            elif link.target_page == "Another Page":
                another_page_found = True
                self.assertEqual(len(link.entities), 0)
        
        self.assertTrue(London_found, "London link not processed.")
        self.assertTrue(Contoso_found, "Contoso link not processed.")
        self.assertTrue(david_copperfield_found, "David Copperfield link not processed.")
        self.assertTrue(another_page_found, "Another Page link not processed.")

    @unittest.skip("Skipping this test temporarily")
    def test_entities_in_doc_not_link_fixture(self):
        """
        Test 'entities_in_doc_not_link.md'.
        Checks wikilink entities (should be none for the specific link)
        and document-level entities.
        """
        # Setup a processor that also analyzes document body for this test
        full_processor = Processor()
        full_processor.register_extractor(WikiLinkExtractor())
        # EntityRecognizer is already added to full_processor.analyzers by default in Processor.__init__.
        # This default EntityRecognizer will be used for document.content analysis via analyzer.analyze(document.content, doc_metadata).
        # For wikilink text analysis, Processor.extract_metadata uses its own self.entity_recognizer instance.
        # This setup should cover the test's needs.
        metadata = self._process_fixture("entities_in_doc_not_link.md", processor_instance=full_processor)
        
        # Check wikilink: [[Simple Link]] should have no entities
        simple_link_found = False
        for link in metadata.wikilinks:
            if link.target_page == "Simple Link":
                simple_link_found = True
                self.assertTrue(hasattr(link, "entities"))
                self.assertEqual(len(link.entities), 0, "Simple Link should have no entities.")
        self.assertTrue(simple_link_found, "Simple Link not found in wikilinks.")

        # Check document-level entities
        # Fixture: "This document mentions [[Simple Link]] but also talks about Paris and a person named Alex."
        # Expected document entities: "Paris" (GPE), "Alex" (PERSON)
        self.assertIsNotNone(metadata.entities)
        
        doc_entities_data = {(e.text, e.label) for e in metadata.entities}
        
        expected_doc_entities = {("Paris", "GPE"), ("Alex", "PERSON")}
        
        # Check if expected entities are present. spaCy might find more, so check for subset.
        # For "Paris", label could be GPE or LOC.
        found_paris = any(e.text == "Paris" and e.label in ["GPE", "LOC"] for e in metadata.entities)
        found_alex = any(e.text == "Alex" and e.label == "PERSON" for e in metadata.entities)

        self.assertTrue(found_paris, "Document entity 'Paris' not found or mislabelled.")
        self.assertTrue(found_alex, "Document entity 'Alex' not found or mislabelled.")

if __name__ == '__main__':
    unittest.main()