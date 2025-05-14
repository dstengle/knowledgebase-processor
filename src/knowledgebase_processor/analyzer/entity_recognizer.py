import spacy
from typing import List

from knowledgebase_processor.analyzer.base import BaseAnalyzer
from knowledgebase_processor.models.metadata import DocumentMetadata, ExtractedEntity

class EntityRecognizer(BaseAnalyzer):
    def __init__(self):
        """
        Initializes the EntityRecognizer by loading the spaCy English model.
        """
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # This can happen if the model is not downloaded.
            # Instruct to download it.
            print(
                "spaCy English model 'en_core_web_sm' not found. "
                "Please run: python -m spacy download en_core_web_sm"
            )
            # Depending on strictness, you might raise an error or exit
            raise

    def analyze(self, content: str, metadata: DocumentMetadata) -> None:
        """
        Analyzes the content to extract named entities and adds them to the metadata.

        Args:
            content: The text content to analyze.
            metadata: The DocumentMetadata object to update with extracted entities.
        """
        if not content:
            return

        doc = self.nlp(content)
        
        extracted_entities: List[ExtractedEntity] = []
        for ent in doc.ents:
            entity = ExtractedEntity(
                text=ent.text,
                label=ent.label_,
                start_char=ent.start_char,
                end_char=ent.end_char,
            )
            extracted_entities.append(entity)
        
        metadata.entities.extend(extracted_entities)
    def analyze_text_for_entities(self, text_to_analyze: str) -> List[ExtractedEntity]:
        """
        Analyzes a specific text string to extract named entities.

        Args:
            text_to_analyze: The text string to analyze.

        Returns:
            A list of ExtractedEntity objects found in the text.
            Returns an empty list if no entities are found.
        """
        if not text_to_analyze:
            return []

        doc = self.nlp(text_to_analyze)
        
        extracted_entities: List[ExtractedEntity] = []
        for ent in doc.ents:
            entity = ExtractedEntity(
                text=ent.text,
                label=ent.label_,
                start_char=ent.start_char,
                end_char=ent.end_char,
            )
            extracted_entities.append(entity)
        
        return extracted_entities