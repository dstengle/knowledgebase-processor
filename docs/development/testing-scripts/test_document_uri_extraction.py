#!/usr/bin/env python3
"""Test document URI extraction to identify potential issues."""

import sys
sys.path.insert(0, '/workspaces/knowledgebase-processor/src')

from knowledgebase_processor.query_interface.sparql_interface import SparqlQueryInterface
from rdflib import Graph, URIRef

def test_document_uri_extraction():
    """Test the document URI extraction method."""
    
    print("=== TESTING DOCUMENT URI EXTRACTION ===\n")
    
    # Load a real RDF file
    rdf_file = "/workspaces/knowledgebase-processor/sample_data/.kbp/temp_rdf/CTO Coffee-2024-11-07.ttl"
    graph = Graph()
    graph.parse(rdf_file, format='turtle')
    
    print(f"Loaded RDF file: {rdf_file}")
    print(f"Number of triples: {len(graph)}")
    print()
    
    # Create SPARQL interface
    sparql_interface = SparqlQueryInterface()
    
    # Test document URI extraction
    print("1. Testing _extract_document_uris method:")
    print("-" * 50)
    
    extracted_uris = sparql_interface._extract_document_uris(graph)
    print(f"Extracted URIs: {extracted_uris}")
    print()
    
    # Manual inspection of what the method is looking for
    print("2. Manual inspection of document entities:")
    print("-" * 50)
    
    kb_document = URIRef("http://example.org/kb/Document")
    rdf_type = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    
    document_entities = []
    for subject, predicate, obj in graph:
        if predicate == rdf_type and obj == kb_document:
            document_entities.append(str(subject))
    
    print(f"Found {len(document_entities)} kb:Document entities:")
    for doc in document_entities:
        print(f"  - {doc}")
    print()
    
    # Check for kb:sourceDocument references
    print("3. Checking kb:sourceDocument references:")
    print("-" * 50)
    
    kb_source_document = URIRef("http://example.org/kb/sourceDocument")
    source_documents = set()
    
    for subject, predicate, obj in graph:
        if predicate == kb_source_document:
            source_documents.add(str(obj))
    
    print(f"Found {len(source_documents)} kb:sourceDocument references:")
    for doc in source_documents:
        print(f"  - {doc}")
    print()
    
    # Compare extraction methods
    print("4. Comparison of extraction methods:")
    print("-" * 50)
    
    all_document_uris = set(document_entities) | source_documents
    print(f"Combined unique document URIs: {len(all_document_uris)}")
    for uri in sorted(all_document_uris):
        print(f"  - {uri}")
    print()
    
    print(f"Method extracted: {len(extracted_uris)} URIs")
    print(f"Manual found: {len(all_document_uris)} URIs")
    print(f"Match: {set(extracted_uris) == all_document_uris}")
    print()
    
    # Test the VALUES clause generation
    print("5. Testing VALUES clause generation:")
    print("-" * 50)
    
    if extracted_uris:
        values_clause = "VALUES ?doc { " + " ".join(f"<{uri}>" for uri in extracted_uris) + " }"
        print("Generated VALUES clause:")
        print(values_clause)
        print()
        
        # Check for potential issues in the URIs
        issues = []
        for uri in extracted_uris:
            if not uri.startswith("http"):
                issues.append(f"URI doesn't start with http: {uri}")
            if ">" in uri or "<" in uri:
                issues.append(f"URI contains angle brackets: {uri}")
            if '"' in uri:
                issues.append(f"URI contains quotes: {uri}")
        
        if issues:
            print("⚠️  Potential issues with URIs:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ URIs look valid for SPARQL VALUES clause")
    
    print("\n=== DOCUMENT URI EXTRACTION TEST COMPLETE ===")

if __name__ == "__main__":
    test_document_uri_extraction()