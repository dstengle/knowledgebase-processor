# Model Consolidation Guide

## Overview

This guide documents the consolidation of duplicate and overlapping data models in the Knowledge Base Processor. The consolidation creates a unified model architecture that eliminates redundancy while preserving all existing functionality.

## Consolidation Summary

### Models Being Consolidated

| Old Models | New Unified Model | Location |
|------------|-------------------|----------|
| `BaseKnowledgeModel` + `KbBaseEntity` | `KnowledgeBaseEntity` | `models/base.py` |
| `ExtractedEntity` + `Kb*Entity` models | `ContentEntity` hierarchy | `models/base.py` + `models/entity_types.py` |
| `TodoItem` + `KbTodoItem` | `TodoEntity` | `models/todo.py` |
| `WikiLink` + `KbWikiLink` | `LinkEntity` | `models/link.py` |
| `Document` + `KbDocument` | `UnifiedDocument` | `models/document.py` |
| `DocumentMetadata` (enhanced) | `UnifiedDocumentMetadata` | `models/document.py` |

## Key Improvements

### 1. Unified Base Class
- Single `KnowledgeBaseEntity` base for all models
- Consistent ID, timestamp, and provenance tracking
- Full RDF support across all models
- Backward compatible with existing code

### 2. Entity Consolidation
- `ContentEntity` base class for all extracted entities
- Type-specific subclasses (`PersonEntity`, `OrganizationEntity`, etc.)
- Maintains extraction position information
- Supports both simple NER and rich RDF entities

### 3. Document Integration
- `UnifiedDocument` includes metadata directly
- No need for separate metadata extraction
- Preserves content preservation capabilities
- Supports both file paths and URIs

## Migration Guide

### Phase 1: Import Updates

#### Before:
```python
from knowledgebase_processor.models.entities import ExtractedEntity
from knowledgebase_processor.models.kb_entities import KbPerson, KbTodoItem
from knowledgebase_processor.models.metadata import DocumentMetadata
from knowledgebase_processor.models.content import Document
```

#### After:
```python
from knowledgebase_processor.models import (
    ExtractedEntity,  # Alias for ContentEntity
    PersonEntity,     # Replaces KbPerson
    TodoEntity,       # Replaces KbTodoItem
    DocumentMetadata, # Alias for UnifiedDocumentMetadata
    Document         # Alias for UnifiedDocument
)

# Or import directly from specific modules:
from knowledgebase_processor.models.entity_types import PersonEntity
from knowledgebase_processor.models.todo import TodoEntity
from knowledgebase_processor.models.document import UnifiedDocument as Document
```

### Phase 2: Model Usage Updates

#### Creating Entities

**Before:**
```python
# Simple entity
entity = ExtractedEntity(
    text="John Doe",
    label="PERSON",
    start_char=0,
    end_char=8
)

# Rich entity
person = KbPerson(
    kb_id="person_123",
    full_name="John Doe",
    label="John Doe"
)
```

**After:**
```python
# Unified approach
from knowledgebase_processor.models import create_entity

# Automatically creates appropriate entity type
entity = create_entity(
    text="John Doe",
    label="PERSON",
    start_char=0,
    end_char=8
)

# Or explicitly create PersonEntity
from knowledgebase_processor.models import PersonEntity

person = PersonEntity(
    id="person_123",
    text="John Doe",
    full_name="John Doe",
    entity_type="person",
    start_char=0,
    end_char=8
)
```

#### Working with Documents

**Before:**
```python
# Process document
document = Document(path="doc.md", content="...")
metadata = extract_metadata(document)
document.metadata = metadata  # Manual attachment
```

**After:**
```python
# Metadata integrated directly
document = UnifiedDocument(
    id="doc_123",
    path="doc.md", 
    content="...",
    metadata=UnifiedDocumentMetadata(
        document_id="doc_123",
        title="My Document",
        entities=[...],
        links=[...],
        todos=[...]
    )
)
```

### Phase 3: Service Updates

#### Entity Service

**Before:**
```python
def process_entity(entity: ExtractedEntity) -> KbPerson:
    return KbPerson(
        kb_id=generate_id(),
        label=entity.text,
        extracted_from_text_span=(entity.start_char, entity.end_char)
    )
```

**After:**
```python
def process_entity(entity: ContentEntity) -> PersonEntity:
    # ContentEntity already has all needed fields
    if entity.entity_type == "person":
        return PersonEntity(**entity.dict())
    return entity
```

#### Processor Updates

**Before:**
```python
def process_document(doc: Document) -> Tuple[Document, DocumentMetadata]:
    # Process document
    metadata = DocumentMetadata(...)
    return doc, metadata
```

**After:**
```python
def process_document(doc: UnifiedDocument) -> UnifiedDocument:
    # Process and attach metadata directly
    doc.metadata = UnifiedDocumentMetadata(
        document_id=doc.id,
        entities=extract_entities(doc),
        links=extract_links(doc),
        todos=extract_todos(doc)
    )
    return doc
```

## Backward Compatibility

### Direct Aliases
The models package provides direct aliases for backward compatibility:
- `ExtractedEntity` = `ContentEntity`
- `Document` = `UnifiedDocument` 
- `DocumentMetadata` = `UnifiedDocumentMetadata`
- `BaseKnowledgeModel` = `KnowledgeBaseEntity`
- `KbBaseEntity` = `KnowledgeBaseEntity`
- `KbPerson` = `PersonEntity`
- `KbOrganization` = `OrganizationEntity`
- `KbLocation` = `LocationEntity`
- `KbDateEntity` = `DateEntity`
- `KbTodoItem` = `TodoEntity`
- `KbWikiLink` = `LinkEntity`
- `KbDocument` = `UnifiedDocument`

### Property Mappings
Models include backward-compatible properties:
- `TodoEntity.is_checked` → `TodoEntity.is_completed`
- `TodoEntity.text` → `TodoEntity.description`
- `LinkEntity.target_page` → `LinkEntity.target_path`
- `ContentEntity.extracted_from_text_span` → `(start_char, end_char)`

### Factory Functions
Use `create_entity()` for automatic entity type selection based on label.

## Testing Updates

### Test Imports
Update test imports to use unified models:

```python
# tests/models/test_entities.py
from knowledgebase_processor.models import (
    ContentEntity,
    PersonEntity,
    create_entity
)

def test_entity_creation():
    entity = create_entity("John Doe", "PERSON", 0, 8)
    assert isinstance(entity, PersonEntity)
    assert entity.text == "John Doe"
    assert entity.entity_type == "person"
```

### Test Helpers
Update test helpers to work with unified models:

```python
def create_test_document():
    return UnifiedDocument(
        id="test_doc",
        path="test.md",
        content="Test content",
        metadata=UnifiedDocumentMetadata(
            document_id="test_doc",
            title="Test Document"
        )
    )
```

## Benefits

1. **Reduced Complexity**: Single inheritance hierarchy instead of three
2. **Consistent RDF Support**: All models support RDF serialization
3. **Better Type Safety**: Clear entity type hierarchy
4. **Simplified Processing**: Metadata integrated into documents
5. **Improved Maintainability**: Less duplicate code
6. **Future-Proof**: Extensible architecture for new entity types

## Rollback Plan

If issues arise during migration:

1. Keep original model files intact initially
2. Use feature flags to switch between old/new models
3. Run parallel testing with both model sets
4. Gradual service-by-service migration
5. Maintain data migration scripts for storage

## Timeline

- **Week 1**: Create unified models, maintain aliases
- **Week 2**: Update core processors and services
- **Week 3**: Update tests and documentation
- **Week 4**: Deprecate old models, monitor for issues
- **Week 5+**: Remove deprecated models after stability confirmed

## Support

For questions or issues during migration:
- Review this guide and the unified.py module documentation
- Check test examples in the updated test suite
- Consult the architecture decision records (ADRs)