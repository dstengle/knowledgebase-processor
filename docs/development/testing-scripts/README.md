# Development Testing Scripts

This directory contains temporary test scripts that were created during development and debugging sessions. These scripts are preserved for future reference and potential reuse.

## Scripts

### SPARQL Upsert Implementation (July 2025)

Created during the implementation of SPARQL upsert functionality to prevent duplicate triples:

- **`debug_sparql_queries.py`** - Interactive debugging script for testing SPARQL queries and analyzing duplicate triple issues
- **`detailed_sparql_analysis.py`** - Comprehensive analysis script for examining RDF data and SPARQL operations 
- **`test_document_uri_extraction.py`** - Unit tests for document URI extraction functionality

These scripts were instrumental in:
- Identifying the duplicate triples issue in Fuseki sync operations
- Testing document-level DELETE/INSERT patterns
- Debugging SPARQL VALUES clause compatibility issues
- Validating cross-document entity reference handling

## Usage

These scripts are preserved as historical artifacts and may be useful for:
- Future debugging of similar SPARQL-related issues
- Understanding the thought process during the upsert implementation
- Providing test cases for regression testing
- Reference examples for SPARQL query development

## Related Work

See PR #56: "feat: Implement SPARQL upsert functionality to prevent duplicate triples"
- Implementation files: `sparql_interface.py`, `sparql_service.py`, `processing_service.py`, `orchestrator.py`, `sync.py`
- Issue resolved: Duplicate triples created during multiple sync operations to Fuseki