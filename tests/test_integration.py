"""End-to-end integration tests for the Knowledge Base Processor."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from rdflib import Namespace, RDF

from knowledgebase_processor.main import KnowledgeBaseProcessor
from knowledgebase_processor.models.content import Document


class TestKnowledgeBaseProcessorIntegration(unittest.TestCase):
    """Test cases for the Knowledge Base Processor integration."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for the knowledge base
        self.temp_dir = tempfile.mkdtemp()
        
        # Define path for the metadata SQLite database file
        # The directory for the SQLite DB file must exist.
        metadata_store_parent_dir = Path(self.temp_dir) / ".metadata_db_storage"
        metadata_store_parent_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_db_file_path = metadata_store_parent_dir / "kb_integration_test.db"
        
        # Create the processor, passing the DB file path as a string
        self.processor = KnowledgeBaseProcessor(self.temp_dir, str(self.metadata_db_file_path))
        
        # Create some test files
        self.create_test_files()
    
    def tearDown(self):
        """Clean up the test environment."""
        shutil.rmtree(self.temp_dir)
    
    def create_test_files(self):
        """Create test files for the knowledge base."""
        # Create a simple markdown file
        with open(os.path.join(self.temp_dir, "test1.md"), "w") as f:
            f.write("""---
title: Test Document 1
tags: [test, markdown]
---

# Test Document 1

This is a test document with some content.

## Section 1

- List item 1
- List item 2
- [ ] Todo item 1
- [x] Todo item 2 (done)

## Section 2

```python
def hello_world():
    print("Hello, world!")
```

> This is a blockquote
> With multiple lines

[Link to another document](test2.md)
""")
        
        # Create another markdown file
        with open(os.path.join(self.temp_dir, "test2.md"), "w") as f:
            f.write("""---
title: Test Document 2 related
tags: [test, related]
---

# Test Document 2 related

This document is related to Test Document 1.

## Related Content

This section references [Test Document 1](test1.md).
""")
        
        # Create a markdown file without frontmatter title
        with open(os.path.join(self.temp_dir, "no-frontmatter-title.md"), "w") as f:
            f.write("""---
author: Test Author
tags: [test, no-title]
---

# Document Content

This document has no title in frontmatter.
""")
    
    def test_process_file(self):
        """Test processing a single file."""
        # Process the first test file
        document = self.processor.process_file("test1.md")
        
        # Check that the document was processed correctly
        self.assertEqual(document.title, "Test Document 1")
        self.assertGreater(len(document.elements), 0)
        
        # Check that different element types were extracted
        element_types = set(e.element_type for e in document.elements)
        expected_types = {"heading", "section", "list", "list_item", "todo_item", "code_block", "blockquote", "link"}
        for expected_type in expected_types:
            self.assertIn(expected_type, element_types, f"Expected element type {expected_type} not found")
        
        # Check that metadata was stored
        metadata = self.processor.get_metadata(document.path)
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.document_id, document.path)
        
        # Check that tags were extracted
        self.assertGreaterEqual(len(metadata.tags), 2)
        self.assertIn("test", metadata.tags)
        self.assertIn("markdown", metadata.tags)
    
    def test_process_all(self):
        """Test processing all files."""
        # Process all markdown files
        documents = self.processor.process_all()
        
        # Check that all documents were processed
        self.assertEqual(len(documents), 3)
        
        # Check that document IDs are correct
        document_ids = [doc.path for doc in documents]
        self.assertIn("test1.md", document_ids)
        self.assertIn("test2.md", document_ids)
        self.assertIn("no-frontmatter-title.md", document_ids)
    
    def test_search(self):
        """Test searching for documents."""
        # Process all files first
        self.processor.process_all()
        
        # Search for documents containing "related"
        results = self.processor.search("related")
        self.assertGreaterEqual(len(results), 1)
        self.assertIn("test2.md", results)
    
    def test_find_by_tag(self):
        """Test finding documents by tag."""
        # Process all files first
        self.processor.process_all()
        
        # Find documents with the "test" tag
        results = self.processor.find_by_tag("test")
        self.assertEqual(len(results), 3)  # Updated to include the new test file
        self.assertIn("test1.md", results)
        self.assertIn("test2.md", results)
        self.assertIn("no-frontmatter-title.md", results)
        
        # Find documents with the "markdown" tag
        results = self.processor.find_by_tag("markdown")
        self.assertEqual(len(results), 1)
        self.assertIn("test1.md", results)
        
    def test_title_fallback(self):
        """Test document title fallback mechanism."""
        # Process all files first
        documents = self.processor.process_all()
        
        # Find the document without frontmatter title
        no_title_doc = None
        for doc in documents:
            if doc.path == "no-frontmatter-title.md":
                no_title_doc = doc
                break
        
        # Check that the document was found
        self.assertIsNotNone(no_title_doc)
        
        # Check that the title was set from the filename
        self.assertEqual(no_title_doc.title, "no frontmatter title")
    
    def test_find_related(self):
        """Test finding related documents."""
        # Process all files first
        self.processor.process_all()
        
        # Find documents related to test1.md
        results = self.processor.find_related("test1.md")
        self.assertGreaterEqual(len(results), 1)
        
        # Check that test2.md is related to test1.md
        related_ids = [r["document_id"] for r in results]
        self.assertIn("test2.md", related_ids)
def test_todo_item_extraction_to_rdf(self):
        """Test that ToDo items are extracted and converted to RDF."""
        # Define the path to the fixture file relative to the temp_dir
        fixture_file_path = Path("fixtures/todo_extraction/daily-note-2024-11-07-Thursday.md")
        
        # Ensure the fixtures directory exists in the temporary directory
        # and copy the fixture file there.
        # The processor works with files within its root_dir (self.temp_dir).
        source_fixture_path = Path(__file__).parent / "fixtures" / "todo_extraction" / "daily-note-2024-11-07-Thursday.md"
        destination_fixture_dir = Path(self.temp_dir) / "fixtures" / "todo_extraction"
        destination_fixture_dir.mkdir(parents=True, exist_ok=True)
        destination_fixture_path = destination_fixture_dir / "daily-note-2024-11-07-Thursday.md"
        shutil.copy(source_fixture_path, destination_fixture_path)

        # Process the fixture file
        # The path provided to process_file should be relative to self.temp_dir
        relative_fixture_path = destination_fixture_path.relative_to(self.temp_dir)
        document = self.processor.process_file(str(relative_fixture_path))
        self.assertIsNotNone(document, "Document processing failed.")
        
        # Get the RDF graph for the processed document
        rdf_graph = self.processor.get_rdf_graph(str(relative_fixture_path))
        self.assertIsNotNone(rdf_graph, "RDF graph generation failed.")
        
        # Define the knowledge base namespace
        kb_ns = Namespace("http://knowledgebase.example.com/schema#")
        
        # Check for the presence of at least one kb:TodoItem
        todo_items_found = list(rdf_graph.subjects(predicate=RDF.type, object=kb_ns.TodoItem))
        self.assertGreater(len(todo_items_found), 0, "No kb:TodoItem found in the RDF graph.")


if __name__ == "__main__":
    unittest.main()