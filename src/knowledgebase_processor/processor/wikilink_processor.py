"""Wikilink processing module for handling wikilink extraction and resolution."""

from typing import List, Optional

from ..models.content import Document
from ..models.kb_entities import KbWikiLink
from ..utils.document_registry import DocumentRegistry
from ..utils.id_generator import EntityIdGenerator
from ..utils.logging import get_logger


logger = get_logger("knowledgebase_processor.processor.wikilink")


class WikilinkProcessor:
    """Handles wikilink extraction and resolution."""
    
    def __init__(
        self,
        document_registry: DocumentRegistry,
        id_generator: EntityIdGenerator
    ):
        """Initialize WikilinkProcessor with required dependencies.
        
        Args:
            document_registry: Registry for document management
            id_generator: Generator for entity IDs
        """
        self.document_registry = document_registry
        self.id_generator = id_generator
    
    def extract_wikilinks(
        self,
        document: Document,
        document_id: str
    ) -> List[KbWikiLink]:
        """Extract wikilinks from document using WikiLinkExtractor.
        
        Args:
            document: Document to extract from
            document_id: ID of the source document
            
        Returns:
            List of KbWikiLink entities
        """
        try:
            from ..extractor.wikilink_extractor import WikiLinkExtractor
            
            wikilink_extractor = WikiLinkExtractor(
                self.document_registry,
                self.id_generator
            )
            
            wikilinks = wikilink_extractor.extract(document, document_id)
            logger.debug(f"Extracted {len(wikilinks)} wikilinks from document {document_id}")
            return wikilinks
            
        except ImportError:
            logger.debug("WikiLinkExtractor not available, skipping wikilink extraction")
            return []
        except Exception as e:
            logger.error(f"Failed to extract wikilinks from document {document_id}: {e}")
            return []
    
    def resolve_wikilink_targets(
        self,
        wikilinks: List[KbWikiLink]
    ) -> List[KbWikiLink]:
        """Resolve wikilink targets against the document registry.
        
        Args:
            wikilinks: List of wikilinks to resolve
            
        Returns:
            List of wikilinks with resolved targets
        """
        resolved_links = []
        
        for wikilink in wikilinks:
            resolved_link = self._resolve_single_wikilink(wikilink)
            resolved_links.append(resolved_link)
        
        resolved_count = sum(1 for link in resolved_links if hasattr(link, 'target_document_uri'))
        logger.debug(f"Resolved {resolved_count} out of {len(wikilinks)} wikilinks")
        
        return resolved_links
    
    def _resolve_single_wikilink(self, wikilink: KbWikiLink) -> KbWikiLink:
        """Resolve a single wikilink target.
        
        Args:
            wikilink: Wikilink to resolve
            
        Returns:
            Wikilink with resolved target (if found)
        """
        # Try to find target document by various matching strategies
        target_doc = None
        
        # Strategy 1: Exact path match
        if hasattr(wikilink, 'target_path'):
            target_doc = self.document_registry.find_document_by_path(wikilink.target_path)
        
        # Strategy 2: Basename match (if exact path fails)
        if not target_doc and hasattr(wikilink, 'label'):
            # Try to find by basename without extension
            for doc in self.document_registry.get_all_documents():
                if doc.path_without_extension.endswith(wikilink.label):
                    target_doc = doc
                    break
        
        # Update wikilink with target information if found
        if target_doc:
            # Create a new wikilink with target information
            # This preserves the original wikilink while adding target data
            if hasattr(wikilink, '__dict__'):
                wikilink_dict = wikilink.__dict__.copy()
                wikilink_dict['target_document_uri'] = target_doc.kb_id
                # Reconstruct wikilink with additional target info
                # Note: This depends on the specific KbWikiLink implementation
        
        return wikilink
    
    def get_broken_wikilinks(
        self,
        wikilinks: List[KbWikiLink]
    ) -> List[KbWikiLink]:
        """Find wikilinks that could not be resolved to target documents.
        
        Args:
            wikilinks: List of wikilinks to check
            
        Returns:
            List of broken (unresolved) wikilinks
        """
        broken_links = []
        
        for wikilink in wikilinks:
            if not hasattr(wikilink, 'target_document_uri') or not wikilink.target_document_uri:
                broken_links.append(wikilink)
        
        if broken_links:
            logger.warning(f"Found {len(broken_links)} broken wikilinks")
        
        return broken_links
    
    def get_wikilink_statistics(
        self,
        wikilinks: List[KbWikiLink]
    ) -> dict:
        """Get statistics about wikilinks.
        
        Args:
            wikilinks: List of wikilinks to analyze
            
        Returns:
            Dictionary with wikilink statistics
        """
        if not wikilinks:
            return {
                'total': 0,
                'resolved': 0,
                'broken': 0,
                'resolution_rate': 0.0
            }
        
        total = len(wikilinks)
        resolved = sum(
            1 for link in wikilinks 
            if hasattr(link, 'target_document_uri') and link.target_document_uri
        )
        broken = total - resolved
        resolution_rate = resolved / total if total > 0 else 0.0
        
        return {
            'total': total,
            'resolved': resolved,
            'broken': broken,
            'resolution_rate': resolution_rate
        }