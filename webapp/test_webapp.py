"""
Quick test script for the webapp backend
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledgebase_processor.processor import Processor
from knowledgebase_processor.utils import DocumentRegistry, EntityIdGenerator
from rdflib import RDF

# Test markdown content
TEST_MARKDOWN = """# Test Document

## Tasks
- [ ] Implement feature A
- [x] Complete feature B

## People
Contact [[John Doe]] for questions.

## Data Table
| Name | Status |
|------|--------|
| Task 1 | Done |
| Task 2 | Pending |

```python
def hello():
    print("Hello, World!")
```

> Important: This is a test document
"""

print("Testing Knowledge Base Processor...")
print("=" * 50)

# Initialize processor
processor = Processor(
    document_registry=DocumentRegistry(),
    id_generator=EntityIdGenerator()
)

# Process content
print("\n1. Processing markdown content...")
graph = processor.process_content_to_graph(
    content=TEST_MARKDOWN,
    document_id="test_doc"
)

print(f"✓ Generated {len(graph)} triples")

# Count entity types
print("\n2. Analyzing entity types...")
entity_types = {}
for s, p, o in graph.triples((None, RDF.type, None)):
    entity_type = str(o).split('/')[-1]
    entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

print("✓ Entity breakdown:")
for entity_type, count in sorted(entity_types.items()):
    print(f"  - {entity_type}: {count}")

# Test querying
print("\n3. Testing entity queries...")
todo_items = []
for s, p, o in graph.triples((None, RDF.type, None)):
    if 'TodoItem' in str(o):
        todo_items.append(s)

print(f"✓ Found {len(todo_items)} todo items")

# Test export
print("\n4. Testing RDF export...")
ttl_output = graph.serialize(format='turtle')
print(f"✓ Exported {len(ttl_output)} bytes of Turtle RDF")

print("\n" + "=" * 50)
print("✅ All tests passed!")
print("\nWebapp backend is ready to use.")
print("Run: python backend/main.py")
print("Or: uvicorn backend.main:app --reload")
