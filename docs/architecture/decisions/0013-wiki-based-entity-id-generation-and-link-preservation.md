# ADR-0013: Wiki-Based Entity ID Generation and Link Preservation

**Date:** 2025-07-21

**Status:** Proposed

## Context

The current entity ID generation strategy uses random UUID suffixes (e.g., `/Organization/galaxy_dynamics_co_7a705a38`), which creates several critical problems:

1. **Duplicate Entities**: The same real-world entity gets multiple IDs across different documents
2. **Broken Wiki Links**: Wiki-style links cannot reliably reference entities
3. **Query Complexity**: Finding all references to an entity requires complex queries
4. **Storage Inefficiency**: Duplicate entities consume unnecessary storage
5. **Loss of Semantic Relationships**: Connections between entity occurrences are lost
6. **Missing Document Entities**: Documents themselves are not represented as entities in the knowledge graph
7. **Link Text Normalization Issues**: Normalizing wiki link text breaks compatibility with file system paths

With our commitment to building a knowledge graph from wiki-style documents ([ADR-0009](0009-knowledge-graph-rdf-store.md)), we need a comprehensive strategy that supports wiki linking conventions, ensures entity uniqueness, and properly represents documents as first-class entities.

## Decision

We will adopt a deterministic, hierarchical entity ID generation system based on wiki linking principles, combined with careful wiki link preservation to maintain file system compatibility.

### Core Principles

1. **Deterministic IDs**: Entity IDs will be generated from entity properties (name, type, path) without random components
2. **Document-Centric Hierarchy**: Documents are root entities with IDs based on file paths
3. **Global Entity Deduplication**: Named entities (Person, Organization, etc.) will have consistent IDs across all documents
4. **Wiki Link Compatibility**: Support for wiki-style links with automatic resolution
5. **Wiki Link Text Preservation**: Original wiki link text must be preserved for file system compatibility
6. **Complete Document Representation**: Every processed document becomes a first-class entity

### ID Patterns

```
# Root Entities
/Document/{normalized-file-path}
/Tag/{normalized-tag-name}
/Person/{normalized-name}
/Organization/{normalized-name}
/Location/{normalized-name}
/Project/{normalized-name}

# Document-Scoped Entities
/Document/{path}/Section/{heading-path}
/Document/{path}/TodoItem/{line}-{content-hash}
/Document/{path}/CodeBlock/{content-hash}

# Virtual Entities
/PlaceholderDocument/{normalized-name}
```

### Normalization Rules

All text normalization for IDs follows these rules:
1. Unicode NFKD normalization
2. Convert to lowercase
3. Replace non-alphanumeric with hyphens
4. Remove consecutive hyphens
5. Trim hyphens from start/end

**Important**: Wiki link text is NOT normalized during link resolution to preserve file system compatibility.

### Dual-Path Document Model

Documents maintain two path representations to support both normalized IDs and wiki link resolution:

```python
class KbDocument:
    kb_id: str                    # Normalized: "/Document/daily-notes/2024-11-07-thursday"
    original_path: str            # Preserved: "Daily Notes/2024-11-07 Thursday.md"
    path_without_extension: str   # For wikis: "Daily Notes/2024-11-07 Thursday"
    title: str                    # Display name from metadata or filename
```

### Wiki Link Resolution Strategy

Resolution follows this priority order:
1. **Document Lookup**: Try to find document by original path (with various extensions)
2. **Typed Entity Resolution**: Try to resolve as typed entity (person:, org:, etc.)
3. **Placeholder Creation**: Create placeholder document for unresolved links

### Always Create Document Entities

Every processed document will have a corresponding Document entity:
- Document entities are created regardless of whether the document contains other entities
- Document metadata (title, created, modified, tags) are stored as entity properties
- Documents serve as the primary nodes in the wiki graph

## Rationale

This comprehensive approach provides:

### Wiki Functionality
- **File System Compatibility**: Wiki links work with actual file naming conventions
- **User Expectations**: Links behave exactly as users expect in wiki systems
- **Case Sensitivity**: Respects file system case sensitivity requirements
- **Existing Content**: Maintains compatibility with existing wiki links

### Entity Management
- **Consistency**: Same entity always gets the same ID across documents
- **Discoverability**: Predictable IDs make entities easier to find and reference
- **Performance**: No need for complex deduplication queries during runtime
- **Clarity**: ID structure reveals entity type and relationships

### Graph Completeness
- **Complete Representation**: Every document is represented in the knowledge graph
- **Rich Metadata**: Document properties are properly stored and queryable
- **Relationship Modeling**: Enables queries like "all documents mentioning person X"
- **Wiki Philosophy**: Documents (pages) are the fundamental unit in wiki systems

## Implementation Strategy

### Phase 1: Core Infrastructure
1. Create new ID generation module with normalization functions
2. Implement dual-path document model
3. Create document registry for efficient path-based lookups

### Phase 2: Entity Management
1. Add entity registry for deduplication and alias management
2. Implement deterministic ID generation for all entity types
3. Create placeholder document support

### Phase 3: Wiki Link Enhancement
1. Enhance wiki link resolution with preserved text matching
2. Implement typed entity resolution (person:, org:, etc.)
3. Add comprehensive link resolution testing

### Phase 4: Integration
1. Refactor existing entity services to use new IDs
2. Update RDF converter to handle document entities properly
3. Ensure all entities are properly represented in graph

### Phase 5: Migration
1. Create migration tools for existing data
2. Map old random IDs to new deterministic IDs
3. Validate migrated data integrity

## Implementation Notes

### Document Registry

A new service is required for efficient path-based document lookups:

```python
class DocumentRegistry:
    def find_by_wiki_link(self, link_text: str) -> Optional[str]:
        # Try with common extensions
        for ext in ['', '.md', '.markdown', '.txt']:
            if doc_id := self.find_by_path(link_text + ext):
                return doc_id
        return None
    
    def register_document(self, original_path: str, normalized_id: str) -> None:
        # Store both path mappings for efficient lookup
        pass
```

### RDF Representation

Documents are fully represented in RDF with all metadata:

```turtle
<http://example.org/kb/Document/daily-notes/2024-11-07-thursday> a kb:Document ;
    rdfs:label "Daily Note 2024-11-07 Thursday" ;
    kb:originalPath "Daily Notes/2024-11-07 Thursday.md" ;
    kb:created "2024-11-07T08:54:54-05:00"^^xsd:dateTime ;
    kb:modified "2024-11-07T10:30:00-05:00"^^xsd:dateTime ;
    kb:hasEntity <http://example.org/kb/Person/alex-cipher> ;
    kb:hasTag <http://example.org/kb/Tag/meeting> .
```

### Entity Deduplication

The entity registry ensures consistent entity identification:

```python
class EntityRegistry:
    def get_or_create_entity(self, entity_type: str, properties: dict) -> str:
        # Generate deterministic ID
        entity_id = self.generate_id(entity_type, properties)
        
        # Check for existing entity and merge if needed
        if existing := self.find_entity(entity_id):
            return self.merge_entities(existing, properties)
        
        return self.create_entity(entity_id, properties)
```

## Consequences

### Positive

1. **Eliminates Duplicates**: Each real-world entity has exactly one ID across all documents
2. **Enables True Wiki Links**: `[[Person Name]]` and `[[Document Name]]` reliably resolve
3. **Simplifies Queries**: Direct ID lookups instead of complex text matching
4. **Reduces Storage**: No duplicate entities in the graph
5. **Improves User Experience**: Predictable, human-readable IDs
6. **Complete Graph**: Every document is represented with full metadata
7. **Wiki Compatibility**: Links work exactly as users expect
8. **Rich Queries**: Can query document properties and relationships
9. **Backwards Compatible**: Existing wiki links continue to work

### Negative

1. **Migration Complexity**: Existing data must be migrated to new IDs
2. **Implementation Scope**: Touches many parts of the codebase
3. **Storage Overhead**: Storing both normalized and original paths
4. **Dual-Path Complexity**: Two-path system adds implementation complexity
5. **Collision Potential**: Different entities might normalize to the same ID (rare but needs handling)
6. **Breaking Change**: Not backwards compatible with existing random IDs

### Neutral

1. **Performance Impact**: ID generation slightly more complex but offset by elimination of deduplication queries
2. **Storage Format**: IDs are longer but more meaningful
3. **Query Updates**: SPARQL queries need updating for new ID format
4. **Path Lookups**: Document registry required for efficient resolution

## Alternatives Considered

### 1. Keep Current Random ID System
- **Pros**: No migration needed, simple implementation
- **Cons**: Perpetuates all current problems with duplicates and broken wiki links

### 2. Normalize Wiki Link Text
- **Pros**: Simpler ID matching logic
- **Cons**: Breaks file system compatibility, makes existing wiki links unusable

### 3. Separate Document and Entity ID Systems
- **Pros**: Could optimize each system independently
- **Cons**: Creates complexity with multiple ID schemes, breaks unified wiki linking

### 4. Content-Based Hashing for IDs
- **Pros**: Deterministic, no collisions
- **Cons**: Opaque IDs, changes with any content update, not wiki-friendly

### 5. Incremental Numeric IDs
- **Pros**: Simple, no collisions
- **Cons**: Not deterministic, requires central counter, meaningless IDs

## Related Decisions

- [ADR-0009: Knowledge Graph and RDF Store](0009-knowledge-graph-rdf-store.md) - Establishes need for proper entity identification
- [ADR-0010: Entity Modeling for RDF Serialization](0010-entity-modeling-for-rdf-serialization.md) - Defines entity model this ID system supports
- [ADR-0012: Entity Modeling with Wiki-Based Architecture](0012-entity-modeling-with-wiki-based-architecture.md) - Updated entity modeling approach
- [ADR-0002: Pydantic for Data Models](0002-pydantic-for-data-models.md) - Models will need updating for new ID strategy

## Notes

- Entity ID format is inspired by REST URL patterns for familiarity
- Normalization rules based on common wiki software practices
- Collision handling will be rare but important to implement correctly
- Performance testing should verify ID generation overhead is acceptable
- Path preservation is essential for wiki functionality
- Document entity creation fills a significant gap in the current implementation
- This represents a foundational change that enables true wiki-style knowledge graphs