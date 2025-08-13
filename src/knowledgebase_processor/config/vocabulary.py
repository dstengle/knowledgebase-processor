"""
Vocabulary configuration module.

This module provides access to the KB vocabulary namespace used throughout
the knowledgebase-processor. The vocabulary is maintained in an external
repository and cached locally for deterministic builds.

Usage:
    from knowledgebase_processor.config.vocabulary import KB
    
    # Use the namespace to create URIs
    document_class = KB.Document
    has_tag_property = KB.hasTag
"""

import json
import os
from pathlib import Path
from typing import Optional

from rdflib import Namespace


def get_vocabulary_metadata() -> dict:
    """
    Load vocabulary metadata from VERSION.json.
    
    Returns:
        Dictionary containing vocabulary metadata including namespace URI.
    """
    # Navigate from this file to project root, then to vocabulary directory
    vocab_dir = Path(__file__).parent.parent.parent.parent / "vocabulary"
    version_file = vocab_dir / "VERSION.json"
    
    if version_file.exists():
        with open(version_file, 'r') as f:
            return json.load(f)
    
    # Return default metadata if file doesn't exist
    return {
        "namespace": "http://example.org/kb/vocab#",
        "version": "unknown",
        "source_repository": "https://github.com/dstengle/knowledgebase-vocabulary"
    }


def get_kb_namespace() -> Namespace:
    """
    Get the KB namespace from vocabulary metadata.
    
    This function reads the namespace URI from the VERSION.json file
    in the vocabulary directory. If the file doesn't exist or can't
    be read, it falls back to a default namespace.
    
    The namespace can be overridden using the KB_VOCABULARY_NAMESPACE
    environment variable for testing or special deployments.
    
    Returns:
        rdflib.Namespace object for the KB vocabulary.
    """
    # Check for environment variable override
    env_namespace = os.environ.get('KB_VOCABULARY_NAMESPACE')
    if env_namespace:
        return Namespace(env_namespace)
    
    # Load from metadata
    metadata = get_vocabulary_metadata()
    return Namespace(metadata["namespace"])


def get_vocabulary_file_path() -> Path:
    """
    Get the path to the local vocabulary file.
    
    Returns:
        Path object pointing to the kb.ttl vocabulary file.
    """
    vocab_dir = Path(__file__).parent.parent.parent.parent / "vocabulary"
    return vocab_dir / "kb.ttl"


def validate_vocabulary() -> bool:
    """
    Validate that the vocabulary file exists and is readable.
    
    Returns:
        True if vocabulary is valid and accessible, False otherwise.
    """
    vocab_file = get_vocabulary_file_path()
    
    if not vocab_file.exists():
        return False
    
    try:
        # Try to parse the vocabulary file
        from rdflib import Graph
        g = Graph()
        g.parse(vocab_file, format='turtle')
        return True
    except Exception:
        return False


# Primary export: the KB namespace
KB = get_kb_namespace()

# Additional exports for vocabulary management
__all__ = [
    'KB',
    'get_vocabulary_metadata',
    'get_kb_namespace', 
    'get_vocabulary_file_path',
    'validate_vocabulary'
]