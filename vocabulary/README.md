# KB Vocabulary Reference

This directory contains the RDF vocabulary/ontology used by the knowledgebase-processor.

## Source

The vocabulary is maintained in the external repository:
- **Repository**: https://github.com/dstengle/knowledgebase-vocabulary
- **Primary File**: `vocabulary/kb.ttl`  
- **License**: MIT

## Current Version

See `VERSION.json` for:
- Source commit reference
- Last sync date
- Namespace URI
- Version information

## Usage in Code

### Import the Namespace

```python
from knowledgebase_processor.config.vocabulary import KB

# Use the namespace
from rdflib import Graph, URIRef

g = Graph()
entity_uri = KB.Document  # Creates URIRef for kb:Document class
property_uri = KB.hasTag  # Creates URIRef for kb:hasTag property
```

### Direct File Access

```python
from pathlib import Path

vocab_file = Path("vocabulary/kb.ttl")
# Load vocabulary for validation or introspection
```

## Vocabulary Structure

The KB vocabulary defines:

### Core Classes
- `kb:Document` - Base class for markdown documents
- `kb:Person` - Individual entities
- `kb:Organization` - Companies and groups
- `kb:Meeting` - Meeting notes and events
- `kb:TodoItem` - Tasks and action items
- `kb:Section` - Document structure elements

### Key Properties
- `kb:hasTag` - Links documents to tags
- `kb:hasAttendee` - Links meetings to participants
- `kb:isCompleted` - Status of todo items
- `kb:mentionedIn` - Entity references in documents

### Integration with Standard Vocabularies
- FOAF for person modeling
- Schema.org for general semantics
- Dublin Core for metadata
- SKOS for tag hierarchies

## Updating the Vocabulary

### Manual Update Process

1. Check for updates in the source repository:
   ```bash
   ./scripts/sync-vocabulary.sh check
   ```

2. Review changes before syncing:
   ```bash
   ./scripts/sync-vocabulary.sh diff
   ```

3. Sync from source repository:
   ```bash
   ./scripts/sync-vocabulary.sh sync
   ```

4. Update VERSION.json with new commit hash and date

5. Test compatibility:
   ```bash
   pytest tests/vocabulary/
   ```

6. Commit changes:
   ```bash
   git add vocabulary/
   git commit -m "chore: sync vocabulary from upstream"
   ```

### Automated Validation

The vocabulary is validated during:
- CI/CD pipeline runs
- Pre-commit hooks (if configured)
- Test suite execution

## For LLM Agent Coders

When working with the vocabulary:

1. **Always use the configured namespace**: Import `KB` from `knowledgebase_processor.config.vocabulary`
2. **Reference this documentation**: The vocabulary structure is documented here
3. **Check VERSION.json**: Ensure you're working with the expected version
4. **Don't modify kb.ttl directly**: Changes should be made in the source repository
5. **Use type hints**: The vocabulary provides semantic types for entities

### Example: Creating RDF Triples

```python
from rdflib import Graph, Literal, URIRef
from knowledgebase_processor.config.vocabulary import KB

# Create a graph
g = Graph()
g.bind("kb", KB)

# Create a document entity
doc_uri = URIRef("http://example.org/documents/my-note")
g.add((doc_uri, RDF.type, KB.Document))
g.add((doc_uri, KB.title, Literal("My Daily Note")))
g.add((doc_uri, KB.hasTag, KB["work"]))

# Create a todo item
todo_uri = URIRef("http://example.org/todos/task-1")
g.add((todo_uri, RDF.type, KB.TodoItem))
g.add((todo_uri, KB.description, Literal("Complete vocabulary integration")))
g.add((todo_uri, KB.isCompleted, Literal(False)))
```

## Vocabulary Evolution

The vocabulary is designed to evolve with the project needs:

1. **Backward Compatibility**: Changes maintain compatibility with existing data
2. **Semantic Versioning**: Version numbers follow semver conventions
3. **Migration Support**: Tools provided for data migration when needed
4. **Documentation**: All changes documented in the source repository

## Troubleshooting

### Namespace Mismatch
If you see namespace errors, ensure:
- VERSION.json matches the namespace in kb.ttl
- Code imports use the configured namespace
- RDF data uses consistent namespace URIs

### Missing Classes/Properties
If a class or property is missing:
1. Check if it exists in the source repository
2. Verify your local copy is up-to-date
3. Consider if it needs to be added to the vocabulary

### Import Errors
If vocabulary imports fail:
1. Ensure the vocabulary directory exists
2. Check that VERSION.json is valid JSON
3. Verify Python path includes the project root

## Related Documentation

- [ADR-0014: Vocabulary Reference Strategy](../architecture/decisions/0014-vocabulary-reference-strategy.md)
- [ADR-0009: Knowledge Graph and RDF Store](../architecture/decisions/0009-knowledge-graph-rdf-store.md)
- [Entity Modeling Documentation](../architecture/decisions/0012-entity-modeling-with-wiki-based-architecture.md)