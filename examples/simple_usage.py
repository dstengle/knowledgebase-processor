#!/usr/bin/env python3
"""
Simple example of using the Knowledge Base Processor.

This script demonstrates how to use the Knowledge Base Processor
to process markdown files and query the knowledge base.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from knowledgebase_processor import KnowledgeBaseProcessor


def create_example_files(base_dir):
    """Create example markdown files for demonstration."""
    # Create a simple markdown file
    with open(os.path.join(base_dir, "document1.md"), "w") as f:
        f.write("""---
title: Example Document 1
tags: [example, markdown, documentation]
---

# Example Document 1

This is an example document with some content.

## Section 1

- List item 1
- List item 2
- [ ] Todo item 1
- [x] Todo item 2 (done)

## Section 2

```python
def hello_world():
    print("Hello, world!")
```

> This is a blockquote
> With multiple lines

[Link to another document](document2.md)
""")
    
    # Create another markdown file
    with open(os.path.join(base_dir, "document2.md"), "w") as f:
        f.write("""---
title: Example Document 2
tags: [example, related]
---

# Example Document 2

This document is related to Example Document 1.

## Related Content

This section references [Example Document 1](document1.md).
""")


def main():
    """Main function to demonstrate the Knowledge Base Processor."""
    # Create a temporary directory for the example
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Created temporary directory: {temp_dir}")
        
        # Create example files
        create_example_files(temp_dir)
        print("Created example markdown files")
        
        # Create metadata directory
        metadata_dir = os.path.join(temp_dir, ".metadata")
        os.makedirs(metadata_dir, exist_ok=True)
        
        # Initialize the Knowledge Base Processor
        processor = KnowledgeBaseProcessor(temp_dir, metadata_dir)
        print("Initialized Knowledge Base Processor")
        
        # Process all markdown files
        documents = processor.process_all()
        print(f"Processed {len(documents)} documents")
        
        # Print document titles
        for doc in documents:
            print(f"  - {doc.title} ({doc.path})")
        
        # Search for documents containing "related"
        print("\nSearching for documents containing 'related':")
        results = processor.search("related")
        for doc_id in results:
            metadata = processor.get_metadata(doc_id)
            print(f"  - {metadata.structure['title']} ({doc_id})")
        
        # Find documents with the "example" tag
        print("\nFinding documents with the 'example' tag:")
        results = processor.find_by_tag("example")
        for doc_id in results:
            metadata = processor.get_metadata(doc_id)
            print(f"  - {metadata.structure['title']} ({doc_id})")
        
        # Find related documents
        print("\nFinding documents related to 'document1.md':")
        results = processor.find_related("document1.md")
        for relation in results:
            related_id = relation["document_id"]
            metadata = processor.get_metadata(related_id)
            print(f"  - {metadata.structure['title']} ({related_id})")


if __name__ == "__main__":
    main()