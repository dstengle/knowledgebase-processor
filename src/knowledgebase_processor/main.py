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
from .analyzer.entities import EntityRecognizer
from .enricher.relationships import RelationshipEnricher
from .metadata_store.store import MetadataStore
from .query_interface.query import QueryInterface
from .models.content import Document
from .models.metadata import DocumentMetadata


class KnowledgeBaseProcessor:
    """Main class for the Knowledge Base Processor.
    
    This class integrates all the components of the knowledge base processor
    and provides a simple interface for using them.
    """
    
    def __init__(self, base_path: str, metadata_path: Optional[str] = None):
        """Initialize the Knowledge Base Processor.
        
        Args:
            base_path: Path to the knowledge base directory
            metadata_path: Path to the metadata store directory (default: {base_path}/.metadata)
        """
        self.base_path = Path(base_path)
        
        # Set up metadata path
        if metadata_path is None:
            metadata_path = os.path.join(base_path, ".metadata")
        
        # Initialize components
        self.reader = Reader(base_path)
        self.processor = Processor()
        self.metadata_store = MetadataStore(metadata_path)
        self.query_interface = QueryInterface(self.metadata_store)
        
        # Register extractors
        self.processor.register_extractor(MarkdownExtractor())
        self.processor.register_extractor(FrontmatterExtractor())
        self.processor.register_extractor(HeadingSectionExtractor())
        self.processor.register_extractor(LinkReferenceExtractor())
        self.processor.register_extractor(CodeQuoteExtractor())
        self.processor.register_extractor(TodoItemExtractor())
        self.processor.register_extractor(TagExtractor())
        self.processor.register_extractor(ListTableExtractor())
        self.processor.register_extractor(WikiLinkExtractor())
        
        # Register analyzers
        self.processor.register_analyzer(TopicAnalyzer())
        self.processor.register_analyzer(EntityRecognizer())
        
        # Register enrichers
        self.processor.register_enricher(RelationshipEnricher())
    
    def process_file(self, file_path: str) -> Document:
        """Process a single file.
        
        Args:
            file_path: Path to the file to process (relative to base_path)
            
        Returns:
            Processed document
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path
        
        document = self.reader.read_file(path)
        processed_document = self.processor.process_document(document)
        
        # Extract and store metadata
        metadata = self.processor.extract_metadata(processed_document)
        self.metadata_store.save(metadata)
        
        return processed_document
    
    def process_all(self, pattern: str = "**/*.md") -> List[Document]:
        """Process all files matching the pattern.
        
        Args:
            pattern: Glob pattern to match files (default: "**/*.md")
            
        Returns:
            List of processed documents
        """
        documents = []
        
        for document in self.reader.read_all(pattern):
            processed_document = self.processor.process_document(document)
            
            # Extract and store metadata
            metadata = self.processor.extract_metadata(processed_document)
            self.metadata_store.save(metadata)
            
            documents.append(processed_document)
        
        return documents
    
    def get_metadata(self, document_id: str) -> Optional[DocumentMetadata]:
        """Get metadata for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Metadata object if found, None otherwise
        """
        return self.metadata_store.get(document_id)
    
    def search(self, query: str) -> List[str]:
        """Search for documents matching a text query.
        
        Args:
            query: The search query
            
        Returns:
            List of matching document IDs
        """
        return self.query_interface.search(query)
    
    def find_by_tag(self, tag: str) -> List[str]:
        """Find documents with a specific tag.
        
        Args:
            tag: The tag to search for
            
        Returns:
            List of document IDs with the specified tag
        """
        return self.query_interface.find_by_tag(tag)
    
    def find_by_topic(self, topic: str) -> List[str]:
        """Find documents related to a specific topic.
        
        Args:
            topic: The topic to search for
            
        Returns:
            List of document IDs related to the specified topic
        """
        return self.query_interface.find_by_topic(topic)
    
    def find_related(self, document_id: str) -> List[Dict[str, Any]]:
        """Find documents related to a specific document.
        
        Args:
            document_id: ID of the document to find relations for
            
        Returns:
            List of dictionaries with related document information
        """
        return self.query_interface.find_related(document_id)