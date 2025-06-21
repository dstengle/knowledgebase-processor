# import spacy  # Commented out - spacy disabled
from typing import List

from knowledgebase_processor.analyzer.base import BaseAnalyzer
from knowledgebase_processor.models.metadata import DocumentMetadata, ExtractedEntity

class EntityRecognizer(BaseAnalyzer):
    def __init__(self, enabled: bool = False):
        """
        Initializes the EntityRecognizer. 
        
        Args:
            enabled: Whether spacy entity recognition is enabled. Default is False (disabled).
        """
        self.enabled = enabled
        if self.enabled:
            try:
                import spacy
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
            except ImportError:
                print("spaCy not installed. Entity recognition will be disabled.")
                self.enabled = False
        else:
            self.nlp = None

    def analyze(self, content: str, metadata: DocumentMetadata) -> None:
        """
        Analyzes the content to extract named entities and adds them to the metadata.

        Args:
            content: The text content to analyze.
            metadata: The DocumentMetadata object to update with extracted entities.
        """
        if not self.enabled or not content:
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
            Returns an empty list if no entities are found or if entity recognition is disabled.
        """
        if not self.enabled or not text_to_analyze:
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