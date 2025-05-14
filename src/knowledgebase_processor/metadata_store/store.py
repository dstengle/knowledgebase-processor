"""Metadata store implementation using SQLite."""

import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models.metadata import DocumentMetadata, Frontmatter # Added Frontmatter
from ..models.entities import ExtractedEntity
from ..models.links import Link, WikiLink


class MetadataStore:
    """Store for document metadata using an SQLite database."""

    def __init__(self, db_path: str = "knowledgebase.db"):
        """Initialize the MetadataStore and connect to the SQLite database.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = Path(db_path)
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Establish a connection to the SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row # Access columns by name
        self.cursor = self.conn.cursor()

    def _create_tables(self):
        """Create database tables if they don't already exist."""
        # Schema based on ADR-0007
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            document_id TEXT PRIMARY KEY,
            file_path TEXT,
            title TEXT,
            created_at TEXT,
            modified_at TEXT,
            raw_content TEXT
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            UNIQUE(name, type)
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_entities (
            document_id TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            PRIMARY KEY (document_id, entity_id),
            FOREIGN KEY (document_id) REFERENCES documents (document_id) ON DELETE CASCADE,
            FOREIGN KEY (entity_id) REFERENCES entities (entity_id) ON DELETE CASCADE
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_tags (
            document_id TEXT NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (document_id, tag_id),
            FOREIGN KEY (document_id) REFERENCES documents (document_id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (tag_id) ON DELETE CASCADE
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT,
            description TEXT NOT NULL,
            status TEXT,
            due_date TEXT,
            context TEXT,
            FOREIGN KEY (document_id) REFERENCES documents (document_id) ON DELETE CASCADE
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS links (
            link_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_document_id TEXT NOT NULL,
            target_document_id TEXT,
            target_url TEXT,
            link_text TEXT,
            type TEXT NOT NULL, -- e.g., 'wikilink', 'url'
            FOREIGN KEY (source_document_id) REFERENCES documents (document_id) ON DELETE CASCADE
        )
        """)
        self.conn.commit()

    def save(self, metadata: DocumentMetadata) -> None:
        """Save metadata to the SQLite database.

        Args:
            metadata: The metadata to save
        """
        if not self.conn or not self.cursor:
            self._connect()

        try:
            self.cursor.execute("BEGIN")

            # 1. Save document details
            doc_title = metadata.title
            if not doc_title and metadata.frontmatter:
                doc_title = metadata.frontmatter.title

            created_at_iso = None
            if metadata.frontmatter and metadata.frontmatter.date:
                created_at_iso = metadata.frontmatter.date.isoformat()
            
            modified_at_iso = datetime.now().isoformat()

            self.cursor.execute(
                """
                INSERT INTO documents (document_id, file_path, title, created_at, modified_at, raw_content)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    file_path = excluded.file_path,
                    title = excluded.title,
                    created_at = CASE WHEN documents.created_at IS NULL THEN excluded.created_at ELSE documents.created_at END, -- Preserve original created_at
                    modified_at = excluded.modified_at,
                    raw_content = excluded.raw_content;
                """,
                (
                    metadata.document_id,
                    metadata.path,
                    doc_title,
                    created_at_iso, # Will be used if new, or if old created_at was NULL
                    modified_at_iso,
                    None,  # raw_content is not in DocumentMetadata
                ),
            )

            # 2. Clear existing associations for this document to handle updates/deletions of specific items
            self.cursor.execute("DELETE FROM document_tags WHERE document_id = ?", (metadata.document_id,))
            self.cursor.execute("DELETE FROM document_entities WHERE document_id = ?", (metadata.document_id,))
            self.cursor.execute("DELETE FROM links WHERE source_document_id = ?", (metadata.document_id,))
            # Tasks are not yet in DocumentMetadata, so no clearing needed for now.

            # 3. Save tags and associations
            if metadata.tags:
                for tag_name_str in metadata.tags:
                    self.cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name_str,))
                    self.cursor.execute("SELECT tag_id FROM tags WHERE name = ?", (tag_name_str,))
                    tag_id_row = self.cursor.fetchone()
                    if tag_id_row:
                        tag_id = tag_id_row['tag_id']
                        self.cursor.execute(
                            "INSERT INTO document_tags (document_id, tag_id) VALUES (?, ?)",
                            (metadata.document_id, tag_id),
                        )

            # 4. Save entities and associations
            if metadata.entities:
                # Keep track of entity IDs already linked to this document in this save operation
                # to prevent duplicate insertions if metadata.entities has duplicates.
                processed_entity_ids_for_doc = set()
                for entity_obj in metadata.entities:
                    # Assuming ExtractedEntity has 'text' for name and 'label' for type
                    entity_name = entity_obj.text
                    entity_type = entity_obj.label
                    self.cursor.execute(
                        "INSERT OR IGNORE INTO entities (name, type) VALUES (?, ?)", (entity_name, entity_type)
                    )
                    self.cursor.execute("SELECT entity_id FROM entities WHERE name = ? AND type = ?", (entity_name, entity_type))
                    entity_id_row = self.cursor.fetchone()
                    if entity_id_row:
                        entity_id = entity_id_row['entity_id']
                        if entity_id not in processed_entity_ids_for_doc:
                            self.cursor.execute(
                                "INSERT INTO document_entities (document_id, entity_id) VALUES (?, ?)",
                                (metadata.document_id, entity_id),
                            )
                            processed_entity_ids_for_doc.add(entity_id)
            
            # 5. Save links (URL links)
            if metadata.links:
                for link_obj in metadata.links:
                    # Assuming Link has 'url' and 'text'
                    self.cursor.execute(
                        """
                        INSERT INTO links (source_document_id, target_url, link_text, type)
                        VALUES (?, ?, ?, ?)
                        """,
                        (metadata.document_id, link_obj.url, getattr(link_obj, 'text', None) or getattr(link_obj, 'title', None) or link_obj.url, 'url')
                    )

            # 6. Save wikilinks
            if metadata.wikilinks:
                for wikilink_obj in metadata.wikilinks:
                    # Assuming WikiLink has 'target' (for target_document_id or part of link_text)
                    # and 'text'. target_document_id might need resolution logic not present here.
                    # For now, storing target as link_text if specific target_id isn't resolved.
                    link_text = wikilink_obj.text or wikilink_obj.target
                    target_doc_id = None # Placeholder: wikilink_obj.resolved_target_id if available
                    # If wikilink_obj.target is an ID, it could be target_doc_id.
                    # For now, we'll assume target_document_id is not directly available from WikiLink model
                    # and store the raw target in link_text or a dedicated column if schema changes.
                    # Current schema has target_document_id, so if wikilink_obj.target is an ID, use it.
                    # Let's assume wikilink_obj.target might be the ID for now.
                    if isinstance(wikilink_obj.target, str) and "/" in wikilink_obj.target: # Heuristic for ID-like target
                        target_doc_id = wikilink_obj.target

                    self.cursor.execute(
                        """
                        INSERT INTO links (source_document_id, target_document_id, link_text, type)
                        VALUES (?, ?, ?, ?)
                        """,
                        (metadata.document_id, target_doc_id, link_text, 'wikilink')
                    )

            self.conn.commit()
        except sqlite3.Error as e:
            if self.conn:
                self.conn.rollback()
            # Re-raise or handle appropriately
            raise RuntimeError(f"Database error during save: {e}") from e

    def get(self, document_id: str) -> Optional[DocumentMetadata]:
        """Get metadata for a document from the SQLite database.

        Args:
            document_id: ID of the document

        Returns:
            Metadata object if found, None otherwise
        """
        if not self.conn or not self.cursor:
            self._connect()

        self.cursor.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,))
        doc_row = self.cursor.fetchone()

        if not doc_row:
            return None

        # Fetch tags
        self.cursor.execute("""
            SELECT t.name FROM tags t
            JOIN document_tags dt ON t.tag_id = dt.tag_id
            WHERE dt.document_id = ?
        """, (document_id,))
        tags_set = {row['name'] for row in self.cursor.fetchall()}

        # Fetch entities
        self.cursor.execute("""
            SELECT e.name, e.type FROM entities e
            JOIN document_entities de ON e.entity_id = de.entity_id
            WHERE de.document_id = ?
        """, (document_id,))
        entities_list = [ExtractedEntity(text=row['name'], label=row['type'], start_char=0, end_char=0) # start/end_char not stored
                         for row in self.cursor.fetchall()]

        # Fetch links (both URL and wikilinks)
        self.cursor.execute("""
            SELECT target_document_id, target_url, link_text, type FROM links
            WHERE source_document_id = ?
        """, (document_id,))
        
        links_list: List[Link] = []
        wikilinks_list: List[WikiLink] = []
        for link_row in self.cursor.fetchall():
            link_text = link_row['link_text']
            if link_row['type'] == 'url':
                target_url = link_row['target_url']
                text_val = link_text or target_url
                # Reconstruct content for Link
                reconstructed_content = f"[{text_val}]({target_url})"
                links_list.append(Link(url=target_url, text=text_val, content=reconstructed_content))
            elif link_row['type'] == 'wikilink':
                target_page = link_row['target_document_id'] or link_text # target_page from WikiLink model
                display_text_val = link_text or target_page # display_text from WikiLink model
                # Reconstruct content for WikiLink
                if target_page == display_text_val:
                    reconstructed_content = f"[[{target_page}]]"
                else:
                    reconstructed_content = f"[[{target_page}|{display_text_val}]]"
                wikilinks_list.append(WikiLink(target_page=target_page,
                                               display_text=display_text_val,
                                               content=reconstructed_content))

        # Reconstruct Frontmatter (partially)
        frontmatter_obj = None
        fm_title = doc_row['title'] # Title from document table might be from frontmatter or overridden
        fm_date = None
        if doc_row['created_at']:
            try:
                fm_date = datetime.fromisoformat(doc_row['created_at'])
            except ValueError: # Handle cases where created_at might not be a valid ISO format
                fm_date = None
        
        # We don't store frontmatter tags separately from document tags in this schema,
        # and custom_fields are not stored.
        frontmatter_obj = Frontmatter(
            title=fm_title, # This might not be the original frontmatter title if document title was different
            date=fm_date,
            tags=list(tags_set), # Using all document tags for simplicity here
            custom_fields={} # Not stored
        )


        return DocumentMetadata(
            document_id=doc_row['document_id'],
            title=doc_row['title'],
            path=doc_row['file_path'],
            frontmatter=frontmatter_obj,
            tags=tags_set,
            links=links_list,
            wikilinks=wikilinks_list,
            entities=entities_list,
            references=[], # Not stored
            structure={}    # Not stored
        )

    def list_all(self) -> List[str]:
        """List all document IDs from the documents table.
        
        Returns:
            List of document IDs
        """
        self.cursor.execute("SELECT document_id FROM documents")
        return [row['document_id'] for row in self.cursor.fetchall()]

    def search(self, query: Dict[str, Any]) -> List[str]: # Return type changed to List[str] for document_ids
        """Search for documents matching the query in the SQLite database.

        Args:
            query: Dictionary of search criteria.
                   Currently supports:
                   - {'tags': 'tag_name'} to find documents with a specific tag.
                   - {'title_contains': 'text'} to find documents where title contains text.
                   More complex queries can be added later.

        Returns:
            List of matching document IDs.
        """
        if not self.conn or not self.cursor:
            self._connect()

        results_doc_ids: List[str] = []
        
        if 'tags' in query and isinstance(query['tags'], str):
            tag_name = query['tags']
            self.cursor.execute("""
                SELECT dt.document_id FROM document_tags dt
                JOIN tags t ON dt.tag_id = t.tag_id
                WHERE t.name = ?
            """, (tag_name,))
            results_doc_ids = [row['document_id'] for row in self.cursor.fetchall()]
        
        elif 'title_contains' in query and isinstance(query['title_contains'], str):
            search_text = f"%{query['title_contains']}%"
            self.cursor.execute("""
                SELECT document_id FROM documents
                WHERE title LIKE ?
            """, (search_text,))
            results_doc_ids = [row['document_id'] for row in self.cursor.fetchall()]

        # To return List[DocumentMetadata] as originally intended, we would call self.get() for each ID.
        # For now, returning IDs as per the immediate need of QueryInterface.find_by_tag
        # and to avoid circular calls if search itself calls get.
        # If DocumentMetadata objects are needed, the caller (e.g., QueryInterface) can fetch them.
        # Example: return [self.get(doc_id) for doc_id in results_doc_ids if self.get(doc_id) is not None]
        
        # For now, let's keep it simple and return document_ids as QueryInterface.find_by_tag expects.
        # The QueryInterface.search method will need adjustment if it's to return DocumentMetadata.
        return results_doc_ids

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # _json_serializer is no longer needed as we are not storing JSON directly in this class.
    # If specific fields from DocumentMetadata need custom serialization before DB storage,
    # that logic will be within the save method.