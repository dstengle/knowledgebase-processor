"""Tests for the FrontmatterExtractor."""

import unittest
from datetime import datetime

from knowledgebase_processor.models.content import Document
from knowledgebase_processor.extractor.frontmatter import FrontmatterExtractor


class TestFrontmatterExtractor(unittest.TestCase):
    """Test cases for the FrontmatterExtractor."""
    
    def setUp(self):
        """Set up the test environment."""
        self.extractor = FrontmatterExtractor()
    
    def test_extract_yaml_frontmatter(self):
        """Test extracting YAML frontmatter."""
        content = """---
title: Test Document
date: 2023-01-01
tags: [tag1, tag2]
---

# Content here
"""
        document = Document(path="test.md", content=content)
        elements = self.extractor.extract(document)
        
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0].element_type, "frontmatter")
        self.assertEqual(elements[0].content.strip(), "title: Test Document\ndate: 2023-01-01\ntags: [tag1, tag2]")
        self.assertEqual(elements[0].metadata["format"], "yaml")
    
    def test_extract_toml_frontmatter(self):
        """Test extracting TOML frontmatter."""
        content = """+++
title = "Test Document"
date = 2023-01-01
tags = ["tag1", "tag2"]
+++

# Content here
"""
        document = Document(path="test.md", content=content)
        elements = self.extractor.extract(document)
        
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0].element_type, "frontmatter")
        self.assertEqual(elements[0].content.strip(), 'title = "Test Document"\ndate = 2023-01-01\ntags = ["tag1", "tag2"]')
        self.assertEqual(elements[0].metadata["format"], "toml")
    
    def test_no_frontmatter(self):
        """Test document with no frontmatter."""
        content = "# Content here\nNo frontmatter in this document."
        document = Document(path="test.md", content=content)
        elements = self.extractor.extract(document)
        
        self.assertEqual(len(elements), 0)
    
    def test_parse_yaml_frontmatter(self):
        """Test parsing YAML frontmatter."""
        yaml_content = """
title: Test Document
date: 2023-01-01
tags: [tag1, tag2]
custom: value
"""
        result = self.extractor.parse_frontmatter(yaml_content, "yaml")
        
        self.assertEqual(result["title"], "Test Document")
        self.assertIsInstance(result["date"], str)
        self.assertEqual(result["tags"], ["tag1", "tag2"])
        self.assertEqual(result["custom"], "value")
    
    def test_parse_toml_frontmatter(self):
        """Test parsing TOML frontmatter."""
        toml_content = """
title = "Test Document"
date = 2023-01-01
tags = ["tag1", "tag2"]
custom = "value"
"""
        result = self.extractor.parse_frontmatter(toml_content, "toml")
        
        self.assertEqual(result["title"], "Test Document")
        self.assertIsInstance(result["date"], str)
        self.assertEqual(result["tags"], ["tag1", "tag2"])
        self.assertEqual(result["custom"], "value")
    
    def test_create_frontmatter_model(self):
        """Test creating a Frontmatter model from a dictionary."""
        frontmatter_dict = {
            "title": "Test Document",
            "date": "2023-01-01",
            "tags": ["tag1", "tag2"],
            "custom": "value"
        }
        
        model = self.extractor.create_frontmatter_model(frontmatter_dict)
        
        self.assertEqual(model.title, "Test Document")
        self.assertIsInstance(model.date, datetime)
        self.assertEqual(model.date.year, 2023)
        self.assertEqual(model.date.month, 1)
        self.assertEqual(model.date.day, 1)
        self.assertEqual(model.tags, ["tag1", "tag2"])
        self.assertEqual(model.custom_fields["custom"], "value")
    
    def test_extract_tags_from_frontmatter(self):
        """Test extracting tags from frontmatter dictionary."""
        # Test list format
        dict_with_list = {"tags": ["tag1", "tag2", "tag3"]}
        tags = self.extractor._extract_tags_from_frontmatter(dict_with_list)
        self.assertEqual(tags, ["tag1", "tag2", "tag3"])
        
        # Test comma-separated string
        dict_with_comma = {"tags": "tag1, tag2, tag3"}
        tags = self.extractor._extract_tags_from_frontmatter(dict_with_comma)
        self.assertEqual(tags, ["tag1", "tag2", "tag3"])
        
        # Test space-separated string
        dict_with_space = {"tags": "tag1 tag2 tag3"}
        tags = self.extractor._extract_tags_from_frontmatter(dict_with_space)
        self.assertEqual(tags, ["tag1", "tag2", "tag3"])
        
        # Test categories
        dict_with_categories = {"categories": ["cat1", "cat2"]}
        tags = self.extractor._extract_tags_from_frontmatter(dict_with_categories)
        self.assertEqual(tags, ["cat1", "cat2"])
        
        # Test both tags and categories
        dict_with_both = {
            "tags": ["tag1", "tag2"],
            "categories": ["cat1", "cat2"]
        }
        tags = self.extractor._extract_tags_from_frontmatter(dict_with_both)
        self.assertEqual(set(tags), {"tag1", "tag2", "cat1", "cat2"})


if __name__ == "__main__":
    unittest.main()