#!/usr/bin/env python3
"""
Script to regenerate expected outputs for all specification tests.

This should be run when the processor output format changes to update
all test expectations to match the current behavior.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from knowledgebase_processor.processor.processor import Processor
from knowledgebase_processor.utils.document_registry import DocumentRegistry
from knowledgebase_processor.utils.id_generator import EntityIdGenerator
from knowledgebase_processor.extractor.markdown import MarkdownExtractor
from knowledgebase_processor.extractor.frontmatter import FrontmatterExtractor
from knowledgebase_processor.extractor.heading_section import HeadingSectionExtractor
from knowledgebase_processor.extractor.link_reference import LinkReferenceExtractor
from knowledgebase_processor.extractor.code_quote import CodeQuoteExtractor
from knowledgebase_processor.extractor.todo_item import TodoItemExtractor
from knowledgebase_processor.extractor.tags import TagExtractor
from knowledgebase_processor.extractor.list_table import ListTableExtractor


def setup_processor():
    """Setup a processor with all necessary extractors."""
    document_registry = DocumentRegistry()
    id_generator = EntityIdGenerator(base_url="http://example.org/kb/")

    processor = Processor(
        document_registry=document_registry,
        id_generator=id_generator,
        config=None,
    )

    # Register all extractors
    processor.register_extractor(MarkdownExtractor())
    processor.register_extractor(FrontmatterExtractor())
    processor.register_extractor(HeadingSectionExtractor())
    processor.register_extractor(LinkReferenceExtractor())
    processor.register_extractor(CodeQuoteExtractor())
    processor.register_extractor(TodoItemExtractor())
    processor.register_extractor(TagExtractor())
    processor.register_extractor(ListTableExtractor())

    return processor


def regenerate_all_outputs():
    """Regenerate expected outputs for all test cases."""
    specs_dir = Path(__file__).parent.parent / "specs" / "test_cases"

    if not specs_dir.exists():
        print(f"Error: Test cases directory not found: {specs_dir}")
        return 1

    test_case_dirs = sorted([d for d in specs_dir.iterdir() if d.is_dir()])

    if not test_case_dirs:
        print(f"Error: No test case directories found in {specs_dir}")
        return 1

    print(f"Found {len(test_case_dirs)} test cases to regenerate")
    print()

    success_count = 0
    error_count = 0

    for test_case_dir in test_case_dirs:
        input_file = test_case_dir / "input.md"
        output_file = test_case_dir / "expected_output.ttl"

        if not input_file.exists():
            print(f"⚠️  Skipping {test_case_dir.name}: input.md not found")
            error_count += 1
            continue

        try:
            # Setup fresh processor for each test
            processor = setup_processor()

            # Read input
            content = input_file.read_text(encoding='utf-8')

            # Process to graph
            document_id = f"test_cases/{test_case_dir.name}"
            graph = processor.process_content_to_graph(content, document_id=document_id)

            # Write expected output
            output_file.write_text(graph.serialize(format='turtle'), encoding='utf-8')

            print(f"✅ {test_case_dir.name}")
            success_count += 1

        except Exception as e:
            print(f"❌ {test_case_dir.name}: {str(e)}")
            error_count += 1

    print()
    print(f"Summary: {success_count} succeeded, {error_count} failed")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(regenerate_all_outputs())
