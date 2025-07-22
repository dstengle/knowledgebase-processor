# DEPRECATED: Revised Entity ID Refactoring Implementation Plan

**This document has been superseded by the [Unified Entity ID Implementation Plan](unified-entity-id-implementation-plan.md).**

The unified plan incorporates all the insights from this revised plan along with alignment to the final ADR-0012 and ADR-0013 decisions.

For current implementation guidance, please refer to:
- [Unified Entity ID Implementation Plan](unified-entity-id-implementation-plan.md)
- [ADR-0012: Entity Modeling with Wiki-Based Architecture](../architecture/decisions/0012-entity-modeling-with-wiki-based-architecture.md)  
- [ADR-0013: Wiki-Based Entity ID Generation and Link Preservation](../architecture/decisions/0013-wiki-based-entity-id-generation-and-link-preservation.md)

---

# Revised Entity ID Refactoring Implementation Plan

## Critical Changes from Original Plan

### 1. Wiki Link Text Preservation
- Wiki links must preserve original text for file path resolution
- Document entities need both normalized IDs and original paths

### 2. Document Entity Creation
- Documents must be created as first-class entities
- Current implementation skips document entity creation entirely

## Phase 1: Foundation (Week 1)

### 1.1 Create New ID Generation Module
**File**: `src/knowledgebase_processor/utils/id_generator.py`

```python
# Core components to implement:
- normalize_text(text: str) -> str  # For ID generation only
- preserve_path(path: str) -> str   # Keep original with extension removed
- generate_document_id(file_path: str) -> Tuple[str, str]  # (normalized_id, original_path)
- generate_tag_id(tag_text: str) -> str
- generate_person_id(name: str) -> str
- generate_organization_id(name: str) -> str
- generate_location_id(name: str, parent: Optional[str]) -> str
- generate_project_id(name: str) -> str
- generate_todo_id(document_id: str, todo_text: str, line_number: int) -> str
- generate_section_id(document_id: str, heading: str, parent_path: List[str]) -> str
- generate_placeholder_id(link_text: str) -> str
```

### 1.2 Create Document Registry
**File**: `src/knowledgebase_processor/services/document_registry.py`

```python
class DocumentRegistry:
    """Registry for document path lookups"""
    def register_document(self, normalized_id: str, original_path: str, full_path: str):
        # Map original path (without extension) to document ID
        # Support multiple lookup strategies
    
    def find_by_wiki_link(self, link_text: str) -> Optional[str]:
        # Try to find document by wiki link text
        # Check with various extensions
        # Return document ID if found
```

### 1.3 Update Document Model
**File**: `src/knowledgebase_processor/models/kb_entities.py`

```python
class KbDocument(KbBaseEntity):
    """Represents a document in the knowledge base."""
    kb_id: str  # Normalized: /Document/daily-notes/2024-11-07-thursday
    original_path: str  # Preserved: "Daily Notes/2024-11-07 Thursday.md"
    path_without_extension: str  # For wiki links: "Daily Notes/2024-11-07 Thursday"
    title: str
    document_type: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    word_count: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "rdf_types": [KB.Document],
            "rdfs_label_fallback_fields": ["title", "path_without_extension"]
        }
```

## Phase 2: Core Refactoring (Week 2)

### 2.1 Update Processor to Create Document Entities
**File**: `src/knowledgebase_processor/processor/processor.py`

**Critical Change**: Always create document entity first

```python
def process_documents_to_rdf(self, documents: List[Document], output_dir: Path) -> Dict[str, Any]:
    # REVISED: Create document entity for EVERY document
    for doc in documents:
        # 1. Create document entity
        doc_entity = self._create_document_entity(doc)
        
        # 2. Convert document entity to RDF
        doc_graph = rdf_converter.kb_entity_to_graph(doc_entity)
        
        # 3. Add document properties
        self._add_document_properties(doc_graph, doc_entity, doc.metadata)
        
        # 4. Process entities within document
        for entity in doc.metadata.entities:
            # ... existing entity processing
        
        # 5. Save RDF even if no other entities found

def _create_document_entity(self, doc: Document) -> KbDocument:
    """Create a document entity with preserved paths"""
    normalized_id, original_path = self.id_generator.generate_document_id(doc.path)
    path_without_ext = original_path.rsplit('.', 1)[0]
    
    return KbDocument(
        kb_id=normalized_id,
        original_path=original_path,
        path_without_extension=path_without_ext,
        title=doc.metadata.title or path_without_ext,
        document_type=doc.metadata.get('type'),
        created=doc.metadata.created,
        modified=doc.metadata.modified,
        source_document_uri=normalized_id  # Self-reference
    )
```

### 2.2 Create Wiki Link Resolver
**File**: `src/knowledgebase_processor/services/wikilink_resolver.py`

```python
class WikiLinkResolver:
    def __init__(self, document_registry: DocumentRegistry, entity_registry: EntityRegistry):
        self.doc_registry = document_registry
        self.entity_registry = entity_registry
    
    def resolve_link(self, link_text: str, context: Dict) -> ResolvedLink:
        """Resolve wiki link preserving original text"""
        # 1. Parse link type from prefix
        link_type, target_text = self._parse_link_type(link_text)
        
        # 2. If no type or doc type, try document lookup
        if not link_type or link_type == 'doc':
            doc_id = self.doc_registry.find_by_wiki_link(target_text)
            if doc_id:
                return ResolvedLink(
                    original_text=link_text,
                    resolved_type='document',
                    entity_id=doc_id
                )
        
        # 3. Try typed entity lookup
        if link_type in ['person', 'org', 'location', 'project']:
            entity_id = self._resolve_typed_entity(link_type, target_text)
            if entity_id:
                return ResolvedLink(
                    original_text=link_text,
                    resolved_type=link_type,
                    entity_id=entity_id
                )
        
        # 4. Create placeholder
        return self._create_placeholder(link_text)
```

### 2.3 Update RDF Converter
**File**: `src/knowledgebase_processor/rdf_converter/converter.py`

Add support for bidirectional relationships:

```python
def add_document_entity_relationships(self, graph: Graph, doc_entity: KbDocument, 
                                    contained_entities: List[KbBaseEntity]):
    """Add relationships between document and its entities"""
    doc_uri = URIRef(doc_entity.kb_id)
    
    for entity in contained_entities:
        entity_uri = URIRef(entity.kb_id)
        # Document -> Entity
        graph.add((doc_uri, KB.hasEntity, entity_uri))
        # Entity -> Document
        graph.add((entity_uri, KB.mentionedIn, doc_uri))
```

## Phase 3: Wiki Link Integration (Week 3)

### 3.1 Enhance Wiki Link Extractor
**File**: `src/knowledgebase_processor/extractor/wikilink_extractor.py`

**Key Change**: Preserve original link text

```python
class WikiLinkExtractor:
    def extract(self, content: str) -> List[WikiLink]:
        """Extract wiki links preserving original text"""
        links = []
        for match in self.WIKI_LINK_PATTERN.finditer(content):
            original_text = match.group(1)  # Text inside [[...]]
            links.append(WikiLink(
                original_text=original_text,
                start_pos=match.start(),
                end_pos=match.end()
            ))
        return links
```

## Phase 4: Testing & Migration (Week 4)

### 4.1 Create Test Suite
**Critical Tests**:
- Document entity creation for all documents
- Wiki link resolution with original paths
- Path preservation in various formats
- Document property vs entity distinction

### 4.2 Migration Tool Updates
**File**: `scripts/migrate_entity_ids.py`

Additional migration steps:
1. Create document entities for all existing documents
2. Populate original_path from file system
3. Update sourceDocument references to use new document entities
4. Build document registry for wiki link resolution

## Key Implementation Differences

### From Original Plan

1. **ID Generation Returns Tuples**: Document ID generation returns both normalized ID and original path
2. **Document Registry Required**: New service for path-based document lookup
3. **Always Create Documents**: Processor creates document entities regardless of content
4. **Preserve Wiki Link Text**: No normalization of wiki link content
5. **Bidirectional References**: Documents reference entities and vice versa

### Priority Order

1. **Document Entity Creation** (Critical - currently missing)
2. **Path Preservation** (Critical - breaks wiki links)
3. **Entity Deduplication** (Important - original goal)
4. **Wiki Link Resolution** (Important - depends on above)
5. **Property Classification** (Nice to have - reduces noise)

## Success Criteria (Revised)

1. **All Documents Have Entities**: Every processed document appears in RDF
2. **Wiki Links Work**: Original wiki link text successfully resolves to documents
3. **No Duplicate Entities**: Same entity has consistent ID across documents
4. **Path Preservation**: Can lookup documents by original file names
5. **Backwards Compatible**: Existing wiki links continue to work
6. **Performance**: Document lookup < 5ms with registry

## Risk Mitigation (Additional)

1. **Path Conflicts**: Handle case-sensitive file systems appropriately
2. **Extension Variations**: Support .md, .markdown, .txt in wiki link resolution
3. **Special Characters**: Properly handle paths with spaces, unicode, etc.
4. **Large Document Sets**: Ensure document registry scales efficiently