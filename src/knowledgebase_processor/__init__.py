"""Knowledge Base Processor - A tool for extracting and analyzing knowledge base content."""

__version__ = "0.1.0"

# Import main components for easier access
from .main import KnowledgeBaseProcessor
from .models.content import Document
from .models.metadata import DocumentMetadata

__all__ = ["KnowledgeBaseProcessor", "Document", "DocumentMetadata"]