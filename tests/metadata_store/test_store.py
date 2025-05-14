import unittest
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Set

from knowledgebase_processor.metadata_store.store import MetadataStore
from knowledgebase_processor.models.metadata import DocumentMetadata, Frontmatter
from knowledgebase_processor.models.entities import ExtractedEntity
from knowledgebase_processor.models.links import Link, WikiLink

class TestMetadataStore(unittest.TestCase):

    def setUp(self):
        """Set up an in-memory SQLite database for each test."""
        self.db_path = ":memory:"
        self.store = MetadataStore(db_path=self.db_path)
        # Ensure tables are created (though __init__ does this)
        self.store._create_tables()

    def tearDown(self):
        """Close the database connection after each test."""
        self.store.close()

    def test_save_and_get_new_document(self):
        """Test saving a new document and retrieving it."""
        now = datetime.now(timezone.utc)
        doc_meta = DocumentMetadata(
            document_id="test_doc_1",
            title="Test Document 1",
            path="/path/to/test_doc_1.md",
            frontmatter=Frontmatter(
                title="FM Title 1",
                date=now,
                tags=["fm_tag1", "fm_tag2"],
                custom_fields={"custom_key": "custom_value"}
            ),
            tags={"tag1", "tag2"},
            links=[Link(url="http://example.com/link1", text="Example Link 1")],
            wikilinks=[WikiLink(target="Another Doc", text="Link to Another Doc")],
            entities=[ExtractedEntity(text="Test Entity", label="PERSON", start_char=0, end_char=10)]
        )

        self.store.save(doc_meta)
        retrieved_meta = self.store.get("test_doc_1")

        self.assertIsNotNone(retrieved_meta)
        self.assertEqual(retrieved_meta.document_id, "test_doc_1")
        self.assertEqual(retrieved_meta.title, "Test Document 1") # Title from doc_meta.title
        self.assertEqual(retrieved_meta.path, "/path/to/test_doc_1.md")
        
        # Verify frontmatter (partially, as not all fields are stored directly)
        self.assertIsNotNone(retrieved_meta.frontmatter)
        self.assertEqual(retrieved_meta.frontmatter.title, "Test Document 1") # Title in FM is doc title
        self.assertEqual(retrieved_meta.frontmatter.date.replace(microsecond=0), now.replace(microsecond=0))
        self.assertEqual(set(retrieved_meta.frontmatter.tags), {"tag1", "tag2"}) # Uses all doc tags

        self.assertEqual(retrieved_meta.tags, {"tag1", "tag2"})
        
        self.assertEqual(len(retrieved_meta.links), 1)
        self.assertEqual(retrieved_meta.links[0].url, "http://example.com/link1")
        
        self.assertEqual(len(retrieved_meta.wikilinks), 1)
        self.assertEqual(retrieved_meta.wikilinks[0].target, "Another Doc")

        self.assertEqual(len(retrieved_meta.entities), 1)
        self.assertEqual(retrieved_meta.entities[0].text, "Test Entity")
        self.assertEqual(retrieved_meta.entities[0].label, "PERSON")

    def test_get_non_existent_document(self):
        """Test getting a document that does not exist."""
        retrieved_meta = self.store.get("non_existent_doc")
        self.assertIsNone(retrieved_meta)

    def test_save_updates_existing_document(self):
        """Test that saving an existing document updates it."""
        now = datetime.now(timezone.utc)
        initial_doc_meta = DocumentMetadata(
            document_id="update_doc_1",
            title="Initial Title",
            path="/path/initial.md",
            frontmatter=Frontmatter(date=now),
            tags={"initial_tag"},
        )
        self.store.save(initial_doc_meta)
        
        retrieved_initial = self.store.get("update_doc_1")
        self.assertIsNotNone(retrieved_initial)
        initial_modified_at_str = self.store.cursor.execute(
            "SELECT modified_at FROM documents WHERE document_id = ?", ("update_doc_1",)
        ).fetchone()['modified_at']
        initial_modified_at = datetime.fromisoformat(initial_modified_at_str)

        # Make some changes and save again
        # Simulate a slight delay for modified_at to change
        # In a real scenario, time.sleep might be too flaky for tests.
        # For robustness, one might mock datetime.now() or check that modified_at is GREATER.
        # Here, we rely on the fact that save() generates a new datetime.now().

        updated_doc_meta = DocumentMetadata(
            document_id="update_doc_1", # Same ID
            title="Updated Title",
            path="/path/updated.md",
            frontmatter=Frontmatter(date=now), # Keep original date for created_at check
            tags={"updated_tag", "another_tag"},
            entities=[ExtractedEntity(text="Updated Entity", label="ORG", start_char=0, end_char=0)]
        )
        self.store.save(updated_doc_meta)

        retrieved_updated = self.store.get("update_doc_1")
        self.assertIsNotNone(retrieved_updated)
        self.assertEqual(retrieved_updated.title, "Updated Title")
        self.assertEqual(retrieved_updated.path, "/path/updated.md")
        self.assertEqual(retrieved_updated.tags, {"updated_tag", "another_tag"})
        self.assertEqual(len(retrieved_updated.entities), 1)
        self.assertEqual(retrieved_updated.entities[0].text, "Updated Entity")

        # Check created_at is preserved (from initial frontmatter.date)
        self.assertIsNotNone(retrieved_updated.frontmatter)
        self.assertEqual(retrieved_updated.frontmatter.date.replace(microsecond=0), now.replace(microsecond=0))
        
        # Check modified_at has changed (or is later)
        updated_modified_at_str = self.store.cursor.execute(
            "SELECT modified_at FROM documents WHERE document_id = ?", ("update_doc_1",)
        ).fetchone()['modified_at']
        updated_modified_at = datetime.fromisoformat(updated_modified_at_str)
        self.assertTrue(updated_modified_at > initial_modified_at)

    def test_save_document_with_no_frontmatter_date(self):
        """Test saving a document where frontmatter or its date is None."""
        doc_meta = DocumentMetadata(
            document_id="no_fm_date_doc",
            title="No FM Date Doc",
            frontmatter=None # No frontmatter at all
        )
        self.store.save(doc_meta)
        retrieved_meta = self.store.get("no_fm_date_doc")
        self.assertIsNotNone(retrieved_meta)
        self.assertIsNotNone(retrieved_meta.frontmatter) # get reconstructs a basic one
        self.assertIsNone(retrieved_meta.frontmatter.date) # Date should be None

        # Check created_at in DB is NULL
        db_created_at = self.store.cursor.execute(
            "SELECT created_at FROM documents WHERE document_id = ?", ("no_fm_date_doc",)
        ).fetchone()['created_at']
        self.assertIsNone(db_created_at)

        doc_meta_fm_no_date = DocumentMetadata(
            document_id="fm_no_date_doc",
            title="FM No Date Doc",
            frontmatter=Frontmatter(title="FM Title") # Frontmatter exists, but no date field
        )
        self.store.save(doc_meta_fm_no_date)
        retrieved_meta_2 = self.store.get("fm_no_date_doc")
        self.assertIsNotNone(retrieved_meta_2)
        self.assertIsNotNone(retrieved_meta_2.frontmatter)
        self.assertIsNone(retrieved_meta_2.frontmatter.date)
        
        db_created_at_2 = self.store.cursor.execute(
            "SELECT created_at FROM documents WHERE document_id = ?", ("fm_no_date_doc",)
        ).fetchone()['created_at']
        self.assertIsNone(db_created_at_2)

if __name__ == '__main__':
    unittest.main()