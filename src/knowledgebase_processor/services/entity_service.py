"""Entity service for handling entity transformation and KB ID generation."""

import uuid
from typing import Optional
from urllib.parse import quote

from ..models.entities import ExtractedEntity
from ..models.kb_entities import KbBaseEntity, KbPerson, KbOrganization, KbLocation, KbDateEntity, KB
from ..utils.logging import get_logger


class EntityService:
    """Handles entity transformation and KB ID generation."""
    
    def __init__(self):
        """Initialize the EntityService."""
        self.logger = get_logger("knowledgebase_processor.services.entity")
    
    def generate_kb_id(self, entity_type_str: str, text: str) -> str:
        """Generates a unique knowledge base ID (URI) for an entity.
        
        Args:
            entity_type_str: The type of entity (e.g., "Person", "Organization")
            text: The text content of the entity
            
        Returns:
            A unique URI for the entity
        """
        # Simple slugification: replace non-alphanumeric with underscore
        slug = "".join(c if c.isalnum() else "_" for c in text.lower())
        # Trim slug to avoid overly long URIs, e.g., first 50 chars
        slug = slug[:50].strip('_')
        return str(KB[f"{entity_type_str}/{slug}_{uuid.uuid4().hex[:8]}"])
    
    def transform_to_kb_entity(self, 
                             extracted_entity: ExtractedEntity,
                             source_doc_relative_path: str) -> Optional[KbBaseEntity]:
        """Transforms an ExtractedEntity to a corresponding KbBaseEntity subclass instance.
        
        Args:
            extracted_entity: The extracted entity to transform
            source_doc_relative_path: Relative path to the source document
            
        Returns:
            A KbBaseEntity instance or None if the entity type is not handled
        """
        kb_id_text = extracted_entity.text
        entity_label_upper = extracted_entity.label.upper()
        self.logger.info(f"Processing entity: {kb_id_text} of type {entity_label_upper}")

        # Create a full URI for the source document
        # Replace spaces with underscores and quote for URI safety.
        # Ensure consistent path separators (/) before quoting.
        normalized_path = source_doc_relative_path.replace("\\", "/")
        safe_path_segment = quote(normalized_path.replace(" ", "_"))
        full_document_uri = str(KB[f"Document/{safe_path_segment}"])

        common_args = {
            "label": extracted_entity.text,
            "source_document_uri": full_document_uri,  # Use the generated full URI
            "extracted_from_text_span": (extracted_entity.start_char, extracted_entity.end_char),
        }

        if entity_label_upper == "PERSON":
            kb_id = self.generate_kb_id("Person", kb_id_text)
            return KbPerson(kb_id=kb_id, full_name=extracted_entity.text, **common_args)
        elif entity_label_upper == "ORG":
            kb_id = self.generate_kb_id("Organization", kb_id_text)
            return KbOrganization(kb_id=kb_id, name=extracted_entity.text, **common_args)
        elif entity_label_upper in ["LOC", "GPE"]:  # GPE (Geopolitical Entity) often maps to Location
            kb_id = self.generate_kb_id("Location", kb_id_text)
            return KbLocation(kb_id=kb_id, name=extracted_entity.text, **common_args)
        elif entity_label_upper == "DATE":
            kb_id = self.generate_kb_id("DateEntity", kb_id_text)
            return KbDateEntity(kb_id=kb_id, date_value=extracted_entity.text, **common_args)
        else:
            self.logger.debug(f"Unhandled entity type: {extracted_entity.label} for text: '{extracted_entity.text}'")
            return None