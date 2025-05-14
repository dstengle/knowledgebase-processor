"""Data models for the Knowledge Base Processor."""

# Import order matters to avoid circular imports
from .common import *
from .preservation import *  # Import preservation before content
from .elements import *      # Import elements before content and markdown
from .entities import *
from .markdown import *      # Depends on elements
from .links import *         # Depends on markdown, entities
from .metadata import *      # Depends on links, entities, common
from .content import *       # Depends on metadata, elements, preservation

# Resolve forward references
Document.model_rebuild()
DocumentMetadata.model_rebuild()
# Potentially add for Link, WikiLink if they also use forward refs and cause issues
# Link.model_rebuild()
# WikiLink.model_rebuild()