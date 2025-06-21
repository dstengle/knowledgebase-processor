"""End-to-end integration tests for the Knowledge Base Processor."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from rdflib import Graph
from knowledgebase_processor.models.kb_entities import KB
from rdflib import Namespace, RDF, SDO

from knowledgebase_processor.main import KnowledgeBaseProcessor
from knowledgebase_processor.models.content import Document


class TestKnowledgeBaseProcessorIntegration(unittest.TestCase):
    """Test cases for the Knowledge Base Processor integration."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for the knowledge base
        self.temp_dir = tempfile.mkdtemp()
        self.temp_dir_obj = Path(self.temp_dir)
        
        # Define path for the metadata SQLite database file
        # The directory for the SQLite DB file must exist.
        metadata_store_parent_dir = Path(self.temp_dir) / ".metadata_db_storage"
        metadata_store_parent_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_db_file_path = metadata_store_parent_dir / "kb_integration_test.db"
        
        self.rdf_output_dir = self.temp_dir_obj / "rdf_output"

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
    @unittest.skip("Spacy entity recognition disabled - test skipped")
    def test_todo_item_extraction_to_rdf(self):
        """Test that ToDo items are extracted and entities are converted to RDF."""
        fixture_filename = "daily-note-2024-11-07-Thursday.md"
        # Correctly get path to original fixture
        original_fixture_path = Path(__file__).resolve().parent / "fixtures" / "todo_extraction" / fixture_filename
        
        # Copy fixture to a subdirectory in temp_dir_obj to match pattern
        temp_fixture_subdir = self.temp_dir_obj / "todo_files" # Uses self.temp_dir_obj
        temp_fixture_subdir.mkdir(parents=True, exist_ok=True)
        destination_fixture_path = temp_fixture_subdir / fixture_filename
        shutil.copy(original_fixture_path, destination_fixture_path)

        # Define the pattern to match only this fixture file
        # The pattern is relative to knowledge_base_path (self.temp_dir_obj)
        pattern_for_fixture = f"todo_files/{fixture_filename}"

        # Process the fixture file and generate RDF
        # self.processor.base_path is already a Path object (self.temp_dir_obj)
        exit_code = self.processor.processor.process_and_generate_rdf(
            reader=self.processor.reader,
            metadata_store=self.processor.metadata_store,
            pattern=pattern_for_fixture,
            knowledge_base_path=self.processor.base_path,
            rdf_output_dir_str=str(self.rdf_output_dir) # Uses self.rdf_output_dir
        )
        self.assertEqual(exit_code, 0, "Processing and RDF generation for fixture failed.")

        # Check if the RDF file was created
        expected_rdf_file = self.rdf_output_dir / fixture_filename.replace(".md", ".ttl")
        self.assertTrue(expected_rdf_file.exists(), f"RDF file {expected_rdf_file} was not created.")
        self.assertGreater(expected_rdf_file.stat().st_size, 0, f"RDF file {expected_rdf_file} is empty.")

        # Load the generated RDF graph
        rdf_graph = Graph()
        rdf_graph.parse(str(expected_rdf_file), format="turtle")
        
        # Check for KbPerson entities
        persons_found = list(rdf_graph.subjects(predicate=RDF.type, object=KB.Person))
        self.assertGreater(len(persons_found), 0, "No kb:Person found in the RDF graph from the fixture.")
        # Example check for a specific person if known from fixture
        # self.assertTrue(any(str(s).endswith("John_Doe_...") for s in persons_found), "John Doe not found")


        # Check for KbDateEntity entities
        dates_found = list(rdf_graph.subjects(predicate=RDF.type, object=KB.DateEntity))
        self.assertGreater(len(dates_found), 0, "No kb:DateEntity found in the RDF graph from the fixture.")
        # Example check for a specific date if known
        # self.assertTrue(any(str(s).endswith("2024_11_08_...") for s in dates_found), "Date 2024-11-08 not found")

        # Check for KbOrganization (Project Alpha might be one)
        orgs_found = list(rdf_graph.subjects(predicate=RDF.type, object=KB.Organization))
        self.assertGreater(len(orgs_found), 0, "No kb:Organization found in the RDF graph from the fixture.")

        # Check for KbTodoItem entities and specifically for "Journalling"
        todo_items_found = list(rdf_graph.subjects(predicate=RDF.type, object=KB.TodoItem))
        self.assertGreater(len(todo_items_found), 0, "No kb:TodoItem found in the RDF graph from the fixture.")

        found_journaling_todo = False
        # Assuming the description/text of the TodoItem is mapped to KB.description
        # If this fails, the predicate might be different (e.g., RDFS.label or a custom one)
        for todo_item_uri in todo_items_found:
            for s, p, o in rdf_graph.triples((todo_item_uri, SDO.description, None)):
                if str(o) == "Journaling":
                    found_journaling_todo = True
                    break
            if found_journaling_todo:
                break
        
        self.assertTrue(found_journaling_todo, "TodoItem with description 'Journalling' not found in the RDF graph.")


if __name__ == "__main__":
    unittest.main()