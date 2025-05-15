import unittest
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Set
import tempfile
import os

from knowledgebase_processor.metadata_store.store import MetadataStore
from knowledgebase_processor.models.metadata import DocumentMetadata, Frontmatter
from knowledgebase_processor.models.entities import ExtractedEntity
from knowledgebase_processor.models.links import Link, WikiLink

class TestMetadataStore(unittest.TestCase):

    def setUp(self):
        """Set up for tests. Some tests use in-memory, others use temp files."""
        self.temp_db_instances_paths = [] # To keep track of (store_instance, path_obj) for cleanup
        
        # Default in-memory store for tests not specifically testing file creation
        self.db_path_memory = ":memory:"
        self.store_memory = MetadataStore(db_path=self.db_path_memory)
        # __init__ of MetadataStore now handles _create_tables, so explicit call might be redundant
        # but harmless if _create_tables is idempotent.
        # self.store_memory._create_tables() 

    def tearDown(self):
        """Close database connections and clean up temporary files."""
        if hasattr(self, 'store_memory') and self.store_memory and self.store_memory.conn:
            self.store_memory.close()
        
        for store_instance, file_path_obj in self.temp_db_instances_paths:
            if store_instance and store_instance.conn:
                store_instance.close()
            if file_path_obj and file_path_obj.exists():
                try:
                    # Ensure the connection is closed by the store instance before removing
                    if store_instance and store_instance.conn:
                         store_instance.close() # Double check, though should be closed above
                    os.remove(file_path_obj)
                except OSError as e:
                    # This can happen on Windows if the file is still locked
                    print(f"Warning: Could not remove temp db file {file_path_obj}: {e}")
        self.temp_db_instances_paths = []

    def _create_temp_db_path(self) -> Path:
        """Creates a temporary file path for a database and returns it.
        The file itself is not created by this helper, only its path.
        """
        # Create a named temporary file, close it, and then use its path.
        # This ensures the name is unique and OS handles temp dir.
        # We delete it immediately so MetadataStore can create it.
        fd, path_str = tempfile.mkstemp(suffix=".db", prefix="test_kb_")
        os.close(fd) 
        path_obj = Path(path_str)
        if path_obj.exists(): # Should exist after mkstemp
            os.remove(path_obj) # Remove it so MetadataStore can test creation
        return path_obj

    def test_initialize_new_db_file(self):
        """Test that MetadataStore creates a new DB file and schema if it doesn't exist."""
        temp_db_path = self._create_temp_db_path()
        self.assertFalse(temp_db_path.exists(), "Temporary DB file should not exist before store initialization")

        store = None
        try:
            store = MetadataStore(db_path=str(temp_db_path))
            self.temp_db_instances_paths.append((store, temp_db_path))

            self.assertTrue(temp_db_path.exists(), "DB file should be created by MetadataStore")
            
            # Verify schema by checking for expected tables
            conn_verify = sqlite3.connect(temp_db_path)
            cursor_verify = conn_verify.cursor()
            cursor_verify.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables_in_db = {row[0] for row in cursor_verify.fetchall()}
            conn_verify.close()

            expected_tables = {"documents", "entities", "document_entities", "tags", "document_tags", "tasks", "links"}
            self.assertTrue(expected_tables.issubset(tables_in_db), f"Expected tables {expected_tables} not found in {tables_in_db}")

        finally:
            # Cleanup is handled by tearDown
            pass

    def test_connect_existing_db_file(self):
        """Test that MetadataStore connects to an existing DB file and can use it."""
        temp_db_path = self._create_temp_db_path()
        
        store1 = None
        try:
            # 1. Create an initial store, save data, and close it. This creates the DB file.
            store1 = MetadataStore(db_path=str(temp_db_path))
            # Don't add to self.temp_db_instances_paths yet, will be managed by its own try/finally
            initial_doc = DocumentMetadata(document_id="existing_doc_1", title="Existing Doc")
            store1.save(initial_doc)
        finally:
            if store1 and store1.conn:
                store1.close()
        
        self.assertTrue(temp_db_path.exists(), "DB file should exist after initial setup and store1.close()")

        store2 = None
        try:
            # 2. Create a new store instance pointing to the *existing* DB file.
            store2 = MetadataStore(db_path=str(temp_db_path))
            self.temp_db_instances_paths.append((store2, temp_db_path)) # Now add for cleanup

            # Verify it can read the data saved by the first store
            retrieved_meta = store2.get("existing_doc_1")
            self.assertIsNotNone(retrieved_meta)
            self.assertEqual(retrieved_meta.title, "Existing Doc")

            # Verify it can write new data
            new_doc = DocumentMetadata(document_id="new_doc_in_existing_db", title="New Doc")
            store2.save(new_doc)
            retrieved_new_meta = store2.get("new_doc_in_existing_db")
            self.assertIsNotNone(retrieved_new_meta)
            self.assertEqual(retrieved_new_meta.title, "New Doc")
        finally:
            # Cleanup handled by tearDown
            pass

    # --- Existing tests adapted to use self.store_memory (in-memory DB) ---
    def test_save_and_get_new_document(self):
        store = self.store_memory
        now = datetime.now(timezone.utc)
        doc_meta = DocumentMetadata(
            document_id="test_doc_1",
            title="Test Document 1",
            path="/path/to/test_doc_1.md",
            frontmatter=Frontmatter(
                title="FM Title 1", # This specific FM title might not be directly retrievable if doc_meta.title is set
                date=now,
                tags=["fm_tag1", "fm_tag2"], # These are illustrative; store saves doc_meta.tags
                custom_fields={"custom_key": "custom_value"} # Not stored
            ),
            tags={"tag1", "tag2"},
            links=[Link(url="http://example.com/link1", text="Example Link 1", content="[Example Link 1](http://example.com/link1)")],
            wikilinks=[WikiLink(target_page="Another Doc", display_text="Link to Another Doc", content="[[Another Doc|Link to Another Doc]]")],
            entities=[ExtractedEntity(text="Test Entity", label="PERSON", start_char=0, end_char=10)]
        )

        store.save(doc_meta)
        retrieved_meta = store.get("test_doc_1")

        self.assertIsNotNone(retrieved_meta)
        self.assertEqual(retrieved_meta.document_id, "test_doc_1")
        self.assertEqual(retrieved_meta.title, "Test Document 1") 
        self.assertEqual(retrieved_meta.path, "/path/to/test_doc_1.md")
        
        self.assertIsNotNone(retrieved_meta.frontmatter)
        self.assertEqual(retrieved_meta.frontmatter.title, "Test Document 1") # Reconstructed FM uses doc title
        self.assertEqual(retrieved_meta.frontmatter.date.replace(microsecond=0), now.replace(microsecond=0))
        self.assertEqual(set(retrieved_meta.frontmatter.tags), {"tag1", "tag2"}) # Reconstructed FM uses doc tags

        self.assertEqual(retrieved_meta.tags, {"tag1", "tag2"})
        
        self.assertEqual(len(retrieved_meta.links), 1)
        self.assertEqual(retrieved_meta.links[0].url, "http://example.com/link1")
        self.assertEqual(retrieved_meta.links[0].text, "Example Link 1")
        
        self.assertEqual(len(retrieved_meta.wikilinks), 1)
        self.assertEqual(retrieved_meta.wikilinks[0].target_page, "Another Doc")
        self.assertEqual(retrieved_meta.wikilinks[0].display_text, "Link to Another Doc")

        self.assertEqual(len(retrieved_meta.entities), 1)
        self.assertEqual(retrieved_meta.entities[0].text, "Test Entity")
        self.assertEqual(retrieved_meta.entities[0].label, "PERSON")

    def test_get_non_existent_document(self):
        store = self.store_memory
        retrieved_meta = store.get("non_existent_doc")
        self.assertIsNone(retrieved_meta)

    def test_save_updates_existing_document(self):
        store = self.store_memory
        now = datetime.now(timezone.utc)
        initial_doc_meta = DocumentMetadata(
            document_id="update_doc_1",
            title="Initial Title",
            path="/path/initial.md",
            frontmatter=Frontmatter(date=now),
            tags={"initial_tag"},
        )
        store.save(initial_doc_meta)
        
        retrieved_initial = store.get("update_doc_1")
        self.assertIsNotNone(retrieved_initial)
        
        # Fetch modified_at directly for comparison
        initial_modified_at_str = store.cursor.execute(
            "SELECT modified_at FROM documents WHERE document_id = ?", ("update_doc_1",)
        ).fetchone()['modified_at']
        initial_modified_at = datetime.fromisoformat(initial_modified_at_str)

        updated_doc_meta = DocumentMetadata(
            document_id="update_doc_1", 
            title="Updated Title",
            path="/path/updated.md",
            frontmatter=Frontmatter(date=now), # Keep original date for created_at check
            tags={"updated_tag", "another_tag"},
            entities=[ExtractedEntity(text="Updated Entity", label="ORG", start_char=0, end_char=0)]
        )
        store.save(updated_doc_meta)

        retrieved_updated = store.get("update_doc_1")
        self.assertIsNotNone(retrieved_updated)
        self.assertEqual(retrieved_updated.title, "Updated Title")
        self.assertEqual(retrieved_updated.path, "/path/updated.md")
        self.assertEqual(retrieved_updated.tags, {"updated_tag", "another_tag"})
        self.assertEqual(len(retrieved_updated.entities), 1)
        self.assertEqual(retrieved_updated.entities[0].text, "Updated Entity")

        self.assertIsNotNone(retrieved_updated.frontmatter)
        self.assertEqual(retrieved_updated.frontmatter.date.replace(microsecond=0), now.replace(microsecond=0))
        
        updated_modified_at_str = store.cursor.execute(
            "SELECT modified_at FROM documents WHERE document_id = ?", ("update_doc_1",)
        ).fetchone()['modified_at']
        updated_modified_at = datetime.fromisoformat(updated_modified_at_str)
        self.assertTrue(updated_modified_at > initial_modified_at)

    def test_save_document_with_no_frontmatter_date(self):
        store = self.store_memory
        doc_meta_no_fm = DocumentMetadata(
            document_id="no_fm_date_doc",
            title="No FM Date Doc",
            frontmatter=None 
        )
        store.save(doc_meta_no_fm)
        retrieved_meta_1 = store.get("no_fm_date_doc")
        self.assertIsNotNone(retrieved_meta_1)
        self.assertIsNotNone(retrieved_meta_1.frontmatter) 
        self.assertIsNone(retrieved_meta_1.frontmatter.date)

        db_created_at_1 = store.cursor.execute(
            "SELECT created_at FROM documents WHERE document_id = ?", ("no_fm_date_doc",)
        ).fetchone()['created_at']
        self.assertIsNone(db_created_at_1)

        doc_meta_fm_no_date = DocumentMetadata(
            document_id="fm_no_date_doc",
            title="FM No Date Doc",
            frontmatter=Frontmatter(title="FM Title Only") 
        )
        store.save(doc_meta_fm_no_date)
        retrieved_meta_2 = store.get("fm_no_date_doc")
        self.assertIsNotNone(retrieved_meta_2)
        self.assertIsNotNone(retrieved_meta_2.frontmatter)
        self.assertIsNone(retrieved_meta_2.frontmatter.date)
        
        db_created_at_2 = store.cursor.execute(
            "SELECT created_at FROM documents WHERE document_id = ?", ("fm_no_date_doc",)
        ).fetchone()['created_at']
        self.assertIsNone(db_created_at_2)

def test_save_wikilink_triggers_attribute_error(self):
        """
        Tests that saving a DocumentMetadata with a WikiLink that uses
        display_text and target_page (as per the model) triggers an AttributeError
        in the current store.save() method due to incorrect attribute access.
        """
        store = self.store_memory
        wikilink_obj = WikiLink(
            target_page="TargetPage",
            display_text="DisplayText",
            content="[[TargetPage|DisplayText]]"
        )
        doc_meta = DocumentMetadata(
            document_id="wikilink_attr_error_doc",
            title="Wikilink Attribute Error Test",
            wikilinks=[wikilink_obj]
        )

        # Expect AttributeError because store.py tries to access wikilink_obj.text
        with self.assertRaisesRegex(AttributeError, "'WikiLink' object has no attribute 'text'"):
            store.save(doc_meta)
if __name__ == '__main__':
    unittest.main()