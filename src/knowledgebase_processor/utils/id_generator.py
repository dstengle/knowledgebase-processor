import hashlib
import base64
import re
import unicodedata
from urllib.parse import urljoin, quote

class EntityIdGenerator:
    """
    Generates deterministic, unique identifiers for knowledge base entities.
    
    Implements the normalization rules from ADR-0013:
    1. Unicode NFKD normalization
    2. Convert to lowercase  
    3. Replace non-alphanumeric with hyphens
    4. Remove consecutive hyphens
    5. Trim hyphens from start/end
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

    def _normalize_text_for_id(self, text: str) -> str:
        """
        Normalizes text for use in deterministic IDs according to ADR-0013 rules.
        
        Args:
            text: The text to normalize
            
        Returns:
            Normalized text suitable for use in IDs
        """
        if not text:
            return ""
            
        # 1. Unicode NFKD normalization
        normalized = unicodedata.normalize('NFKD', text)
        
        # 2. Convert to lowercase
        normalized = normalized.lower()
        
        # 3. Replace non-alphanumeric with hyphens
        normalized = re.sub(r'[^a-z0-9]', '-', normalized)
        
        # 4. Remove consecutive hyphens
        normalized = re.sub(r'-+', '-', normalized)
        
        # 5. Trim hyphens from start/end
        normalized = normalized.strip('-')
        
        return normalized

    def _generate_deterministic_hash(self, *parts: str) -> str:
        """
        Creates a short, URL-safe hash from a set of input strings.
        """
        combined_string = "".join(parts)
        # Use SHA-256 for a strong hash
        sha256_hash = hashlib.sha256(combined_string.encode('utf-8')).digest()
        # Use URL-safe base64 encoding and take the first 16 characters for a reasonable length
        return base64.urlsafe_b64encode(sha256_hash).decode('utf-8').rstrip('=')[:16]

    def generate_document_id(self, file_path: str) -> str:
        """
        Generates a unique, deterministic URI for a document entity.
        
        Uses the ADR-0013 pattern: /Document/{normalized-file-path}

        Args:
            file_path: The original file path of the document.

        Returns:
            A full URI for the document entity.
        """
        # Normalize the file path using ADR-0013 rules
        normalized_path = self._normalize_text_for_id(file_path)
        
        # Remove file extension for the ID
        if '.' in normalized_path:
            normalized_path = normalized_path.rsplit('.', 1)[0]
        
        return urljoin(self.base_url, f"Document/{normalized_path}")

    def generate_placeholder_document_id(self, title: str) -> str:
        """
        Generates a unique, deterministic URI for a placeholder document entity.
        
        Uses the ADR-0013 pattern: /PlaceholderDocument/{normalized-name}

        Args:
            title: The title or name of the placeholder document.

        Returns:
            A full URI for the placeholder document entity.
        """
        normalized_name = self._normalize_text_for_id(title)
        return urljoin(self.base_url, f"PlaceholderDocument/{normalized_name}")

    def generate_person_id(self, name: str) -> str:
        """
        Generates a unique, deterministic URI for a person entity.
        
        Uses the ADR-0013 pattern: /Person/{normalized-name}

        Args:
            name: The person's name.

        Returns:
            A full URI for the person entity.
        """
        normalized_name = self._normalize_text_for_id(name)
        return urljoin(self.base_url, f"Person/{normalized_name}")

    def generate_organization_id(self, name: str) -> str:
        """
        Generates a unique, deterministic URI for an organization entity.
        
        Uses the ADR-0013 pattern: /Organization/{normalized-name}

        Args:
            name: The organization's name.

        Returns:
            A full URI for the organization entity.
        """
        normalized_name = self._normalize_text_for_id(name)
        return urljoin(self.base_url, f"Organization/{normalized_name}")

    def generate_location_id(self, name: str) -> str:
        """
        Generates a unique, deterministic URI for a location entity.
        
        Uses the ADR-0013 pattern: /Location/{normalized-name}

        Args:
            name: The location's name.

        Returns:
            A full URI for the location entity.
        """
        normalized_name = self._normalize_text_for_id(name)
        return urljoin(self.base_url, f"Location/{normalized_name}")

    def generate_project_id(self, name: str) -> str:
        """
        Generates a unique, deterministic URI for a project entity.
        
        Uses the ADR-0013 pattern: /Project/{normalized-name}

        Args:
            name: The project's name.

        Returns:
            A full URI for the project entity.
        """
        normalized_name = self._normalize_text_for_id(name)
        return urljoin(self.base_url, f"Project/{normalized_name}")

    def generate_tag_id(self, name: str) -> str:
        """
        Generates a unique, deterministic URI for a tag entity.
        
        Uses the ADR-0013 pattern: /Tag/{normalized-name}

        Args:
            name: The tag's name.

        Returns:
            A full URI for the tag entity.
        """
        normalized_name = self._normalize_text_for_id(name)
        return urljoin(self.base_url, f"Tag/{normalized_name}")

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

    def generate_markdown_element_id(self, element_type: str, identifier: str, source_document_id: str) -> str:
        """
        Generates a unique, deterministic URI for a markdown structure element.

        Pattern: DOCUMENT_IRI + "/{element_type}/" + normalized_identifier

        Args:
            element_type: The type of markdown element (e.g., 'heading', 'section', 'list', etc.)
            identifier: A unique identifier for the element (e.g., heading text, element ID)
            source_document_id: The unique ID/URI of the document containing the element

        Returns:
            A full URI for the markdown element entity.
        """
        normalized_identifier = self._normalize_text_for_id(identifier)

        # Ensure the identifier is not empty
        if not normalized_identifier:
            normalized_identifier = "unnamed-element"

        # Limit identifier length to keep URIs reasonable
        if len(normalized_identifier) > 100:
            normalized_identifier = normalized_identifier[:100]

        # If source_document_id is already a full URI, append to it
        # Otherwise, construct from base URL
        if source_document_id.startswith('http://') or source_document_id.startswith('https://'):
            # Remove trailing slash if present
            doc_uri = source_document_id.rstrip('/')
            return f"{doc_uri}/{element_type}/{normalized_identifier}"
        else:
            # Fallback: construct from base URL
            return urljoin(self.base_url, f"documents/{source_document_id}/{element_type}/{normalized_identifier}")