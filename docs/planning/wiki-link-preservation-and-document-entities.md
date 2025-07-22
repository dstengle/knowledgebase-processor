# Critical Design Revisions: Wiki Link Preservation and Document Entities

## Issue 1: Wiki Link Text Must Be Preserved

**Problem**: The current design proposes normalizing wiki link text, which would break links to actual documents.

**Example**:
- Wiki link: `[[Daily Note 2024-11-07 Thursday]]`
- Current design would normalize to: `/Document/daily-note-2024-11-07-thursday`
- But the actual file might be: `Daily Note 2024-11-07 Thursday.md`

**Solution**: Wiki links must preserve the original text exactly as written.

### Revised Wiki Link Resolution

```python
class WikiLink:
    """Represents a wiki link with preserved original text"""
    original_text: str  # Exactly as written: "Daily Note 2024-11-07 Thursday"
    link_type: Optional[str]  # From prefix: "person", "org", etc.
    target_path: str  # For file lookup: "Daily Note 2024-11-07 Thursday.md"
    resolved_entity_id: Optional[str]  # After resolution
```

### Document Entity ID Generation

Documents should have TWO key properties:
1. **Original Path**: Preserved exactly for wiki link resolution
2. **Normalized ID**: For consistent entity identification

```python
class KbDocument(KbBaseEntity):
    """Document entity with preserved path information"""
    kb_id: str  # Normalized: /Document/daily-notes/2024-11-07-thursday
    original_path: str  # Preserved: "Daily Notes/2024-11-07 Thursday.md"
    title: str
    document_type: Optional[str]
    
    # This allows wiki links to find documents by original path
    # while maintaining normalized IDs for consistency
```

## Issue 2: Document Entities Are Not Being Created

**Problem**: The current implementation only creates entities for things WITHIN documents, not for the documents themselves.

**Evidence**: 
- RDF output shows `kb:sourceDocument` references but no actual Document entities
- The processor skips documents without entities or todos (line 357-359)

### Current Flow (Problematic)
```
Document → Extract Entities → Convert Entities to RDF
         ↓
         Skip if no entities found
```

### Revised Flow (Correct)
```
Document → Create Document Entity → Extract Other Entities → Convert All to RDF
         ↓
         Always create document entity
```

## Revised Implementation

### 1. Document Entity Creation

```python
def process_document(self, doc: Document) -> Graph:
    """Process a document, always creating a document entity"""
    
    # 1. ALWAYS create document entity first
    doc_entity = self.create_document_entity(doc)
    doc_graph = self.entity_to_rdf(doc_entity)
    
    # 2. Add document metadata as properties
    doc_uri = URIRef(doc_entity.kb_id)
    if doc.metadata.created:
        doc_graph.add((doc_uri, KB.created, Literal(doc.metadata.created)))
    if doc.metadata.modified:
        doc_graph.add((doc_uri, KB.modified, Literal(doc.metadata.modified)))
    # ... other properties
    
    # 3. Then process entities within the document
    for entity in doc.metadata.entities:
        entity_graph = self.process_entity(entity, doc_entity)
        doc_graph += entity_graph
    
    return doc_graph
```

### 2. Wiki Link Resolution with Path Preservation

```python
def resolve_wiki_link(self, link_text: str, current_doc: KbDocument) -> ResolvedLink:
    """Resolve wiki link preserving original text"""
    
    # 1. Parse link
    original_text = link_text.strip('[]')
    link_type, target = self.parse_link_type(original_text)
    
    # 2. Try to find document by original path
    if not link_type or link_type == 'doc':
        # Try exact match first
        doc = self.find_document_by_path(original_text + '.md')
        if not doc:
            # Try with different extensions
            for ext in ['.markdown', '.txt', '']:
                doc = self.find_document_by_path(original_text + ext)
                if doc:
                    break
        
        if doc:
            return ResolvedLink(
                original_text=original_text,
                resolved_type='document',
                entity_id=doc.kb_id,
                original_path=doc.original_path
            )
    
    # 3. Try to resolve as named entity
    if link_type in ['person', 'org', 'project']:
        entity_id = self.generate_entity_id(link_type, original_text)
        return ResolvedLink(
            original_text=original_text,
            resolved_type=link_type,
            entity_id=entity_id
        )
    
    # 4. Create placeholder
    return ResolvedLink(
        original_text=original_text,
        resolved_type='placeholder',
        entity_id=f'/PlaceholderDocument/{self.normalize_for_id(original_text)}'
    )
```

### 3. Updated RDF Generation

The RDF output should include:

```turtle
# Document entity (currently missing!)
<http://example.org/kb/Document/daily-notes/2024-11-07-thursday> a kb:Document ;
    rdfs:label "Daily Note 2024-11-07 Thursday" ;
    kb:originalPath "Daily Notes/2024-11-07 Thursday.md" ;
    kb:created "2024-11-07T08:54:54-05:00"^^xsd:dateTime ;
    kb:modified "2024-11-07T10:30:00-05:00"^^xsd:dateTime ;
    kb:hasEntity <http://example.org/kb/Person/alex-cipher> ;
    kb:hasEntity <http://example.org/kb/Organization/galaxy-dynamics> ;
    kb:hasTodoItem <http://example.org/kb/Document/daily-notes/2024-11-07-thursday/TodoItem/15-a3f5b2c8> .

# Entities reference back to document
<http://example.org/kb/Person/alex-cipher> a kb:Person ;
    rdfs:label "Alex Cipher" ;
    kb:mentionedIn <http://example.org/kb/Document/daily-notes/2024-11-07-thursday> .
```

## Key Design Changes

1. **Document Path Preservation**:
   - Store original path as a property
   - Use original path for wiki link resolution
   - Generate normalized ID for consistency

2. **Always Create Document Entities**:
   - Documents are first-class entities
   - Create even if no other entities found
   - Include document metadata as properties

3. **Wiki Link Resolution Order**:
   - First: Try to find document by original path
   - Second: Try to resolve as typed entity
   - Third: Create placeholder

4. **Bidirectional Relationships**:
   - Documents reference their entities
   - Entities reference documents they appear in

## Implementation Priority

1. **Update Document Model** to include original_path
2. **Modify Processor** to always create document entities
3. **Implement Path-Preserving Wiki Link Resolver**
4. **Update RDF Converter** to emit document entities
5. **Add Tests** for path preservation and document creation

## Migration Considerations

For existing data:
- Generate document entities for all processed files
- Preserve original file paths in new original_path property
- Update wiki link resolution to use original paths