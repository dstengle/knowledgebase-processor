"""Processing service for orchestrating document processing operations."""

from pathlib import Path
from typing import Any, List, Optional

from ..main import KnowledgeBaseProcessor
from ..utils.logging import get_logger


class ProcessingService:
    """Orchestrates document processing operations."""
    
    def __init__(self, kb_processor: Optional[KnowledgeBaseProcessor] = None):
        """Initialize the ProcessingService.
        
        Args:
            kb_processor: KnowledgeBaseProcessor instance (optional)
        """
        self.kb_processor = kb_processor
        self.logger = get_logger("knowledgebase_processor.services.processing")
    
    def process_documents(self, pattern: str, knowledge_base_path: Path,
                         rdf_output_dir: Optional[Path] = None,
                         config=None) -> int:
        """Process documents matching pattern with optional RDF generation.
        
        Args:
            pattern: File pattern to match (e.g., "**/*.md")
            knowledge_base_path: Path to the knowledge base directory
            rdf_output_dir: Optional directory to save RDF output files
            config: Configuration object
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        if not self.kb_processor:
            raise ValueError("KnowledgeBaseProcessor instance is required for document processing.")
        
        rdf_output_dir_str = str(rdf_output_dir) if rdf_output_dir else None
        
        self.logger.info(f"Processing files matching pattern: {pattern} in knowledge base: {knowledge_base_path}")
        if rdf_output_dir_str:
            self.logger.info(f"RDF output directory specified: {rdf_output_dir_str}")
            
            # Auto-enable entity analysis when RDF output is requested but analysis is disabled
            if config and not config.analyze_entities:
                self.logger.warning(
                    "Entity analysis is disabled but RDF output was requested. "
                    "Automatically enabling entity analysis for this run to generate meaningful RDF output."
                )
                config.analyze_entities = True
                # Reinitialize the processor with updated config
                self._reinitialize_processor_with_config(config)

        # Call the processing method on the Processor instance within KnowledgeBaseProcessor
        return_code = self.kb_processor.processor.process_and_generate_rdf(
            reader=self.kb_processor.reader,
            metadata_store=self.kb_processor.metadata_store,
            pattern=pattern,
            knowledge_base_path=knowledge_base_path,
            rdf_output_dir_str=rdf_output_dir_str
        )
        return return_code
    
    def process_single_document(self, file_path: Path) -> Any:
        """Process a single document.
        
        Args:
            file_path: Path to the document to process
            
        Returns:
            Processed document result
        """
        if not self.kb_processor:
            raise ValueError("KnowledgeBaseProcessor instance is required for document processing.")
        
        # This is a placeholder for single document processing
        # The actual implementation would depend on the specific requirements
        self.logger.info(f"Processing single document: {file_path}")
        
        # For now, we'll use the existing processor methods
        # This could be expanded to handle single file processing more efficiently
        return self.kb_processor.processor.process_file(file_path)
    
    def query_documents(self, query_string: str, query_type: str = "text") -> List[Any]:
        """Query the processed documents.
        
        Args:
            query_string: The query string to search for
            query_type: Type of query ("text", "tag", "topic")
            
        Returns:
            List of matching results
        """
        if not self.kb_processor:
            raise ValueError("KnowledgeBaseProcessor instance is required for querying.")
        
        self.logger.info(f"Querying with {query_type} query: {query_string}")
        
        try:
            if query_type == "tag":
                results = self.kb_processor.find_by_tag(query_string)
            elif query_type == "topic":
                self.logger.warning("Topic-based querying is not fully implemented yet.")
                results = []
            else:  # text query
                results = self.kb_processor.search(query_string)
            
            return results
        except Exception as e:
            self.logger.error(f"An error occurred during query execution: {e}", exc_info=True)
            raise
    
    def _reinitialize_processor_with_config(self, config):
        """Reinitialize the processor with updated configuration.
        
        Args:
            config: Updated configuration object
        """
        from knowledgebase_processor.processor.processor import Processor
        from knowledgebase_processor.extractor.markdown import MarkdownExtractor
        from knowledgebase_processor.extractor.frontmatter import FrontmatterExtractor
        from knowledgebase_processor.extractor.heading_section import HeadingSectionExtractor
        from knowledgebase_processor.extractor.link_reference import LinkReferenceExtractor
        from knowledgebase_processor.extractor.code_quote import CodeQuoteExtractor
        from knowledgebase_processor.extractor.todo_item import TodoItemExtractor
        from knowledgebase_processor.extractor.tags import TagExtractor
        from knowledgebase_processor.extractor.list_table import ListTableExtractor
        from knowledgebase_processor.extractor.wikilink_extractor import WikiLinkExtractor
        from knowledgebase_processor.analyzer.topics import TopicAnalyzer
        from knowledgebase_processor.enricher.relationships import RelationshipEnricher
        
        self.kb_processor.processor = Processor(config=config)
        
        # Re-register all extractors
        self.kb_processor.processor.register_extractor(MarkdownExtractor())
        self.kb_processor.processor.register_extractor(FrontmatterExtractor())
        self.kb_processor.processor.register_extractor(HeadingSectionExtractor())
        self.kb_processor.processor.register_extractor(LinkReferenceExtractor())
        self.kb_processor.processor.register_extractor(CodeQuoteExtractor())
        self.kb_processor.processor.register_extractor(TodoItemExtractor())
        self.kb_processor.processor.register_extractor(TagExtractor())
        self.kb_processor.processor.register_extractor(ListTableExtractor())
        self.kb_processor.processor.register_extractor(WikiLinkExtractor())
        
        # Re-register analyzers
        self.kb_processor.processor.register_analyzer(TopicAnalyzer())
        
        # Re-register enrichers
        self.kb_processor.processor.register_enricher(RelationshipEnricher())