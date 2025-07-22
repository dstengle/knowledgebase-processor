# Test Cases ADR Alignment Analysis

**Date:** 2025-07-21  
**Status:** Analysis Complete  
**Based on:** ADR-0012, ADR-0013, and existing test cases  

## Overview

This document analyzes how the existing entity ID generation test cases align with the architectural decisions in ADR-0012 and ADR-0013, and identifies any gaps or updates needed.

## Test Case Alignment Assessment

### ✅ Fully Aligned Test Cases

#### 1. Text Normalization Tests
**Status:** ✅ Fully Compatible  
**ADR Reference:** ADR-0013 Normalization Rules

The existing normalization test cases perfectly match ADR-0013 requirements:
- Unicode NFKD normalization
- Convert to lowercase
- Replace non-alphanumeric with hyphens
- Remove consecutive hyphens
- Trim hyphens from start/end

**Examples that align:**
```python
("John Smith", "john-smith")          # ✅ Matches ADR-0013
("Café", "cafe")                      # ✅ Unicode normalization
("John  Smith", "john-smith")         # ✅ Multiple spaces handled
```

#### 2. Person Entity ID Tests
**Status:** ✅ Fully Compatible  
**ADR Reference:** ADR-0013 ID Patterns

```python
("Alex Cipher", "/Person/alex-cipher")           # ✅ Matches pattern
("Dr. Jane Smith", "/Person/jane-smith")         # ✅ Title removal
("Martin Luther King Jr.", "/Person/martin-luther-king-jr")  # ✅ Suffix handling
```

#### 3. Organization Entity ID Tests
**Status:** ✅ Fully Compatible  
**ADR Reference:** ADR-0013 ID Patterns

```python
("Galaxy Dynamics Co.", "/Organization/galaxy-dynamics")     # ✅ Company suffix removal
("AT&T Inc.", "/Organization/at-t")                          # ✅ Special character handling
```

#### 4. Tag ID Tests
**Status:** ✅ Fully Compatible  
**ADR Reference:** ADR-0013 ID Patterns

```python
("#meeting-notes", "/Tag/meeting-notes")         # ✅ Hash removal
("#status/in-progress", "/Tag/status/in-progress")  # ✅ Hierarchical tags
```

### ⚠️ Partially Aligned Test Cases (Need Updates)

#### 1. Document ID Generation Tests
**Status:** ⚠️ Needs Extension  
**ADR Reference:** ADR-0013 Dual-Path Document Model

**Current tests:**
```python
("daily-notes/2024-11-07.md", "/Document/daily-notes/2024-11-07")
```

**Missing from current tests (per ADR-0013):**
- Original path preservation
- Path without extension for wiki links
- Dual-path return values

**Required additions:**
```python
# Test should verify all three return values
input_path = "Daily Notes/2024-11-07 Thursday.md"
expected = (
    "/Document/daily-notes/2024-11-07-thursday",    # normalized_id
    "Daily Notes/2024-11-07 Thursday.md",           # original_path  
    "Daily Notes/2024-11-07 Thursday"               # path_without_extension
)
```

#### 2. Wiki Link Resolution Tests
**Status:** ⚠️ Needs Critical Updates  
**ADR Reference:** ADR-0013 Wiki Link Text Preservation

**Current tests assume normalization:**
```python
("[[Daily Note 2024-11-07]]", {}, "/Document/daily-note-2024-11-07")
```

**ADR-0013 requires text preservation:**
```python
# Original text must be preserved for path matching
("[[Daily Note 2024-11-07 Thursday]]", {}, 
 should_resolve_to="/Document/daily-notes/2024-11-07-thursday")
 
# Resolution happens through document registry, not text normalization
```

**Critical updates needed:**
1. Wiki link text must NOT be normalized during resolution
2. Test document registry path matching instead
3. Add tests for file extension variations (.md, .markdown, .txt)

### ❌ Missing Test Categories (Critical Gaps)

#### 1. Document Entity Creation Tests
**Status:** ❌ Missing - Critical  
**ADR Reference:** ADR-0012/0013 Document as First-Class Entity

**Required new tests:**
```python
def test_document_entity_always_created():
    """Test that every document creates an entity"""
    # Test documents with no other entities still create document entity
    # Test document properties are stored correctly
    # Test document appears in RDF output

def test_document_dual_path_model():
    """Test dual-path document model"""
    # Test normalized ID generation
    # Test original path preservation  
    # Test path_without_extension for wiki links
```

#### 2. Document Registry Tests
**Status:** ❌ Missing - Critical  
**ADR Reference:** ADR-0013 Document Registry

**Required new tests:**
```python
def test_document_registry_wiki_link_resolution():
    """Test document registry path-based lookups"""
    # Test exact path matches
    # Test extension variations (.md, .markdown, .txt)
    # Test case sensitivity handling
    # Test path normalization vs original preservation

def test_document_registry_registration():
    """Test document registration process"""
    # Test mapping of paths to IDs
    # Test duplicate registration handling
    # Test path conflict resolution
```

#### 3. Entity Registry Deduplication Tests
**Status:** ❌ Missing - Important  
**ADR Reference:** ADR-0013 Entity Deduplication

**Required new tests:**
```python
def test_entity_registry_deduplication():
    """Test cross-document entity deduplication"""
    # Test same entity in multiple documents gets same ID
    # Test alias management
    # Test entity merging with additional properties

def test_entity_registry_collision_handling():
    """Test entity ID collision scenarios"""
    # Test different entities that normalize to same ID
    # Test disambiguation strategies
    # Test collision detection and resolution
```

#### 4. Bidirectional Relationship Tests  
**Status:** ❌ Missing - Important
**ADR Reference:** ADR-0012 Updated Pipeline

**Required new tests:**
```python
def test_document_entity_relationships():
    """Test bidirectional document-entity relationships"""
    # Test document -> entity relationships (hasEntity)
    # Test entity -> document relationships (mentionedIn)
    # Test relationship RDF generation
```

#### 5. Property vs Entity Classification Tests
**Status:** ❌ Missing - Important  
**ADR Reference:** ADR-0012 Property Distinction

**Current property tests are basic:**
```python
("created", "2024-11-07", False)
("author", "Alex Cipher", True)
```

**Need comprehensive classification tests:**
```python
def test_frontmatter_property_classification():
    """Test property vs entity classification rules"""
    # Test date fields as properties
    # Test person references as entities
    # Test wiki link detection in values
    # Test array handling (tags, attendees)
```

## Test Implementation Updates Required

### 1. Update Document ID Tests
**File:** `tests/utils/test_id_generator.py`

```python
class TestDocumentIdGeneration:
    def test_dual_path_generation(self):
        """Test document ID generation returns all required paths"""
        generator = EntityIdGenerator()
        
        test_cases = [
            {
                "input": "Daily Notes/2024-11-07 Thursday.md",
                "expected_id": "/Document/daily-notes/2024-11-07-thursday",
                "expected_original": "Daily Notes/2024-11-07 Thursday.md", 
                "expected_wiki_path": "Daily Notes/2024-11-07 Thursday"
            }
        ]
        
        for case in test_cases:
            result_id, result_original, result_wiki = generator.generate_document_id(case["input"])
            assert result_id == case["expected_id"]
            assert result_original == case["expected_original"] 
            assert result_wiki == case["expected_wiki_path"]
```

### 2. Add Document Registry Tests
**File:** `tests/services/test_document_registry.py`

```python
class TestDocumentRegistry:
    def test_wiki_link_resolution_with_original_text(self):
        """Test wiki link resolution preserving original text"""
        registry = DocumentRegistry()
        
        # Register document with original path
        registry.register_document(
            "/Document/daily-notes/2024-11-07-thursday",
            "Daily Notes/2024-11-07 Thursday.md",
            "Daily Notes/2024-11-07 Thursday"
        )
        
        # Test resolution with exact original text
        result = registry.find_by_wiki_link("Daily Notes/2024-11-07 Thursday")
        assert result == "/Document/daily-notes/2024-11-07-thursday"
        
        # Test with extension variations
        result_md = registry.find_by_wiki_link("Daily Notes/2024-11-07 Thursday.md")
        assert result_md == "/Document/daily-notes/2024-11-07-thursday"
```

### 3. Add Integration Tests
**File:** `tests/integration/test_complete_entity_pipeline.py`

```python
class TestCompleteEntityPipeline:
    def test_document_with_entities_creates_all_expected_entities(self):
        """Test complete pipeline creates document + content entities"""
        markdown_content = '''
        ---
        author: Alex Cipher
        attendees:
          - Alex Cipher  
          - Jane Smith
        created: 2024-11-07
        ---
        
        Met with [[Alex Cipher]] and [[Jane Smith]] today.
        
        ## Action Items
        - [ ] Alex Cipher to review PR
        - [ ] Jane Smith to update docs
        '''
        
        # Process document
        result = processor.process_markdown_to_entities(
            markdown_content, 
            "Daily Notes/2024-11-07 Thursday.md"
        )
        
        # Verify document entity created
        assert "/Document/daily-notes/2024-11-07-thursday" in result.entities
        
        # Verify person entities deduplicated (Alex appears 3 times but one entity)
        alex_entities = [e for e in result.entities if "alex-cipher" in e.kb_id]
        assert len(alex_entities) == 1
        
        # Verify document-entity relationships
        doc_entity = result.get_document_entity()
        assert doc_entity.original_path == "Daily Notes/2024-11-07 Thursday.md"
```

## Priority Recommendations

### Critical (Week 1)
1. **Update document ID tests** - Add dual-path verification
2. **Add document registry tests** - Essential for wiki link resolution
3. **Add document entity creation tests** - Currently missing entirely

### Important (Week 2)  
1. **Update wiki link resolution tests** - Remove normalization assumptions
2. **Add entity registry tests** - Test deduplication across documents
3. **Add integration tests** - End-to-end pipeline verification

### Enhancement (Week 3)
1. **Add property classification tests** - Comprehensive frontmatter handling
2. **Add bidirectional relationship tests** - Document-entity links
3. **Add performance benchmark tests** - Verify ID generation speed

## Test Coverage Analysis

### Current Coverage Estimate: ~60%
- ✅ Basic ID generation patterns: Well covered
- ✅ Text normalization rules: Complete coverage
- ⚠️ Document handling: Partial coverage (missing dual-path)
- ❌ Document registry: No coverage
- ❌ Entity registry: No coverage  
- ❌ Wiki link resolution: Incorrect assumptions
- ❌ Integration scenarios: Minimal coverage

### Target Coverage: >90%
After implementing missing tests and updates, should achieve comprehensive coverage of ADR-0012/0013 requirements.

## Conclusion

The existing test cases provide a solid foundation for basic entity ID generation, but significant gaps exist for the critical features introduced in ADR-0012 and ADR-0013:

1. **Document entity creation** - No tests exist for this critical requirement
2. **Wiki link text preservation** - Current tests assume incorrect normalization behavior  
3. **Document registry** - No coverage of this essential service
4. **Entity deduplication** - Limited coverage of cross-document scenarios

The test suite requires substantial additions to ensure the implementation meets the ADR requirements and prevents regressions during the refactoring process.