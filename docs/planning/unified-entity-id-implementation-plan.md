# Unified Entity ID Implementation Plan

**Status:** Final Implementation Plan  
**Date:** 2025-07-21  
**Based on:** ADR-0012 and ADR-0013  

## Overview

This unified plan combines all entity-id refactoring work and aligns with the final architectural decisions in ADR-0012 (Entity Modeling with Wiki-Based Architecture) and ADR-0013 (Wiki-Based Entity ID Generation and Link Preservation).

## Critical Requirements

### 1. Document Entity Creation (Critical Fix)
- **Issue**: Documents are not being created as entities in the knowledge graph
- **Impact**: Missing document entities break the wiki concept and RDF references
- **Priority**: Phase 1 (Week 1)

### 2. Wiki Link Text Preservation (Critical Fix) 
- **Issue**: Normalizing wiki link text breaks file path resolution
- **Impact**: Wiki links cannot resolve to actual documents
- **Priority**: Phase 1 (Week 1)

### 3. Entity Deduplication (Original Goal)
- **Issue**: Same entities get multiple random IDs across documents
- **Impact**: Duplicate entities in knowledge graph
- **Priority**: Phase 2 (Week 2)

## Implementation Phases

### Phase 1: Critical Infrastructure (Week 1)

#### 1.1 ID Generator Module
**File**: `src/knowledgebase_processor/utils/id_generator.py`

```python
class EntityIdGenerator:
    """Generates deterministic entity IDs following ADR-0013 patterns"""
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for ID generation (not for wiki links)"""
        # Unicode NFKD normalization
        # Convert to lowercase
        # Replace non-alphanumeric with hyphens
        # Remove consecutive hyphens
        # Trim hyphens from start/end
        
    def generate_document_id(self, file_path: str) -> Tuple[str, str, str]:
        """Generate document ID with path preservation
        
        Returns:
            Tuple[normalized_id, original_path, path_without_extension]
        """
        # Normalize path for ID: /Document/{normalized-path}
        # Preserve original: "Daily Notes/2024-11-07 Thursday.md"
        # Path for wiki: "Daily Notes/2024-11-07 Thursday"
        
    def generate_person_id(self, name: str) -> str:
        """Generate: /Person/{normalized-name}"""
        
    def generate_organization_id(self, name: str) -> str:
        """Generate: /Organization/{normalized-name}"""
        
    def generate_tag_id(self, tag_text: str) -> str:
        """Generate: /Tag/{normalized-name}"""
        
    def generate_todo_id(self, document_id: str, todo_text: str, line_number: int) -> str:
        """Generate: /Document/{path}/TodoItem/{line}-{hash}"""
        
    def generate_section_id(self, document_id: str, heading: str, parent_path: List[str]) -> str:
        """Generate: /Document/{path}/Section/{heading-path}"""
        
    def generate_placeholder_id(self, link_text: str) -> str:
        """Generate: /PlaceholderDocument/{normalized-name}"""
```

#### 1.2 Document Registry Service
**File**: `src/knowledgebase_processor/services/document_registry.py`

```python
class DocumentRegistry:
    """Registry for document path-based lookups"""
    
    def __init__(self):
        # Map original paths to document IDs
        self._path_to_id: Dict[str, str] = {}
        # Map normalized paths to document IDs  
        self._normalized_to_id: Dict[str, str] = {}
        
    def register_document(self, doc_id: str, original_path: str, normalized_path: str):
        """Register document with both path formats"""
        
    def find_by_wiki_link(self, link_text: str) -> Optional[str]:
        """Find document by wiki link text preserving original format"""
        # Try exact match first
        # Try with common extensions (.md, .markdown, .txt)
        # Try case variations
        # Return document ID if found
        
    def get_all_documents(self) -> List[Tuple[str, str, str]]:
        """Return all registered documents"""
```

#### 1.3 Update Document Model
**File**: `src/knowledgebase_processor/models/kb_entities.py`

```python
class KbDocument(KbBaseEntity):
    """Document entity with dual-path support per ADR-0013"""
    kb_id: str                      # Normalized: "/Document/daily-notes/2024-11-07-thursday"
    original_path: str              # Preserved: "Daily Notes/2024-11-07 Thursday.md"
    path_without_extension: str     # For wikis: "Daily Notes/2024-11-07 Thursday"
    title: str                      # From metadata or filename
    document_type: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    word_count: Optional[int] = None
    content_hash: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "rdf_types": [KB.Document],
            "rdfs_label_fallback_fields": ["title", "path_without_extension"]
        }
```

### Phase 2: Core Entity Processing (Week 2)

#### 2.1 Update Processor for Document Entity Creation
**File**: `src/knowledgebase_processor/processor/processor.py`

**Critical Change**: Always create document entity first

```python
def process_documents_to_rdf(self, documents: List[Document], output_dir: Path) -> Dict[str, Any]:
    """Process documents with mandatory document entity creation"""
    
    for doc in documents:
        # 1. Create document entity (ALWAYS)
        doc_entity = self._create_document_entity(doc)
        self.document_registry.register_document(
            doc_entity.kb_id, 
            doc_entity.original_path,
            doc_entity.path_without_extension
        )
        
        # 2. Convert document entity to RDF
        doc_graph = self.rdf_converter.kb_entity_to_graph(doc_entity)
        
        # 3. Add document properties from metadata
        self._add_document_properties(doc_graph, doc_entity, doc.metadata)
        
        # 4. Process entities within document
        contained_entities = []
        for entity in doc.metadata.entities:
            kb_entity = self._process_entity_with_deduplication(entity, doc_entity.kb_id)
            if kb_entity:
                contained_entities.append(kb_entity)
                entity_graph = self.rdf_converter.kb_entity_to_graph(kb_entity)
                doc_graph += entity_graph
        
        # 5. Add bidirectional relationships
        self._add_document_entity_relationships(doc_graph, doc_entity, contained_entities)
        
        # 6. Save RDF (even if no other entities found)
        self._save_rdf_graph(doc_graph, doc_entity.kb_id, output_dir)

def _create_document_entity(self, doc: Document) -> KbDocument:
    """Create document entity with preserved paths per ADR-0013"""
    doc_id, original_path, path_without_ext = self.id_generator.generate_document_id(doc.path)
    
    return KbDocument(
        kb_id=doc_id,
        original_path=original_path,
        path_without_extension=path_without_ext,
        title=doc.metadata.title or Path(path_without_ext).name,
        document_type=doc.metadata.get('type'),
        created=doc.metadata.created,
        modified=doc.metadata.modified,
        word_count=len(doc.content.split()) if doc.content else None,
        source_document_uri=doc_id  # Self-reference
    )
```

#### 2.2 Entity Registry for Deduplication
**File**: `src/knowledgebase_processor/services/entity_registry.py`

```python
class EntityRegistry:
    """Global entity deduplication per ADR-0013"""
    
    def __init__(self):
        # Map entity IDs to entity data
        self._entities: Dict[str, KbBaseEntity] = {}
        # Map aliases to canonical IDs
        self._aliases: Dict[str, str] = {}
        
    def get_or_create_entity(self, entity_type: str, properties: Dict) -> Tuple[str, bool]:
        """Get existing entity or create new one
        
        Returns:
            Tuple[entity_id, was_created]
        """
        # Generate deterministic ID
        entity_id = self._generate_entity_id(entity_type, properties)
        
        # Check if entity exists
        if entity_id in self._entities:
            # Merge any new aliases
            self._merge_aliases(entity_id, properties)
            return entity_id, False
        
        # Create new entity
        entity = self._create_entity(entity_type, entity_id, properties)
        self._entities[entity_id] = entity
        self._register_aliases(entity_id, properties)
        
        return entity_id, True
```

#### 2.3 Update Entity Service
**File**: `src/knowledgebase_processor/services/entity_service.py`

Replace random ID generation with deterministic IDs:

```python
def generate_kb_id(self, entity_type_str: str, text: str, context: Dict = None) -> str:
    """Generate deterministic ID per ADR-0013"""
    
    if entity_type_str == "Person":
        return self.id_generator.generate_person_id(text)
    elif entity_type_str == "Organization":
        return self.id_generator.generate_organization_id(text)
    elif entity_type_str == "Tag":
        return self.id_generator.generate_tag_id(text)
    elif entity_type_str == "Location":
        return self.id_generator.generate_location_id(text)
    elif entity_type_str == "Project":
        return self.id_generator.generate_project_id(text)
    else:
        # Fallback for unknown types
        normalized = self.id_generator.normalize_text(text)
        return f"/{entity_type_str}/{normalized}"
```

### Phase 3: Wiki Link Integration (Week 3)

#### 3.1 Wiki Link Resolver
**File**: `src/knowledgebase_processor/services/wikilink_resolver.py`

```python
class WikiLinkResolver:
    """Resolve wiki links preserving original text per ADR-0013"""
    
    def __init__(self, document_registry: DocumentRegistry, entity_registry: EntityRegistry):
        self.doc_registry = document_registry
        self.entity_registry = entity_registry
        
    def resolve_link(self, link_text: str, context: Dict = None) -> ResolvedLink:
        """Resolve wiki link with original text preservation"""
        
        # 1. Parse typed links (person:Name, org:Company, etc.)
        link_type, target_text = self._parse_typed_link(link_text)
        
        # 2. Try document resolution first (if no type or doc type)
        if not link_type or link_type == 'doc':
            doc_id = self.doc_registry.find_by_wiki_link(target_text)
            if doc_id:
                return ResolvedLink(
                    original_text=link_text,
                    resolved_type='document',
                    entity_id=doc_id,
                    confidence=1.0
                )
        
        # 3. Try typed entity resolution
        if link_type in ['person', 'org', 'organization', 'location', 'project', 'tag']:
            entity_id = self._resolve_typed_entity(link_type, target_text)
            if entity_id:
                return ResolvedLink(
                    original_text=link_text,
                    resolved_type=link_type,
                    entity_id=entity_id,
                    confidence=1.0
                )
        
        # 4. Try context-based resolution
        if context:
            entity_id = self._resolve_with_context(target_text, context)
            if entity_id:
                return ResolvedLink(
                    original_text=link_text,
                    resolved_type='entity',
                    entity_id=entity_id,
                    confidence=0.8
                )
        
        # 5. Create placeholder document
        placeholder_id = self.id_generator.generate_placeholder_id(target_text)
        return ResolvedLink(
            original_text=link_text,
            resolved_type='placeholder',
            entity_id=placeholder_id,
            confidence=0.0
        )
    
    def _parse_typed_link(self, link_text: str) -> Tuple[Optional[str], str]:
        """Parse typed wiki links like 'person:Alex Cipher'"""
        if ':' in link_text and not link_text.startswith('http'):
            type_hint, text = link_text.split(':', 1)
            return type_hint.lower().strip(), text.strip()
        return None, link_text
```

#### 3.2 Enhanced Wiki Link Extractor
**File**: `src/knowledgebase_processor/extractor/wikilink_extractor.py`

```python
class WikiLinkExtractor:
    """Extract wiki links preserving original text per ADR-0013"""
    
    def extract(self, content: str) -> List[WikiLink]:
        """Extract wiki links with original text preservation"""
        links = []
        
        for match in self.WIKI_LINK_PATTERN.finditer(content):
            original_text = match.group(1)  # Text inside [[...]]
            
            # Don't normalize the text - preserve exactly as written
            links.append(WikiLink(
                original_text=original_text,
                start_pos=match.start(),
                end_pos=match.end(),
                line_number=content[:match.start()].count('\n') + 1
            ))
            
        return links
```

### Phase 4: RDF Integration (Week 3-4)

#### 4.1 Update RDF Converter
**File**: `src/knowledgebase_processor/rdf_converter/converter.py`

```python
def add_document_entity_relationships(self, graph: Graph, doc_entity: KbDocument, 
                                    contained_entities: List[KbBaseEntity]):
    """Add bidirectional document-entity relationships per ADR-0013"""
    doc_uri = URIRef(doc_entity.kb_id)
    
    # Add document properties
    graph.add((doc_uri, RDF.type, KB.Document))
    graph.add((doc_uri, RDFS.label, Literal(doc_entity.title)))
    graph.add((doc_uri, KB.originalPath, Literal(doc_entity.original_path)))
    
    if doc_entity.created:
        graph.add((doc_uri, KB.created, Literal(doc_entity.created, datatype=XSD.dateTime)))
    if doc_entity.modified:
        graph.add((doc_uri, KB.modified, Literal(doc_entity.modified, datatype=XSD.dateTime)))
    
    # Add bidirectional relationships
    for entity in contained_entities:
        entity_uri = URIRef(entity.kb_id)
        # Document -> Entity
        graph.add((doc_uri, KB.hasEntity, entity_uri))
        # Entity -> Document  
        graph.add((entity_uri, KB.mentionedIn, doc_uri))

def handle_document_properties(self, graph: Graph, doc_entity: KbDocument, 
                             metadata: DocumentMetadata):
    """Handle document properties vs entity references per ADR-0012"""
    doc_uri = URIRef(doc_entity.kb_id)
    
    # Properties become literals
    for prop, value in metadata.properties.items():
        if prop in ['created', 'modified', 'type', 'status', 'word_count']:
            if value is not None:
                graph.add((doc_uri, KB[prop], Literal(value)))
    
    # Entity references become object properties
    for entity_ref in metadata.entity_references:
        graph.add((doc_uri, KB.references, URIRef(entity_ref.kb_id)))
```

### Phase 5: Testing & Migration (Week 4)

#### 5.1 Comprehensive Test Suite

**File**: `tests/test_entity_id_integration.py`

Based on the test cases from `entity-id-generation-test-cases.md`:

```python
class TestEntityIdIntegration:
    """Integration tests for complete entity ID system"""
    
    def test_document_entity_creation(self):
        """Test that all documents create entities"""
        # From test cases: document creation scenarios
        
    def test_wiki_link_preservation(self):
        """Test wiki link text preservation"""
        # Test: [[Daily Note 2024-11-07 Thursday]] resolves correctly
        
    def test_entity_deduplication(self):
        """Test entity deduplication across documents"""
        # Test: "Galaxy Dynamics Co." gets same ID everywhere
        
    def test_deterministic_ids(self):
        """Test ID generation determinism"""
        # Use test cases from entity-id-generation-test-cases.md
        
    def test_property_vs_entity_distinction(self):
        """Test property classification"""
        # Use property_tests from test cases
```

#### 5.2 Migration Tool
**File**: `scripts/migrate_entity_ids.py`

```python
class EntityIdMigrator:
    """Migrate existing data to new ID system"""
    
    def migrate_existing_data(self):
        """Complete migration process"""
        # 1. Load existing RDF data
        # 2. Create document entities for all files
        # 3. Map old random IDs to new deterministic IDs
        # 4. Update all references in RDF
        # 5. Validate migration completeness
        
    def create_document_entities_for_existing_files(self):
        """Create missing document entities"""
        # Scan file system for all processed documents
        # Create document entities with preserved paths
        # Register in document registry
        
    def map_old_to_new_ids(self):
        """Create ID mapping table"""
        # Map: Organization/galaxy_dynamics_co_7a705a38 -> /Organization/galaxy-dynamics
        # Store mapping for reference updates
```

## Implementation Priorities

### Critical (Week 1)
1. **Document Entity Creation** - Fix missing document entities
2. **Path Preservation** - Implement dual-path document model
3. **ID Generator** - Create deterministic ID generation

### Important (Week 2)
1. **Entity Deduplication** - Implement entity registry
2. **Update Processor** - Always create document entities
3. **Update Entity Service** - Remove random ID generation

### Enhancement (Week 3-4)
1. **Wiki Link Resolution** - Full wiki link support
2. **RDF Integration** - Bidirectional relationships
3. **Testing & Migration** - Complete test coverage

## Success Criteria

1. **100% Document Entity Coverage**: Every processed document has an entity
2. **Wiki Link Resolution**: All existing wiki links resolve correctly
3. **Zero Entity Duplication**: Same entities have consistent IDs
4. **Path Preservation**: Original file paths are maintained
5. **Performance**: < 1ms per ID generation, < 5ms document lookup
6. **Test Coverage**: >90% coverage of new functionality
7. **Migration Success**: All existing data migrated without loss

## Risk Mitigation

### Critical Risks
1. **Wiki Link Breakage**: Test extensively with real wiki content
2. **Performance Impact**: Profile document registry with large datasets
3. **Data Loss**: Comprehensive backup before migration

### Implementation Risks
1. **ID Collisions**: Implement collision detection and handling
2. **Path Conflicts**: Handle case-sensitive file systems
3. **Memory Usage**: Monitor entity registry size with large datasets

## Dependencies

- ADR-0012: Entity Modeling with Wiki-Based Architecture
- ADR-0013: Wiki-Based Entity ID Generation and Link Preservation
- Existing entity models and RDF infrastructure
- Test cases from `entity-id-generation-test-cases.md`

## Documentation Updates

1. Update implementation guides
2. Create migration documentation  
3. Update API documentation for new ID patterns
4. Create troubleshooting guide for wiki link issues

---

**Note**: This plan supersedes the individual implementation plans and represents the final, comprehensive approach aligned with ADR-0012 and ADR-0013.