"""Configuration implementation."""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field


class Config(BaseModel):
    """Configuration for the Knowledge Base Processor."""
    
    # Base paths
    knowledge_base_path: str = Field(..., description="Path to the knowledge base directory")
    metadata_store_path: str = Field(..., description="Path to the metadata store directory")
    
    # Processing options
    file_patterns: list[str] = Field(default=["**/*.md"], description="Glob patterns for files to process")
    exclude_patterns: list[str] = Field(default=[], description="Glob patterns for files to exclude")
    
    # Feature flags
    extract_frontmatter: bool = Field(default=True, description="Extract frontmatter metadata")
    extract_tags: bool = Field(default=True, description="Extract tags")
    analyze_topics: bool = Field(default=True, description="Analyze topics")
    analyze_entities: bool = Field(default=False, description="Analyze entities using spaCy (disabled by default)")
    enrich_relationships: bool = Field(default=True, description="Enrich with relationship information")
    
    # Advanced options
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Maximum file size to process in bytes")
    cache_enabled: bool = Field(default=True, description="Enable caching")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # SPARQL options
    sparql_endpoint_url: Optional[str] = Field(default=None, description="SPARQL query endpoint URL")
    sparql_update_endpoint_url: Optional[str] = Field(default=None, description="SPARQL update endpoint URL")
    sparql_default_graph: Optional[str] = Field(default=None, description="Default graph URI for SPARQL operations")


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from a file.
    
    Args:
        config_path: Path to the configuration file (optional)
        
    Returns:
        Config object
        
    If config_path is not provided, the function will look for a config file
    in the following locations:
    1. ./kbp_config.json
    2. ~/.kbp_config.json
    3. /etc/kbp_config.json
    
    If no config file is found, default values will be used.
    """
    # Default configuration
    default_config = {
        "knowledge_base_path": os.path.expanduser("~/knowledge_base"),
        "metadata_store_path": os.path.expanduser("~/.kbp/metadata"),
        "file_patterns": ["**/*.md"],
        "exclude_patterns": [],
        "extract_frontmatter": True,
        "extract_tags": True,
        "analyze_topics": True,
        "analyze_entities": False,
        "enrich_relationships": True,
        "max_file_size": 10 * 1024 * 1024,
        "cache_enabled": True,
        "log_level": "INFO",
        "sparql_endpoint_url": None,
        "sparql_update_endpoint_url": None,
        "sparql_default_graph": None
    }
    
    # If a config path is provided, use it
    if config_path:
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                return Config(**{**default_config, **config_data})
    
    # Otherwise, look for config files in standard locations
    config_paths = [
        Path("./kbp_config.json"),
        Path(os.path.expanduser("~/.kbp_config.json")),
        Path("/etc/kbp_config.json")
    ]
    
    for path in config_paths:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                return Config(**{**default_config, **config_data})
    
    # If no config file is found, use default values
    return Config(**default_config)