"""Document processing module for handling document registration and basic operations."""

from pathlib import Path
from typing import List, Tuple, Optional
import os

from ..models.content import Document
from ..models.kb_entities import KbDocument
from ..utils.document_registry import DocumentRegistry
from ..utils.id_generator import EntityIdGenerator
from ..utils.logging import get_logger
from ..reader.reader import Reader


logger = get_logger("knowledgebase_processor.processor.document")


class DocumentProcessor:
    """Handles document reading, registration, and basic document operations."""
    
    def __init__(
        self,
        document_registry: DocumentRegistry,
        id_generator: EntityIdGenerator
    ):
        """Initialize DocumentProcessor with required dependencies."""
        self.document_registry = document_registry
        self.id_generator = id_generator
    
    def create_document_entity(
        self,
        doc_path: str,
        knowledge_base_path: Path,
        document: Optional[Document] = None
    ) -> Optional[KbDocument]:
        """Creates a KbDocument entity from a file path.
        
        Args:
            doc_path: Path to the document file
            knowledge_base_path: Base path of the knowledge base
            document: Optional Document object with metadata
            
        Returns:
            KbDocument entity or None if creation fails
        """
        try:
            original_path = os.path.relpath(doc_path, knowledge_base_path)
            normalized_path = original_path.replace("\\", "/")
            path_without_extension, _ = os.path.splitext(normalized_path)
            
            doc_id = self.id_generator.generate_document_id(normalized_path)
            
            # Use title from document metadata if available
            if document and document.title:
                label = document.title
            else:
                label = Path(original_path).stem.replace("_", " ").replace("-", " ")
            
            document_entity = KbDocument(
                kb_id=doc_id,
                label=label,
                original_path=original_path,
                path_without_extension=path_without_extension,
                source_document_uri=doc_id,
            )
            
            return document_entity
            
        except Exception as e:
            logger.error(f"Failed to create document entity for {doc_path}: {e}", exc_info=True)
            return None
    
    def register_document(self, document_entity: KbDocument) -> None:
        """Register a document entity in the registry."""
        self.document_registry.register_document(document_entity)
    
    def read_and_register_documents(
        self,
        reader: Reader,
        pattern: str,
        knowledge_base_path: Path
    ) -> List[Tuple[str, Document, KbDocument]]:
        """Read all documents matching pattern and register them.
        
        Args:
            reader: Reader instance for file reading
            pattern: File pattern to match
            knowledge_base_path: Base path of knowledge base
            
        Returns:
            List of tuples containing (file_path, document, kb_document)
        """
        documents = []
        
        for file_path in reader.read_all_paths(pattern):
            document = reader.read_file(file_path)
            
            # Create and register document entity
            kb_document = self.create_document_entity(
                str(file_path),
                knowledge_base_path,
                document
            )
            
            if kb_document:
                self.register_document(kb_document)
                documents.append((str(file_path), document, kb_document))
            else:
                logger.warning(f"Failed to create document entity for {file_path}")
        
        logger.info(f"Registered {len(documents)} documents.")
        return documents
    
    def find_document_by_path(self, relative_path: str) -> Optional[KbDocument]:
        """Find a registered document by its relative path.
        
        Args:
            relative_path: Relative path from knowledge base root
            
        Returns:
            KbDocument if found, None otherwise
        """
        return self.document_registry.find_document_by_path(relative_path)
    
    def get_all_documents(self) -> List[KbDocument]:
        """Get all registered documents.
        
        Returns:
            List of all registered KbDocument entities
        """
        return self.document_registry.get_all_documents()