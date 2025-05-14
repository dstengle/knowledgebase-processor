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