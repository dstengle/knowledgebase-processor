"""Main integration module for the Knowledge Base Processor.

This module provides a simple interface for using the knowledge base processor
by integrating all the components together.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator

from .reader.reader import Reader
from .processor.processor import Processor
from .extractor.markdown import MarkdownExtractor
from .extractor.frontmatter import FrontmatterExtractor
from .extractor.heading_section import HeadingSectionExtractor
from .extractor.link_reference import LinkReferenceExtractor
from .extractor.code_quote import CodeQuoteExtractor
from .extractor.todo_item import TodoItemExtractor
from .extractor.tags import TagExtractor
from .extractor.list_table import ListTableExtractor
from .extractor.wikilink_extractor import WikiLinkExtractor
from .analyzer.topics import TopicAnalyzer
from .analyzer.entity_recognizer import EntityRecognizer
from .enricher.relationships import RelationshipEnricher
from .metadata_store.factory import get_metadata_store
from .query_interface.query import QueryInterface
from .models.content import Document
from .models.metadata import DocumentMetadata
from .utils.document_registry import DocumentRegistry
from .utils.id_generator import EntityIdGenerator
from .services.processing_service import ProcessingService


class KnowledgeBaseProcessor:
    """Main class for the Knowledge Base Processor."""

    def __init__(
        self,
        knowledge_base_dir: str,
        metadata_store_path: str,
        metadata_store_backend: str = "sqlite",
        config=None,
    ):
        """Initialize the Knowledge Base Processor."""
        self.base_path = Path(knowledge_base_dir)
        self.config = config

        # Initialize components
        self.reader = Reader(knowledge_base_dir)
        self.document_registry = DocumentRegistry()
        self.id_generator = EntityIdGenerator(base_url="http://example.org/kb/")
        self.processor = Processor(
            document_registry=self.document_registry,
            id_generator=self.id_generator,
            config=config,
        )
        self.metadata_store = get_metadata_store(
            backend=metadata_store_backend, db_path=metadata_store_path
        )
        self.query_interface = QueryInterface(self.metadata_store)
        self.processing_service = ProcessingService(
            processor=self.processor,
            reader=self.reader,
            metadata_store=self.metadata_store,
            config=config,
        )

        # Register extractors
        self.processor.register_extractor(MarkdownExtractor())
        self.processor.register_extractor(FrontmatterExtractor())
        self.processor.register_extractor(HeadingSectionExtractor())
        self.processor.register_extractor(LinkReferenceExtractor())
        self.processor.register_extractor(CodeQuoteExtractor())
        self.processor.register_extractor(TodoItemExtractor())
        self.processor.register_extractor(TagExtractor())
        self.processor.register_extractor(ListTableExtractor())
        # WikiLinkExtractor is now initialized within the Processor

        # Register analyzers
        self.processor.register_analyzer(TopicAnalyzer())

        # Register enrichers
        self.processor.register_enricher(RelationshipEnricher())

    def process_all(self, pattern: str = "**/*.md", rdf_output_dir: Optional[str] = None) -> int:
        """Process all files matching the pattern."""
        return self.processing_service.process_documents(
            pattern=pattern,
            knowledge_base_path=self.base_path,
            rdf_output_dir=Path(rdf_output_dir) if rdf_output_dir else None,
        )

    def get_metadata(self, document_id: str) -> Optional[DocumentMetadata]:
        """Get metadata for a document."""
        return self.metadata_store.get(document_id)

    def search(self, query: str) -> List[str]:
        """Search for documents matching a text query."""
        return self.query_interface.search(query)

    def find_by_tag(self, tag: str) -> List[str]:
        """Find documents with a specific tag."""
        return self.query_interface.find_by_tag(tag)

    def find_by_topic(self, topic: str) -> List[str]:
        """Find documents related to a specific topic."""
        return self.query_interface.find_by_topic(topic)

    def find_related(self, document_id: str) -> List[Dict[str, Any]]:
        """Find documents related to a specific document."""
        return self.query_interface.find_related(document_id)