"""Entity related data models for the Knowledge Base Processor."""

from pydantic import BaseModel, Field

class ExtractedEntity(BaseModel):
    """Represents an entity extracted from text, with character offsets."""
    text: str = Field(..., description="The actual text of the entity")
    label: str = Field(..., description="The type or label of the entity (e.g., PERSON, ORG)")
    start_char: int = Field(..., description="The starting character offset of the entity in the source text")
    end_char: int = Field(..., description="The ending character offset of the entity in the source text")