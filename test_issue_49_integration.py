#!/usr/bin/env python3
"""
Integration test for issue #49 implementation.
Tests the complete flow of document registration, ID generation, and wikilink resolution.
"""

from knowledgebase_processor.models.kb_entities import KbDocument, KbWikiLink
from knowledgebase_processor.models.content import Document
from knowledgebase_processor.utils.id_generator import EntityIdGenerator
from knowledgebase_processor.utils.document_registry import DocumentRegistry
from knowledgebase_processor.extractor.wikilink_extractor import WikiLinkExtractor


def test_issue_49_integration():
    """Test the complete integration of issue #49 features."""
    # Create components
    id_generator = EntityIdGenerator(base_url="http://example.org/kb/")
    doc_registry = DocumentRegistry()
    wikilink_extractor = WikiLinkExtractor(doc_registry, id_generator)
    
    # Register some documents
    doc1_path = "docs/architecture/decisions/adr-001.md"
    doc1_id = id_generator.generate_document_id(doc1_path)
    doc1 = KbDocument(
        kb_id=doc1_id,
        label="ADR 001",
        original_path=doc1_path,
        path_without_extension="docs/architecture/decisions/adr-001"
    )
    doc_registry.register_document(doc1)
    
    doc2_path = "docs/planning/test-plan.md"
    doc2_id = id_generator.generate_document_id(doc2_path)
    doc2 = KbDocument(
        kb_id=doc2_id,
        label="Test Plan",
        original_path=doc2_path,
        path_without_extension="docs/planning/test-plan"
    )
    doc_registry.register_document(doc2)
    
    # Test document with wikilinks
    test_content = """
    # Test Document
    
    This document references [[adr-001]] and [[test-plan|the test plan]].
    It also has a broken link to [[non-existent-doc]].
    """
    
    test_doc = Document(path="test.md", content=test_content)
    test_doc_id = id_generator.generate_document_id("test.md")
    
    # Extract wikilinks
    wikilinks = wikilink_extractor.extract(test_doc, test_doc_id)
    
    # Verify results
    assert len(wikilinks) == 3
    
    # Check first link (resolved)
    link1 = wikilinks[0]
    assert link1.target_path == "adr-001"
    assert link1.original_text == "[[adr-001]]"
    assert link1.alias is None
    assert link1.resolved_document_uri == doc1_id
    
    # Check second link (resolved with alias)
    link2 = wikilinks[1]
    assert link2.target_path == "test-plan"
    assert link2.original_text == "[[test-plan|the test plan]]"
    assert link2.alias == "the test plan"
    assert link2.resolved_document_uri == doc2_id
    
    # Check third link (unresolved)
    link3 = wikilinks[2]
    assert link3.target_path == "non-existent-doc"
    assert link3.original_text == "[[non-existent-doc]]"
    assert link3.alias is None
    assert link3.resolved_document_uri is None
    
    # Verify ID generation consistency
    assert id_generator.generate_document_id(doc1_path) == doc1_id
    assert id_generator.generate_wikilink_id(test_doc_id, "[[adr-001]]") == link1.kb_id
    
    print("✅ All integration tests passed!")
    print(f"  - Document registry working correctly")
    print(f"  - ID generation is consistent")
    print(f"  - Wikilink extraction preserves original text")
    print(f"  - Wikilink resolution works for existing documents")
    print(f"  - Unresolved links are handled gracefully")


if __name__ == "__main__":
    test_issue_49_integration()