# Wiki-Based Entity ID Architecture Summary

## Executive Summary

This architectural update addresses the critical issue of duplicate entities in the knowledge base by introducing a deterministic, wiki-compatible entity ID generation system. The new approach ensures that each real-world entity has exactly one ID across all documents, enabling true wiki-style linking and eliminating data duplication.

## Problem Statement

The current system generates entity IDs with random UUID suffixes (e.g., `/Organization/galaxy_dynamics_co_7a705a38`), causing:
- Multiple IDs for the same entity
- Broken wiki-style links
- Complex queries to find all entity references
- Wasted storage on duplicate data
- Loss of semantic relationships

## Solution Overview

### Core Design Principles

1. **Deterministic IDs**: Generated from entity properties without random components
2. **Document-First**: Documents are root entities with IDs based on file paths
3. **Wiki Compatibility**: Full support for `[[Wiki Links]]` with automatic resolution
4. **Clear Entity Hierarchy**: Distinction between global entities, document-scoped entities, and properties
5. **Smart Deduplication**: Entities with the same normalized name share the same ID

### Entity Types and ID Patterns

| Entity Type | ID Pattern | Example |
|------------|------------|---------|
| Document | `/Document/{path}` | `/Document/daily-notes/2024-11-07` |
| Person | `/Person/{name}` | `/Person/alex-cipher` |
| Organization | `/Organization/{name}` | `/Organization/galaxy-dynamics` |
| Tag | `/Tag/{name}` | `/Tag/meeting-notes` |
| TodoItem | `/Document/{path}/TodoItem/{line}-{hash}` | `/Document/daily/TodoItem/15-a3f5b2c8d1` |
| PlaceholderDocument | `/PlaceholderDocument/{name}` | `/PlaceholderDocument/future-ideas` |

### Property vs Entity Rules

**Entities** (have their own ID):
- People, organizations, locations, projects
- Documents and tags
- Complex structures (todos, sections)
- Anything referenced across documents

**Properties** (stored as literals):
- Timestamps (created, modified)
- Simple metadata (status, version)
- Computed values (word count)
- Document-specific attributes

## Implementation Plan

### Phase 1: Foundation (Week 1)
- Create ID generation module with normalization
- Build entity registry for deduplication
- Update base entity models

### Phase 2: Core Refactoring (Week 2)
- Refactor entity service to use new IDs
- Update processor with deduplication logic
- Add Document and PlaceholderDocument entities

### Phase 3: Wiki Integration (Week 3)
- Enhance wiki link parser
- Create link resolver service
- Update RDF converter

### Phase 4: Testing & Migration (Week 4)
- Comprehensive test suite
- Migration tools for existing data
- Performance optimization

## Key Benefits

1. **Data Integrity**: Each entity has one canonical ID
2. **True Wiki Links**: `[[Person Name]]` reliably links to the person
3. **Simplified Queries**: Direct ID lookups instead of text searches
4. **Storage Efficiency**: No duplicate entities
5. **Better UX**: Predictable, human-readable IDs

## Technical Details

### Text Normalization Algorithm
```python
def normalize_text(text: str) -> str:
    # Unicode normalization (NFKD)
    # Convert to lowercase
    # Replace non-alphanumeric with hyphens
    # Remove consecutive hyphens
    # Trim hyphens from edges
```

### Wiki Link Resolution Flow
1. Parse link text and type hints
2. Check for existing document
3. Check for existing entity
4. Create placeholder if needed
5. Return resolved entity ID

## Migration Strategy

1. Generate mapping from old to new IDs
2. Update all entity references
3. Maintain backwards compatibility during transition
4. Provide tools for data migration

## Success Metrics

- **Zero Duplicates**: Same entity always gets same ID
- **100% Link Resolution**: All wiki links resolve correctly
- **Performance**: < 1ms per ID generation
- **Test Coverage**: > 90% of new code
- **Smooth Migration**: No data loss

## Documentation Updates

- [ADR-0012: Wiki-Based Entity ID Generation](../architecture/decisions/0012-wiki-based-entity-id-generation.md)
- [ADR-0010 Update: Entity Modeling with Wiki-Based Architecture](../architecture/decisions/0010-entity-modeling-for-rdf-serialization-update.md)

## Related Documents

1. [Entity ID Duplication Analysis](entity-id-duplication-analysis.md)
2. [Wiki-Based Entity ID Strategy](wiki-based-entity-id-strategy.md)
3. [Entity Hierarchy Architecture](entity-hierarchy-architecture.md)
4. [Entity Types and ID Algorithms](entity-types-and-id-algorithms.md)
5. [Property vs Entity Rules](property-vs-entity-rules.md)
6. [Implementation Plan](entity-id-refactoring-implementation-plan.md)
7. [Test Cases](entity-id-generation-test-cases.md)

## Next Steps

1. Review and approve the architectural design
2. Create GitHub issue for implementation
3. Begin Phase 1 implementation
4. Set up monitoring for duplicate detection
5. Plan user communication about changes

## Conclusion

This architectural update transforms the knowledge base from a collection of disconnected documents with duplicate entities into a true knowledge graph with stable, wiki-compatible entity identification. The deterministic ID generation ensures data integrity while enabling powerful wiki-style linking and querying capabilities.