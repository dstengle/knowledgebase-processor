"""Tests for the TagExtractor."""

import unittest
from unittest.mock import patch, MagicMock

from knowledgebase_processor.models.content import Document, ContentElement
from knowledgebase_processor.models.metadata import Tag
from knowledgebase_processor.extractor.tags import TagExtractor


class TestTagExtractor(unittest.TestCase):
    """Test cases for the TagExtractor."""
    
    def setUp(self):
        """Set up the test environment."""
        self.extractor = TagExtractor()
    
    def test_extract_hashtags(self):
        """Test extracting hashtags."""
        content = """
# Document Title

This is a document with #tag1 and #tag2 hashtags.
"""
        document = Document(path="test.md", content=content)
        elements = self.extractor.extract(document)
        
        # Filter only hashtag elements
        hashtags = [e for e in elements if e.element_type == "tag" and "source" not in e.position]
        
        self.assertEqual(len(hashtags), 2)
        self.assertEqual(hashtags[0].content, "tag1")
        self.assertEqual(hashtags[1].content, "tag2")
    
    def test_extract_inline_tags(self):
        """Test that inline tags in square brackets are NOT extracted."""
        content = """
# Document Title

This is a document with [tag1] and [tag2] inline tags.
"""
        document = Document(path="test.md", content=content)
        elements = self.extractor.extract(document)
        
        # Filter only tag elements
        inline_tags = [e for e in elements if e.element_type == "tag" and "source" not in e.position]
        
        self.assertEqual(len(inline_tags), 0)
    
    def test_extract_category_tags(self):
        """Test extracting category tags."""
        content = """
# Document Title

This is a document with @category1/tag1 and @category2/tag2 category tags.
"""
        document = Document(path="test.md", content=content)
        elements = self.extractor.extract(document)
        
        # Filter only category tag elements
        category_tags = [e for e in elements if e.element_type == "tag" and e.metadata.get("category")]
        
        self.assertEqual(len(category_tags), 2)
        self.assertEqual(category_tags[0].content, "tag1")
        self.assertEqual(category_tags[0].metadata["category"], "category1")
        self.assertEqual(category_tags[1].content, "tag2")
        self.assertEqual(category_tags[1].metadata["category"], "category2")
    
    def test_extract_frontmatter_tags(self):
        """Test extracting tags from frontmatter."""
        # Create a mock frontmatter element
        mock_frontmatter_element = ContentElement(
            element_type="frontmatter",
            content="tags: [tag1, tag2]",
            position={"start": 0, "end": 20},
            metadata={"format": "yaml"}
        )
        
        # Mock the frontmatter extractor to return our mock element
        with patch.object(self.extractor.frontmatter_extractor, 'extract') as mock_extract:
            mock_extract.return_value = [mock_frontmatter_element]
            
            # Mock the parse_frontmatter method
            with patch.object(self.extractor.frontmatter_extractor, 'parse_frontmatter') as mock_parse:
                mock_parse.return_value = {"tags": ["tag1", "tag2"]}
                
                document = Document(path="test.md", content="---\ntags: [tag1, tag2]\n---\n")
                elements = self.extractor.extract(document)
                
                # Filter only frontmatter tag elements
                frontmatter_tags = [e for e in elements if e.element_type == "tag" and e.metadata.get("source") == "frontmatter"]
                
                self.assertEqual(len(frontmatter_tags), 2)
                self.assertEqual(frontmatter_tags[0].content, "tag1")
                self.assertEqual(frontmatter_tags[1].content, "tag2")
    
    def test_extract_mixed_tags(self):
        """Test extracting mixed tag types."""
        content = """---
title: Test Document
tags: [fm1, fm2]
---

# Document Title

This is a document with #hashtag1 and [inline1] tags.
It also has @category/categorized tags.
"""
        document = Document(path="test.md", content=content)
        
        # Mock the frontmatter extraction
        with patch.object(self.extractor.frontmatter_extractor, 'extract') as mock_extract:
            mock_frontmatter_element = ContentElement(
                element_type="frontmatter",
                content="title: Test Document\ntags: [fm1, fm2]",
                position={"start": 0, "end": 50},
                metadata={"format": "yaml"}
            )
            mock_extract.return_value = [mock_frontmatter_element]
            
            # Mock the parse_frontmatter method
            with patch.object(self.extractor.frontmatter_extractor, 'parse_frontmatter') as mock_parse:
                mock_parse.return_value = {"title": "Test Document", "tags": ["fm1", "fm2"]}
                
                elements = self.extractor.extract(document)
                
                # We should have 4 tags: 2 from frontmatter, 1 hashtag, 1 category (no inline tag)
                self.assertEqual(len([e for e in elements if e.element_type == "tag"]), 4)
    
    def test_get_all_tags(self):
        """Test getting all unique tags from a document."""
        content = """---
title: Test Document
tags: [tag1, tag2]
---

# Document Title

This is a document with #tag1 and [tag3] tags.
It also has @category/tag4 tags.
"""
        document = Document(path="test.md", content=content)
        
        # Mock the frontmatter extraction
        with patch.object(self.extractor.frontmatter_extractor, 'extract') as mock_extract:
            mock_frontmatter_element = ContentElement(
                element_type="frontmatter",
                content="title: Test Document\ntags: [tag1, tag2]",
                position={"start": 0, "end": 50},
                metadata={"format": "yaml"}
            )
            mock_extract.return_value = [mock_frontmatter_element]
            
            # Mock the parse_frontmatter method
            with patch.object(self.extractor.frontmatter_extractor, 'parse_frontmatter') as mock_parse:
                mock_parse.return_value = {"title": "Test Document", "tags": ["tag1", "tag2"]}
                
                # Mock the extract method to return predefined elements
                with patch.object(self.extractor, 'extract') as mock_extract_tags:
                    mock_extract_tags.return_value = [
                        ContentElement(
                            element_type="tag",
                            content="tag1",
                            position={"start": 0, "end": 10},
                            metadata={"source": "frontmatter"}
                        ),
                        ContentElement(
                            element_type="tag",
                            content="tag2",
                            position={"start": 0, "end": 10},
                            metadata={"source": "frontmatter"}
                        ),
                        ContentElement(
                            element_type="tag",
                            content="tag1",
                            position={"start": 100, "end": 110}
                        ),
                        ContentElement(
                            element_type="tag",
                            content="tag3",
                            position={"start": 120, "end": 130}
                        ),
                        ContentElement(
                            element_type="tag",
                            content="tag4",
                            position={"start": 140, "end": 150},
                            metadata={"category": "category"}
                        )
                    ]
                    
                    tags = self.extractor.get_all_tags(document)
                    
                    # We should have 4 unique tags
                    self.assertEqual(len(tags), 4)
                    
                    # Convert to list for easier assertion
                    tag_list = list(tags)
                    
                    # Check that we have the expected tags
                    tag_names = {tag.name for tag in tag_list}
                    self.assertEqual(tag_names, {"tag1", "tag2", "tag3", "tag4"})
                    
                    # Check that tag4 has the correct category
                    tag4 = next(tag for tag in tag_list if tag.name == "tag4")
                    self.assertEqual(tag4.category, "category")

def test_bracketed_text_not_tag(self):
        """Test that text like '  [Conversion]  ' does NOT produce a tag."""
        content = "  [Conversion]  "
        document = Document(path="test.md", content=content)
        elements = self.extractor.extract(document)
        # Filter only tag elements
        tags = [e for e in elements if e.element_type == "tag" and "source" not in e.position]
        # --- Step 1: Assert current (buggy) behavior: this will pass if bug exists ---
        # self.assertEqual(len(tags), 1)
        # self.assertEqual(tags[0].content, "Conversion")
        # --- Step 2: Assert correct behavior: should NOT extract any tags ---
        self.assertEqual(len(tags), 0)

def test_hashtag_preceded_by_non_whitespace(self):
        """Hashtags should only be extracted if preceded by whitespace or start-of-line."""
        content = (
            "#tag1 word #tag2 word#notatag\n"
            "another#notatag2\n"
            " #tag3\n"
            "word\t#tag4"
        )
        document = Document(path="test.md", content=content)
        elements = self.extractor.extract(document)
        tags = [e.content for e in elements if e.element_type == "tag" and "source" not in e.position]
        self.assertIn("tag1", tags)
        self.assertIn("tag2", tags)
        self.assertIn("tag3", tags)
        self.assertIn("tag4", tags)
        self.assertNotIn("notatag", tags)
        self.assertNotIn("notatag2", tags)
        def test_fixture_tag_cases(self):
            """Test tag extraction against the markdown-to-html fixture cases."""
            cases = [
                # (input, expected_tags)
                ("#hashtag", ["hashtag"]),
                ("#HasHTAg", ["HasHTAg"]),
                ("#hash #tag", ["hash", "tag"]),
                ("multiple #hash #tags in one #line", ["hash", "tags", "line"]),
                ("preceeding #space", ["space"]),
                ("missing preceeding#space", []),
                ("#test#tag", ["test"]),
                ("#t-a_g", ["t"]),
                ("#äöüß", []),
                ("#<3", []),
                ("#<3 and other #hashtags", ["hashtags"]),
                ("#0", ["0"]),
                ("there is no # hashtag", []),
                ("still no #", []),
                ("##notag", []),
                ("hashtag #hashtag", ["hashtag"]),
                ("not a#hashtag #hashtag", ["hashtag"]),
                ("#tag1\n#tag2\n#tag3", ["tag1", "tag2", "tag3"]),
            ]
            extractor = TagExtractor()
            for text, expected in cases:
                doc = Document(path="test.md", content=text)
                elements = extractor.extract(doc)
                tags = [e.content for e in elements if e.element_type == "tag" and "source" not in e.position]
                self.assertEqual(tags, expected, f"Failed for input: {text}")

        def test_fixture_ignores_code_and_links(self):
            """Test that hashtags in code, code blocks, links, images, and titles are ignored."""
            extractor = TagExtractor()
            code_cases = [
                ("`don't render #hashtags in inline code`", []),
                ("```\ndon't render #hashtags in code blocks\n```", []),
                ("[#hashtag](http://awe.so.me)", []),
                ("[there is a #hashtag](http://awe.so.me)", []),
                ("[link](http://awe.so.me \"#title\")", []),
                ("[link](http://awe.so.me \"there is a #title\")", []),
                ("![a #hashtag](http://awe.so.me/image.gif)", []),
                ("![image](http://awe.so.me/image.gif \"a #title\")", []),
                ("# hashtag", ["hashtag"]),  # heading with space is a tag
                ("<h1>hashtag</h1>", []),
                ("<div>#</div>", []),
            ]
            for text, expected in code_cases:
                doc = Document(path="test.md", content=text)
                elements = extractor.extract(doc)
                tags = [e.content for e in elements if e.element_type == "tag" and "source" not in e.position]
                self.assertEqual(tags, expected, f"Failed for input: {text}")
if __name__ == "__main__":
    unittest.main()