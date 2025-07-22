# Entity ID Duplication Analysis

## Current Issue

The knowledge base processor is creating duplicate entities with different IDs for the same conceptual entity. This is caused by the current ID generation strategy that appends random UUID suffixes to entity identifiers.

### Examples from RDF Output

Looking at the generated RDF for `daily-note-2024-11-07-Thursday.ttl`:

1. **Duplicate Organizations:**
   - "Galaxy Dynamics Co." appears twice with different IDs:
     - `<http://example.org/kb/Organization/galaxy_dynamics_co_04e2d63a>`
     - `<http://example.org/kb/Organization/galaxy_dynamics_co_7a705a38>`

2. **Duplicate Date Entities:**
   - "daily" appears twice with different IDs:
     - `<http://example.org/kb/DateEntity/daily_121df41b>`
     - `<http://example.org/kb/DateEntity/daily_6d899477>`

### Root Cause

The ID generation code in both `processor.py` and `entity_service.py` uses:

```python
return str(KB[f"{entity_type_str}/{slug}_{uuid.uuid4().hex[:8]}"])
```

This appends a random 8-character hex string to each entity ID, making it impossible to:
- Identify the same entity across different documents
- Create stable links between entities
- Build a coherent knowledge graph

## Impact

1. **Data Integrity:** The same real-world entity (person, organization, location) gets multiple representations in the graph
2. **Query Complexity:** Finding all references to an entity requires complex queries instead of simple ID lookups
3. **Link Breakage:** Wiki-style links cannot reliably reference entities
4. **Storage Inefficiency:** Duplicate entities consume unnecessary storage
5. **Semantic Loss:** Relationships between occurrences of the same entity are lost

## Requirements for Solution

1. **Deterministic IDs:** Entity IDs must be reproducible based on entity properties
2. **Document Context:** Sub-document entities should include parent document ID for uniqueness
3. **Wiki Compatibility:** Support wiki-style linking conventions
4. **Type Safety:** Different entity types should have distinct ID patterns
5. **Property Distinction:** Document properties should not become separate entities