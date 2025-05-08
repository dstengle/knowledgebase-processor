"""Text processing utilities for the Knowledge Base Processor."""

import re
from typing import Optional


def clean_text(text: str) -> str:
    """Clean text by removing control characters and normalizing whitespace.
    
    Args:
        text: The text to clean
        
    Returns:
        Cleaned text
    """
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normalize whitespace
    return normalize_whitespace(text)


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text.
    
    Args:
        text: The text to normalize
        
    Returns:
        Text with normalized whitespace
    """
    # Replace multiple whitespace characters with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Trim leading and trailing whitespace
    return text.strip()


def extract_text_between(text: str, start_marker: str, end_marker: str) -> Optional[str]:
    """Extract text between two markers.
    
    Args:
        text: The text to extract from
        start_marker: The starting marker
        end_marker: The ending marker
        
    Returns:
        Extracted text, or None if markers not found
    """
    pattern = re.escape(start_marker) + r'(.*?)' + re.escape(end_marker)
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        return match.group(1)
    
    return None


def count_words(text: str) -> int:
    """Count the number of words in text.
    
    Args:
        text: The text to count words in
        
    Returns:
        Word count
    """
    # Clean and normalize the text first
    text = clean_text(text)
    
    # Split by whitespace and count non-empty words
    words = [word for word in text.split() if word]
    
    return len(words)