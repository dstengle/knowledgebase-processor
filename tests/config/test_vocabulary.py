"""
Tests for vocabulary configuration and integration.
"""

import json
from pathlib import Path
import pytest
from rdflib import Graph, URIRef, Literal, RDF

from knowledgebase_processor.config.vocabulary import (
    KB,
    get_vocabulary_metadata,
    get_vocabulary_file_path,
    validate_vocabulary,
    get_kb_namespace
)


class TestVocabularyConfiguration:
    """Test vocabulary configuration module."""
    
    def test_kb_namespace_import(self):
        """Test that KB namespace can be imported."""
        assert KB is not None
        assert str(KB) == "http://example.org/kb/vocab#"
    
    def test_vocabulary_metadata_loading(self):
        """Test loading vocabulary metadata."""
        metadata = get_vocabulary_metadata()
        
        assert isinstance(metadata, dict)
        assert "namespace" in metadata
        assert "source_repository" in metadata
        assert metadata["source_repository"] == "https://github.com/dstengle/knowledgebase-vocabulary"
    
    def test_vocabulary_file_path(self):
        """Test getting vocabulary file path."""
        vocab_path = get_vocabulary_file_path()
        
        assert isinstance(vocab_path, Path)
        assert vocab_path.name == "kb.ttl"
        assert vocab_path.parent.name == "vocabulary"
    
    def test_vocabulary_validation(self):
        """Test vocabulary validation."""
        is_valid = validate_vocabulary()
        
        # Should be valid after our setup
        assert is_valid is True
    
    def test_vocabulary_file_exists(self):
        """Test that vocabulary file exists."""
        vocab_path = get_vocabulary_file_path()
        assert vocab_path.exists()
    
    def test_vocabulary_file_parseable(self):
        """Test that vocabulary file can be parsed as RDF."""
        vocab_path = get_vocabulary_file_path()
        
        g = Graph()
        # Should not raise an exception
        g.parse(vocab_path, format='turtle')
        
        # Check that it contains some expected content
        assert len(g) > 0
    
    def test_kb_namespace_usage(self):
        """Test using KB namespace to create URIs."""
        # Test creating class URIs
        document_uri = KB.Document
        assert isinstance(document_uri, URIRef)
        assert str(document_uri) == "http://example.org/kb/vocab#Document"
        
        # Test creating property URIs
        has_tag_uri = KB.hasTag
        assert isinstance(has_tag_uri, URIRef)
        assert str(has_tag_uri) == "http://example.org/kb/vocab#hasTag"
        
        # Test creating dynamic URIs
        tag_uri = KB["python"]
        assert isinstance(tag_uri, URIRef)
        assert str(tag_uri) == "http://example.org/kb/vocab#python"
    
    def test_vocabulary_in_rdf_graph(self):
        """Test using vocabulary in RDF graph operations."""
        g = Graph()
        g.bind("kb", KB)
        
        # Create a document entity
        doc_uri = URIRef("http://example.org/documents/test-doc")
        g.add((doc_uri, RDF.type, KB.Document))
        g.add((doc_uri, KB.title, Literal("Test Document")))
        g.add((doc_uri, KB.hasTag, KB["test"]))
        
        # Verify triples were added
        assert (doc_uri, RDF.type, KB.Document) in g
        assert (doc_uri, KB.title, Literal("Test Document")) in g
        assert (doc_uri, KB.hasTag, KB["test"]) in g
        
        # Test serialization includes namespace binding
        turtle_output = g.serialize(format='turtle')
        assert "@prefix kb:" in turtle_output
        assert "kb:Document" in turtle_output or str(KB.Document) in turtle_output


class TestVocabularyIntegration:
    """Test vocabulary integration with other modules."""
    
    def test_kb_entities_import(self):
        """Test that kb_entities module uses centralized vocabulary."""
        from knowledgebase_processor.models.kb_entities import KB as entities_KB
        from knowledgebase_processor.config.vocabulary import KB as config_KB
        
        # Should be the same namespace
        assert str(entities_KB) == str(config_KB)
    
    def test_rdf_converter_import(self):
        """Test that rdf_converter module uses centralized vocabulary."""
        from knowledgebase_processor.rdf_converter.converter import KB as converter_KB
        from knowledgebase_processor.config.vocabulary import KB as config_KB
        
        # Should be the same namespace
        assert str(converter_KB) == str(config_KB)
    
    def test_vocabulary_consistency(self):
        """Test that vocabulary is consistently used across modules."""
        from knowledgebase_processor.models.kb_entities import KbTodoItem
        from knowledgebase_processor.rdf_converter.converter import RdfConverter
        
        # Create a todo item
        todo = KbTodoItem(
            kb_id="todo-1",
            description="Test todo item",
            is_completed=False
        )
        
        # Convert to RDF
        converter = RdfConverter()
        g = converter.kb_entity_to_graph(todo)
        
        # Check that it uses the correct namespace
        assert len(g) > 0
        
        # The entity should have the KB.Entity type (from base class)
        todo_uri = URIRef("http://example.org/kb/todo-1")
        assert any((todo_uri, RDF.type, o) for s, p, o in g if s == todo_uri)


class TestVersionFile:
    """Test VERSION.json file structure."""
    
    def test_version_file_exists(self):
        """Test that VERSION.json exists."""
        version_path = Path(__file__).parent.parent.parent / "vocabulary" / "VERSION.json"
        assert version_path.exists()
    
    def test_version_file_structure(self):
        """Test VERSION.json has required fields."""
        version_path = Path(__file__).parent.parent.parent / "vocabulary" / "VERSION.json"
        
        with open(version_path) as f:
            version_data = json.load(f)
        
        required_fields = [
            "source_repository",
            "source_commit", 
            "sync_date",
            "namespace",
            "version"
        ]
        
        for field in required_fields:
            assert field in version_data, f"Missing required field: {field}"
        
        # Validate field values
        assert version_data["source_repository"] == "https://github.com/dstengle/knowledgebase-vocabulary"
        assert version_data["namespace"] == "http://example.org/kb/vocab#"