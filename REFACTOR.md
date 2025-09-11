Refactoring Plan: Specification-Driven TestingThis document outlines the process for refactoring the existing test suite into a specification-driven format. The goal is to capture the current "as-is" behavior of the system in declarative artifacts, which will enable a more robust, maintainable, and agent-friendly development workflow.🎯 Phase 1: Setup and ScaffoldingThis phase lays the foundation for the new testing structure.Task 1.1: Create the Specification Directory StructureCreate the following new directories in the root of the repository:specs/
├── README.md
├── reference_corpus/
└── test_cases/
specs/README.md: Create this file and add a brief explanation of the purpose of this new testing structure.specs/reference_corpus/: Copy the contents of the existing sample_data/ directory into this new directory. This will be our integration and regression testing suite.specs/test_cases/: This directory will hold the individual unit tests, with each feature getting its own subdirectory.Task 1.2: Create the Generic Test RunnerCreate a new test file, tests/test_specifications.py. This single file will eventually replace most of the existing unit tests. It will contain a generic, data-driven test runner.# tests/test_specifications.py
import pytest
from pathlib import Path
from knowledgebase_processor.processor import Processor 

# You will need a way to compare two RDF graphs. 
# The `rdflib.compare.isomorphic` function is perfect for this.
from rdflib import Graph
from rdflib.compare import isomorphic

def run_spec_test(test_case_dir: Path):
    """
    Runs a single specification-driven test.
    """
    input_md_path = test_case_dir / "input.md"
    expected_output_ttl_path = test_case_dir / "expected_output.ttl"

    # 1. Read the input markdown file
    input_md_content = input_md_path.read_text()
    
    # 2. Run the processor to get the "as-is" RDF graph
    # NOTE: You will need a method on your Processor that can take a string
    # of markdown and return an rdflib.Graph object.
    processor = Processor(...) # Configure your processor as needed
    as_is_graph = processor.process_content_to_graph(input_md_content) 
    
    # 3. Read the "to-be" (expected) RDF graph
    expected_graph = Graph()
    expected_graph.parse(str(expected_output_ttl_path), format="turtle")
    
    # 4. Compare the two RDF graphs for isomorphism (i.e., they are equivalent)
    assert isomorphic(as_is_graph, expected_graph)

# This function will automatically discover all your test cases
def get_test_cases():
    specs_dir = Path("specs/test_cases")
    if not specs_dir.exists():
        return []
    return [d for d in specs_dir.iterdir() if d.is_dir()]

@pytest.mark.parametrize("test_case_dir", get_test_cases())
def test_specifications(test_case_dir):
    run_spec_test(test_case_dir)
🔬 Phase 2: "As-Is" State Capture (Unit Tests)This phase is the core of the refactoring effort. You will systematically convert each existing unit test into the new declarative format.Task 2.1: Convert test_todo_item_extractor.pyFor each test function in tests/extractor/test_todo_item_extractor.py:Create a Test Case Directory: Create a new subdirectory in specs/test_cases/ that describes the test (e.g., 01_extract_incomplete_todo).Create input.md: Take the Markdown string being used in the test and save it as input.md in the new directory.Generate expected_output.ttl: Temporarily modify the test function to run the full processor on the input and serialize the resulting RDF graph to a file. Save this as expected_output.ttl in the new directory.Run the New Test: Run pytest tests/test_specifications.py. The new test case should now be discovered and pass, confirming that you have successfully captured the "as-is" state.Delete the Old Test: Once the new test is passing, delete the original Python test function.Repeat this process until test_todo_item_extractor.py is empty, then delete the file.Task 2.2: Convert Remaining Extractor TestsRepeat the process from Task 2.1 for all remaining test files in the tests/extractor/ directory.Task 2.3: Convert Other Unit TestsContinue this process for all other relevant unit test files in the tests/ directory, such as those in tests/analyzer/ and tests/parser/.🚗 Phase 3: Integration and CleanupThis phase establishes the regression test suite and cleans up the old test files.Task 3.1: Create the Reference Corpus TestGenerate "As-Is" TTLs: Write a one-off script that iterates through every .md file in your specs/reference_corpus/ directory. For each file, run the processor and save the resulting RDF graph as a corresponding .ttl file in the same directory.Create a New Integration Test: Add a new test file, tests/test_reference_corpus.py. This test will be similar to the unit test runner but will work on the entire reference corpus.# tests/test_reference_corpus.py
import pytest
from pathlib import Path
from knowledgebase_processor.processor import Processor
from rdflib import Graph
from rdflib.compare import isomorphic

def run_corpus_test(markdown_path: Path):
    expected_ttl_path = markdown_path.with_suffix(".ttl")
    
    input_content = markdown_path.read_text()
    
    processor = Processor(...) # Configure processor
    as_is_graph = processor.process_content_to_graph(input_content)
    
    expected_graph = Graph()
    expected_graph.parse(str(expected_ttl_path), format="turtle")
    
    assert isomorphic(as_is_graph, expected_graph)

def get_corpus_files():
    corpus_dir = Path("specs/reference_corpus")
    if not corpus_dir.exists():
        return []
    return list(corpus_dir.glob("*.md"))

@pytest.mark.parametrize("markdown_path", get_corpus_files())
def test_reference_corpus(markdown_path):
    run_corpus_test(markdown_path)
Task 3.2: Final CleanupReview the tests/ directory and remove any remaining test files that have been made redundant by the new specification-driven approach.By the end of this process, your tests/ directory will be much smaller, and you will have a comprehensive, version-controlled, and easily updatable specification of your entire system's behavior in the specs/ directory.