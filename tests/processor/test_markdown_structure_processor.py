"""Tests for the MarkdownStructureProcessor."""

import pytest
from knowledgebase_processor.processor.markdown_structure_processor import (
    MarkdownStructureProcessor
)
from knowledgebase_processor.models.content import Document
from knowledgebase_processor.models.markdown import (
    Heading, Section, MarkdownList, ListItem, Table, CodeBlock, Blockquote
)
from knowledgebase_processor.models.kb_entities import (
    KbHeading, KbSection, KbList, KbListItem, KbTable, KbCodeBlock, KbBlockquote
)
from knowledgebase_processor.utils.id_generator import EntityIdGenerator
from knowledgebase_processor.utils.document_registry import DocumentRegistry


@pytest.fixture
def id_generator():
    """Create an EntityIdGenerator for testing."""
    return EntityIdGenerator(base_url="http://example.org/kb/")


@pytest.fixture
def processor(id_generator):
    """Create a MarkdownStructureProcessor for testing."""
    return MarkdownStructureProcessor(id_generator)


def test_heading_conversion(processor):
    """Test converting a Heading to KbHeading."""
    # Create a heading element
    heading = Heading(
        id="h1",
        level=2,
        text="Test Heading",
        content="Test Heading",
        position={'start': 1, 'end': 1}
    )

    # Create a document with the heading
    document = Document(
        path="test.md",
        title="Test Document",
        content="## Test Heading",
        elements=[heading]
    )

    # Extract entities
    entities = processor.extract_markdown_structure_entities(document, "doc_1")

    # Verify
    assert len(entities) == 1
    assert isinstance(entities[0], KbHeading)
    assert entities[0].level == 2
    assert entities[0].text == "Test Heading"
    assert entities[0].position_start == 1
    assert entities[0].position_end == 1


def test_section_conversion(processor):
    """Test converting a Section to KbSection."""
    # Create heading and section
    heading = Heading(
        id="h1",
        level=1,
        text="Section Title",
        content="Section Title",
        position={'start': 1, 'end': 1}
    )

    section = Section(
        id="s1",
        content="",
        position={'start': 2, 'end': 5},
        heading_id="h1"
    )

    # Create document
    document = Document(
        path="test.md",
        title="Test",
        content="# Section Title\nContent here",
        elements=[heading, section]
    )

    # Extract entities
    entities = processor.extract_markdown_structure_entities(document, "doc_1")

    # Verify
    assert len(entities) == 2
    kb_heading = next(e for e in entities if isinstance(e, KbHeading))
    kb_section = next(e for e in entities if isinstance(e, KbSection))

    assert kb_section.heading_uri == kb_heading.kb_id


def test_list_conversion(processor):
    """Test converting a MarkdownList to KbList."""
    # Create list with items
    item1 = ListItem(
        id="i1",
        text="First item",
        content="First item",
        position={'start': 1, 'end': 1},
        parent_id="list1"
    )

    item2 = ListItem(
        id="i2",
        text="Second item",
        content="Second item",
        position={'start': 2, 'end': 2},
        parent_id="list1"
    )

    markdown_list = MarkdownList(
        id="list1",
        ordered=False,
        content="",
        position={'start': 1, 'end': 2},
        items=[item1, item2]
    )

    # Create document
    document = Document(
        path="test.md",
        title="Test",
        content="- First item\n- Second item",
        elements=[markdown_list, item1, item2]
    )

    # Extract entities
    entities = processor.extract_markdown_structure_entities(document, "doc_1")

    # Verify
    assert len(entities) == 3
    kb_list = next(e for e in entities if isinstance(e, KbList))
    kb_items = [e for e in entities if isinstance(e, KbListItem)]

    assert kb_list.ordered is False
    assert kb_list.item_count == 2
    assert len(kb_items) == 2


def test_table_conversion(processor):
    """Test converting a Table to KbTable."""
    # Create table
    table = Table(
        id="t1",
        content="",
        position={'start': 1, 'end': 3},
        headers=["Name", "Age", "City"],
        rows=[["Alice", "30", "NYC"], ["Bob", "25", "LA"]],
        cells=[]
    )

    # Create document
    document = Document(
        path="test.md",
        title="Test",
        content="| Name | Age | City |\n|------|-----|------|\n| Alice | 30 | NYC |",
        elements=[table]
    )

    # Extract entities
    entities = processor.extract_markdown_structure_entities(document, "doc_1")

    # Verify
    assert len(entities) == 1
    kb_table = entities[0]
    assert isinstance(kb_table, KbTable)
    assert kb_table.row_count == 3  # Headers + 2 rows
    assert kb_table.column_count == 3
    assert kb_table.headers == ["Name", "Age", "City"]


def test_code_block_conversion(processor):
    """Test converting a CodeBlock to KbCodeBlock."""
    # Create code block
    code = "def hello():\n    print('Hello')"
    code_block = CodeBlock(
        id="c1",
        language="python",
        code=code,
        content=code,
        position={'start': 1, 'end': 3}
    )

    # Create document
    document = Document(
        path="test.md",
        title="Test",
        content=f"```python\n{code}\n```",
        elements=[code_block]
    )

    # Extract entities
    entities = processor.extract_markdown_structure_entities(document, "doc_1")

    # Verify
    assert len(entities) == 1
    kb_code = entities[0]
    assert isinstance(kb_code, KbCodeBlock)
    assert kb_code.language == "python"
    assert kb_code.code == code
    assert kb_code.line_count == 2


def test_blockquote_conversion(processor):
    """Test converting a Blockquote to KbBlockquote."""
    # Create blockquote
    blockquote = Blockquote(
        id="bq1",
        level=1,
        content="This is a quote",
        position={'start': 1, 'end': 1}
    )

    # Create document
    document = Document(
        path="test.md",
        title="Test",
        content="> This is a quote",
        elements=[blockquote]
    )

    # Extract entities
    entities = processor.extract_markdown_structure_entities(document, "doc_1")

    # Verify
    assert len(entities) == 1
    kb_quote = entities[0]
    assert isinstance(kb_quote, KbBlockquote)
    assert kb_quote.level == 1
    assert kb_quote.text == "This is a quote"


def test_mixed_elements(processor):
    """Test processing a document with multiple element types."""
    # Create various elements
    heading = Heading(
        id="h1",
        level=1,
        text="Title",
        content="Title",
        position={'start': 1, 'end': 1}
    )

    code_block = CodeBlock(
        id="c1",
        language="javascript",
        code="console.log('test')",
        content="console.log('test')",
        position={'start': 3, 'end': 4}
    )

    markdown_list = MarkdownList(
        id="list1",
        ordered=True,
        content="",
        position={'start': 6, 'end': 8},
        items=[]
    )

    # Create document
    document = Document(
        path="test.md",
        title="Test",
        content="# Title\n\n```js\nconsole.log('test')\n```\n\n1. Item",
        elements=[heading, code_block, markdown_list]
    )

    # Extract entities
    entities = processor.extract_markdown_structure_entities(document, "doc_1")

    # Verify
    assert len(entities) == 3
    assert any(isinstance(e, KbHeading) for e in entities)
    assert any(isinstance(e, KbCodeBlock) for e in entities)
    assert any(isinstance(e, KbList) for e in entities)


def test_statistics(processor):
    """Test getting structure statistics."""
    # Create document with various elements
    document = Document(
        path="test.md",
        title="Test",
        content="# Title\n```python\ncode\n```\n- item",
        elements=[
            Heading(id="h1", level=1, text="Title", content="Title", position={'start': 1, 'end': 1}),
            CodeBlock(id="c1", language="python", code="code", content="code", position={'start': 2, 'end': 3}),
            MarkdownList(id="l1", ordered=False, content="", position={'start': 4, 'end': 4}, items=[])
        ]
    )

    # Extract entities
    entities = processor.extract_markdown_structure_entities(document, "doc_1")

    # Get statistics
    stats = processor.get_structure_statistics(entities)

    # Verify
    assert stats['total'] == 3
    assert stats['headings'] == 1
    assert stats['code_blocks'] == 1
    assert stats['lists'] == 1
    assert stats['sections'] == 0


def test_empty_document(processor):
    """Test processing an empty document."""
    document = Document(
        path="test.md",
        title="Empty",
        content="",
        elements=[]
    )

    entities = processor.extract_markdown_structure_entities(document, "doc_1")

    assert len(entities) == 0
