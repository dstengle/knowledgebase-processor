"""Integration tests for the KnowledgeBaseAPI."""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from src.knowledgebase_processor.api import KnowledgeBaseAPI
from src.knowledgebase_processor.config.config import Config
from src.knowledgebase_processor.models.entities import ExtractedEntity


class TestKnowledgeBaseAPIIntegration(unittest.TestCase):
    """Integration test cases for KnowledgeBaseAPI that verify service coordination."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.kb_path = os.path.join(self.temp_dir, "knowledge_base")
        self.metadata_path = os.path.join(self.temp_dir, "metadata.db")
        self.rdf_output_path = os.path.join(self.temp_dir, "rdf_output")
        
        # Create directories
        os.makedirs(self.kb_path, exist_ok=True)
        os.makedirs(self.rdf_output_path, exist_ok=True)
        
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
        # Add SPARQL endpoints for testing
        self.config.sparql_endpoint = "http://localhost:3030/test/query"
        self.config.sparql_update_endpoint = "http://localhost:3030/test/update"
        
        # Initialize API
        self.api = KnowledgeBaseAPI(self.config)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_api_service_coordination(self):
        """Test that API correctly coordinates between different services."""
        # Create test markdown files
        test_file1 = os.path.join(self.kb_path, "document1.md")
        test_file2 = os.path.join(self.kb_path, "document2.md")
        
        with open(test_file1, 'w', encoding='utf-8') as f:
            f.write("---\ntitle: Test Document 1\ntags: [test, important]\n---\n\n# Document 1\n\nThis is a test document.")
        
        with open(test_file2, 'w', encoding='utf-8') as f:
            f.write("---\ntitle: Test Document 2\ntags: [test, demo]\n---\n\n# Document 2\n\nAnother test document.")
        
        # Test document processing
        result = self.api.process_documents("**/*.md")
        self.assertEqual(result, 0)  # Success
        
        # Test search functionality
        search_results = self.api.search("test")
        self.assertIsInstance(search_results, list)
        
        # Test tag-based search
        tag_results = self.api.find_by_tag("test")
        self.assertIsInstance(tag_results, list)
    
    def test_entity_service_integration(self):
        """Test integration between API and EntityService."""
        # Test KB ID generation
        kb_id = self.api.generate_kb_id("Person", "John Doe")
        self.assertIsInstance(kb_id, str)
        self.assertIn("Person", kb_id)
        self.assertIn("john_doe", kb_id.lower())
        
        # Test entity transformation
        extracted_entity = ExtractedEntity(
            text="Alice Smith",
            label="PERSON",
            start_char=10,
            end_char=21
        )
        
        kb_entity = self.api.transform_to_kb_entity(extracted_entity, "test/document.md")
        self.assertIsNotNone(kb_entity)
        self.assertEqual(kb_entity.label, "Alice Smith")
    
    def test_processing_service_integration(self):
        """Test integration between API and ProcessingService."""
        # Create test file
        test_file = os.path.join(self.kb_path, "test_processing.md")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("# Test Document\n\nThis document tests processing integration.")
        
        # Test processing with RDF output
        result = self.api.process_documents("**/*.md", rdf_output_dir=Path(self.rdf_output_path))
        self.assertEqual(result, 0)
        
        # Test single document processing - use process_file instead
        relative_path = os.path.relpath(test_file, self.kb_path)
        document = self.api.process_file(relative_path)
        self.assertIsNotNone(document)
    
    @patch('src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_sparql_service_integration(self, mock_sparql_interface_class):
        """Test integration between API and SparqlService (mocked SPARQL)."""
        # Setup mock
        mock_interface = Mock()
        mock_sparql_interface_class.return_value = mock_interface
        mock_interface.select.return_value = [{"name": "test", "value": "result"}]
        
        # Test SPARQL query through API
        result = self.api.sparql_query("SELECT ?name ?value WHERE { ?s ?name ?value }")
        self.assertIsInstance(result, str)
        
        # Verify interface was called
        mock_interface.select.assert_called_once()
    
    @patch('src.knowledgebase_processor.services.sparql_service.SparqlQueryInterface')
    def test_sparql_load_integration(self, mock_sparql_interface_class):
        """Test RDF file loading through API (mocked SPARQL)."""
        # Setup mock
        mock_interface = Mock()
        mock_sparql_interface_class.return_value = mock_interface
        
        # Create test RDF file
        test_rdf_file = os.path.join(self.temp_dir, "test.ttl")
        with open(test_rdf_file, 'w', encoding='utf-8') as f:
            f.write("@prefix : <http://example.org/> .\n:person1 :name 'John' .")
        
        # Test RDF loading through API
        self.api.sparql_load(Path(test_rdf_file), graph_uri="http://example.org/graph1")
        
        # Verify interface was called
        mock_interface.load_file.assert_called_once()
    
    def test_query_coordination(self):
        """Test that different query types are properly coordinated."""
        # Create test files with different content
        test_file1 = os.path.join(self.kb_path, "tagged_doc.md")
        test_file2 = os.path.join(self.kb_path, "topic_doc.md")
        
        with open(test_file1, 'w', encoding='utf-8') as f:
            f.write("---\ntags: [important, research]\n---\n\n# Tagged Document\n\nThis has tags.")
        
        with open(test_file2, 'w', encoding='utf-8') as f:
            f.write("# Topic Document\n\nThis document discusses machine learning and AI.")
        
        # Process documents first
        self.api.process_documents("**/*.md")
        
        # Test different query types through API
        text_results = self.api.query("machine learning", query_type="text")
        self.assertIsInstance(text_results, list)
        
        tag_results = self.api.query("important", query_type="tag")
        self.assertIsInstance(tag_results, list)
        
        topic_results = self.api.query("AI", query_type="topic")
        self.assertIsInstance(topic_results, list)
    
    def test_error_handling_coordination(self):
        """Test that errors are properly handled across service boundaries."""
        # Test processing with invalid pattern (should handle gracefully)
        result = self.api.process_documents("")
        self.assertIsInstance(result, int)  # Should return an exit code
        
        # Test search with empty query (should handle gracefully)
        results = self.api.search("")
        self.assertIsInstance(results, list)
    
    def test_configuration_propagation(self):
        """Test that configuration is properly propagated to services."""
        # Verify config is available in services
        self.assertEqual(self.api.config, self.config)
        self.assertEqual(self.api.sparql_service.config, self.config)
        
        # Test that processing service has access to config through kb_processor
        self.assertIsNotNone(self.api.processing_service.kb_processor)
    
    def test_api_convenience_methods(self):
        """Test that convenience methods work correctly with services."""
        # Create test file
        test_file = os.path.join(self.kb_path, "convenience_test.md")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("# Convenience Test\n\nTesting convenience methods.")
        
        # Test process_all convenience method
        documents = self.api.process_all("**/*.md")
        self.assertIsInstance(documents, list)
        
        # Test process_file convenience method
        relative_path = os.path.relpath(test_file, self.kb_path)
        document = self.api.process_file(relative_path)
        self.assertIsNotNone(document)
    
    def test_metadata_operations(self):
        """Test metadata operations through the API."""
        # Test getting metadata for non-existent document
        metadata = self.api.get_metadata("non_existent_doc")
        self.assertIsNone(metadata)
        
        # This test would be expanded with actual metadata operations
        # once documents are processed and stored
    
    def test_related_documents_functionality(self):
        """Test finding related documents through API."""
        # Create test files with potential relationships
        test_file1 = os.path.join(self.kb_path, "related1.md")
        test_file2 = os.path.join(self.kb_path, "related2.md")
        
        with open(test_file1, 'w', encoding='utf-8') as f:
            f.write("# Document 1\n\nThis mentions [[related2]] document.")
        
        with open(test_file2, 'w', encoding='utf-8') as f:
            f.write("# Document 2\n\nThis is referenced by document 1.")
        
        # Process documents
        self.api.process_documents("**/*.md")
        
        # Test finding related documents
        related = self.api.find_related("related1")
        self.assertIsInstance(related, list)
    
    def test_service_initialization_order(self):
        """Test that services are initialized in correct order with dependencies."""
        # Verify all services are properly initialized
        self.assertIsNotNone(self.api.kb_processor)
        self.assertIsNotNone(self.api.entity_service)
        self.assertIsNotNone(self.api.sparql_service)
        self.assertIsNotNone(self.api.processing_service)
        
        # Verify processing service has reference to kb_processor
        self.assertEqual(
            self.api.processing_service.kb_processor,
            self.api.kb_processor
        )
        
        # Verify sparql service has reference to config
        self.assertEqual(
            self.api.sparql_service.config,
            self.config
        )
    
    def test_full_pipeline_integration(self):
        """Test a complete pipeline from document processing to querying."""
        # Create comprehensive test document
        test_content = """---
title: Integration Test Document
author: Test Author
tags: [integration, testing, api]
date: 2024-01-15
---

# Integration Test Document

This document tests the full pipeline integration.

## People
- John Doe (person mentioned)
- Jane Smith (another person)

## Organizations
- OpenAI (organization)
- Microsoft (another org)

## Locations
- San Francisco (location)
- New York (another location)

## TODO Items
- [ ] Test entity extraction
- [x] Complete integration tests
- [ ] Verify RDF generation

## Links
See also: [[related-document]]

#important #machine-learning
"""
        
        test_file = os.path.join(self.kb_path, "integration_test.md")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Step 1: Process documents
        process_result = self.api.process_documents("**/*.md")
        self.assertEqual(process_result, 0)
        
        # Step 2: Search for content
        search_results = self.api.search("integration")
        self.assertIsInstance(search_results, list)
        
        # Step 3: Find by tags
        tag_results = self.api.find_by_tag("testing")
        self.assertIsInstance(tag_results, list)
        
        # Step 4: Test entity operations (with sample entity)
        sample_entity = ExtractedEntity(
            text="Integration Tester",
            label="PERSON",
            start_char=0,
            end_char=18
        )
        kb_entity = self.api.transform_to_kb_entity(sample_entity, "integration_test.md")
        self.assertIsNotNone(kb_entity)
        
        # Step 5: Test convenience methods
        all_docs = self.api.process_all("**/*.md")
        self.assertIsInstance(all_docs, list)


if __name__ == '__main__':
    unittest.main()