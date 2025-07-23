"""Tests for todo IRI generation in EntityIdGenerator."""

import pytest
from knowledgebase_processor.utils.id_generator import EntityIdGenerator


class TestTodoIdGeneration:
    """Test todo ID generation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = EntityIdGenerator("http://example.org/kb/")
        self.doc_uri = "http://example.org/kb/documents/daily-note-2024-11-07.md"
    
    def test_basic_todo_id_generation(self):
        """Test basic todo ID generation with simple text."""
        todo_text = "Complete the project documentation"
        todo_id = self.generator.generate_todo_id(self.doc_uri, todo_text)
        
        expected = "http://example.org/kb/documents/daily-note-2024-11-07.md/todo/complete-the-project-documentation"
        assert todo_id == expected
    
    def test_todo_id_deterministic(self):
        """Test that same todo text always generates same ID."""
        todo_text = "Review pull requests"
        
        # Generate ID multiple times
        id1 = self.generator.generate_todo_id(self.doc_uri, todo_text)
        id2 = self.generator.generate_todo_id(self.doc_uri, todo_text)
        id3 = self.generator.generate_todo_id(self.doc_uri, todo_text)
        
        # All should be identical
        assert id1 == id2 == id3
    
    def test_todo_id_normalization(self):
        """Test that todo text is properly normalized."""
        # Different variations of same todo
        variations = [
            "Fix the bug in authentication",
            "  Fix the bug in authentication  ",  # Extra spaces
            "Fix  the   bug  in   authentication",  # Multiple spaces
            "Fix the bug in authentication!",  # Punctuation
            "Fix the bug in authentication.",  # Different punctuation
            "FIX THE BUG IN AUTHENTICATION",  # Uppercase
        ]
        
        # All should normalize to the same ID
        base_id = self.generator.generate_todo_id(self.doc_uri, variations[0])
        
        for variation in variations[1:]:
            assert self.generator.generate_todo_id(self.doc_uri, variation) == base_id
    
    def test_special_characters_normalization(self):
        """Test normalization of special characters."""
        test_cases = [
            ("Add @mention support", "add-mention-support"),
            ("Fix #123: Memory leak", "fix-123-memory-leak"),
            ("Update config.yaml file", "update-configyaml-file"),
            ("Implement feature/branch-name", "implement-featurebranch-name"),
            ("Test with 100% coverage", "test-with-100-coverage"),
            ("Use C++ compiler", "use-c-compiler"),
        ]
        
        for input_text, expected_suffix in test_cases:
            todo_id = self.generator.generate_todo_id(self.doc_uri, input_text)
            expected = f"{self.doc_uri}/todo/{expected_suffix}"
            assert todo_id == expected
    
    def test_empty_todo_handling(self):
        """Test handling of empty or whitespace-only todos."""
        empty_cases = ["", "   ", "\t", "\n", "   \t\n   "]
        
        for empty_text in empty_cases:
            todo_id = self.generator.generate_todo_id(self.doc_uri, empty_text)
            expected = f"{self.doc_uri}/todo/unnamed-todo"
            assert todo_id == expected
    
    def test_hyphen_normalization(self):
        """Test proper handling of hyphens in normalization."""
        test_cases = [
            ("Fix - the - bug", "fix-the-bug"),
            ("---Leading hyphens", "leading-hyphens"),
            ("Trailing hyphens---", "trailing-hyphens"),
            ("Multiple---consecutive---hyphens", "multiple-consecutive-hyphens"),
        ]
        
        for input_text, expected_suffix in test_cases:
            todo_id = self.generator.generate_todo_id(self.doc_uri, input_text)
            expected = f"{self.doc_uri}/todo/{expected_suffix}"
            assert todo_id == expected
    
    def test_non_uri_document_id(self):
        """Test handling of non-URI document IDs."""
        doc_id = "daily-note-2024-11-07.md"
        todo_text = "Complete the task"
        
        todo_id = self.generator.generate_todo_id(doc_id, todo_text)
        expected = "http://example.org/kb/documents/daily-note-2024-11-07.md/todo/complete-the-task"
        assert todo_id == expected
    
    def test_different_documents_same_todo(self):
        """Test that same todo in different documents gets different IDs."""
        todo_text = "Review code changes"
        doc1 = "http://example.org/kb/documents/doc1.md"
        doc2 = "http://example.org/kb/documents/doc2.md"
        
        id1 = self.generator.generate_todo_id(doc1, todo_text)
        id2 = self.generator.generate_todo_id(doc2, todo_text)
        
        # IDs should be different
        assert id1 != id2
        
        # But both should end with the same normalized text
        assert id1.endswith("/todo/review-code-changes")
        assert id2.endswith("/todo/review-code-changes")
    
    def test_unicode_handling(self):
        """Test handling of unicode characters."""
        test_cases = [
            ("café meeting", "café-meeting"),  # Accented characters preserved (part of \w)
            ("使用中文", "使用中文"),  # Unicode characters preserved
            ("emoji 🎉 party", "emoji-party"),  # Emojis removed
            ("résumé review", "résumé-review"),  # Accented characters preserved
        ]
        
        for input_text, expected_suffix in test_cases:
            todo_id = self.generator.generate_todo_id(self.doc_uri, input_text)
            if expected_suffix == "unnamed-todo":
                expected = f"{self.doc_uri}/todo/{expected_suffix}"
            else:
                expected = f"{self.doc_uri}/todo/{expected_suffix}"
            assert todo_id == expected