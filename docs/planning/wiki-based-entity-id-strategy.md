# Wiki-Based Entity ID Generation Strategy

## Core Principles

### 1. Document-Centric Architecture
- Documents are first-class entities with stable IDs based on their file paths
- All other entities exist in relation to documents
- Wiki links naturally reference documents or entities within documents

### 2. Entity Hierarchy

```
Root Entities (Global Scope)
├── Documents
├── Tags
└── Named Entities (deduplicated across documents)
    ├── People
    ├── Organizations
    ├── Locations
    └── Projects

Document-Scoped Entities
├── Sections (based on heading structure)
├── Todo Items
├── Frontmatter Properties
└── Code Blocks
```

## ID Generation Algorithms

### 1. Document IDs
```
Pattern: /Document/{normalized-file-path}
Example: /Document/daily-notes/2024-11-07-Thursday
```
- Remove file extension
- Preserve directory structure
- Replace spaces with hyphens
- Lowercase normalization

### 2. Tag IDs
```
Pattern: /Tag/{normalized-tag-name}
Example: /Tag/meeting-notes
```
- Lowercase normalization
- Replace spaces with hyphens
- Remove special characters except hyphens

### 3. Named Entity IDs (Global)
```
Pattern: /{EntityType}/{normalized-name}
Examples:
- /Person/alex-cipher
- /Organization/galaxy-dynamics-co
- /Location/san-francisco
- /Project/knowledgebase-processor
```
- Type-specific normalization rules
- No random suffixes
- Consistent across all documents

### 4. Document-Scoped Entity IDs
```
Pattern: /Document/{doc-path}/{entity-type}/{deterministic-identifier}
Examples:
- /Document/daily-notes/2024-11-07/TodoItem/hash-of-todo-text
- /Document/daily-notes/2024-11-07/Section/meetings
- /Document/project-docs/readme/Section/installation
```

### 5. Wiki Link Resolution

#### Direct Document Links
```
[[Daily Note 2024-11-07]] → /Document/daily-note-2024-11-07
[[projects/KB Processor]] → /Document/projects/kb-processor
```

#### Entity References
```
[[Alex Cipher]] → /Person/alex-cipher (if person entity exists)
                → /Document/alex-cipher (if document exists)
                → /PlaceholderDocument/alex-cipher (if neither exists)
```

#### Tagged Links
```
[[person:Alex Cipher]] → /Person/alex-cipher
[[org:Galaxy Dynamics]] → /Organization/galaxy-dynamics
[[doc:README]] → /Document/readme
```

## Placeholder Documents

When a wiki link references a non-existent document:
```
Pattern: /PlaceholderDocument/{normalized-link-target}
Properties:
- title: Original link text
- status: "placeholder"
- referenced_by: [list of documents that link to it]
```

## Entity Type Detection

### From Frontmatter
```yaml
type: person
name: Alex Cipher
# Creates: /Person/alex-cipher
```

### From Context
- Links in "Attendees:" section → Person entities
- Links in "Company:" field → Organization entities
- Links with location prepositions → Location entities

### From Tags
```
#person/alex-cipher → /Person/alex-cipher
#org/galaxy-dynamics → /Organization/galaxy-dynamics
#location/san-francisco → /Location/san-francisco
```

## Deduplication Strategy

1. **Normalization Rules:**
   - Lowercase all text
   - Replace whitespace and special chars with hyphens
   - Remove consecutive hyphens
   - Trim hyphens from start/end
   - Apply Unicode normalization (NFKD)

2. **Alias Handling:**
   ```
   "Alex Cipher", "A. Cipher", "Alexander Cipher" → /Person/alex-cipher
   Managed through alias properties on the canonical entity
   ```

3. **Collision Resolution:**
   - Use type prefixes to prevent collisions
   - Add minimal disambiguation only when necessary
   - Example: /Person/john-smith-1, /Person/john-smith-2

## Implementation Considerations

1. **Backwards Compatibility:**
   - Migration tool to update existing IDs
   - Redirect/alias system for old IDs

2. **Performance:**
   - Cache normalized forms
   - Index by both original and normalized names

3. **Validation:**
   - Ensure ID uniqueness within type
   - Validate ID format compliance
   - Check for reserved words/patterns