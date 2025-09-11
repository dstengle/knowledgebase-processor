# tests/test_reference_corpus.py
"""
Integration tests for the reference corpus.

This test file implements the specification-driven testing approach outlined in REFACTOR.md.
It validates that the processor continues to generate the same RDF output for all files
in the reference corpus, ensuring consistency and preventing regressions.
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

from rdflib import Graph, Namespace
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
    
    # Register all extractors (same as in main.py and generation script)
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


def run_corpus_test(markdown_path: Path):
    """
    Run a corpus test for a single markdown file.
    
    This function:
    1. Reads the markdown content
    2. Processes it through the processor to get an RDF graph
    3. Compares it with the expected TTL file for isomorphism
    4. Asserts that they are equivalent
    """
    expected_ttl_path = markdown_path.with_suffix(".ttl")
    
    # Ensure the expected TTL file exists
    if not expected_ttl_path.exists():
        pytest.fail(f"Expected TTL file not found: {expected_ttl_path}")
    
    # Read the markdown content
    input_content = markdown_path.read_text(encoding='utf-8')
    
    # Setup processor and process content
    processor = setup_processor()
    
    # Generate document ID (same logic as generation script)
    clean_stem = markdown_path.stem.replace(" ", "_").replace("-", "_").replace(":", "_")
    document_id = f"test_corpus/{clean_stem}"
    
    # Process content to get "as-is" RDF graph
    as_is_graph = processor.process_content_to_graph(input_content, document_id=document_id)
    
    # Read the expected RDF graph
    expected_graph = Graph()
    expected_graph.parse(str(expected_ttl_path), format="turtle")
    
    # Remove timestamps from both graphs for comparison
    as_is_clean = remove_timestamps_from_graph(as_is_graph)
    expected_clean = remove_timestamps_from_graph(expected_graph)
    
    # Compare the two RDF graphs for isomorphism
    # This checks if they contain the same triples regardless of ordering
    if not isomorphic(as_is_clean, expected_clean):
        # Provide helpful debugging information
        as_is_triples = len(as_is_clean)
        expected_triples = len(expected_clean)
        
        pytest.fail(
            f"RDF graphs are not isomorphic for {markdown_path.name}!\n"
            f"As-is graph: {as_is_triples} triples (excluding timestamps)\n"
            f"Expected graph: {expected_triples} triples (excluding timestamps)\n"
            f"This indicates the processor output has changed."
        )


def get_corpus_files() -> List[Path]:
    """
    Get all markdown files in the reference corpus directory.
    
    Returns:
        List of Path objects for markdown files
    """
    corpus_dir = Path(__file__).parent.parent / "specs" / "reference_corpus"
    
    if not corpus_dir.exists():
        return []
    
    return list(corpus_dir.glob("*.md"))


@pytest.mark.parametrize("markdown_path", get_corpus_files())
def test_reference_corpus(markdown_path: Path):
    """
    Parametrized test that runs for each markdown file in the reference corpus.
    
    This test ensures that the processor generates the same RDF output for each
    file as when the reference TTL files were generated. This serves as a
    regression test to catch any unintended changes to the processor behavior.
    
    Args:
        markdown_path: Path to the markdown file to test
    """
    run_corpus_test(markdown_path)


def test_corpus_directory_exists():
    """
    Test to ensure the reference corpus directory exists and contains files.
    """
    corpus_dir = Path(__file__).parent.parent / "specs" / "reference_corpus"
    assert corpus_dir.exists(), f"Reference corpus directory not found: {corpus_dir}"
    
    md_files = list(corpus_dir.glob("*.md"))
    assert len(md_files) > 0, "No markdown files found in reference corpus"
    
    ttl_files = list(corpus_dir.glob("*.ttl"))
    assert len(ttl_files) > 0, "No TTL files found in reference corpus"
    
    # Each markdown file should have a corresponding TTL file
    for md_file in md_files:
        ttl_file = md_file.with_suffix(".ttl")
        assert ttl_file.exists(), f"Missing TTL file for {md_file.name}: {ttl_file}"


if __name__ == "__main__":
    # Allow running this test file directly for debugging
    pytest.main([__file__, "-v"])