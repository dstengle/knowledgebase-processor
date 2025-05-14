import re
from typing import List
from knowledgebase_processor.models.links import WikiLink
from knowledgebase_processor.extractor.base import BaseExtractor # Revert to absolute import
from knowledgebase_processor.models.content import Document

class WikiLinkExtractor(BaseExtractor):
    """
    Extracts wikilinks ([[Page Name]] or [[Page Name|Display Text]]) from markdown text.
    """

    # Disallow nested [[ inside the link target
    WIKILINK_PATTERN = re.compile(
        r"\[\[([^\[\]\|\n]+?)(?:\|([^\[\]\n]+?))?\]\]"
    )

    def extract(self, document: Document) -> List[WikiLink]:
        wikilinks = []
        text = document.content
        for match in self.WIKILINK_PATTERN.finditer(text):
            target_page = match.group(1).strip()
            display_text = match.group(2).strip() if match.group(2) else target_page
            position = {
                "start_offset": match.start(),
                "end_offset": match.end(),
            }
            wikilinks.append(
                WikiLink(
                    element_type="wikilink",
                    target_page=target_page,
                    display_text=display_text,
                    content=match.group(0),
                    position=position,
                )
            )
        return wikilinks