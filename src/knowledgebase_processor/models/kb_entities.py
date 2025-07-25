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
            "rdf_types": [KB.Person, SCHEMA.Person], # Added SCHEMA.Person
            "rdfs_label_fallback_fields": ["full_name", "label"] # Added label
        }


class KbOrganization(KbBaseEntity):
    """
    Pydantic model for organization entities.
    """
    name: Optional[str] = Field(
        None,
        json_schema_extra={
            "rdf_property": SCHEMA.name,
            "rdf_datatype": XSD.string
        }
    )

    class Config:
        json_schema_extra = {
            "rdf_types": [KB.Organization, SCHEMA.Organization],
            "rdfs_label_fallback_fields": ["name", "label"]
        }


class KbLocation(KbBaseEntity):
    """
    Pydantic model for location entities.
    """
    name: Optional[str] = Field(
        None,
        json_schema_extra={
            "rdf_property": SCHEMA.name,
            "rdf_datatype": XSD.string
        }
    )
    address: Optional[str] = Field(
        None,
        json_schema_extra={
            "rdf_property": SCHEMA.address,
            "rdf_datatype": XSD.string
        }
    )

    class Config:
        json_schema_extra = {
            "rdf_types": [KB.Location, SCHEMA.Place],
            "rdfs_label_fallback_fields": ["name", "label"]
        }


class KbDateEntity(KbBaseEntity):
    """
    Pydantic model for date entities.
    """
    date_value: Optional[str] = Field( # Using str for flexibility with date formats from NER
        None,
        description="The string representation of the date.",
        json_schema_extra={
            "rdf_property": KB.dateValue, # Custom property for the date string
            "rdf_datatype": XSD.string
        }
    )
    # If a structured date is needed, consider adding a datetime field
    # structured_date: Optional[datetime] = Field(None, json_schema_extra={"rdf_property": SCHEMA.dateCreated, "rdf_datatype": XSD.date})

    class Config:
        json_schema_extra = {
            "rdf_types": [KB.DateEntity, SCHEMA.Date], # SCHEMA.Date might be too specific if date_value is just a string
            "rdfs_label_fallback_fields": ["date_value", "label"]
        }


class KbDocument(KbBaseEntity):
    """
    Pydantic model for document entities.
    """
    original_path: str = Field(
        ...,
        description="The original, unmodified file path of the document.",
        json_schema_extra={
            "rdf_property": KB.originalPath,
            "rdf_datatype": XSD.string,
        },
    )
    path_without_extension: str = Field(
        ...,
        description="The file path without its extension, used for linking.",
        json_schema_extra={
            "rdf_property": KB.pathWithoutExtension,
            "rdf_datatype": XSD.string,
        },
    )

    class Config:
        json_schema_extra = {
            "rdf_types": [KB.Document, SCHEMA.CreativeWork],
            "rdfs_label_fallback_fields": ["label", "original_path"],
        }


class KbWikiLink(KbBaseEntity):
    """
    Pydantic model for representing preserved WikiLinks.
    """
    original_text: str = Field(
        ...,
        description="The original, unmodified text of the wikilink (e.g., '[[Link Text|Alias]]').",
        json_schema_extra={
            "rdf_property": KB.originalText,
            "rdf_datatype": XSD.string,
        },
    )
    target_path: str = Field(
        ...,
        description="The target path extracted from the wikilink.",
        json_schema_extra={
            "rdf_property": KB.targetPath,
            "rdf_datatype": XSD.string,
        },
    )
    alias: Optional[str] = Field(
        None,
        description="The alias text from the wikilink, if present.",
        json_schema_extra={
            "rdf_property": KB.alias,
            "rdf_datatype": XSD.string,
        },
    )
    resolved_document_uri: Optional[str] = Field(
        None,
        description="The URI of the resolved KbDocument entity.",
        json_schema_extra={
            "rdf_property": KB.resolvedDocument,
            "is_object_property": True,
            "rdf_datatype": XSD.anyURI,
        },
    )

    class Config:
        json_schema_extra = {
            "rdf_types": [KB.WikiLink],
            "rdfs_label_fallback_fields": ["alias", "target_path"],
        }