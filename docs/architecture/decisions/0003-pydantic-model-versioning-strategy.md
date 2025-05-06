# ADR-0003: Pydantic Model Versioning Strategy

**Date:** 2025-05-05

**Status:** Proposed

## Context

The Knowledge Base Processor uses Pydantic for data modeling (as per [ADR-0002](0002-pydantic-for-data-models.md)). As the system evolves, the structure of these Pydantic models will change. We need a way to document and track these changes directly within the model definitions to understand the history of fields (e.g., when they were added or deprecated) and to identify the overall version of a given model schema. This ADR focuses on establishing the initial method for embedding this evolutionary metadata, identifying the model schema version, and providing a consistent way to access field metadata. Specific backward compatibility mechanisms for handling breaking changes like renamed fields or complex type transformations will be addressed in separate ADRs if they become necessary.

## Decision

1.  We will use **`typing.Annotated`** in conjunction with a custom metadata class (e.g., `FieldMeta`) attached to Pydantic model fields as the primary method for documenting *field-level* schema evolution. This allows embedding information like the version a field was added or deprecated directly into the field's definition.
2.  We will define a **custom base model** (e.g., `VersionedBaseModel`) inheriting from `pydantic.BaseModel`.
    * This base model will include helper methods, such as `get_field_meta`, to provide a standardized way to access the `FieldMeta` information attached to fields.
    * This base model will include a **`model_version` class variable**, typed using `typing.Literal`, intended to be **overridden by each inheriting model** to explicitly declare the version of that specific model schema.
3.  All versioned data models in the system will inherit from this custom base model (`VersionedBaseModel`).

This decision establishes the *documentation* strategy for schema changes (both field-level and model-level) and a *consistent access pattern* for field metadata. It does *not* initially mandate the use of more complex backward compatibility features from "Approach 3" (like `alias`, `default_factory`, or complex validators). Those techniques remain options but will be considered and documented in separate ADRs if specific compatibility problems arise.

## Rationale

1.  **Explicit Field Metadata**: Using `Annotated` provides a clear, explicit way to document the history and status of each field directly within the model code.
2.  **Explicit Model Version**: Including `model_version` on the base model mandates that each concrete model definition declares its schema version explicitly, aiding in tracking and potentially informing future migration or compatibility logic.
3.  **Consistent Metadata Access**: The custom base model (`VersionedBaseModel`) encapsulates the logic for retrieving `FieldMeta`, ensuring a uniform and convenient way to access this information across all models.
4.  **Simplicity (Initial)**: This approach is simple to implement for the base case of tracking and accessing field metadata and declaring the model version. It avoids the upfront complexity of implementing potentially unnecessary backward compatibility logic.
5.  **Foundation for Compatibility**: The embedded metadata (`FieldMeta` and `model_version`) provides valuable context that can inform future decisions and implementations of backward compatibility logic if needed.
6.  **Pydantic V2 Alignment**: Leverages Pydantic V2's first-class support for `Annotated` metadata and standard inheritance patterns.

## Alternatives Considered

### No Explicit Model Version Field
- **Description**: Only use `Annotated` `FieldMeta` without a dedicated `model_version` on the base class. Model version would be implicit or tracked externally.
- **Reason Not Chosen**: Less explicit tracking of the overall schema version. Adding `model_version` provides a clear, mandatory declaration on each model definition.

### No Custom Base Model
- **Description**: Use `Annotated` and `FieldMeta` but require each model or utility function to implement its own logic for accessing the metadata.
- **Reason Not Chosen**: Leads to code duplication and potential inconsistencies in how metadata is accessed.

### Full Approach 3 (Metadata + Compatibility Fields) Initially
- **Description**: Immediately adopt all techniques from Approach 3, including `alias`, `default_factory`, and validators for backward compatibility alongside metadata.
- **Reason Not Chosen**: Introduces potentially unnecessary complexity upfront.

### Approach 1: Separate Model Classes Per Version
- **Description**: Define distinct `BaseModel` subclasses for each schema version.
- **Reason Not Chosen**: High code duplication and maintenance overhead.

### Approach 2: Versioning with Discriminated Unions
- **Description**: Use `Union` with a `discriminator` field.
- **Reason Not Chosen**: Requires an explicit discriminator field *in the data*, often impractical for existing content. The `model_version` here identifies the *schema definition version*, not necessarily a field within the data instance itself.

## Consequences

### Positive
- Provides clear, self-documenting history for model fields.
- Provides explicit declaration of the schema definition version for each model.
- Standardizes access to field evolution metadata via the base model.
- Simple initial implementation focused on metadata tracking and access.
- Defers complexity of advanced backward compatibility until needed.
- Establishes a pattern for future schema evolution documentation and model definition.

### Negative
- Introduces a custom base model dependency for all versioned models.
- Requires developers to correctly set the `model_version` literal in each inheriting model.
- Does *not* automatically provide backward compatibility for breaking changes (these require future ADRs).
- Requires discipline in maintaining the metadata within `Annotated`.
- May lead to future work defining ADRs for specific compatibility mechanisms.

## Implementation Approach

We will define a `FieldMeta` dataclass, a `VersionedBaseModel` inheriting from `pydantic.BaseModel` containing the access methods and the `model_version` class variable, and ensure relevant models inherit from `VersionedBaseModel` and set their `model_version`.

```python
from typing import Annotated, Optional, Type, List, Any, Literal, ClassVar, Dict
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo
from dataclasses import dataclass
import datetime

@dataclass
class FieldMeta:
    """Metadata for tracking field evolution."""
    version_added: str # Using string for SemVer-like versions
    description: str
    deprecated_in: Optional[str] = None # Version when field was deprecated

class VersionedBaseModel(BaseModel):
    """
    Custom base model providing access to FieldMeta and requiring
    a model version declaration.
    """
    # Class variable to be overridden by subclasses with a Literal
    # Defining it here ensures type checkers know about it,
    # but the actual value must be set in the child class.
    # We use a placeholder Literal; actual usage requires specific Literals in children.
    model_version: ClassVar[Literal['Unset']] = 'Unset'

    @classmethod
    def get_field_meta(cls, field_name: str) -> list[FieldMeta]:
        """Retrieves FieldMeta instances attached to a specific field."""
        if field_info := cls.model_fields.get(field_name):
            # Ensure metadata is treated as a tuple/list even if single Annotated arg
            metadata_tuple = field_info.metadata if isinstance(field_info.metadata, (list, tuple)) else (field_info.metadata,)
            return [m for m in metadata_tuple if isinstance(m, FieldMeta)]
        return []

    @classmethod
    def get_all_field_meta(cls) -> Dict[str, list[FieldMeta]]:
        """Retrieves FieldMeta for all fields in the model."""
        all_meta = {}
        for name, field_info in cls.model_fields.items():
            metadata_tuple = field_info.metadata if isinstance(field_info.metadata, (list, tuple)) else (field_info.metadata,)
            field_meta_list = [m for m in metadata_tuple if isinstance(m, FieldMeta)]
            if field_meta_list:
                all_meta[name] = field_meta_list
        return all_meta

    # Ensure subclasses override model_version
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Optional runtime check to remind developers to set the version
        if cls.model_version == 'Unset' and cls.__name__ != 'VersionedBaseModel':
             # In a real implementation, might raise an error or warning
             print(f"Warning: Model '{cls.__name__}' inheriting from VersionedBaseModel should override 'model_version'.")


# Example Usage in a Model inheriting from the custom base
class DocumentMetadata(VersionedBaseModel):
    # Override the class variable with the specific version Literal
    model_version: ClassVar[Literal['2.1']] = '2.1'

    title: Annotated[str, FieldMeta(version_added="1.0", description="Primary title of the document")]
    author: Annotated[Optional[str], FieldMeta(version_added="1.0", deprecated_in="2.0", description="Original author field")] = None
    # Added later
    contributors: Annotated[list[str], FieldMeta(version_added="2.0", description="List of contributors")] = Field(default_factory=list)
    # Added even later
    last_accessed: Annotated[Optional[datetime.datetime], FieldMeta(version_added="2.1", description="Timestamp of last access")] = None

# Example: Accessing metadata and model version
print(f"DocumentMetadata schema version: {DocumentMetadata.model_version}")
# Output: DocumentMetadata schema version: 2.1

meta_list = DocumentMetadata.get_field_meta('contributors')
if meta_list:
   print(f"Contributors added in version: {meta_list[0].version_added}")
   # Output: Contributors added in version: 2.0

all_meta = DocumentMetadata.get_all_field_meta()
# print(all_meta)
# Output: {'title': [FieldMeta(...)], 'author': [FieldMeta(...)], 'contributors': [FieldMeta(...)], 'last_accessed': [FieldMeta(...)]}

```

Specific backward compatibility techniques (using `validation_alias`, `default_factory` for complex defaults, validators for type changes or complex transformations) will be introduced via separate ADRs if and when required by schema evolution.

## Related Decisions

- Builds upon [ADR-0002: Pydantic for Data Models](0002-pydantic-for-data-models.md).
- Influences how developers document changes to Pydantic models and how they define new models.
- Sets the stage for potential future ADRs regarding specific backward compatibility techniques.

## Notes

- All Pydantic models intended to use this versioning metadata system *must* inherit from `VersionedBaseModel` and **override `model_version`** with a `typing.Literal` specific to their version.
- Consistent use of the `FieldMeta` structure is key.
- The versioning scheme used in `model_version`, `version_added`, and `deprecated_in` (e.g., SemVer string) should be consistent.
