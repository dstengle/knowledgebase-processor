import re
from typing import List

from knowledgebase_processor.extractor.base import BaseExtractor
from knowledgebase_processor.models.content import Document
from knowledgebase_processor.models.kb_entities import KbWikiLink
from knowledgebase_processor.utils.document_registry import DocumentRegistry
from knowledgebase_processor.utils.id_generator import EntityIdGenerator


class WikiLinkExtractor(BaseExtractor):
    """
    Extracts wikilinks, preserves their original text, and resolves them
    against a document registry.
    """

    WIKILINK_PATTERN = re.compile(r"\[\[([^\[\]\|\n]+?)(?:\|([^\[\]\n]+?))?\]\]")

    def __init__(
        self,
        document_registry: DocumentRegistry,
        id_generator: EntityIdGenerator,
    ):
        self.document_registry = document_registry
        self.id_generator = id_generator

    def extract(
        self, document: Document, source_document_id: str
    ) -> List[KbWikiLink]:
        """
        Extracts and resolves wikilinks from the document content.

        Args:
            document: The document to process.
            source_document_id: The unique ID of the source document.

        Returns:
            A list of KbWikiLink entities found in the document.
        """
        wikilinks = []
        text = document.content
        for match in self.WIKILINK_PATTERN.finditer(text):
            original_text = match.group(0)
            target_path = match.group(1).strip()
            alias = match.group(2).strip() if match.group(2) else None

            resolved_document = self.document_registry.find_document_by_path(
                target_path
            )
            resolved_uri = resolved_document.kb_id if resolved_document else None

            link_id = self.id_generator.generate_wikilink_id(
                source_document_id, original_text
            )

            wikilink = KbWikiLink(
                kb_id=link_id,
                label=alias or target_path,
                source_document_uri=source_document_id,
                original_text=original_text,
                target_path=target_path,
                alias=alias,
                resolved_document_uri=resolved_uri,
                extracted_from_text_span=(match.start(), match.end()),
            )
            wikilinks.append(wikilink)

        return wikilinks