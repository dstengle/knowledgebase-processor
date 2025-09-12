"""Specific entity type models for the Knowledge Base Processor.

This module provides consolidated entity models that replace both
ExtractedEntity and the various Kb*Entity models.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import Field
from rdflib.namespace import SDO as SCHEMA, XSD

# Import KB namespace from centralized configuration
from knowledgebase_processor.config.vocabulary import KB
from .base import ContentEntity


class PersonEntity(ContentEntity):
    """Represents a person entity.
    
    Consolidates KbPerson with ExtractedEntity capabilities.
    """
    
    entity_type: str = "person"
    
    # Person Attributes
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
    aliases: List[str] = Field(
        default_factory=list,
        json_schema_extra={
            "rdf_property": SCHEMA.alternateName,
            "rdf_datatype": XSD.string
        }
    )
    email: Optional[str] = Field(
        None,
        json_schema_extra={
            "rdf_property": SCHEMA.email,
            "rdf_datatype": XSD.string
        }
    )
    roles: List[str] = Field(
        default_factory=list,
        description="e.g., 'Developer', 'Manager'",
        json_schema_extra={
            "rdf_property": SCHEMA.roleName,
            "rdf_datatype": XSD.string
        }
    )
    
    class Config:
        json_schema_extra = {
            "rdf_types": [KB.Person, SCHEMA.Person],
            "rdfs_label_fallback_fields": ["full_name", "text", "label"]
        }


class OrganizationEntity(ContentEntity):
    """Represents an organization entity.
    
    Consolidates KbOrganization with ExtractedEntity capabilities.
    """
    
    entity_type: str = "organization"
    
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
            "rdfs_label_fallback_fields": ["name", "text", "label"]
        }


class LocationEntity(ContentEntity):
    """Represents a location entity.
    
    Consolidates KbLocation with ExtractedEntity capabilities.
    """
    
    entity_type: str = "location"
    
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
            "rdfs_label_fallback_fields": ["name", "text", "label"]
        }


class DateEntity(ContentEntity):
    """Represents a date entity.
    
    Consolidates KbDateEntity with ExtractedEntity capabilities.
    """
    
    entity_type: str = "date"
    
    date_value: Optional[str] = Field(
        None,
        description="String representation of the date",
        json_schema_extra={
            "rdf_property": KB.dateValue,
            "rdf_datatype": XSD.string
        }
    )
    structured_date: Optional[datetime] = Field(
        None,
        json_schema_extra={
            "rdf_property": SCHEMA.dateCreated,
            "rdf_datatype": XSD.dateTime
        }
    )
    
    class Config:
        json_schema_extra = {
            "rdf_types": [KB.DateEntity, SCHEMA.Date],
            "rdfs_label_fallback_fields": ["date_value", "text", "label"]
        }


# Factory function for creating appropriate entity types
def create_entity(text: str, label: str, start_char: int, end_char: int, **kwargs) -> ContentEntity:
    """Factory function to create appropriate entity type based on label.
    
    Maintains backward compatibility with ExtractedEntity creation pattern.
    
    Args:
        text: The entity text
        label: The entity label/type
        start_char: Starting character position
        end_char: Ending character position
        **kwargs: Additional entity-specific fields
        
    Returns:
        The appropriate entity instance
    """
    entity_map = {
        'PERSON': PersonEntity,
        'PER': PersonEntity,
        'ORG': OrganizationEntity,
        'ORGANIZATION': OrganizationEntity,
        'LOC': LocationEntity,
        'LOCATION': LocationEntity,
        'GPE': LocationEntity,  # Geo-political entity
        'DATE': DateEntity,
        'TIME': DateEntity,
    }
    
    entity_class = entity_map.get(label.upper(), ContentEntity)
    
    return entity_class(
        id=f"entity_{start_char}_{end_char}_{label.lower()}",
        text=text,
        entity_type=label.lower(),
        start_char=start_char,
        end_char=end_char,
        **kwargs
    )