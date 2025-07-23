import hashlib
import base64
import re
from urllib.parse import urljoin, quote

class EntityIdGenerator:
    """
    Generates deterministic, unique identifiers for knowledge base entities.
    """

    def __init__(self, base_url: str):
        """
        Initializes the ID generator with a base URL for constructing URIs.

        Args:
            base_url: The base URL for the knowledge base (e.g., "http://example.org/kb/").
        """
        if not base_url.endswith('/'):
            base_url += '/'
        self.base_url = base_url

    def _generate_deterministic_hash(self, *parts: str) -> str:
        """
        Creates a short, URL-safe hash from a set of input strings.
        """
        combined_string = "".join(parts)
        # Use SHA-256 for a strong hash
        sha256_hash = hashlib.sha256(combined_string.encode('utf-8')).digest()
        # Use URL-safe base64 encoding and take the first 16 characters for a reasonable length
        return base64.urlsafe_b64encode(sha256_hash).decode('utf-8').rstrip('=')[:16]

    def generate_document_id(self, normalized_path: str) -> str:
        """
        Generates a unique, deterministic URI for a document entity.

        Args:
            normalized_path: The normalized, unique path of the document.

        Returns:
            A full URI for the document entity.
        """
        # Sanitize the path for use in a URI
        safe_path = quote(normalized_path)
        return urljoin(self.base_url, f"documents/{safe_path}")

    def generate_wikilink_id(self, source_document_id: str, original_text: str) -> str:
        """
        Generates a unique, deterministic URI for a WikiLink entity.

        The ID is based on the source document and the original link text to ensure
        uniqueness within that document context.

        Args:
            source_document_id: The unique ID of the document containing the link.
            original_text: The exact original text of the wikilink (e.g., "[[...]]").

        Returns:
            A full URI for the WikiLink entity.
        """
        link_hash = self._generate_deterministic_hash(source_document_id, original_text)
        return urljoin(self.base_url, f"wikilinks/{link_hash}")

    def generate_todo_id(self, source_document_id: str, todo_text: str) -> str:
        """
        Generates a unique, human-readable URI for a TodoItem entity.

        The ID is based on the source document URI and the normalized todo text (excluding
        checkbox state) to ensure stability even when the todo's completion status changes.

        Pattern: DOCUMENT_IRI + "/todo/" + normalized_todo_text

        Args:
            source_document_id: The unique ID/URI of the document containing the todo.
            todo_text: The text content of the todo item (without checkbox).

        Returns:
            A full URI for the TodoItem entity.
        """
        # Normalize the todo text for use in URI
        # - Strip whitespace
        # - Replace spaces with hyphens
        # - Remove special characters but keep alphanumeric and hyphens
        # - Convert to lowercase for consistency
        normalized_text = todo_text.strip().lower()
        # Remove special characters except alphanumeric, spaces, and hyphens
        normalized_text = re.sub(r'[^\w\s-]', '', normalized_text)
        # Replace multiple spaces with single space
        normalized_text = re.sub(r'\s+', ' ', normalized_text)
        # Replace spaces with hyphens for URI-friendly format
        normalized_text = normalized_text.replace(' ', '-')
        # Remove multiple consecutive hyphens
        normalized_text = re.sub(r'-+', '-', normalized_text)
        # Remove leading/trailing hyphens
        normalized_text = normalized_text.strip('-')
        
        # Ensure the text is not empty after normalization
        if not normalized_text:
            normalized_text = "unnamed-todo"
        
        # If source_document_id is already a full URI, append to it
        # Otherwise, construct from base URL
        if source_document_id.startswith('http://') or source_document_id.startswith('https://'):
            # Remove trailing slash if present
            doc_uri = source_document_id.rstrip('/')
            return f"{doc_uri}/todo/{normalized_text}"
        else:
            # Fallback: construct from base URL
            return urljoin(self.base_url, f"documents/{source_document_id}/todo/{normalized_text}")