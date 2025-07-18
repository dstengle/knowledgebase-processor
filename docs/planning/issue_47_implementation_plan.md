# Implementation Plan for Issue #47: Add CLI command to process and load knowledgebase directory into SPARQL endpoint in one step

## Overview

This plan outlines the steps to implement a new CLI command (`kbp process-and-load`) that processes all files in a knowledgebase directory, generates RDF data, and loads it into a SPARQL endpoint in a single step.

## Goals

- Provide a single CLI command for processing and loading
- Support all existing processing options (pattern matching, etc.)
- Generate RDF for all processed documents
- Automatically load RDF into the configured SPARQL endpoint
- Provide progress feedback and error reporting
- Allow specifying a named graph
- Optionally clean up temporary RDF files
- Ensure unit and E2E test coverage
- Update documentation with usage examples

## Steps

1. **CLI Extension**
   - Add a new command `process-and-load` to [`src/knowledgebase_processor/cli/main.py`](src/knowledgebase_processor/cli/main.py)
   - Support options: `--pattern`, `--graph`, `--endpoint`, `--update-endpoint`, `--cleanup`, etc.

2. **Orchestration Logic**
   - Implement orchestration in [`src/knowledgebase_processor/services/processing_service.py`](src/knowledgebase_processor/services/processing_service.py) or a new service.
   - Reuse `process_documents` and `sparql_load` logic.
   - Use a temporary directory for RDF output if cleanup is requested.

3. **Batch Loading**
   - Add batch loading support in [`src/knowledgebase_processor/services/sparql_service.py`](src/knowledgebase_processor/services/sparql_service.py).
   - Optimize for large numbers of RDF files.

4. **Progress & Error Handling**
   - Provide progress feedback (logging, optional progress bar).
   - Collect and report errors at the end, continue processing other files.

5. **Testing**
   - Add unit tests in `tests/services/` and `tests/cli/`.
   - Add E2E tests for the full workflow.

6. **Documentation**
   - Update CLI documentation and add usage examples.

## Technical Considerations

- Memory efficiency for large knowledge bases
- Streaming/chunking for large datasets
- Maintain separation of concerns between processing and loading

## Example Usage

```bash
# Basic usage
kbp process-and-load

# With options
kbp process-and-load \
  --pattern "**/*.md" \
  --graph "http://example.org/kb/2024" \
  --endpoint "http://localhost:3030/kb/sparql" \
  --update-endpoint "http://localhost:3030/kb/update" \
  --cleanup
```

## Success Metrics

- Comparable processing/loading time to separate commands
- Reasonable memory usage for 1000+ documents
- Clear error reporting and user feedback

## Related Issues

- Builds on processing (#29) and SPARQL integration
- May benefit from batch/parallel processing in the future
