# Property vs Entity Distinction Rules

## Core Principle

The fundamental question: **"Does this data represent an independent concept that exists beyond a single document?"**

## Decision Framework

### Should Be an Entity If:

1. **Has Independent Identity**
   - Can be referenced from multiple documents
   - Has meaning outside the context of a single document
   - Examples: People, Organizations, Projects

2. **Requires Unique Identification**
   - Needs to be linked to consistently
   - Benefits from deduplication across documents
   - Examples: Tags, Locations

3. **Has Complex Relationships**
   - Relates to other entities
   - Part of a larger knowledge graph
   - Examples: Meeting attendees, Project team members

4. **Evolves Over Time**
   - Properties change independently of documents
   - Has its own lifecycle
   - Examples: Project status, Person roles

### Should Be a Property If:

1. **Document-Specific Metadata**
   - Only meaningful in context of the document
   - Doesn't need cross-referencing
   - Examples: created date, word count, file size

2. **Simple Scalar Values**
   - Basic data types without complex structure
   - No need for independent identity
   - Examples: boolean flags, timestamps, numbers

3. **Immutable Document Attributes**
   - Set once and never changes
   - Intrinsic to the document itself
   - Examples: creation date, original author

4. **Formatting or Display Information**
   - Presentation-related data
   - No semantic meaning for knowledge graph
   - Examples: font settings, color themes

## Specific Examples

### Frontmatter Fields

| Field | Property or Entity | Reasoning |
|-------|-------------------|-----------|
| `title` | Property | Document-specific, display name |
| `created` | Property | Immutable document metadata |
| `modified` | Property | Document-specific timestamp |
| `tags` | Entity (Tag) | Referenced across documents |
| `author` | Entity (Person) | Independent identity, cross-referenced |
| `status` | Property | Simple scalar, document-specific |
| `type` | Property | Document classification |
| `attendees` | Entity (Person) | Independent people, relationships |
| `project` | Entity (Project) | Cross-document reference |
| `word_count` | Property | Computed value, document-specific |
| `language` | Property | Simple attribute |
| `version` | Property | Document-specific version |

### Content Elements

| Element | Property or Entity | Reasoning |
|---------|-------------------|-----------|
| Heading text | Property | Part of document structure |
| Todo item | Entity (TodoItem) | Complex structure, may reference people |
| Wiki link | Entity (various) | References to other entities |
| Code block | Entity (CodeBlock) | Complex content, may be referenced |
| Bold text | Property | Formatting only |
| Table | Entity (Table) | Complex structure, queryable |
| Footnote | Property | Document-specific annotation |
| Image alt text | Property | Descriptive metadata |

### Special Cases

#### 1. Author vs Creator
- **Author as Entity**: When author is a person who exists in the knowledge base
  ```yaml
  author: "[[Alex Cipher]]"  # Entity reference
  ```
- **Creator as Property**: When it's just metadata about who created the file
  ```yaml
  created_by: "system"  # Simple property
  ```

#### 2. Dates and Times
- **Meeting Date as Property**: Specific to that document
  ```yaml
  meeting_date: 2024-11-07  # Property
  ```
- **Project Deadline as Entity Property**: Belongs to the Project entity
  ```yaml
  project: "[[Q4 Planning]]"  # Links to Project entity with deadline
  ```

#### 3. Status Fields
- **Document Status as Property**: State of the document
  ```yaml
  status: "draft"  # Property
  ```
- **Project Status**: Property of the Project entity, not the document

#### 4. Lists and Collections
- **Simple List as Property**: No complex relationships
  ```yaml
  categories: ["tech", "meeting", "planning"]  # Property
  ```
- **People List as Entities**: Each item has identity
  ```yaml
  attendees: 
    - "[[Alex Cipher]]"      # Entity
    - "[[Jane Smith]]"       # Entity
  ```

## Implementation Guidelines

### 1. Entity Extraction Rules

```python
def should_be_entity(field_name: str, value: Any, context: Dict) -> bool:
    """Determine if a field should be treated as an entity reference."""
    
    # Explicit entity fields
    entity_fields = {
        'author', 'authors', 'attendees', 'participants',
        'assignee', 'assignees', 'reviewer', 'reviewers',
        'team', 'members', 'project', 'projects',
        'organization', 'company', 'client', 'customer'
    }
    
    if field_name.lower() in entity_fields:
        return True
    
    # Wiki link pattern
    if isinstance(value, str) and '[[' in value and ']]' in value:
        return True
    
    # Tag pattern
    if isinstance(value, str) and value.startswith('#'):
        return True
    
    # List of potential entities
    if isinstance(value, list) and value:
        return any(should_be_entity(field_name, item, context) for item in value)
    
    return False
```

### 2. Property Storage

Properties should be stored as:
- **Document metadata** in the document model
- **RDF literals** with appropriate datatypes
- **Not as separate entities** in the knowledge graph

Example RDF:
```turtle
<http://example.org/kb/Document/daily-notes/2024-11-07> 
    kb:created "2024-11-07T09:00:00Z"^^xsd:dateTime ;  # Property
    kb:wordCount 1500^^xsd:integer ;                    # Property
    kb:hasAuthor <http://example.org/kb/Person/alex-cipher> ;  # Entity reference
    kb:hasTag <http://example.org/kb/Tag/meeting-notes> .      # Entity reference
```

### 3. Migration Considerations

When refactoring existing code:

1. **Identify Current Entities**: Find what's currently being created as entities
2. **Apply Rules**: Determine what should be properties
3. **Update Models**: Modify Pydantic models to reflect proper classification
4. **Adjust RDF Generation**: Ensure properties become literals, not entity references
5. **Test Queries**: Verify SPARQL queries work with new structure

## Benefits of Proper Distinction

1. **Reduced Complexity**: Fewer unnecessary entities in the graph
2. **Better Performance**: Less data to index and query
3. **Clearer Semantics**: Graph represents actual relationships
4. **Easier Maintenance**: Clear rules prevent confusion
5. **Accurate Deduplication**: Only deduplicate true entities

## Common Mistakes to Avoid

1. **Over-Entityization**: Making everything an entity
   - Wrong: Every date becomes a DateEntity
   - Right: Only significant dates (deadlines, milestones)

2. **Under-Entityization**: Missing important relationships
   - Wrong: Storing people names as strings
   - Right: Creating Person entities for cross-referencing

3. **Inconsistent Treatment**: Same concept treated differently
   - Wrong: Author as entity in some docs, property in others
   - Right: Consistent rules based on context

4. **Context Ignorance**: Not considering document type
   - Wrong: All "name" fields become entities
   - Right: Context-aware decisions (person doc vs. note)