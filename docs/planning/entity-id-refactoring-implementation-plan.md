# DEPRECATED: Entity ID Refactoring Implementation Plan

**This document has been superseded by the [Unified Entity ID Implementation Plan](unified-entity-id-implementation-plan.md).**

This original plan predates critical discoveries about wiki link preservation and document entity creation. The unified plan incorporates all learnings and aligns with the final ADR-0012 and ADR-0013 decisions.

For current implementation guidance, please refer to:
- [Unified Entity ID Implementation Plan](unified-entity-id-implementation-plan.md)
- [ADR-0012: Entity Modeling with Wiki-Based Architecture](../architecture/decisions/0012-entity-modeling-with-wiki-based-architecture.md)  
- [ADR-0013: Wiki-Based Entity ID Generation and Link Preservation](../architecture/decisions/0013-wiki-based-entity-id-generation-and-link-preservation.md)

---

# Entity ID Refactoring Implementation Plan

## Overview

This plan outlines the steps to refactor the entity ID generation system from random UUID-based IDs to deterministic, wiki-compatible IDs.

## Phase 1: Foundation (Week 1)

### 1.1 Create New ID Generation Module
**File**: `src/knowledgebase_processor/utils/id_generator.py`

```python
# Core components to implement:
- normalize_text(text: str) -> str
- generate_document_id(file_path: str) -> str
- generate_tag_id(tag_text: str) -> str
- generate_person_id(name: str) -> str
- generate_organization_id(name: str) -> str
- generate_location_id(name: str, parent: Optional[str]) -> str
- generate_project_id(name: str) -> str
- generate_todo_id(document_id: str, todo_text: str, line_number: int) -> str
- generate_section_id(document_id: str, heading: str, parent_path: List[str]) -> str
- generate_placeholder_id(link_text: str) -> str
```

### 1.2 Create Entity Registry
**File**: `src/knowledgebase_processor/services/entity_registry.py`

```python
# Components:
- EntityRegistry class for managing entity deduplication
- In-memory cache for fast lookups
- Alias resolution system
- Collision detection and handling
```

### 1.3 Update Base Models
**Files to modify**:
- `src/knowledgebase_processor/models/kb_entities.py`
- `src/knowledgebase_processor/models/entities.py`

**Changes**:
- Add `aliases` field to Person, Organization, Location entities
- Add `canonical_id` field for tracking the primary ID
- Remove UUID generation from kb_id assignment

## Phase 2: Core Refactoring (Week 2)

### 2.1 Refactor Entity Service
**File**: `src/knowledgebase_processor/services/entity_service.py`

**Changes**:
```python
# Replace current generate_kb_id method:
def generate_kb_id(self, entity_type_str: str, text: str) -> str:
    # Remove: return str(KB[f"{entity_type_str}/{slug}_{uuid.uuid4().hex[:8]}"])
    # Add: Use new id_generator module
    
    if entity_type_str == "Person":
        return id_generator.generate_person_id(text)
    elif entity_type_str == "Organization":
        return id_generator.generate_organization_id(text)
    # ... etc
```

### 2.2 Refactor Processor
**File**: `src/knowledgebase_processor/processor/processor.py`

**Changes**:
- Update `_generate_kb_id` method to use new ID generator
- Add entity deduplication logic using EntityRegistry
- Implement proper document ID generation from file paths

### 2.3 Add Document Entity Model
**File**: `src/knowledgebase_processor/models/kb_entities.py`

```python
class KbDocument(KbBaseEntity):
    """Represents a document in the knowledge base."""
    path: str
    title: str
    document_type: Optional[str]
    content_hash: str
    # Remove frontmatter fields that should be properties
```

### 2.4 Create PlaceholderDocument Model
**File**: `src/knowledgebase_processor/models/kb_entities.py`

```python
class KbPlaceholderDocument(KbBaseEntity):
    """Represents a non-existent wiki link target."""
    title: str
    referenced_by: List[str]
    suggested_type: Optional[str]
```

## Phase 3: Wiki Link Integration (Week 3)

### 3.1 Enhance Wiki Link Extractor
**File**: `src/knowledgebase_processor/extractor/wikilink_extractor.py`

**Enhancements**:
- Parse typed wiki links (e.g., `[[person:Alex Cipher]]`)
- Extract context for type inference
- Generate appropriate entity IDs

### 3.2 Create Wiki Link Resolver
**File**: `src/knowledgebase_processor/services/wikilink_resolver.py`

```python
class WikiLinkResolver:
    def resolve_link(self, link_text: str, context: Dict) -> ResolvedLink:
        # Determine if link is to document, entity, or placeholder
        # Apply type detection rules
        # Return resolved entity ID
```

### 3.3 Update RDF Converter
**File**: `src/knowledgebase_processor/rdf_converter/converter.py`

**Changes**:
- Remove random ID handling
- Add proper document entity generation
- Implement property vs entity distinction

## Phase 4: Property Distinction (Week 3-4)

### 4.1 Refactor Frontmatter Processing
**File**: `src/knowledgebase_processor/extractor/frontmatter.py`

**Changes**:
- Identify which fields should be properties vs entities
- Store properties in document metadata
- Extract entities for separate processing

### 4.2 Update RDF Generation
**File**: `src/knowledgebase_processor/rdf_converter/converter.py`

**Changes**:
```python
def document_to_rdf(self, document: KbDocument, metadata: DocumentMetadata) -> Graph:
    # Add document as entity
    doc_uri = URIRef(document.kb_id)
    
    # Add properties as literals
    for prop, value in metadata.properties.items():
        g.add((doc_uri, KB[prop], Literal(value)))
    
    # Add entity references
    for entity_ref in metadata.entity_references:
        g.add((doc_uri, KB.references, URIRef(entity_ref.kb_id)))
```

## Phase 5: Testing and Migration (Week 4)

### 5.1 Create Test Suite
**Files**:
- `tests/utils/test_id_generator.py`
- `tests/services/test_entity_registry.py`
- `tests/services/test_wikilink_resolver.py`

### 5.2 Create Migration Tool
**File**: `scripts/migrate_entity_ids.py`

```python
# Tool to migrate existing data:
- Load existing RDF data
- Map old IDs to new deterministic IDs
- Generate redirect/alias mappings
- Update all references
```

### 5.3 Integration Tests
**File**: `tests/integration/test_entity_id_generation.py`

Test scenarios:
- Document with multiple references to same entity
- Wiki links to non-existent documents
- Entity deduplication across documents
- Property vs entity distinction

## Implementation Order

1. **Start with foundation** - ID generator and registry (low risk)
2. **Add new models** - Document and Placeholder entities
3. **Refactor services** - Update ID generation in existing code
4. **Enhance extractors** - Better wiki link and type detection
5. **Update RDF layer** - Proper property/entity handling
6. **Test thoroughly** - Unit and integration tests
7. **Create migration** - Tools for existing data

## Risk Mitigation

### Backwards Compatibility
- Keep old ID format support during transition
- Create ID mapping table
- Provide migration tools

### Performance Impact
- Use efficient caching in EntityRegistry
- Index entities by normalized names
- Batch entity lookups

### Data Integrity
- Validate all generated IDs
- Log ID collisions for review
- Maintain audit trail of ID changes

## Success Criteria

1. **No Duplicate Entities**: Same entity has consistent ID across documents
2. **Wiki Link Support**: All wiki link patterns resolve correctly
3. **Property Distinction**: Only true entities in knowledge graph
4. **Performance**: ID generation < 1ms per entity
5. **Migration Success**: All existing data migrated without loss
6. **Test Coverage**: >90% coverage of new ID generation code

## Rollback Plan

If issues arise:
1. Keep old ID generation code available
2. Feature flag for new vs old ID generation
3. Ability to regenerate IDs if needed
4. Database backup before migration

## Timeline

- **Week 1**: Foundation components
- **Week 2**: Core refactoring
- **Week 3**: Wiki integration & properties
- **Week 4**: Testing & migration
- **Week 5**: Buffer for issues & documentation

## Dependencies

- No external library changes required
- Requires coordination with RDF store updates
- May impact downstream SPARQL queries

## Documentation Updates

1. Update ADR-0010 with new entity model approach
2. Create new ADR for wiki-based ID generation
3. Update API documentation
4. Create migration guide
5. Update contributor guidelines