"""Todo item models for the Knowledge Base Processor.

This module consolidates TodoItem from markdown.py and KbTodoItem 
from kb_entities.py into a single unified TodoEntity model.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import Field
from rdflib.namespace import SDO as SCHEMA, XSD

# Import KB namespace from centralized configuration
from knowledgebase_processor.config.vocabulary import KB
from .base import MarkdownEntity


class TodoEntity(MarkdownEntity):
    """Unified todo item model.
    
    Consolidates TodoItem from markdown.py and KbTodoItem from kb_entities.py.
    Supports both simple markdown todos and rich RDF-aware todos.
    """
    
    entity_type: str = "todo"
    element_type: str = "todo_item"  # For markdown compatibility
    
    # Core Todo Attributes
    description: str = Field(
        ...,
        description="Todo description/text",
        json_schema_extra={
            "rdf_property": SCHEMA.description,
            "rdf_datatype": XSD.string
        }
    )
    is_completed: bool = Field(
        False,
        description="Whether the todo is completed",
        json_schema_extra={
            "rdf_property": KB.isCompleted,
            "rdf_datatype": XSD.boolean
        }
    )
    
    # Extended Attributes (from KbTodoItem)
    due_date: Optional[datetime] = Field(
        None,
        json_schema_extra={
            "rdf_property": KB.dueDate,
            "rdf_datatype": XSD.dateTime
        }
    )
    priority: Optional[str] = Field(
        None,
        description="Priority level (high, medium, low)",
        json_schema_extra={
            "rdf_property": KB.priority,
            "rdf_datatype": XSD.string
        }
    )
    context: Optional[str] = Field(
        None,
        description="Brief context or link to context",
        json_schema_extra={
            "rdf_property": KB.context,
            "rdf_datatype": XSD.string
        }
    )
    
    # Assignments (RDF-aware)
    assigned_to_uris: List[str] = Field(
        default_factory=list,
        description="List of URIs to PersonEntity",
        json_schema_extra={
            "rdf_property": KB.assignee,
            "is_object_property": True,
            "rdf_datatype": XSD.anyURI
        }
    )
    related_project_uri: Optional[str] = Field(
        None,
        description="URI to a project entity",
        json_schema_extra={
            "rdf_property": KB.relatedProject,
            "is_object_property": True,
            "rdf_datatype": XSD.anyURI
        }
    )
    
    # Backward compatibility properties
    @property
    def text(self) -> str:
        """Backward compatibility for markdown TodoItem."""
        return self.description
    
    @text.setter
    def text(self, value: str):
        """Backward compatibility setter for text property."""
        self.description = value
    
    @property
    def is_checked(self) -> bool:
        """Backward compatibility for markdown TodoItem."""
        return self.is_completed
    
    @is_checked.setter
    def is_checked(self, value: bool):
        """Backward compatibility setter for is_checked property."""
        self.is_completed = value
    
    class Config:
        json_schema_extra = {
            "rdf_types": [KB.TodoItem, SCHEMA.Action],
            "rdfs_label_fallback_fields": ["description", "text"]
        }


# Backward compatibility alias
TodoItem = TodoEntity