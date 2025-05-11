import spacy
from typing import List, Optional
from knowledgebase_processor.models.metadata import Entity

class EntityRecognizer:
    def __init__(self, model_name: str = "en_core_web_sm"):
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            print(f"Spacy model '{model_name}' not found. Please download it: python -m spacy download {model_name}")
            self.nlp = None

    def extract_entities(self, text: str) -> Optional[List[Entity]]:
        if not self.nlp or not text:
            return None
        doc = self.nlp(text)
        extracted_entities = []
        for ent in doc.ents:
            extracted_entities.append(
                Entity(
                    text=ent.text,
                    label=ent.label_,
                    start_char=ent.start_char,
                    end_char=ent.end_char
                )
            )
        return extracted_entities if extracted_entities else None

    def analyze(self, document):
        """
        Analyze the document and attach extracted entities to document.entities.
        """
        if hasattr(document, "content") and document.content:
            entities = self.extract_entities(document.content)
            setattr(document, "entities", entities)
        else:
            setattr(document, "entities", None)