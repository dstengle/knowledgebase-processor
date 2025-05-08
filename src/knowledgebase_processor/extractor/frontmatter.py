"""Frontmatter extractor implementation."""

import re
from typing import List, Dict, Any, Optional, Tuple
import datetime

import yaml
try:
    import tomli as toml
except ImportError:
    import tomllib as toml

from .base import BaseExtractor
from ..models.content import Document, ContentElement
from ..models.metadata import Frontmatter


class FrontmatterExtractor(BaseExtractor):
    """Extractor for frontmatter metadata in markdown documents.
    
    Extracts YAML frontmatter enclosed between --- markers or
    TOML frontmatter enclosed between +++ markers at the beginning
    of markdown documents.
    """
    
    def __init__(self):
        """Initialize the FrontmatterExtractor."""
        # Regex pattern for YAML frontmatter: content between --- markers at start of file
        self.yaml_pattern = re.compile(r'^\s*---\s*\n(.*?)\n\s*---\s*\n', re.DOTALL)
        # Regex pattern for TOML frontmatter: content between +++ markers at start of file
        self.toml_pattern = re.compile(r'^\s*\+\+\+\s*\n(.*?)\n\s*\+\+\+\s*\n', re.DOTALL)
    
    def extract(self, document: Document) -> List[ContentElement]:
        """Extract frontmatter from a document.
        
        Args:
            document: The document to extract from
            
        Returns:
            List containing a single ContentElement with the frontmatter if found,
            or an empty list if no frontmatter is found
        """
        # Try to match YAML frontmatter first
        yaml_match = self.yaml_pattern.match(document.content)
        if yaml_match:
            frontmatter_content = yaml_match.group(1)
            frontmatter_format = "yaml"
            match_end = yaml_match.end()
        else:
            # Try to match TOML frontmatter
            toml_match = self.toml_pattern.match(document.content)
            if toml_match:
                frontmatter_content = toml_match.group(1)
                frontmatter_format = "toml"
                match_end = toml_match.end()
            else:
                # No frontmatter found
                return []
        
        # Create a ContentElement for the frontmatter
        element = ContentElement(
            element_type="frontmatter",
            content=frontmatter_content,
            position={"start": 0, "end": match_end},
            metadata={"format": frontmatter_format}
        )
        
        return [element]
    
    def parse_frontmatter(self, frontmatter_content: str, format_type: str = "yaml") -> Dict[str, Any]:
        """Parse frontmatter content into a dictionary.
        
        Uses proper YAML and TOML parsers to handle complex structures.
        
        Args:
            frontmatter_content: The raw frontmatter content
            format_type: The format of the frontmatter ("yaml" or "toml")
            
        Returns:
            Dictionary of parsed frontmatter fields
        """
        try:
            result = {}
            if format_type.lower() == "toml":
                parsed = toml.loads(frontmatter_content)
            else:  # Default to YAML
                parsed = yaml.safe_load(frontmatter_content) or {}
            
            # Convert datetime objects to strings for consistency
            for key, value in parsed.items():
                if isinstance(value, (datetime.date, datetime.datetime)):
                    # Convert to ISO format string
                    result[key] = value.isoformat()
                else:
                    result[key] = value
            
            return result if result else parsed
        except Exception as e:
            # Log the error and return an empty dict on parsing failure
            print(f"Error parsing frontmatter: {e}")
            return {}
    
    def create_frontmatter_model(self, frontmatter_dict: Dict[str, Any]) -> Frontmatter:
        """Convert a frontmatter dictionary to a Frontmatter model.
        
        Args:
            frontmatter_dict: Dictionary of parsed frontmatter fields
            
        Returns:
            Frontmatter model with structured data
        """
        # Extract known fields
        title = frontmatter_dict.get("title")
        
        # Handle date field - could be string or datetime
        date_value = frontmatter_dict.get("date")
        date = self._parse_date(date_value) if date_value else None
        
        # Extract tags
        tags = self._extract_tags_from_frontmatter(frontmatter_dict)
        
        # Create a copy of the dict for custom fields
        custom_fields = frontmatter_dict.copy()
        
        # Remove known fields from custom_fields
        for field in ["title", "date", "tags"]:
            if field in custom_fields:
                del custom_fields[field]
        
        # Create and return the Frontmatter model
        return Frontmatter(
            title=title,
            date=date,
            tags=tags,
            custom_fields=custom_fields
        )
    
    def _parse_date(self, date_value: Any) -> Optional[datetime.datetime]:
        """Parse a date value into a datetime object.
        
        Args:
            date_value: The date value from frontmatter
            
        Returns:
            Datetime object or None if parsing fails
        """
        if isinstance(date_value, (datetime.datetime, datetime.date)):
            if isinstance(date_value, datetime.date) and not isinstance(date_value, datetime.datetime):
                # Convert date to datetime
                return datetime.datetime.combine(date_value, datetime.time())
            return date_value
        
        if isinstance(date_value, str):
            try:
                # Try different date formats
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d", "%d-%m-%Y"]:
                    try:
                        return datetime.datetime.strptime(date_value, fmt)
                    except ValueError:
                        continue
            except Exception:
                pass
        
        return None
    
    def _extract_tags_from_frontmatter(self, frontmatter_dict: Dict[str, Any]) -> List[str]:
        """Extract tags from frontmatter dictionary.
        
        Tags can be specified in different formats:
        - List of strings: tags: ["tag1", "tag2"]
        - Single string with comma separation: tags: "tag1, tag2"
        - Single string with space separation: tags: "tag1 tag2"
        
        Args:
            frontmatter_dict: Dictionary of parsed frontmatter fields
            
        Returns:
            List of tag strings
        """
        tags = []
        
        # Get the tags field if it exists
        tags_field = frontmatter_dict.get("tags", [])
        
        # Handle different formats
        if isinstance(tags_field, list):
            # List format: ["tag1", "tag2"]
            tags = [str(tag).strip() for tag in tags_field if tag]
        elif isinstance(tags_field, str):
            # String format: could be comma-separated or space-separated
            if "," in tags_field:
                # Comma-separated: "tag1, tag2"
                tags = [tag.strip() for tag in tags_field.split(",") if tag.strip()]
            else:
                # Space-separated: "tag1 tag2"
                tags = [tag.strip() for tag in tags_field.split() if tag.strip()]
        
        # Also check for "categories" field which is common in some systems
        categories = frontmatter_dict.get("categories", [])
        if categories:
            if isinstance(categories, list):
                tags.extend([str(cat).strip() for cat in categories if cat])
            elif isinstance(categories, str):
                if "," in categories:
                    tags.extend([cat.strip() for cat in categories.split(",") if cat.strip()])
                else:
                    tags.extend([cat.strip() for cat in categories.split() if cat.strip()])
        
        return tags