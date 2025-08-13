# Vocabulary Usage Guide for LLM Agent Coders

This guide explains how to work with the KB vocabulary when developing features for the knowledgebase-processor.

## Quick Start

### 1. Import the Vocabulary

Always import the KB namespace from the centralized configuration:

```python
from knowledgebase_processor.config.vocabulary import KB
```

**Never hardcode the namespace URI directly in your code.**

### 2. Using the Vocabulary

The KB namespace works like any RDFlib Namespace object:

```python
from rdflib import Graph, Literal, URIRef, RDF
from knowledgebase_processor.config.vocabulary import KB

# Create RDF triples
g = Graph()
g.bind("kb", KB)  # Bind prefix for serialization

# Reference vocabulary classes
doc_uri = URIRef("http://example.org/doc/1")
g.add((doc_uri, RDF.type, KB.Document))
g.add((doc_uri, KB.title, Literal("My Document")))

# Reference vocabulary properties
g.add((doc_uri, KB.hasTag, KB["python"]))
g.add((doc_uri, KB.created, Literal("2025-08-13")))
```

## Common Vocabulary Elements

### Document Types
- `KB.Document` - Base document class
- `KB.DailyNote` - Daily note documents
- `KB.Meeting` - Meeting notes
- `KB.GroupMeeting` - Group meetings
- `KB.OneOnOneMeeting` - 1-on-1 meetings
- `KB.PersonProfile` - Person profiles
- `KB.BookNote` - Book notes
- `KB.ProjectDocument` - Project documents

### Entity Types
- `KB.Person` - Individual people
- `KB.Company` - Organizations
- `KB.Place` - Locations
- `KB.Book` - Books
- `KB.Todo` - Action items
- `KB.Tag` - Tags/categories

### Common Properties
- `KB.title` - Document title
- `KB.created` - Creation date
- `KB.hasTag` - Link to tags
- `KB.hasSection` - Document sections
- `KB.hasAttendee` - Meeting attendees
- `KB.isCompleted` - Todo completion status
- `KB.mentionedIn` - Entity mentions
- `KB.describes` - What a document describes

## Code Patterns

### Creating Entities

```python
def create_document_entity(doc_id: str, title: str) -> Graph:
    """Create RDF representation of a document."""
    from knowledgebase_processor.config.vocabulary import KB
    
    g = Graph()
    g.bind("kb", KB)
    
    doc_uri = URIRef(f"http://example.org/documents/{doc_id}")
    g.add((doc_uri, RDF.type, KB.Document))
    g.add((doc_uri, KB.title, Literal(title)))
    
    return g
```

### Checking Entity Types

```python
def is_meeting_document(g: Graph, uri: URIRef) -> bool:
    """Check if a URI represents a meeting document."""
    from knowledgebase_processor.config.vocabulary import KB
    
    return (uri, RDF.type, KB.Meeting) in g or \
           (uri, RDF.type, KB.GroupMeeting) in g or \
           (uri, RDF.type, KB.OneOnOneMeeting) in g
```

### Working with Properties

```python
def add_tags_to_document(g: Graph, doc_uri: URIRef, tags: List[str]):
    """Add tags to a document."""
    from knowledgebase_processor.config.vocabulary import KB
    
    for tag in tags:
        tag_uri = KB[tag.replace(" ", "_")]
        g.add((doc_uri, KB.hasTag, tag_uri))
```

## Best Practices

### DO:
- ✅ Import KB from `knowledgebase_processor.config.vocabulary`
- ✅ Use vocabulary classes for RDF.type assertions
- ✅ Use vocabulary properties for relationships
- ✅ Bind the KB prefix when creating graphs
- ✅ Check the vocabulary file for available terms

### DON'T:
- ❌ Hardcode namespace URIs like `"http://example.org/kb/"`
- ❌ Create custom properties without checking the vocabulary
- ❌ Modify the vocabulary file directly
- ❌ Import Namespace and create your own KB namespace

## Vocabulary Structure

The vocabulary follows these patterns:

1. **Classes** (Types):
   - Named with PascalCase: `Document`, `Person`, `TodoItem`
   - Represent entity types in the knowledge base

2. **Properties** (Relationships):
   - Named with camelCase: `hasTag`, `isCompleted`, `mentionedIn`
   - Connect entities or add attributes

3. **Instances** (Individuals):
   - Can be created dynamically: `KB["tag_name"]`
   - Used for tags, categories, etc.

## Finding Available Terms

To see what's available in the vocabulary:

1. **Check the documentation**: `/vocabulary/README.md`
2. **Read the vocabulary file**: `/vocabulary/kb.ttl`
3. **Use introspection**:

```python
from knowledgebase_processor.config.vocabulary import get_vocabulary_file_path
from rdflib import Graph

# Load and explore the vocabulary
g = Graph()
g.parse(get_vocabulary_file_path(), format='turtle')

# Find all classes
for s, p, o in g.triples((None, RDF.type, OWL.Class)):
    print(f"Class: {s}")

# Find all properties
for s, p, o in g.triples((None, RDF.type, OWL.ObjectProperty)):
    print(f"Property: {s}")
```

## Adding New Terms

If you need a term that doesn't exist:

1. **Check if a similar term exists** in the vocabulary
2. **Consider using standard vocabularies** (Schema.org, FOAF, Dublin Core)
3. **Propose additions** to the source repository
4. **Document temporary extensions** clearly in your code

Example of documenting a temporary extension:

```python
# TODO: Propose kb:reviewStatus to vocabulary
# Temporary: Using custom property until vocabulary updated
REVIEW_STATUS = URIRef("http://example.org/kb/vocab#reviewStatus")
g.add((doc_uri, REVIEW_STATUS, Literal("pending")))
```

## Testing with the Vocabulary

```python
def test_document_creation():
    """Test creating a document with vocabulary."""
    from knowledgebase_processor.config.vocabulary import KB, validate_vocabulary
    
    # Ensure vocabulary is available
    assert validate_vocabulary(), "Vocabulary not properly configured"
    
    # Test document creation
    g = Graph()
    g.bind("kb", KB)
    
    doc = URIRef("test:doc1")
    g.add((doc, RDF.type, KB.Document))
    
    # Verify the triple was added
    assert (doc, RDF.type, KB.Document) in g
```

## Environment Variables

For testing or special deployments, you can override the vocabulary namespace:

```bash
export KB_VOCABULARY_NAMESPACE="http://test.example.org/kb/"
python your_script.py
```

## Common Issues and Solutions

### Issue: "KB is not defined"
**Solution**: Import from the correct module:
```python
from knowledgebase_processor.config.vocabulary import KB
```

### Issue: "Unknown property kb:someProperty"
**Solution**: Check if the property exists in the vocabulary:
```bash
grep "someProperty" vocabulary/kb.ttl
```

### Issue: "Namespace mismatch in RDF output"
**Solution**: Ensure you're binding the namespace:
```python
g.bind("kb", KB)  # Always bind before serializing
```

## Summary

The vocabulary is your semantic schema. It defines:
- What types of things exist (classes)
- How they relate (properties)
- What they mean (semantics)

Always use the centralized vocabulary configuration to ensure consistency across the codebase. When in doubt, check the vocabulary file and documentation.