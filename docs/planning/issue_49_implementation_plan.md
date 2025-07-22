# GitHub Issue #49 Implementation Plan: Document Entity Creation and Wiki Link Text Preservation

**Status:** Implementation Plan Ready  
**Date:** 2025-07-22  
**Issue:** [#49 - Implement Document Entity Creation and Wiki Link Text Preservation](https://github.com/dstengle/knowledgebase-processor/issues/49)

## Executive Summary

This plan addresses two critical architectural gaps identified in ADR-0012/0013 that are fundamental to the wiki-based knowledge graph implementation:

1. **Document Entity Creation (Critical Bug)**: Documents are not being created as entities in the knowledge graph, breaking the fundamental wiki concept where documents are first-class entities.

2. **Wiki Link Text Preservation (Critical Bug)**: Current normalization approach would break existing wiki links by preventing file system path resolution.

## Critical Requirements Analysis

### 1. Document Entity Creation
- **Current State**: Only entities WITHIN documents are processed; documents themselves are ignored
- **Required State**: Every processed document creates a corresponding Document entity with full metadata
- **Impact**: Missing document entities prevent proper wiki graph representation and RDF document references
- **Priority**: 🔴 Critical - Phase 1 (Week 1)

### 2. Wiki Link Text Preservation  
- **Current State**: Wiki link text normalization would break file path resolution
- **Required State**: Original wiki link text preserved exactly for file system compatibility
- **Impact**: All existing wiki links would stop working if text is normalized during resolution
- **Priority**: 🔴 Critical - Phase 1 (Week 1)

### 3. Dual-Path Document Model
- **Requirement**: Documents must maintain both normalized IDs for RDF and original paths for wiki resolution
- **Implementation**: Three-tuple return: `(normalized_id, original_path, path_without_extension)`
- **Purpose**: Enable both deterministic IDs and wiki link compatibility

### 4. Entity Deduplication
- **Requirement**: Consistent IDs for same entities across documents
- **Current Issue**: Random UUID suffixes create duplicates (e.g., `galaxy_dynamics_co_7a705a38`)
- **Solution**: Deterministic ID generation with entity registry

## Implementation Phases

### Phase 1: Critical Infrastructure (Week 1)

#### 1.1 Create EntityIdGenerator Class
**File**: `src/knowledgebase_processor/utils/id_generator.py` (new)

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
        # Example: "Daily Notes/2024-11-07 Thursday.md" -> 
        # ("/Document/daily-notes/2024-11-07-thursday", 
        #  "Daily Notes/2024-11-07 Thursday.md",
        #  "Daily Notes/2024-11-07 Thursday")
```

#### 1.2 Create DocumentRegistry Service  
**File**: `src/knowledgebase_processor/services/document_registry.py` (new)

```python
class DocumentRegistry:
    """Registry for document path-based lookups"""
    
    def register_document(self, doc_id: str, original_path: str, normalized_path: str):
        """Register document with both path formats"""
        
    def find_by_wiki_link(self, link_text: str) -> Optional[str]:
        """Find document by wiki link text preserving original format"""
        # Try exact match first
        # Try with common extensions (.md, .markdown, .txt)
        # Try case variations if needed
        # Return document ID if found
```

#### 1.3 Update KbDocument Model
**File**: `src/knowledgebase_processor/models/kb_entities.py` (update)

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
    
    class Config:
        json_schema_extra = {
            "rdf_types": [KB.Document],
            "rdfs_label_fallback_fields": ["title", "path_without_extension"]
        }
```

#### 1.4 Update Processor for Document Entity Creation
**File**: `src/knowledgebase_processor/processor/processor.py` (critical update)

**Key Change**: Always create document entity first before processing content entities.

```python
def process_documents_to_rdf(self, documents: List[Document], output_dir: Path) -> Dict[str, Any]:
    """Process documents with mandatory document entity creation"""
    
    for doc in documents:
        # 1. Create document entity (ALWAYS - this is currently missing)
        doc_entity = self._create_document_entity(doc)
        self.document_registry.register_document(
            doc_entity.kb_id, 
            doc_entity.original_path,
            doc_entity.path_without_extension
        )
        
        # 2. Convert document entity to RDF
        doc_graph = self.rdf_converter.kb_entity_to_graph(doc_entity)
        
        # 3. Process entities within document (existing logic)
        # ... existing entity processing ...
        
        # 4. Save RDF (even if no other entities found)
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

#### 1.5 Update WikiLink Extractor
**File**: `src/knowledgebase_processor/extractor/wikilink_extractor.py` (critical update)

**Key Change**: Do NOT normalize wiki link text during extraction.

```python
def extract(self, content: str) -> List[WikiLink]:
    """Extract wiki links with original text preservation per ADR-0013"""
    links = []
    
    for match in self.WIKI_LINK_PATTERN.finditer(content):
        original_text = match.group(1)  # Text inside [[...]]
        
        # CRITICAL: Don't normalize the text - preserve exactly as written
        links.append(WikiLink(
            original_text=original_text,  # Preserve "Daily Note 2024-11-07 Thursday"
            start_pos=match.start(),
            end_pos=match.end(),
            line_number=content[:match.start()].count('\n') + 1
        ))
        
    return links
```

### Phase 2: Entity Management (Week 2)

#### 2.1 Create EntityRegistry for Deduplication
**File**: `src/knowledgebase_processor/services/entity_registry.py` (new)

```python
class EntityRegistry:
    """Global entity deduplication per ADR-0013"""
    
    def get_or_create_entity(self, entity_type: str, properties: Dict) -> Tuple[str, bool]:
        """Get existing entity or create new one
        
        Returns:
            Tuple[entity_id, was_created]
        """
        # Generate deterministic ID
        entity_id = self._generate_entity_id(entity_type, properties)
        
        # Check if entity exists and merge properties
        # Return entity_id and whether it was newly created
```

#### 2.2 Update Entity Service
**File**: `src/knowledgebase_processor/services/entity_service.py` (update)

Replace random ID generation with deterministic IDs:

```python
def generate_kb_id(self, entity_type_str: str, text: str, context: Dict = None) -> str:
    """Generate deterministic ID per ADR-0013"""
    
    if entity_type_str == "Person":
        return self.id_generator.generate_person_id(text)
    elif entity_type_str == "Organization":
        return self.id_generator.generate_organization_id(text)
    # ... other entity types ...
```

### Phase 3: Testing & Validation (Week 3)

#### 3.1 Critical Test Cases
**File**: `tests/test_entity_id_integration.py` (new)

```python
class TestCriticalRequirements:
    def test_document_entity_always_created(self):
        """Test that every document creates an entity (Issue #49 requirement 1)"""
        # Test documents with no other entities still create document entity
        
    def test_wiki_link_text_preservation(self):
        """Test wiki link text preservation (Issue #49 requirement 2)"""
        # Test: [[Daily Note 2024-11-07 Thursday]] resolves correctly without normalization
        
    def test_dual_path_document_model(self):
        """Test document dual-path model implementation"""
        # Verify normalized_id, original_path, path_without_extension
        
    def test_entity_deduplication_across_documents(self):
        """Test entity deduplication prevents duplicates"""
        # Same entity in multiple documents gets same ID
```

#### 3.2 Integration Test Scenarios
Based on test cases from `entity-id-generation-test-cases.md`:

```python
def test_complete_document_processing_pipeline(self):
    """End-to-end test with document containing multiple entity references"""
    markdown_content = '''
    ---
    author: Alex Cipher
    attendees:
      - Alex Cipher  
      - Jane Smith
    ---
    
    Met with [[Alex Cipher]] and [[Jane Smith]] today.
    
    - [ ] Alex Cipher to review PR
    '''
    
    # Expected: 
    # - 1 Document entity with dual paths
    # - 1 Alex Cipher entity (deduplicated across 3 mentions)  
    # - 1 Jane Smith entity
    # - 1 TodoItem entity
    # - Proper bidirectional relationships
```

## Success Criteria

### Functional Requirements
1. **100% Document Entity Coverage**: Every processed document has a corresponding Document entity
2. **Wiki Link Resolution**: All existing wiki links resolve correctly through path matching
3. **Zero Entity Duplication**: Same entities have consistent IDs across all documents  
4. **Path Preservation**: Original file paths are maintained for wiki compatibility

### Technical Requirements
5. **Performance**: < 1ms per ID generation, < 5ms document lookup
6. **Test Coverage**: >90% coverage of new functionality
7. **Backwards Compatibility**: All existing wiki links continue to work

### Validation Criteria
8. **RDF Output**: Every document appears in RDF with full metadata
9. **Deterministic Behavior**: Same input always produces same IDs
10. **File System Compatibility**: Wiki links work with actual file naming conventions

## Risk Mitigation

### Critical Risks
1. **Wiki Link Breakage**: 
   - **Risk**: Changing resolution logic breaks existing links
   - **Mitigation**: Extensive testing with real wiki content, preserve exact text matching

2. **Performance Impact**: 
   - **Risk**: Document registry becomes bottleneck with large datasets
   - **Mitigation**: Profile with sample data, implement efficient indexing

3. **Data Loss During Migration**:
   - **Risk**: Migration process corrupts existing data
   - **Mitigation**: Comprehensive backup strategy, staged rollout

### Implementation Risks
4. **ID Collisions**: 
   - **Risk**: Different entities normalize to same ID
   - **Mitigation**: Collision detection, disambiguation strategies

5. **Path Conflicts**: 
   - **Risk**: Case-sensitive file systems cause issues
   - **Mitigation**: Test on multiple platforms, handle case sensitivity

## Migration Strategy

### Phase 1: New Implementation
1. Implement new components without touching existing data
2. Run parallel processing to validate output
3. Compare old vs new entity generation

### Phase 2: Data Migration  
1. Create document entities for all existing processed files
2. Map old random IDs to new deterministic IDs
3. Update all references in existing RDF data

### Phase 3: Validation
1. Verify all wiki links still resolve
2. Confirm no data loss
3. Performance testing with production datasets

## Files to Create/Update

### New Files
- `src/knowledgebase_processor/utils/id_generator.py`
- `src/knowledgebase_processor/services/document_registry.py`  
- `src/knowledgebase_processor/services/entity_registry.py`
- `tests/test_entity_id_integration.py`
- `tests/services/test_document_registry.py`

### Files to Update
- `src/knowledgebase_processor/models/kb_entities.py` (add KbDocument)
- `src/knowledgebase_processor/processor/processor.py` (always create document entities)
- `src/knowledgebase_processor/extractor/wikilink_extractor.py` (preserve text)
- `src/knowledgebase_processor/services/entity_service.py` (deterministic IDs)

## Implementation Timeline

### Week 1: Critical Infrastructure
- [ ] Create EntityIdGenerator with dual-path document ID generation
- [ ] Create DocumentRegistry with wiki link resolution  
- [ ] Update KbDocument model with dual-path fields
- [ ] Update processor to always create document entities

### Week 2: Entity Management
- [ ] Create EntityRegistry for deduplication
- [ ] Update entity service to use deterministic IDs
- [ ] Implement wiki link resolver with text preservation

### Week 3: Testing & Integration
- [ ] Create comprehensive test suite
- [ ] Run integration tests with sample data
- [ ] Performance testing and optimization
- [ ] Migration planning and testing

## Dependencies

- ADR-0012: Entity Modeling with Wiki-Based Architecture
- ADR-0013: Wiki-Based Entity ID Generation and Link Preservation  
- Existing entity models and RDF infrastructure
- Test cases from `entity-id-generation-test-cases.md`

## Expected Outcomes

After implementation:
1. Every document will be represented as a first-class entity in the knowledge graph
2. Wiki links will resolve reliably through preserved path matching
3. Entity duplication will be eliminated through deterministic ID generation
4. The knowledge graph will support true wiki-style document relationships
5. Performance will meet established benchmarks (< 1ms ID generation)

This implementation plan provides the foundation for a robust wiki-based knowledge graph that maintains compatibility while eliminating critical architectural gaps.