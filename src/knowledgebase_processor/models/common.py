"""Common data models used across the Knowledge Base Processor."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class BaseKnowledgeModel(BaseModel):
    """Base model for all knowledge base models."""
    
    id: Optional[str] = Field(None, description="Unique identifier for the model instance")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")