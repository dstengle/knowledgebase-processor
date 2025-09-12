"""Data models for the Knowledge Base Processor.

This package provides both the new unified model architecture and
backward compatibility with the legacy model structure.
"""

# New unified model imports (recommended for new code)
from .base import KnowledgeBaseEntity, ContentEntity, MarkdownEntity, DocumentEntity
from .entity_types import PersonEntity, OrganizationEntity, LocationEntity, DateEntity, create_entity
from .todo import TodoEntity
from .link import LinkEntity, Reference, Citation
from .document import UnifiedDocument, UnifiedDocumentMetadata, PlaceholderDocument

# Direct backward compatibility aliases (simpler approach)
ExtractedEntity = ContentEntity  # Direct alias for existing imports
BaseKnowledgeModel = KnowledgeBaseEntity  # Alias for old base class  
KbBaseEntity = KnowledgeBaseEntity  # Alias for RDF base class

# Entity type aliases
KbPerson = PersonEntity
KbOrganization = OrganizationEntity  
KbLocation = LocationEntity
KbDateEntity = DateEntity
KbTodoItem = TodoEntity
KbWikiLink = LinkEntity
KbDocument = UnifiedDocument
KbPlaceholderDocument = PlaceholderDocument

# Unified model aliases (for easy migration)
Document = UnifiedDocument
DocumentMetadata = UnifiedDocumentMetadata
TodoItem = TodoEntity
WikiLink = LinkEntity
Link = LinkEntity

# Legacy imports (for backward compatibility during migration)
from .common import *
from .preservation import *
from .elements import *      
from .entities import *
from .markdown import *      
from .links import *         
from .metadata import *      
from .content import *       

# Resolve forward references for both legacy and unified models
try:
    # Legacy model references
    if 'Document' in globals() and hasattr(globals()['Document'], 'model_rebuild'):
        globals()['Document'].model_rebuild()
    if 'DocumentMetadata' in globals() and hasattr(globals()['DocumentMetadata'], 'model_rebuild'):  
        globals()['DocumentMetadata'].model_rebuild()
        
    # Unified model references
    UnifiedDocument.model_rebuild()
    UnifiedDocumentMetadata.model_rebuild()
except Exception:
    # Ignore rebuild errors during import
    pass

# Export the primary unified models for new code
__all__ = [
    # Primary unified models
    'KnowledgeBaseEntity',
    'ContentEntity', 
    'UnifiedDocument',
    'UnifiedDocumentMetadata',
    'PersonEntity',
    'OrganizationEntity',
    'LocationEntity', 
    'DateEntity',
    'TodoEntity',
    'LinkEntity',
    'PlaceholderDocument',
    
    # Convenience aliases
    'Document',
    'DocumentMetadata', 
    'TodoItem',
    'WikiLink',
    'Link',
    
    # Factory functions
    'create_entity',
    
    # Backward compatibility
    'ExtractedEntity',
    'BaseKnowledgeModel',
    'KbBaseEntity',
]

