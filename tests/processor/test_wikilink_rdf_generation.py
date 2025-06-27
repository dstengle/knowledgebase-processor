"""
Test WikiLink entity processing for RDF generation.

This module tests that WikiLink entities are properly added to document metadata
and that RDF files are generated when WikiLinks contain entities.
"""
import unittest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import shutil

from knowledgebase_processor.models.content import Document
from knowledgebase_processor.models.metadata import DocumentMetadata
from knowledgebase_processor.models.links import WikiLink
from knowledgebase_processor.models.metadata import ExtractedEntity as ModelExtractedEntity
from knowledgebase_processor.processor.processor import Processor
from knowledgebase_processor.config.config import Config


class TestWikiLinkRDFGeneration(unittest.TestCase):
    """Test WikiLink entity processing for RDF generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        # Create test config
        self.config = Config(
            knowledge_base_path=self.temp_dir,
            metadata_store_path=str(Path(self.temp_dir) / "metadata"),
            analyze_entities=False  # Test with entity analysis disabled
        )
        
        # Create processor instance
        self.processor = Processor(config=self.config)

    def test_wikilink_entities_added_to_document_metadata(self):
        """Test that WikiLink entities are added to document metadata."""
        # Create a mock document with a WikiLink element
        wikilink = WikiLink(
            content="[[John Doe]]",
            element_type="wikilink",
            position={"start": 0, "end": 11},
            target_page="John Doe",
            display_text="John Doe"
        )
        
        # Create mock entities that would be extracted from the WikiLink
        mock_entity = ModelExtractedEntity(
            text="John Doe",
            label="PERSON",
            start_char=0,
            end_char=8,
            confidence=0.95
        )
        
        document = Document(
            path="test.md",
            title="Test Document",
            content="[[John Doe]] is a person.",
            elements=[wikilink]
        )
        
        # Mock the entity recognizer to return our mock entity
        with patch.object(self.processor.entity_recognizer, 'analyze_text_for_entities') as mock_analyze:
            mock_analyze.return_value = [mock_entity]
            
            # Process the document
            processed_doc = self.processor.process_document(document)
            
            # Check that the WikiLink entity was added to document metadata
            self.assertIsNotNone(processed_doc.metadata)
            self.assertEqual(len(processed_doc.metadata.entities), 1)
            self.assertEqual(processed_doc.metadata.entities[0], mock_entity)
            self.assertEqual(len(processed_doc.metadata.wikilinks), 1)
            self.assertEqual(processed_doc.metadata.wikilinks[0].entities, [mock_entity])

    def test_wikilink_rdf_generation_without_entity_analysis(self):
        """Test that RDF is generated for WikiLink entities without enabling entity analysis."""
        # Create temporary RDF output directory
        rdf_output_dir = Path(self.temp_dir) / "rdf_output"
        
        # Create a document with WikiLink
        wikilink = WikiLink(
            content="[[Jane Smith]]",
            element_type="wikilink",
            position={"start": 0, "end": 14},
            target_page="Jane Smith",
            display_text="Jane Smith"
        )
        
        mock_entity = ModelExtractedEntity(
            text="Jane Smith",
            label="PERSON",
            start_char=0,
            end_char=10,
            confidence=0.90
        )
        
        document = Document(
            path="wikilink_test.md",
            title="WikiLink Test",
            content="[[Jane Smith]] works here.",
            elements=[wikilink]
        )
        
        # Mock reader and metadata store
        mock_reader = Mock()
        mock_reader.read_all.return_value = [document]
        
        mock_metadata_store = Mock()
        
        # Mock the entity recognizer
        with patch.object(self.processor.entity_recognizer, 'analyze_text_for_entities') as mock_analyze:
            mock_analyze.return_value = [mock_entity]
            
            # Process and generate RDF
            result = self.processor.process_and_generate_rdf(
                reader=mock_reader,
                metadata_store=mock_metadata_store,
                pattern="*.md",
                knowledge_base_path=Path(self.temp_dir),
                rdf_output_dir_str=str(rdf_output_dir)
            )
            
            # Check that processing succeeded
            self.assertEqual(result, 0)
            
            # Check that RDF file was created
            expected_rdf_file = rdf_output_dir / "wikilink_test.ttl"
            self.assertTrue(expected_rdf_file.exists())
            
            # Check that the file has content
            with open(expected_rdf_file, 'r') as f:
                rdf_content = f.read()
                self.assertIn("Jane Smith", rdf_content)
                
    def test_multiple_wikilink_entities_in_document(self):
        """Test processing of multiple WikiLink entities in a single document."""
        # Create WikiLinks with different entity types
        person_wikilink = WikiLink(
            content="[[Alice Wonder]]",
            element_type="wikilink",
            position={"start": 0, "end": 15},
            target_page="Alice Wonder",
            display_text="Alice Wonder"
        )
        
        org_wikilink = WikiLink(
            content="[[ACME Corp]]",
            element_type="wikilink",
            position={"start": 30, "end": 43},
            target_page="ACME Corp",
            display_text="ACME Corp"
        )
        
        person_entity = ModelExtractedEntity(
            text="Alice Wonder",
            label="PERSON",
            start_char=0,
            end_char=12,
            confidence=0.95
        )
        
        org_entity = ModelExtractedEntity(
            text="ACME Corp",
            label="ORG",
            start_char=0,
            end_char=9,
            confidence=0.90
        )
        
        document = Document(
            path="multi_wikilink.md",
            title="Multiple WikiLinks",
            content="[[Alice Wonder]] works at [[ACME Corp]].",
            elements=[person_wikilink, org_wikilink]
        )
        
        # Mock entity recognizer to return different entities for different texts
        def mock_analyze_side_effect(text):
            if text == "Alice Wonder":
                return [person_entity]
            elif text == "ACME Corp":
                return [org_entity]
            return []
        
        with patch.object(self.processor.entity_recognizer, 'analyze_text_for_entities') as mock_analyze:
            mock_analyze.side_effect = mock_analyze_side_effect
            
            # Process the document
            processed_doc = self.processor.process_document(document)
            
            # Check that both entities were added to document metadata
            self.assertEqual(len(processed_doc.metadata.entities), 2)
            entity_texts = [e.text for e in processed_doc.metadata.entities]
            self.assertIn("Alice Wonder", entity_texts)
            self.assertIn("ACME Corp", entity_texts)

    def test_duplicate_wikilink_entities_not_duplicated(self):
        """Test that duplicate WikiLink entities are not added multiple times."""
        # Create two WikiLinks with the same entity
        wikilink1 = WikiLink(
            content="[[Bob Builder]]",
            element_type="wikilink",
            position={"start": 0, "end": 15},
            target_page="Bob Builder",
            display_text="Bob Builder"
        )
        
        wikilink2 = WikiLink(
            content="[[Bob Builder]]",
            element_type="wikilink",
            position={"start": 30, "end": 45},
            target_page="Bob Builder",
            display_text="Bob Builder"
        )
        
        mock_entity = ModelExtractedEntity(
            text="Bob Builder",
            label="PERSON",
            start_char=0,
            end_char=11,
            confidence=0.95
        )
        
        document = Document(
            path="duplicate_wikilink.md",
            title="Duplicate WikiLinks",
            content="[[Bob Builder]] and [[Bob Builder]] again.",
            elements=[wikilink1, wikilink2]
        )
        
        with patch.object(self.processor.entity_recognizer, 'analyze_text_for_entities') as mock_analyze:
            mock_analyze.return_value = [mock_entity]
            
            # Process the document
            processed_doc = self.processor.process_document(document)
            
            # Check that only one entity was added despite two WikiLinks
            self.assertEqual(len(processed_doc.metadata.entities), 1)
            self.assertEqual(processed_doc.metadata.entities[0].text, "Bob Builder")


if __name__ == '__main__':
    unittest.main()