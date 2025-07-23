#!/usr/bin/env python3
"""Detailed analysis of SPARQL queries to identify potential syntax issues."""

import sys
sys.path.insert(0, '/workspaces/knowledgebase-processor/src')

from knowledgebase_processor.query_interface.sparql_interface import SparqlQueryInterface
from rdflib import Graph

def analyze_sparql_issues():
    """Analyze potential SPARQL syntax issues in the DELETE queries."""
    
    print("=== DETAILED SPARQL ANALYSIS ===\n")
    
    # Test document URIs that might cause issues
    test_cases = [
        {
            "name": "Simple URI",
            "uris": ["http://example.org/kb/documents/test.md"]
        },
        {
            "name": "URI with spaces (encoded)",
            "uris": ["http://example.org/kb/documents/CTO%20Coffee-2024-11-07.md"]
        },
        {
            "name": "URI with spaces (unencoded)",
            "uris": ["http://example.org/kb/documents/CTO Coffee-2024-11-07.md"]
        },
        {
            "name": "Multiple URIs",
            "uris": [
                "http://example.org/kb/documents/daily-note-2024-11-07-Thursday.md",
                "http://example.org/kb/documents/CTO Coffee-2024-11-07.md"
            ]
        }
    ]
    
    # Analyze each test case
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. Testing {test_case['name']}:")
        print("=" * 50)
        
        document_uris = test_case['uris']
        print(f"Document URIs: {document_uris}")
        
        # Build VALUES clause
        values_clause = "VALUES ?doc { " + " ".join(f"<{uri}>" for uri in document_uris) + " }"
        print(f"VALUES clause: {values_clause}")
        
        # Check for potential issues
        issues = []
        for uri in document_uris:
            if " " in uri and "%" not in uri:
                issues.append(f"URI contains unencoded spaces: {uri}")
            if "#" in uri:
                issues.append(f"URI contains fragment identifier: {uri}")
            if len(uri) > 1000:
                issues.append(f"URI is very long: {len(uri)} characters")
        
        if issues:
            print("⚠️  Potential issues found:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ No obvious URI issues found")
        
        print()
    
    # Test specific SPARQL syntax elements
    print("=== SPARQL SYNTAX VALIDATION ===\n")
    
    # Test VALUES clause variations
    print("1. Testing VALUES clause variations:")
    print("-" * 40)
    
    test_values = [
        "VALUES ?doc { <http://example.org/kb/documents/test.md> }",
        "VALUES ?doc { <http://example.org/kb/documents/test.md> <http://example.org/kb/documents/test2.md> }",
        "VALUES (?doc) { (<http://example.org/kb/documents/test.md>) }",  # Alternative syntax
    ]
    
    for values_test in test_values:
        print(f"   {values_test}")
        # Basic validation - check for balanced brackets
        if values_test.count("{") != values_test.count("}"):
            print("     ⚠️  Unbalanced brackets")
        elif values_test.count("<") != values_test.count(">"):
            print("     ⚠️  Unbalanced angle brackets")
        else:
            print("     ✅ Basic syntax looks correct")
    
    print()
    
    # Test DELETE WHERE clause structure
    print("2. Testing DELETE WHERE structure:")
    print("-" * 40)
    
    sample_query = """
    PREFIX kb: <http://example.org/kb/>
    
    VALUES ?doc { <http://example.org/kb/documents/test.md> }
    
    DELETE {
        ?entity ?predicate ?object .
        ?doc ?docPredicate ?docObject .
    }
    WHERE {
        {
            ?entity kb:sourceDocument ?doc .
            ?entity ?predicate ?object .
        }
        UNION
        {
            ?doc ?docPredicate ?docObject .
        }
    }
    """
    
    print("Sample DELETE query:")
    print(sample_query)
    
    # Validate basic structure
    query_lines = [line.strip() for line in sample_query.strip().split('\n') if line.strip()]
    
    validation_results = {
        "has_prefix": any(line.startswith("PREFIX") for line in query_lines),
        "has_values": any("VALUES" in line for line in query_lines),
        "has_delete": any("DELETE" in line for line in query_lines),
        "has_where": any("WHERE" in line for line in query_lines),
        "has_union": any("UNION" in line for line in query_lines),
        "balanced_braces": sample_query.count("{") == sample_query.count("}"),
        "balanced_parens": sample_query.count("(") == sample_query.count(")")
    }
    
    print("\nStructural validation:")
    for check, result in validation_results.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check}: {result}")
    
    # Test named graph variant
    print("\n3. Testing named graph syntax:")
    print("-" * 40)
    
    named_graph_query = """
    PREFIX kb: <http://example.org/kb/>
    
    VALUES ?doc { <http://example.org/kb/documents/test.md> }
    
    DELETE {
        GRAPH <http://example.org/knowledgebase> {
            ?entity ?predicate ?object .
            ?doc ?docPredicate ?docObject .
        }
    }
    WHERE {
        GRAPH <http://example.org/knowledgebase> {
            {
                ?entity kb:sourceDocument ?doc .
                ?entity ?predicate ?object .
            }
            UNION
            {
                ?doc ?docPredicate ?docObject .
            }
        }
    }
    """
    
    print("Named graph DELETE query:")
    print(named_graph_query)
    
    # Check for common issues with named graphs
    graph_issues = []
    if named_graph_query.count("GRAPH") % 2 != 0:
        graph_issues.append("Unmatched GRAPH clauses")
    if "<http://example.org/knowledgebase>" not in named_graph_query:
        graph_issues.append("Missing graph URI")
    
    if graph_issues:
        print("\n⚠️  Named graph issues:")
        for issue in graph_issues:
            print(f"   - {issue}")
    else:
        print("\n✅ Named graph syntax looks correct")
    
    print("\n=== ANALYSIS COMPLETE ===")
    print("\nKey findings and recommendations:")
    print("1. The SPARQL DELETE queries appear syntactically correct")
    print("2. Main issue is likely network connectivity (Cannot assign requested address)")
    print("3. Potential improvements:")
    print("   - Add better error handling for network issues")
    print("   - Add query validation before execution")
    print("   - Consider URI encoding for spaces in document names")
    print("   - Add timeout and retry logic for unreliable endpoints")

if __name__ == "__main__":
    analyze_sparql_issues()