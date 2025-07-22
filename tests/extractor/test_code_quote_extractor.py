"""Tests for the code block and blockquote extractor."""

import unittest
from pathlib import Path
from unittest.mock import Mock

from knowledgebase_processor.models.content import Document
from knowledgebase_processor.models.markdown import CodeBlock, Blockquote
from knowledgebase_processor.extractor.code_quote import CodeQuoteExtractor


class TestCodeQuoteExtractor(unittest.TestCase):
    """Test cases for the code block and blockquote extractor."""
    
    def setUp(self):
        """Set up the test environment."""
        self.extractor = CodeQuoteExtractor()
    
    def test_extract_empty_document(self):
        """Test extracting from an empty document."""
        document = Document(path="test.md", content="", title="Test")
        elements = self.extractor.extract(document)
        self.assertEqual(len(elements), 0)
    
    def test_extract_code_block_without_language(self):
        """Test extracting a code block without language specification."""
        content = "```\nprint('Hello, world!')\n```"
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        self.assertEqual(len(elements), 1)
        self.assertIsInstance(elements[0], CodeBlock)
        self.assertIsNone(elements[0].language)
        self.assertEqual(elements[0].code, "print('Hello, world!')")
    
    def test_extract_code_block_with_language(self):
        """Test extracting a code block with language specification."""
        content = "```python\nprint('Hello, world!')\n```"
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        self.assertEqual(len(elements), 1)
        self.assertIsInstance(elements[0], CodeBlock)
        self.assertEqual(elements[0].language, "python")
        self.assertEqual(elements[0].code, "print('Hello, world!')")
    
    def test_extract_multiple_code_blocks(self):
        """Test extracting multiple code blocks."""
        content = """
        # Code Examples
        
        Python example:
        
        ```python
        def hello():
            print('Hello, world!')
        ```
        
        JavaScript example:
        
        ```javascript
        function hello() {
            console.log('Hello, world!');
        }
        ```
        """
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        self.assertEqual(len(elements), 2)
        self.assertIsInstance(elements[0], CodeBlock)
        self.assertIsInstance(elements[1], CodeBlock)
        
        self.assertEqual(elements[0].language, "python")
        self.assertEqual(elements[0].code, "def hello():\n    print('Hello, world!')")
        
        self.assertEqual(elements[1].language, "javascript")
        self.assertEqual(elements[1].code, "function hello() {\n    console.log('Hello, world!');\n}")
    
    def test_extract_simple_blockquote(self):
        """Test extracting a simple blockquote."""
        content = "> This is a blockquote."
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        self.assertEqual(len(elements), 1)
        self.assertIsInstance(elements[0], Blockquote)
        self.assertEqual(elements[0].level, 1)
        self.assertEqual(elements[0].content, "This is a blockquote.")
    
    def test_extract_multiline_blockquote(self):
        """Test extracting a multiline blockquote."""
        content = """> This is a blockquote
> with multiple lines
> spanning three lines."""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        self.assertEqual(len(elements), 1)
        self.assertIsInstance(elements[0], Blockquote)
        self.assertEqual(elements[0].level, 1)
        self.assertEqual(elements[0].content, "This is a blockquote\nwith multiple lines\nspanning three lines.")
    
    def test_extract_nested_blockquotes(self):
        """Test extracting nested blockquotes."""
        content = """> Level 1 blockquote
>> Level 2 blockquote
>>> Level 3 blockquote
>> Back to level 2
> Back to level 1"""
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        self.assertEqual(len(elements), 5)
        
        # Check levels
        levels = [e.level for e in elements]
        self.assertEqual(levels, [1, 2, 3, 2, 1])
        
        # Check content
        self.assertEqual(elements[0].content, "Level 1 blockquote")
        self.assertEqual(elements[1].content, "Level 2 blockquote")
        self.assertEqual(elements[2].content, "Level 3 blockquote")
        self.assertEqual(elements[3].content, "Back to level 2")
        self.assertEqual(elements[4].content, "Back to level 1")
    
    def test_extract_mixed_content(self):
        """Test extracting a mix of code blocks and blockquotes."""
        content = """
        # Mixed Content Example
        
        > This is a blockquote
        
        ```python
        def hello():
            print('Hello, world!')
        ```
        
        > Another blockquote
        >> With nesting
        
        ```javascript
        console.log('Hello!');
        ```
        """
        document = Document(path="test.md", content=content, title="Test")
        elements = self.extractor.extract(document)
        
        # We should have 2 code blocks and 3 blockquotes
        code_blocks = [e for e in elements if isinstance(e, CodeBlock)]
        blockquotes = [e for e in elements if isinstance(e, Blockquote)]
        
        self.assertEqual(len(code_blocks), 2)
        self.assertEqual(len(blockquotes), 3)
        
        # Check code blocks
        self.assertEqual(code_blocks[0].language, "python")
        self.assertEqual(code_blocks[1].language, "javascript")
        
        # Check blockquotes
        self.assertEqual(blockquotes[0].level, 1)
        self.assertEqual(blockquotes[1].level, 1)
        self.assertEqual(blockquotes[2].level, 2)
    
    @unittest.skip("Processor now requires arguments")
    def test_integration_with_processor(self):
        """Test integration with the processor."""
        from knowledgebase_processor.processor.processor import Processor
        
        processor = Processor(Mock(), Mock())
        processor.register_extractor(self.extractor)
        
        content = """
        # Test Document
        
        > This is a blockquote
        
        ```python
        def hello():
            print('Hello, world!')
        ```
        
        > Another blockquote
        >> With nesting
        """
        document = Document(path="test.md", content=content, title="Test")
        processed_doc = processor.process_document(document)
        
        # Check that elements were added to the document
        self.assertGreater(len(processed_doc.elements), 0)
        
        # Check that we have code blocks and blockquotes
        code_blocks = [e for e in processed_doc.elements if isinstance(e, CodeBlock)]
        blockquotes = [e for e in processed_doc.elements if isinstance(e, Blockquote)]
        
        self.assertEqual(len(code_blocks), 1)
        self.assertEqual(len(blockquotes), 3)


if __name__ == "__main__":
    unittest.main()