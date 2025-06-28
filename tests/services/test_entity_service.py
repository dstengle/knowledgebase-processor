"""Unit tests for EntityService."""

import unittest
from unittest.mock import Mock, patch

from src.knowledgebase_processor.services.entity_service import EntityService
from src.knowledgebase_processor.models.entities import ExtractedEntity
from src.knowledgebase_processor.models.kb_entities import (
    KbPerson, KbOrganization, KbLocation, KbDateEntity
)


class TestEntityService(unittest.TestCase):
    """Test cases for EntityService."""

    def setUp(self):
        """Set up test fixtures."""
        self.entity_service = EntityService()

    def test_generate_kb_id_person(self):
        """Test KB ID generation for a person entity."""
        entity_type = "Person"
        text = "John Doe"
        
        kb_id = self.entity_service.generate_kb_id(entity_type, text)
        
        self.assertIsInstance(kb_id, str)
        self.assertIn("Person", kb_id)
        self.assertIn("john_doe", kb_id)
        # Should contain a UUID component
        self.assertTrue(any(c.isalnum() for c in kb_id.split('_')[-1]))

    def test_generate_kb_id_organization(self):
        """Test KB ID generation for an organization entity."""
        entity_type = "Organization"
        text = "OpenAI Inc."
        
        kb_id = self.entity_service.generate_kb_id(entity_type, text)
        
        self.assertIsInstance(kb_id, str)
        self.assertIn("Organization", kb_id)
        self.assertIn("openai_inc", kb_id)

    def test_generate_kb_id_special_characters(self):
        """Test KB ID generation with special characters."""
        entity_type = "Person"
        text = "Jean-Paul Sartre (Philosopher)"
        
        kb_id = self.entity_service.generate_kb_id(entity_type, text)
        
        self.assertIsInstance(kb_id, str)
        # Special characters should be replaced with underscores
        self.assertNotIn("-", kb_id)
        self.assertNotIn("(", kb_id)
        self.assertNotIn(")", kb_id)
        self.assertIn("jean_paul_sartre", kb_id)

    def test_generate_kb_id_long_text(self):
        """Test KB ID generation with very long text."""
        entity_type = "Organization"
        text = "A" * 100  # Very long name
        
        kb_id = self.entity_service.generate_kb_id(entity_type, text)
        
        self.assertIsInstance(kb_id, str)
        # Should be truncated to reasonable length
        slug_part = kb_id.split('/')[-1].split('_')[0]
        self.assertLessEqual(len(slug_part), 50)

    def test_transform_to_kb_entity_person(self):
        """Test transformation of extracted person entity to KB entity."""
        extracted_entity = ExtractedEntity(
            text="Alice Smith",
            label="PERSON",
            start_char=10,
            end_char=21
        )
        source_doc_path = "documents/test.md"
        
        kb_entity = self.entity_service.transform_to_kb_entity(
            extracted_entity, source_doc_path
        )
        
        self.assertIsInstance(kb_entity, KbPerson)
        self.assertEqual(kb_entity.full_name, "Alice Smith")
        self.assertEqual(kb_entity.label, "Alice Smith")
        self.assertEqual(kb_entity.extracted_from_text_span, (10, 21))
        self.assertIn("Document/documents/test.md", kb_entity.source_document_uri)

    def test_transform_to_kb_entity_organization(self):
        """Test transformation of extracted organization entity to KB entity."""
        extracted_entity = ExtractedEntity(
            text="Microsoft",
            label="ORG",
            start_char=5,
            end_char=14
        )
        source_doc_path = "docs/company.md"
        
        kb_entity = self.entity_service.transform_to_kb_entity(
            extracted_entity, source_doc_path
        )
        
        self.assertIsInstance(kb_entity, KbOrganization)
        self.assertEqual(kb_entity.name, "Microsoft")
        self.assertEqual(kb_entity.label, "Microsoft")
        self.assertEqual(kb_entity.extracted_from_text_span, (5, 14))

    def test_transform_to_kb_entity_location_loc(self):
        """Test transformation of extracted location entity (LOC label) to KB entity."""
        extracted_entity = ExtractedEntity(
            text="New York",
            label="LOC",
            start_char=20,
            end_char=28
        )
        source_doc_path = "travel/notes.md"
        
        kb_entity = self.entity_service.transform_to_kb_entity(
            extracted_entity, source_doc_path
        )
        
        self.assertIsInstance(kb_entity, KbLocation)
        self.assertEqual(kb_entity.name, "New York")
        self.assertEqual(kb_entity.label, "New York")

    def test_transform_to_kb_entity_location_gpe(self):
        """Test transformation of extracted GPE entity to KB entity."""
        extracted_entity = ExtractedEntity(
            text="United States",
            label="GPE",
            start_char=0,
            end_char=13
        )
        source_doc_path = "politics/analysis.md"
        
        kb_entity = self.entity_service.transform_to_kb_entity(
            extracted_entity, source_doc_path
        )
        
        self.assertIsInstance(kb_entity, KbLocation)
        self.assertEqual(kb_entity.name, "United States")

    def test_transform_to_kb_entity_date(self):
        """Test transformation of extracted date entity to KB entity."""
        extracted_entity = ExtractedEntity(
            text="2024-01-15",
            label="DATE",
            start_char=30,
            end_char=40
        )
        source_doc_path = "calendar/events.md"
        
        kb_entity = self.entity_service.transform_to_kb_entity(
            extracted_entity, source_doc_path
        )
        
        self.assertIsInstance(kb_entity, KbDateEntity)
        self.assertEqual(kb_entity.date_value, "2024-01-15")
        self.assertEqual(kb_entity.label, "2024-01-15")

    def test_transform_to_kb_entity_unsupported_type(self):
        """Test transformation of unsupported entity type returns None."""
        extracted_entity = ExtractedEntity(
            text="123.45",
            label="MONEY",
            start_char=0,
            end_char=6
        )
        source_doc_path = "finance/report.md"
        
        kb_entity = self.entity_service.transform_to_kb_entity(
            extracted_entity, source_doc_path
        )
        
        self.assertIsNone(kb_entity)

    def test_transform_to_kb_entity_case_insensitive(self):
        """Test that entity label matching is case insensitive."""
        extracted_entity = ExtractedEntity(
            text="Bob Johnson",
            label="person",  # lowercase
            start_char=0,
            end_char=11
        )
        source_doc_path = "test.md"
        
        kb_entity = self.entity_service.transform_to_kb_entity(
            extracted_entity, source_doc_path
        )
        
        self.assertIsInstance(kb_entity, KbPerson)
        self.assertEqual(kb_entity.full_name, "Bob Johnson")

    def test_source_document_uri_with_spaces(self):
        """Test that source document paths with spaces are properly handled."""
        extracted_entity = ExtractedEntity(
            text="Test Entity",
            label="PERSON",
            start_char=0,
            end_char=11
        )
        source_doc_path = "folder with spaces/file name.md"
        
        kb_entity = self.entity_service.transform_to_kb_entity(
            extracted_entity, source_doc_path
        )
        
        self.assertIsInstance(kb_entity, KbPerson)
        # Spaces should be replaced with underscores and properly quoted
        self.assertIn("folder_with_spaces/file_name.md", kb_entity.source_document_uri)

    def test_source_document_uri_with_backslashes(self):
        """Test that backslashes in paths are normalized to forward slashes."""
        extracted_entity = ExtractedEntity(
            text="Test Entity",
            label="PERSON",
            start_char=0,
            end_char=11
        )
        source_doc_path = "folder\\subfolder\\file.md"
        
        kb_entity = self.entity_service.transform_to_kb_entity(
            extracted_entity, source_doc_path
        )
        
        self.assertIsInstance(kb_entity, KbPerson)
        # Backslashes should be normalized to forward slashes
        self.assertIn("folder/subfolder/file.md", kb_entity.source_document_uri)
        self.assertNotIn("\\", kb_entity.source_document_uri)

    @patch('src.knowledgebase_processor.services.entity_service.get_logger')
    def test_logging_for_supported_entity(self, mock_get_logger):
        """Test that processing supported entities generates appropriate log messages."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        entity_service = EntityService()
        extracted_entity = ExtractedEntity(
            text="Test Person",
            label="PERSON",
            start_char=0,
            end_char=11
        )
        
        entity_service.transform_to_kb_entity(extracted_entity, "test.md")
        
        # Should log info about processing the entity
        mock_logger.info.assert_called_with(
            "Processing entity: Test Person of type PERSON"
        )

    @patch('src.knowledgebase_processor.services.entity_service.get_logger')
    def test_logging_for_unsupported_entity(self, mock_get_logger):
        """Test that processing unsupported entities generates debug log messages."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        entity_service = EntityService()
        extracted_entity = ExtractedEntity(
            text="123.45",
            label="MONEY",
            start_char=0,
            end_char=6
        )
        
        result = entity_service.transform_to_kb_entity(extracted_entity, "test.md")
        
        self.assertIsNone(result)
        # Should log debug about unhandled entity type
        mock_logger.debug.assert_called_with(
            "Unhandled entity type: MONEY for text: '123.45'"
        )

    def test_kb_id_uniqueness(self):
        """Test that generated KB IDs are unique even for identical inputs."""
        entity_type = "Person"
        text = "John Doe"
        
        kb_id1 = self.entity_service.generate_kb_id(entity_type, text)
        kb_id2 = self.entity_service.generate_kb_id(entity_type, text)
        
        self.assertNotEqual(kb_id1, kb_id2)
        # Both should contain the same text-based part but different UUID parts
        self.assertIn("john_doe", kb_id1)
        self.assertIn("john_doe", kb_id2)


if __name__ == '__main__':
    unittest.main()