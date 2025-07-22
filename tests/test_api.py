"""Tests for the KnowledgeBaseAPI facade."""

import unittest
import tempfile
import os
from pathlib import Path

from knowledgebase_processor.api import KnowledgeBaseAPI
from knowledgebase_processor.config.config import Config
from knowledgebase_processor.services.entity_service import EntityService
from knowledgebase_processor.services.sparql_service import SparqlService
from knowledgebase_processor.services.processing_service import ProcessingService


class TestKnowledgeBaseAPI(unittest.TestCase):
    """Test cases for KnowledgeBaseAPI."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.kb_path = os.path.join(self.temp_dir, "knowledge_base")
        self.metadata_path = os.path.join(self.temp_dir, "metadata.db")
        
        # Create knowledge base directory
        os.makedirs(self.kb_path, exist_ok=True)
        
        # Create test configuration
        self.config = Config(
            knowledge_base_path=self.kb_path,
            metadata_store_path=self.metadata_path,
            file_patterns=["**/*.md"],
            extract_frontmatter=True,
            extract_tags=True,
            analyze_topics=True,
            analyze_entities=False,  # Keep disabled for faster tests
            enrich_relationships=True
        )
        
        # Initialize API
        self.api = KnowledgeBaseAPI(self.config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_api_initialization(self):
        """Test that API initializes correctly with all services."""
        self.assertIsNotNone(self.api.kb_processor)
        self.assertIsInstance(self.api.entity_service, EntityService)
        self.assertIsInstance(self.api.sparql_service, SparqlService)
        self.assertIsInstance(self.api.processing_service, ProcessingService)
        self.assertEqual(self.api.config, self.config)
    
    def test_entity_service_delegation(self):
        """Test that entity service methods are properly delegated."""
        # Test generate_kb_id
        kb_id = self.api.generate_kb_id("Person", "John Doe")
        self.assertIsInstance(kb_id, str)
        self.assertIn("Person", kb_id)
        self.assertIn("john_doe", kb_id.lower())
    
    def test_process_documents_delegation(self):
        """Test that process_documents is properly delegated."""
        # Create a test markdown file
        test_file = os.path.join(self.kb_path, "test.md")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("# Test Document\n\nThis is a test document.")
        
        # Process documents
        result = self.api.process_documents("**/*.md")
        self.assertEqual(result, 0)  # Should return success code
    
    def test_search_methods_delegation(self):
        """Test that search methods are properly delegated."""
        # These methods should not raise errors even with empty database
        results = self.api.search("test")
        self.assertIsInstance(results, list)
        
        results = self.api.find_by_tag("test")
        self.assertIsInstance(results, list)
        
        results = self.api.find_by_topic("test")
        self.assertIsInstance(results, list)
    
    def test_sparql_query_method_exists(self):
        """Test that SPARQL query method exists and has correct signature."""
        # We can't test actual SPARQL functionality without a running endpoint,
        # but we can verify the method exists and would delegate properly
        self.assertTrue(hasattr(self.api, 'sparql_query'))
        self.assertTrue(callable(self.api.sparql_query))
        
        self.assertTrue(hasattr(self.api, 'sparql_load'))
        self.assertTrue(callable(self.api.sparql_load))
    
    def test_convenience_methods(self):
        """Test convenience methods that wrap kb_processor functionality."""
        # Create a test markdown file
        test_file = os.path.join(self.kb_path, "test.md")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("# Test Document\n\nThis is a test document.")
        
        # Test process_all
        result = self.api.process_all("**/*.md")
        self.assertEqual(result, 0)
        
        # Test get_metadata (should return None for non-existent document)
        metadata = self.api.get_metadata("non_existent_doc")
        self.assertIsNone(metadata)


if __name__ == '__main__':
    unittest.main()