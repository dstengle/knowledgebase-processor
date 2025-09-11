# Specification-Driven Testing

This directory contains the specification-driven testing structure for the knowledgebase-processor project. This approach captures the current "as-is" behavior of the system in declarative artifacts, enabling a more robust, maintainable, and agent-friendly development workflow.

## Directory Structure

### `reference_corpus/`
Contains the integration and regression testing suite. These are real-world markdown files that represent the expected inputs the system should handle. Each `.md` file has a corresponding `.ttl` file that represents the expected RDF output.

### `test_cases/`
Contains individual unit test specifications. Each subdirectory represents a specific test case with:
- `input.md` - The markdown input for the test
- `expected_output.ttl` - The expected RDF output in Turtle format

## Usage

The specification-driven tests are executed through:

1. **Unit Tests**: `tests/test_specifications.py` - Runs all test cases in the `test_cases/` directory
2. **Integration Tests**: `tests/test_reference_corpus.py` - Validates the entire reference corpus

## Benefits

- **Declarative**: Test behavior is captured in files rather than code
- **Version Controlled**: Changes to expected behavior are tracked in git
- **Agent-Friendly**: AI agents can easily understand and modify test specifications
- **Maintainable**: No need to maintain complex Python test code for most scenarios
- **Comprehensive**: Full system behavior is captured as artifacts

## Test Philosophy

This approach follows the principle that the system's behavior should be specified through examples rather than code. When behavior changes, the specifications are updated to reflect the new expected behavior, providing a clear audit trail of system evolution.