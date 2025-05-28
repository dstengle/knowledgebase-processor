from datetime import datetime, timezone
from typing import Optional, Tuple, List

from pydantic import BaseModel, Field
from rdflib.namespace import SDO as SCHEMA, RDFS, XSD, Namespace # Changed SCHEMA to SDO as SCHEMA
from rdflib import URIRef

# Define custom namespace
KB = Namespace("http://example.org/kb/")


class KbBaseEntity(BaseModel):
    """
    Base model for all Knowledge Base entities.
    """
    kb_id: str = Field(
        ...,
        description="Unique identifier within the knowledge base, potentially a URI.",
        json_schema_extra={
            "rdf_property": RDFS.seeAlso,  # Example, might need a more specific KB property
            "is_object_property": True, # Assuming kb_id is a URI linking to the entity itself
            "rdf_datatype": XSD.anyURI
        }
    )
    label: Optional[str] = Field(
        None,
        description="A human-readable label for the entity.",
        json_schema_extra={
            "rdf_property": RDFS.label,
            "rdf_datatype": XSD.string
        }
    )
    source_document_uri: Optional[str] = Field(
        None,
        description="URI of the source document.",
        json_schema_extra={
            "rdf_property": KB.sourceDocument,
            "is_object_property": True,
            "rdf_datatype": XSD.anyURI
        }
    )
    extracted_from_text_span: Optional[Tuple[int, int]] = Field(
        None,
        description="Character offsets in the source document."
        # Not directly mapped to RDF, but could be part of a PROV-O annotation
    )
    creation_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        json_schema_extra={
            "rdf_property": SCHEMA.dateCreated,
            "rdf_datatype": XSD.dateTime
        }
    )
    last_modified_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        json_schema_extra={
            "rdf_property": SCHEMA.dateModified,
            "rdf_datatype": XSD.dateTime
        }
    )

    class Config:
        json_schema_extra = {
            "rdf_types": [KB.Entity]  # Generic base entity type
        }


class KbTodoItem(KbBaseEntity):
    """
    Pydantic model for to-do items.
    """
    description: str = Field(
        ...,
        json_schema_extra={
            "rdf_property": SCHEMA.description,
            "rdf_datatype": XSD.string,
        }
    )
    is_completed: bool = Field(
        False,
        json_schema_extra={
            "rdf_property": KB.isCompleted, # Using custom KB namespace
            "rdf_datatype": XSD.boolean
        }
    )
    due_date: Optional[datetime] = Field(
        None,
        json_schema_extra={
            "rdf_property": KB.dueDate,
            "rdf_datatype": XSD.dateTime
        }
    )
    priority: Optional[str] = Field(
        None,
        description="e.g., 'high', 'medium', 'low'",
        json_schema_extra={
            "rdf_property": KB.priority,
            "rdf_datatype": XSD.string
        }
    )
    context: Optional[str] = Field(
        None,
        description="Brief context or link to context.",
        json_schema_extra={
            "rdf_property": KB.context,
            "rdf_datatype": XSD.string # Could also be XSD.anyURI if it's a link
        }
    )
    assigned_to_uris: Optional[List[str]] = Field(
        None,
        description="List of URIs to KbPerson.",
        json_schema_extra={
            "rdf_property": KB.assignee,
            "is_object_property": True,
            "rdf_datatype": XSD.anyURI # Each item in the list is a URI
        }
    )
    related_project_uri: Optional[str] = Field(
        None,
        description="URI to a KbProject entity.",
        json_schema_extra={
            "rdf_property": KB.relatedProject,
            "is_object_property": True,
            "rdf_datatype": XSD.anyURI
        }
    )

    class Config:
        json_schema_extra = {
            "rdf_types": [KB.TodoItem, SCHEMA.Action],
            "rdfs_label_fallback_fields": ["description"]
        }


class KbPerson(KbBaseEntity):
    """
    Pydantic model for person entities.
    """
    full_name: Optional[str] = Field(
        None,
        json_schema_extra={
            "rdf_property": KB.fullName,
            "rdf_datatype": XSD.string,
            "rdfs_label_fallback": True
        }
    )
    given_name: Optional[str] = Field(
        None,
        json_schema_extra={
            "rdf_property": SCHEMA.givenName,
            "rdf_datatype": XSD.string
        }
    )
    family_name: Optional[str] = Field(
        None,
        json_schema_extra={
            "rdf_property": SCHEMA.familyName,
            "rdf_datatype": XSD.string
        }
    )
    aliases: Optional[List[str]] = Field(
        None,
        json_schema_extra={
            "rdf_property": SCHEMA.alternateName, # Or a custom KB.alias
            "rdf_datatype": XSD.string # Each alias is a string
        }
    )
    email: Optional[str] = Field(
        None,
        json_schema_extra={
            "rdf_property": SCHEMA.email,
            "rdf_datatype": XSD.string # Technically, could be XSD.anyURI if mailto:
        }
    )
    roles: Optional[List[str]] = Field(
        None,
        description="e.g., 'Developer', 'Manager'",
        json_schema_extra={
            "rdf_property": SCHEMA.roleName, # Or KB.role
            "rdf_datatype": XSD.string # Each role is a string
        }
    )

    class Config:
        json_schema_extra = {
            "rdf_types": [KB.Person],
            "rdfs_label_fallback_fields": ["full_name"]
        }