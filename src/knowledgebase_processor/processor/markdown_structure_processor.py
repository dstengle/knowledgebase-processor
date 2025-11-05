"""Processor for converting markdown structure elements to KB entities."""

from typing import List, Optional, Dict

from ..models.content import Document
from ..models.markdown import (
    Heading, Section, MarkdownList, ListItem, TodoItem,
    Table, CodeBlock, Blockquote
)
from ..models.kb_entities import (
    KbBaseEntity, KbHeading, KbSection, KbList, KbListItem,
    KbTable, KbCodeBlock, KbBlockquote
)
from ..utils.id_generator import EntityIdGenerator
from ..utils.logging import get_logger


logger = get_logger("knowledgebase_processor.processor.markdown_structure")


class MarkdownStructureProcessor:
    """Processes markdown structure elements and converts them to KB entities."""

    def __init__(self, id_generator: EntityIdGenerator):
        """Initialize MarkdownStructureProcessor.

        Args:
            id_generator: Generator for entity IDs
        """
        self.id_generator = id_generator

    def extract_markdown_structure_entities(
        self,
        document: Document,
        document_id: str
    ) -> List[KbBaseEntity]:
        """Extract markdown structure entities from a document.

        Args:
            document: Document to process
            document_id: ID of the source document

        Returns:
            List of KB entities representing markdown structure
        """
        entities = []

        # Create a mapping of element IDs to KB entity URIs for relationships
        element_id_to_uri: Dict[str, str] = {}

        # First pass: Convert all elements to KB entities
        for element in document.elements:
            kb_entity = self._convert_element_to_kb_entity(
                element,
                document_id,
                element_id_to_uri
            )

            if kb_entity:
                entities.append(kb_entity)
                element_id_to_uri[element.id] = kb_entity.kb_id

        # Second pass: Update relationships using the URI mapping
        for entity in entities:
            self._update_entity_relationships(entity, element_id_to_uri)

        logger.info(f"Extracted {len(entities)} markdown structure entities from document")
        return entities

    def _convert_element_to_kb_entity(
        self,
        element,
        document_id: str,
        element_id_to_uri: Dict[str, str]
    ) -> Optional[KbBaseEntity]:
        """Convert a markdown element to a KB entity.

        Args:
            element: Markdown element to convert
            document_id: ID of the source document
            element_id_to_uri: Mapping of element IDs to KB URIs

        Returns:
            KB entity or None if conversion not supported
        """
        # Skip TodoItem elements as they're handled by TodoProcessor
        if isinstance(element, TodoItem):
            return None

        # Convert based on element type
        if isinstance(element, Heading):
            return self._heading_to_kb_entity(element, document_id)
        elif isinstance(element, Section):
            return self._section_to_kb_entity(element, document_id, element_id_to_uri)
        elif isinstance(element, MarkdownList):
            return self._list_to_kb_entity(element, document_id, element_id_to_uri)
        elif isinstance(element, ListItem):
            return self._list_item_to_kb_entity(element, document_id, element_id_to_uri)
        elif isinstance(element, Table):
            return self._table_to_kb_entity(element, document_id)
        elif isinstance(element, CodeBlock):
            return self._code_block_to_kb_entity(element, document_id)
        elif isinstance(element, Blockquote):
            return self._blockquote_to_kb_entity(element, document_id)

        return None

    def _heading_to_kb_entity(
        self,
        heading: Heading,
        document_id: str
    ) -> KbHeading:
        """Convert a Heading element to KbHeading entity.

        Args:
            heading: Heading element
            document_id: Source document ID

        Returns:
            KbHeading entity
        """
        entity_id = self.id_generator.generate_markdown_element_id(
            "heading",
            f"h{heading.level}-{heading.text[:50]}",
            document_id
        )

        position_start = heading.position.get('start') if heading.position else None
        position_end = heading.position.get('end') if heading.position else None

        return KbHeading(
            kb_id=entity_id,
            label=heading.text,
            source_document_uri=document_id,
            level=heading.level,
            text=heading.text,
            position_start=position_start,
            position_end=position_end,
            parent_heading_uri=None  # Will be updated in second pass if needed
        )

    def _section_to_kb_entity(
        self,
        section: Section,
        document_id: str,
        element_id_to_uri: Dict[str, str]
    ) -> KbSection:
        """Convert a Section element to KbSection entity.

        Args:
            section: Section element
            document_id: Source document ID
            element_id_to_uri: Mapping for relationship resolution

        Returns:
            KbSection entity
        """
        position_start = section.position.get('start') if section.position else 0
        position_end = section.position.get('end') if section.position else 0

        # Use position for deterministic ID generation
        entity_id = self.id_generator.generate_markdown_element_id(
            "section",
            f"pos-{position_start}-{position_end}",
            document_id
        )

        # Resolve heading URI if heading_id is present
        heading_uri = None
        if section.heading_id and section.heading_id in element_id_to_uri:
            heading_uri = element_id_to_uri[section.heading_id]

        return KbSection(
            kb_id=entity_id,
            label=f"Section {position_start}-{position_end}",
            source_document_uri=document_id,
            heading_uri=heading_uri,
            position_start=position_start,
            position_end=position_end
        )

    def _list_to_kb_entity(
        self,
        markdown_list: MarkdownList,
        document_id: str,
        element_id_to_uri: Dict[str, str]
    ) -> KbList:
        """Convert a MarkdownList element to KbList entity.

        Args:
            markdown_list: MarkdownList element
            document_id: Source document ID
            element_id_to_uri: Mapping for relationship resolution

        Returns:
            KbList entity
        """
        position_start = markdown_list.position.get('start') if markdown_list.position else 0
        position_end = markdown_list.position.get('end') if markdown_list.position else 0

        # Use position for deterministic ID generation
        entity_id = self.id_generator.generate_markdown_element_id(
            "list",
            f"pos-{position_start}-{position_end}",
            document_id
        )

        list_type = "ordered" if markdown_list.ordered else "unordered"

        return KbList(
            kb_id=entity_id,
            label=f"{list_type.capitalize()} list",
            source_document_uri=document_id,
            ordered=markdown_list.ordered,
            item_count=len(markdown_list.items),
            position_start=position_start,
            position_end=position_end,
            parent_list_uri=None  # Will be updated if nested
        )

    def _list_item_to_kb_entity(
        self,
        list_item: ListItem,
        document_id: str,
        element_id_to_uri: Dict[str, str]
    ) -> KbListItem:
        """Convert a ListItem element to KbListItem entity.

        Args:
            list_item: ListItem element
            document_id: Source document ID
            element_id_to_uri: Mapping for relationship resolution

        Returns:
            KbListItem entity
        """
        entity_id = self.id_generator.generate_markdown_element_id(
            "list-item",
            list_item.text[:50],
            document_id
        )

        position_start = list_item.position.get('start') if list_item.position else None
        position_end = list_item.position.get('end') if list_item.position else None

        # Resolve parent list URI if available
        parent_list_uri = None
        if list_item.parent_id and list_item.parent_id in element_id_to_uri:
            parent_list_uri = element_id_to_uri[list_item.parent_id]

        return KbListItem(
            kb_id=entity_id,
            label=list_item.text[:50],
            source_document_uri=document_id,
            text=list_item.text,
            parent_list_uri=parent_list_uri,
            position_start=position_start,
            position_end=position_end
        )

    def _table_to_kb_entity(
        self,
        table: Table,
        document_id: str
    ) -> KbTable:
        """Convert a Table element to KbTable entity.

        Args:
            table: Table element
            document_id: Source document ID

        Returns:
            KbTable entity
        """
        position_start = table.position.get('start') if table.position else 0
        position_end = table.position.get('end') if table.position else 0

        # Use position for deterministic ID generation
        entity_id = self.id_generator.generate_markdown_element_id(
            "table",
            f"pos-{position_start}-{position_end}",
            document_id
        )

        row_count = len(table.rows) + (1 if table.headers else 0)
        column_count = len(table.headers) if table.headers else (len(table.rows[0]) if table.rows else 0)

        return KbTable(
            kb_id=entity_id,
            label=f"Table with {row_count} rows",
            source_document_uri=document_id,
            row_count=row_count,
            column_count=column_count,
            headers=table.headers if table.headers else None,
            position_start=position_start,
            position_end=position_end
        )

    def _code_block_to_kb_entity(
        self,
        code_block: CodeBlock,
        document_id: str
    ) -> KbCodeBlock:
        """Convert a CodeBlock element to KbCodeBlock entity.

        Args:
            code_block: CodeBlock element
            document_id: Source document ID

        Returns:
            KbCodeBlock entity
        """
        position_start = code_block.position.get('start') if code_block.position else 0
        position_end = code_block.position.get('end') if code_block.position else 0

        # Use position for deterministic ID generation
        lang = code_block.language or 'unknown'
        entity_id = self.id_generator.generate_markdown_element_id(
            "code",
            f"{lang}-pos-{position_start}-{position_end}",
            document_id
        )

        line_count = len(code_block.code.splitlines())

        language_label = code_block.language or "unknown"

        return KbCodeBlock(
            kb_id=entity_id,
            label=f"{language_label} code block",
            source_document_uri=document_id,
            language=code_block.language,
            code=code_block.code,
            line_count=line_count,
            position_start=position_start,
            position_end=position_end
        )

    def _blockquote_to_kb_entity(
        self,
        blockquote: Blockquote,
        document_id: str
    ) -> KbBlockquote:
        """Convert a Blockquote element to KbBlockquote entity.

        Args:
            blockquote: Blockquote element
            document_id: Source document ID

        Returns:
            KbBlockquote entity
        """
        entity_id = self.id_generator.generate_markdown_element_id(
            "blockquote",
            blockquote.content[:50],
            document_id
        )

        position_start = blockquote.position.get('start') if blockquote.position else None
        position_end = blockquote.position.get('end') if blockquote.position else None

        return KbBlockquote(
            kb_id=entity_id,
            label=blockquote.content[:50],
            source_document_uri=document_id,
            level=blockquote.level,
            text=blockquote.content,
            position_start=position_start,
            position_end=position_end
        )

    def _update_entity_relationships(
        self,
        entity: KbBaseEntity,
        element_id_to_uri: Dict[str, str]
    ) -> None:
        """Update entity relationships based on URI mappings.

        This is called in a second pass after all entities are created
        to properly resolve parent/child relationships.

        Args:
            entity: Entity to update
            element_id_to_uri: Mapping of element IDs to KB URIs
        """
        # For now, relationships are handled during conversion
        # This method is a placeholder for future enhancements
        # such as hierarchical heading relationships
        pass

    def get_structure_statistics(
        self,
        structure_entities: List[KbBaseEntity]
    ) -> Dict[str, int]:
        """Get statistics about extracted markdown structure entities.

        Args:
            structure_entities: List of structure entities

        Returns:
            Dictionary with entity type counts
        """
        stats = {
            'total': len(structure_entities),
            'headings': 0,
            'sections': 0,
            'lists': 0,
            'list_items': 0,
            'tables': 0,
            'code_blocks': 0,
            'blockquotes': 0
        }

        for entity in structure_entities:
            if isinstance(entity, KbHeading):
                stats['headings'] += 1
            elif isinstance(entity, KbSection):
                stats['sections'] += 1
            elif isinstance(entity, KbList):
                stats['lists'] += 1
            elif isinstance(entity, KbListItem):
                stats['list_items'] += 1
            elif isinstance(entity, KbTable):
                stats['tables'] += 1
            elif isinstance(entity, KbCodeBlock):
                stats['code_blocks'] += 1
            elif isinstance(entity, KbBlockquote):
                stats['blockquotes'] += 1

        return stats
