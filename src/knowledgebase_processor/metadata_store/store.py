"""Metadata store implementation using SQLite."""

import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..models.metadata import DocumentMetadata, Frontmatter # Added Frontmatter
from ..models.entities import ExtractedEntity
from ..models.links import Link, WikiLink

logger = logging.getLogger(__name__)


from .interface import MetadataStoreInterface

class SQLiteMetadataStore(MetadataStoreInterface):
    """Store for document metadata using an SQLite database."""

    def __init__(self, db_path: str = "knowledgebase.db"):
        """Initialize the SQLiteMetadataStore and connect to the SQLite database.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = Path(db_path)
        self.conn = None
        self.cursor = None

        db_existed = self.db_path.exists()

        if not db_existed:
            logger.info(f"Database file not found at {self.db_path}. Attempting to initialize new database.")
            try:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Ensured parent directory exists: {self.db_path.parent}")
            except OSError as e:
                logger.error(f"Could not create parent directory for database {self.db_path.parent}: {e}")
                # We might still be able to create the DB if the path is in the current dir,
                # so we don't raise here but let connect() fail if it must.
        else:
            logger.info(f"Connecting to existing database at {self.db_path}")

        try:
            self._connect()
            # If connection is successful, self.conn will be set
            if self.conn:
                self._create_tables() # Ensures tables exist, whether DB is new or old
                if not db_existed:
                    logger.info(f"Successfully initialized new database and created tables at {self.db_path}")
                else:
                    logger.info(f"Successfully connected to existing database and ensured tables exist at {self.db_path}")
            else:
                # This case should ideally be covered by _connect() raising an exception
                logger.error(f"Database connection attempt failed for {self.db_path}. Store is not operational.")
                # No further action like _create_tables() if connection failed.

        except RuntimeError as e: # Catch error from _connect()
            logger.error(f"Failed to initialize SQLiteMetadataStore due to connection error: {e}")
            # self.conn remains None, store is not operational.

    def _connect(self):
        """Establish a connection to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Access columns by name
            self.cursor = self.conn.cursor()
            logger.debug(f"Successfully established database connection: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database {self.db_path}: {e}")
            self.conn = None # Ensure conn is None on failure
            self.cursor = None
            # Raise a more specific error or a custom one to be caught by __init__
            raise RuntimeError(f"Failed to connect to database {self.db_path}") from e

    def _create_tables(self):
        """Create database tables if they don't already exist."""
        if not self.conn or not self.cursor:
            logger.error("Cannot create tables: no active database connection.")
            return # Do not proceed if connection isn't there

        try:
            logger.debug(f"Ensuring tables exist in {self.db_path}...")
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
            logger.debug(f"Tables ensured/created successfully in {self.db_path}.")
        except sqlite3.Error as e:
            logger.error(f"Error creating tables in {self.db_path}: {e}")
            if self.conn: # Attempt rollback only if connection exists
                try:
                    self.conn.rollback()
                except sqlite3.Error as rb_err:
                    logger.error(f"Error during rollback after table creation failure: {rb_err}")
            # Propagate the error so the caller knows table creation failed.
            raise RuntimeError(f"Failed to create tables in {self.db_path}") from e


    def save(self, metadata: DocumentMetadata) -> None:
        """Save metadata to the SQLite database.

        Args:
            metadata: The metadata to save
        """
        if not self.conn or not self.cursor:
            logger.warning("No active DB connection in save(). Attempting to reconnect.")
            try:
                self._connect()
            except RuntimeError as e:
                 logger.error(f"Failed to reconnect in save(): {e}. Cannot save metadata.")
                 raise # Re-raise to indicate save failure
            if not self.conn: # Still no connection
                logger.error("Reconnection failed in save(). Cannot save metadata.")
                raise RuntimeError("Database connection unavailable for save operation.")


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
                    link_text = wikilink_obj.display_text or wikilink_obj.target_page
                    target_doc_id = None # Placeholder: wikilink_obj.resolved_target_id if available
                    # If wikilink_obj.target is an ID, it could be target_doc_id.
                    # For now, we'll assume target_document_id is not directly available from WikiLink model
                    # and store the raw target in link_text or a dedicated column if schema changes.
                    # Current schema has target_document_id, so if wikilink_obj.target is an ID, use it.
                    # Let's assume wikilink_obj.target might be the ID for now.
                    if isinstance(wikilink_obj.target_page, str) and "/" in wikilink_obj.target_page: # Heuristic for ID-like target
                        target_doc_id = wikilink_obj.target_page

                    self.cursor.execute(
                        """
                        INSERT INTO links (source_document_id, target_document_id, link_text, type)
                        VALUES (?, ?, ?, ?)
                        """,
                        (metadata.document_id, target_doc_id, link_text, 'wikilink')
                    )

            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database error during save operation for document {metadata.document_id}: {e}")
            if self.conn:
                try:
                    self.conn.rollback()
                except sqlite3.Error as rb_err:
                    logger.error(f"Error during rollback after save failure: {rb_err}")
            raise RuntimeError(f"Database error during save for document {metadata.document_id}") from e
        except RuntimeError as e: # Catch connection errors from potential _connect call
            logger.error(f"Save operation failed due to runtime error (likely connection issue): {e}")
            raise # Re-raise to signal failure


    def get(self, document_id: str) -> Optional[DocumentMetadata]:
        """Get metadata for a document from the SQLite database.

        Args:
            document_id: ID of the document

        Returns:
            Metadata object if found, None otherwise
        """
        if not self.conn or not self.cursor:
            logger.warning("No active DB connection in get(). Attempting to reconnect.")
            try:
                self._connect()
            except RuntimeError as e:
                logger.error(f"Failed to reconnect in get(): {e}. Cannot fetch document.")
                return None # Or raise, depending on desired behavior for critical ops
            if not self.conn: # Still no connection
                logger.error("Reconnection failed in get(). Cannot fetch document.")
                return None


        try:
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
        except sqlite3.Error as e:
            logger.error(f"Database error during get operation for document {document_id}: {e}")
            return None # Or raise, depending on desired error handling
        except RuntimeError as e: # Catch connection errors
            logger.error(f"Get operation failed for document {document_id} due to runtime error: {e}")
            return None


    def list_all(self) -> List[str]:
        """List all document IDs from the documents table.
        
        Returns:
            List of document IDs
        """
        if not self.conn or not self.cursor:
            logger.warning("No active DB connection in list_all(). Attempting to reconnect.")
            try:
                self._connect()
            except RuntimeError as e:
                logger.error(f"Failed to reconnect in list_all(): {e}. Cannot list documents.")
                return []
            if not self.conn:
                logger.error("Reconnection failed in list_all(). Cannot list documents.")
                return []
        
        try:
            self.cursor.execute("SELECT document_id FROM documents")
            return [row['document_id'] for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Database error during list_all operation: {e}")
            return []
        except RuntimeError as e: # Catch connection errors
            logger.error(f"List_all operation failed due to runtime error: {e}")
            return []


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
            logger.warning("No active DB connection in search(). Attempting to reconnect.")
            try:
                self._connect()
            except RuntimeError as e:
                logger.error(f"Failed to reconnect in search(): {e}. Cannot perform search.")
                return []
            if not self.conn:
                logger.error("Reconnection failed in search(). Cannot perform search.")
                return []

        results_doc_ids: List[str] = []
        
        try:
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
            
            return results_doc_ids
        except sqlite3.Error as e:
            logger.error(f"Database error during search operation with query {query}: {e}")
            return []
        except RuntimeError as e: # Catch connection errors
            logger.error(f"Search operation failed with query {query} due to runtime error: {e}")
            return []


    def close(self):
        """Close the database connection."""
        if self.conn:
            try:
                self.conn.close()
                logger.info(f"Database connection closed for {self.db_path}")
            except sqlite3.Error as e:
                logger.error(f"Error closing database connection for {self.db_path}: {e}")
            finally: # Ensure these are reset even if close() fails
                self.conn = None
                self.cursor = None
        else:
            logger.debug("Attempted to close an already closed or uninitialized database connection.")


    def __enter__(self):
        # __init__ already handles connection. If it failed, self.conn is None.
        # This context manager doesn't re-attempt connection if __init__ failed.
        if not self.conn:
             # This might happen if __init__ failed to connect.
             # Attempting to connect here could be an option, or rely on __init__.
             # For simplicity, let's assume __init__ sets up a usable state or raises.
             logger.warning("Entering context but database connection was not established during __init__.")
             # raise RuntimeError("Database not connected. Cannot enter context.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # _json_serializer is no longer needed as we are not storing JSON directly in this class.
    # If specific fields from DocumentMetadata need custom serialization before DB storage,
    # that logic will be within the save method.