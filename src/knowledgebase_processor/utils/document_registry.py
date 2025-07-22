from typing import Dict, Optional
import os

from knowledgebase_processor.models.kb_entities import KbDocument


class DocumentRegistry:
    """
    A registry for managing and looking up document entities by various path representations.
    """

    def __init__(self):
        self._documents_by_id: Dict[str, KbDocument] = {}
        self._id_by_original_path: Dict[str, str] = {}
        self._id_by_path_without_extension: Dict[str, str] = {}
        self._id_by_basename_without_extension: Dict[str, str] = {}

    def register_document(self, document: KbDocument):
        """
        Registers a new document entity, making it available for lookup.

        Args:
            document: The KbDocument entity to register.
        """
        if document.kb_id in self._documents_by_id:
            # Optionally, log a warning or handle updates if re-registration is expected
            return

        self._documents_by_id[document.kb_id] = document
        self._id_by_original_path[document.original_path] = document.kb_id
        self._id_by_path_without_extension[
            document.path_without_extension
        ] = document.kb_id
        
        # Also index by basename without extension for wikilink resolution
        basename_without_ext = os.path.splitext(os.path.basename(document.original_path))[0]
        self._id_by_basename_without_extension[basename_without_ext] = document.kb_id

    def get_document_by_id(self, kb_id: str) -> Optional[KbDocument]:
        """
        Retrieves a document by its unique knowledge base ID.
        """
        return self._documents_by_id.get(kb_id)

    def find_document_by_path(self, path: str) -> Optional[KbDocument]:
        """
        Finds a document by its original path, path without extension, or basename.

        This method allows resolving links where the exact path might vary (e.g., with
        or without a file extension, or just the filename).

        Args:
            path: The path to look up.

        Returns:
            The matching KbDocument, or None if no document is found.
        """
        # First, try a direct lookup by original path
        doc_id = self._id_by_original_path.get(path)
        if doc_id:
            return self.get_document_by_id(doc_id)

        # If not found, try looking up by path without extension
        doc_id = self._id_by_path_without_extension.get(path)
        if doc_id:
            return self.get_document_by_id(doc_id)
        
        # If still not found, try looking up by basename without extension
        # This handles wikilinks that use just the filename
        doc_id = self._id_by_basename_without_extension.get(path)
        if doc_id:
            return self.get_document_by_id(doc_id)

        return None

    def get_all_documents(self) -> list[KbDocument]:
        """
        Returns a list of all registered documents.
        """
        return list(self._documents_by_id.values())