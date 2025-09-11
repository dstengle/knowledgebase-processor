# tests/test_specifications.py
"""
Specification-driven tests for individual test cases.

This test file implements the specification-driven testing approach outlined in REFACTOR.md.
It runs tests for all test cases in the specs/test_cases/ directory, where each test case
contains an input.md file and an expected_output.ttl file.
"""

import pytest
import sys
from pathlib import Path
from typing import List

# Add the src directory to the path to import our modules
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

from rdflib import Graph
from rdflib.compare import isomorphic
from rdflib.namespace import SDO as SCHEMA


def setup_processor() -> Processor:
    """Setup a processor with all necessary extractors for testing."""
    document_registry = DocumentRegistry()
    id_generator = EntityIdGenerator(base_url="http://example.org/kb/")
    
    processor = Processor(
        document_registry=document_registry,
        id_generator=id_generator,
        config=None,
    )
    
    # Register all extractors (same as in reference corpus tests)
    processor.register_extractor(MarkdownExtractor())
    processor.register_extractor(FrontmatterExtractor())
    processor.register_extractor(HeadingSectionExtractor())
    processor.register_extractor(LinkReferenceExtractor())
    processor.register_extractor(CodeQuoteExtractor())
    processor.register_extractor(TodoItemExtractor())
    processor.register_extractor(TagExtractor())
    processor.register_extractor(ListTableExtractor())
    
    return processor


def remove_timestamps_from_graph(graph: Graph) -> Graph:
    """
    Remove timestamp triples from the graph to allow for consistent comparison.
    
    This removes schema:dateCreated and schema:dateModified triples that change
    every time the processor runs, making the graphs non-isomorphic.
    """
    cleaned_graph = Graph()
    
    # Copy all namespaces from the original graph
    for prefix, namespace in graph.namespaces():
        cleaned_graph.bind(prefix, namespace)
    
    # Copy all triples except timestamp triples
    for subj, pred, obj in graph:
        if pred not in [SCHEMA.dateCreated, SCHEMA.dateModified]:
            cleaned_graph.add((subj, pred, obj))
    
    return cleaned_graph


def run_spec_test(test_case_dir: Path):
    """
    Runs a single specification-driven test.
    
    This function:
    1. Reads the input.md file
    2. Processes it through the processor to get an RDF graph
    3. Compares it with the expected_output.ttl file for isomorphism
    4. Asserts that they are equivalent
    """
    input_md_path = test_case_dir / "input.md"
    expected_output_ttl_path = test_case_dir / "expected_output.ttl"

    # Ensure required files exist
    if not input_md_path.exists():
        pytest.fail(f"Input markdown file not found: {input_md_path}")
    if not expected_output_ttl_path.exists():
        pytest.fail(f"Expected TTL file not found: {expected_output_ttl_path}")

    # 1. Read the input markdown file
    input_md_content = input_md_path.read_text(encoding='utf-8')
    
    # 2. Run the processor to get the "as-is" RDF graph
    processor = setup_processor()
    
    # Use test case directory name as document_id
    document_id = f"test_cases/{test_case_dir.name}"
    as_is_graph = processor.process_content_to_graph(input_md_content, document_id=document_id)
    
    # 3. Read the "to-be" (expected) RDF graph
    expected_graph = Graph()
    expected_graph.parse(str(expected_output_ttl_path), format="turtle")
    
    # 4. Remove timestamps from both graphs for comparison
    as_is_clean = remove_timestamps_from_graph(as_is_graph)
    expected_clean = remove_timestamps_from_graph(expected_graph)
    
    # 5. Compare the two RDF graphs for isomorphism (i.e., they are equivalent)
    if not isomorphic(as_is_clean, expected_clean):
        # Provide helpful debugging information
        as_is_triples = len(as_is_clean)
        expected_triples = len(expected_clean)
        
        pytest.fail(
            f"RDF graphs are not isomorphic for {test_case_dir.name}!\n"
            f"As-is graph: {as_is_triples} triples (excluding timestamps)\n"
            f"Expected graph: {expected_triples} triples (excluding timestamps)\n"
            f"This indicates the processor output has changed."
        )

def get_test_cases() -> List[Path]:
    """
    Get all test case directories in the specs/test_cases/ directory.
    
    Returns:
        List of Path objects for test case directories
    """
    specs_dir = Path(__file__).parent.parent / "specs" / "test_cases"
    
    if not specs_dir.exists():
        return []
    
    return [d for d in specs_dir.iterdir() if d.is_dir()]


@pytest.mark.parametrize("test_case_dir", get_test_cases())
def test_specifications(test_case_dir: Path):
    """
    Parametrized test that runs for each test case directory in specs/test_cases/.
    
    This test ensures that the processor generates the same RDF output for each
    test case as specified in the expected_output.ttl file. This serves as a
    unit test to verify specific behaviors and catch any unintended changes.
    
    Args:
        test_case_dir: Path to the test case directory containing input.md and expected_output.ttl
    """
    run_spec_test(test_case_dir)


def test_test_cases_directory_exists():
    """
    Test to ensure the test cases directory exists and contains test cases.
    """
    test_cases_dir = Path(__file__).parent.parent / "specs" / "test_cases"
    assert test_cases_dir.exists(), f"Test cases directory not found: {test_cases_dir}"
    
    test_case_dirs = [d for d in test_cases_dir.iterdir() if d.is_dir()]
    assert len(test_case_dirs) > 0, "No test case directories found in specs/test_cases"
    
    # Each test case directory should have both input.md and expected_output.ttl
    for test_dir in test_case_dirs:
        input_file = test_dir / "input.md"
        expected_file = test_dir / "expected_output.ttl"
        
        assert input_file.exists(), f"Missing input.md in {test_dir.name}: {input_file}"
        assert expected_file.exists(), f"Missing expected_output.ttl in {test_dir.name}: {expected_file}"


if __name__ == "__main__":
    # Allow running this test file directly for debugging
    pytest.main([__file__, "-v"])