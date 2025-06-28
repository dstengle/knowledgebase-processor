"""Unit tests for ProcessingService."""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.knowledgebase_processor.services.processing_service import ProcessingService
from src.knowledgebase_processor.main import KnowledgeBaseProcessor


class TestProcessingService(unittest.TestCase):
    """Test cases for ProcessingService."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_kb_processor = Mock(spec=KnowledgeBaseProcessor)
        self.mock_processor = Mock()
        self.mock_reader = Mock()
        self.mock_metadata_store = Mock()
        
        self.mock_kb_processor.processor = self.mock_processor
        self.mock_kb_processor.reader = self.mock_reader
        self.mock_kb_processor.metadata_store = self.mock_metadata_store
        
        self.processing_service = ProcessingService(self.mock_kb_processor)

    def test_initialization_with_processor(self):
        """Test ProcessingService initialization with KB processor."""
        service = ProcessingService(self.mock_kb_processor)
        self.assertEqual(service.kb_processor, self.mock_kb_processor)
        self.assertIsNotNone(service.logger)

    def test_initialization_without_processor(self):
        """Test ProcessingService initialization without KB processor."""
        service = ProcessingService()
        self.assertIsNone(service.kb_processor)
        self.assertIsNotNone(service.logger)

    def test_process_documents_success(self):
        """Test successful document processing."""
        # Setup mocks
        self.mock_processor.process_and_generate_rdf.return_value = 0
        
        pattern = "**/*.md"
        knowledge_base_path = Path("/tmp/kb")
        rdf_output_dir = Path("/tmp/rdf")
        
        result = self.processing_service.process_documents(
            pattern=pattern,
            knowledge_base_path=knowledge_base_path,
            rdf_output_dir=rdf_output_dir
        )
        
        # Verify processor was called correctly
        self.mock_processor.process_and_generate_rdf.assert_called_once_with(
            reader=self.mock_kb_processor.reader,
            metadata_store=self.mock_kb_processor.metadata_store,
            pattern=pattern,
            knowledge_base_path=knowledge_base_path,
            rdf_output_dir_str=str(rdf_output_dir)
        )
        self.assertEqual(result, 0)

    def test_process_documents_without_rdf_output(self):
        """Test document processing without RDF output directory."""
        # Setup mocks
        self.mock_processor.process_and_generate_rdf.return_value = 0
        
        pattern = "**/*.md"
        knowledge_base_path = Path("/tmp/kb")
        
        result = self.processing_service.process_documents(
            pattern=pattern,
            knowledge_base_path=knowledge_base_path
        )
        
        # Verify processor was called with None for RDF output
        self.mock_processor.process_and_generate_rdf.assert_called_once_with(
            reader=self.mock_kb_processor.reader,
            metadata_store=self.mock_kb_processor.metadata_store,
            pattern=pattern,
            knowledge_base_path=knowledge_base_path,
            rdf_output_dir_str=None
        )
        self.assertEqual(result, 0)

    def test_process_documents_no_processor_raises_error(self):
        """Test that processing without KB processor raises ValueError."""
        service = ProcessingService()  # No processor
        
        with self.assertRaises(ValueError) as context:
            service.process_documents("**/*.md", Path("/tmp/kb"))
        
        self.assertIn("KnowledgeBaseProcessor instance is required", str(context.exception))

    def test_process_documents_with_entity_analysis_auto_enable(self):
        """Test that entity analysis is auto-enabled when RDF output is requested."""
        # Setup config mock
        mock_config = Mock()
        mock_config.analyze_entities = False
        
        # Setup mocks
        self.mock_processor.process_and_generate_rdf.return_value = 0
        
        with patch.object(self.processing_service, '_reinitialize_processor_with_config') as mock_reinit:
            result = self.processing_service.process_documents(
                pattern="**/*.md",
                knowledge_base_path=Path("/tmp/kb"),
                rdf_output_dir=Path("/tmp/rdf"),
                config=mock_config
            )
            
            # Verify entity analysis was enabled
            self.assertTrue(mock_config.analyze_entities)
            # Verify processor was reinitialized
            mock_reinit.assert_called_once_with(mock_config)

    def test_process_documents_entity_analysis_already_enabled(self):
        """Test that entity analysis is not changed when already enabled."""
        # Setup config mock
        mock_config = Mock()
        mock_config.analyze_entities = True
        
        # Setup mocks
        self.mock_processor.process_and_generate_rdf.return_value = 0
        
        with patch.object(self.processing_service, '_reinitialize_processor_with_config') as mock_reinit:
            result = self.processing_service.process_documents(
                pattern="**/*.md",
                knowledge_base_path=Path("/tmp/kb"),
                rdf_output_dir=Path("/tmp/rdf"),
                config=mock_config
            )
            
            # Verify entity analysis remains enabled
            self.assertTrue(mock_config.analyze_entities)
            # Verify processor was not reinitialized
            mock_reinit.assert_not_called()

    def test_process_single_document_success(self):
        """Test successful single document processing."""
        # Setup mocks
        mock_document = Mock()
        self.mock_processor.process_file.return_value = mock_document
        
        file_path = Path("/tmp/test.md")
        
        result = self.processing_service.process_single_document(file_path)
        
        # Verify processor was called correctly
        self.mock_processor.process_file.assert_called_once_with(file_path)
        self.assertEqual(result, mock_document)

    def test_process_single_document_no_processor_raises_error(self):
        """Test that single document processing without KB processor raises ValueError."""
        service = ProcessingService()  # No processor
        
        with self.assertRaises(ValueError) as context:
            service.process_single_document(Path("/tmp/test.md"))
        
        self.assertIn("KnowledgeBaseProcessor instance is required", str(context.exception))

    def test_query_documents_text_query(self):
        """Test text-based document querying."""
        # Setup mocks
        mock_results = ["doc1", "doc2"]
        self.mock_kb_processor.search.return_value = mock_results
        
        query_string = "test query"
        
        result = self.processing_service.query_documents(query_string, query_type="text")
        
        # Verify search was called
        self.mock_kb_processor.search.assert_called_once_with(query_string)
        self.assertEqual(result, mock_results)

    def test_query_documents_tag_query(self):
        """Test tag-based document querying."""
        # Setup mocks
        mock_results = ["doc1", "doc3"]
        self.mock_kb_processor.find_by_tag.return_value = mock_results
        
        query_string = "important"
        
        result = self.processing_service.query_documents(query_string, query_type="tag")
        
        # Verify find_by_tag was called
        self.mock_kb_processor.find_by_tag.assert_called_once_with(query_string)
        self.assertEqual(result, mock_results)

    def test_query_documents_topic_query_not_implemented(self):
        """Test topic-based document querying (not fully implemented)."""
        query_string = "machine learning"
        
        result = self.processing_service.query_documents(query_string, query_type="topic")
        
        # Should return empty list and log warning
        self.assertEqual(result, [])

    def test_query_documents_default_text_query(self):
        """Test that default query type is text."""
        # Setup mocks
        mock_results = ["doc1"]
        self.mock_kb_processor.search.return_value = mock_results
        
        query_string = "test"
        
        result = self.processing_service.query_documents(query_string)
        
        # Verify search was called (default behavior)
        self.mock_kb_processor.search.assert_called_once_with(query_string)
        self.assertEqual(result, mock_results)

    def test_query_documents_no_processor_raises_error(self):
        """Test that querying without KB processor raises ValueError."""
        service = ProcessingService()  # No processor
        
        with self.assertRaises(ValueError) as context:
            service.query_documents("test query")
        
        self.assertIn("KnowledgeBaseProcessor instance is required", str(context.exception))

    def test_query_documents_exception_handling(self):
        """Test that query exceptions are properly handled and re-raised."""
        # Setup mock to raise exception
        self.mock_kb_processor.search.side_effect = Exception("Search failed")
        
        with self.assertRaises(Exception) as context:
            self.processing_service.query_documents("test query")
        
        self.assertIn("Search failed", str(context.exception))

    @patch('knowledgebase_processor.processor.processor.Processor')
    @patch('knowledgebase_processor.extractor.markdown.MarkdownExtractor')
    @patch('knowledgebase_processor.extractor.frontmatter.FrontmatterExtractor')
    @patch('knowledgebase_processor.extractor.heading_section.HeadingSectionExtractor')
    @patch('knowledgebase_processor.extractor.link_reference.LinkReferenceExtractor')
    @patch('knowledgebase_processor.extractor.code_quote.CodeQuoteExtractor')
    @patch('knowledgebase_processor.extractor.todo_item.TodoItemExtractor')
    @patch('knowledgebase_processor.extractor.tags.TagExtractor')
    @patch('knowledgebase_processor.extractor.list_table.ListTableExtractor')
    @patch('knowledgebase_processor.extractor.wikilink_extractor.WikiLinkExtractor')
    @patch('knowledgebase_processor.analyzer.topics.TopicAnalyzer')
    @patch('knowledgebase_processor.enricher.relationships.RelationshipEnricher')
    def test_reinitialize_processor_with_config(self, mock_enricher, mock_analyzer, 
                                               mock_wikilink, mock_list_table, mock_tag,
                                               mock_todo, mock_code, mock_link, mock_heading,
                                               mock_frontmatter, mock_markdown, mock_processor_class):
        """Test processor reinitialization with updated config."""
        # Setup mocks
        mock_config = Mock()
        mock_new_processor = Mock()
        mock_processor_class.return_value = mock_new_processor
        
        # Create mock extractor instances
        mock_extractors = {
            'markdown': Mock(),
            'frontmatter': Mock(),
            'heading': Mock(),
            'link': Mock(),
            'code': Mock(),
            'todo': Mock(),
            'tag': Mock(),
            'list_table': Mock(),
            'wikilink': Mock()
        }
        
        mock_markdown.return_value = mock_extractors['markdown']
        mock_frontmatter.return_value = mock_extractors['frontmatter']
        mock_heading.return_value = mock_extractors['heading']
        mock_link.return_value = mock_extractors['link']
        mock_code.return_value = mock_extractors['code']
        mock_todo.return_value = mock_extractors['todo']
        mock_tag.return_value = mock_extractors['tag']
        mock_list_table.return_value = mock_extractors['list_table']
        mock_wikilink.return_value = mock_extractors['wikilink']
        
        mock_topic_analyzer = Mock()
        mock_analyzer.return_value = mock_topic_analyzer
        mock_relationship_enricher = Mock()
        mock_enricher.return_value = mock_relationship_enricher
        
        # Call the method
        self.processing_service._reinitialize_processor_with_config(mock_config)
        
        # Verify processor was created with config
        mock_processor_class.assert_called_once_with(config=mock_config)
        self.assertEqual(self.mock_kb_processor.processor, mock_new_processor)
        
        # Verify all extractors were registered
        for extractor in mock_extractors.values():
            mock_new_processor.register_extractor.assert_any_call(extractor)
        
        # Verify analyzer was registered
        mock_new_processor.register_analyzer.assert_called_with(mock_topic_analyzer)
        
        # Verify enricher was registered
        mock_new_processor.register_enricher.assert_called_with(mock_relationship_enricher)

    @patch('src.knowledgebase_processor.services.processing_service.get_logger')
    def test_logging_for_process_documents(self, mock_get_logger):
        """Test that processing documents generates appropriate log messages."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        # Setup full mock processor with all required attributes
        mock_kb_processor = Mock(spec=KnowledgeBaseProcessor)
        mock_processor = Mock()
        mock_reader = Mock()
        mock_metadata_store = Mock()
        
        mock_kb_processor.processor = mock_processor
        mock_kb_processor.reader = mock_reader
        mock_kb_processor.metadata_store = mock_metadata_store
        
        service = ProcessingService(mock_kb_processor)
        mock_processor.process_and_generate_rdf.return_value = 0
        
        pattern = "**/*.md"
        kb_path = Path("/tmp/kb")
        rdf_path = Path("/tmp/rdf")
        
        service.process_documents(pattern, kb_path, rdf_path)
        
        # Verify logging calls
        mock_logger.info.assert_any_call(f"Processing files matching pattern: {pattern} in knowledge base: {kb_path}")
        mock_logger.info.assert_any_call(f"RDF output directory specified: {str(rdf_path)}")

    @patch('src.knowledgebase_processor.services.processing_service.get_logger')
    def test_logging_for_entity_analysis_auto_enable(self, mock_get_logger):
        """Test logging when entity analysis is auto-enabled."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        # Setup full mock processor with all required attributes
        mock_kb_processor = Mock(spec=KnowledgeBaseProcessor)
        mock_processor = Mock()
        mock_reader = Mock()
        mock_metadata_store = Mock()
        
        mock_kb_processor.processor = mock_processor
        mock_kb_processor.reader = mock_reader
        mock_kb_processor.metadata_store = mock_metadata_store
        
        service = ProcessingService(mock_kb_processor)
        mock_processor.process_and_generate_rdf.return_value = 0
        
        mock_config = Mock()
        mock_config.analyze_entities = False
        
        with patch.object(service, '_reinitialize_processor_with_config'):
            service.process_documents("**/*.md", Path("/tmp/kb"), Path("/tmp/rdf"), mock_config)
        
        # Verify warning was logged
        mock_logger.warning.assert_called_once_with(
            "Entity analysis is disabled but RDF output was requested. "
            "Automatically enabling entity analysis for this run to generate meaningful RDF output."
        )

    @patch('src.knowledgebase_processor.services.processing_service.get_logger')
    def test_logging_for_single_document_processing(self, mock_get_logger):
        """Test logging for single document processing."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        service = ProcessingService(self.mock_kb_processor)
        self.mock_processor.process_file.return_value = Mock()
        
        file_path = Path("/tmp/test.md")
        service.process_single_document(file_path)
        
        # Verify logging
        mock_logger.info.assert_called_with(f"Processing single document: {file_path}")

    @patch('src.knowledgebase_processor.services.processing_service.get_logger')
    def test_logging_for_queries(self, mock_get_logger):
        """Test logging for document queries."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        service = ProcessingService(self.mock_kb_processor)
        self.mock_kb_processor.search.return_value = []
        self.mock_kb_processor.find_by_tag.return_value = []
        
        # Test text query logging
        service.query_documents("test", "text")
        mock_logger.info.assert_any_call("Querying with text query: test")
        
        # Test tag query logging
        service.query_documents("important", "tag")
        mock_logger.info.assert_any_call("Querying with tag query: important")
        
        # Test topic query warning
        service.query_documents("ml", "topic")
        mock_logger.warning.assert_called_with("Topic-based querying is not fully implemented yet.")

    @patch('src.knowledgebase_processor.services.processing_service.get_logger')
    def test_logging_for_query_exception(self, mock_get_logger):
        """Test logging when query execution fails."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        service = ProcessingService(self.mock_kb_processor)
        test_exception = Exception("Query failed")
        self.mock_kb_processor.search.side_effect = test_exception
        
        with self.assertRaises(Exception):
            service.query_documents("test")
        
        # Verify error was logged
        mock_logger.error.assert_called_once_with(
            "An error occurred during query execution: Query failed",
            exc_info=True
        )


if __name__ == '__main__':
    unittest.main()