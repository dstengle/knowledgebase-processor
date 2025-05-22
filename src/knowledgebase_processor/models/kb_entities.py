from datetime import datetime, timezone
from typing import Optional, Tuple, List

from pydantic import BaseModel, Field


class KbBaseEntity(BaseModel):
    """
    Base model for all Knowledge Base entities.
    """
    kb_id: str  # Unique identifier within the knowledge base, potentially a URI
    label: Optional[str] = None  # A human-readable label for the entity
    source_document_uri: Optional[str] = None  # URI of the source document
    extracted_from_text_span: Optional[Tuple[int, int]] = None  # Character offsets
    creation_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_modified_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class KbTodoItem(KbBaseEntity):
    """
    Pydantic model for to-do items.
    """
    description: str
    is_completed: bool = False
    due_date: Optional[datetime] = None
    priority: Optional[str] = None  # e.g., "high", "medium", "low"
    context: Optional[str] = None  # Brief context or link to context
    assigned_to_uris: Optional[List[str]] = None  # List of URIs to KbPerson
    related_project_uri: Optional[str] = None  # URI to a KbProject entity


class KbPerson(KbBaseEntity):
    """
    Pydantic model for person entities.
    """
    full_name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    aliases: Optional[List[str]] = None
    email: Optional[str] = None
    roles: Optional[List[str]] = None  # e.g., "Developer", "Manager"