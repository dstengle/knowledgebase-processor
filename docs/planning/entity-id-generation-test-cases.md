# Entity ID Generation Test Cases

**CRITICAL UPDATE (2025-07-21):** This document has been updated to align with ADR-0013 (Wiki-Based Entity ID Generation and Link Preservation). Key changes:

1. **Document ID tests now show dual-path model**: Tests return `(normalized_id, original_path, path_without_extension)` tuples
2. **Wiki link tests preserve original text**: No normalization of wiki link text during resolution
3. **Document registry-based resolution**: Wiki links resolve through path matching, not text normalization

These fixes are essential - the previous tests incorrectly showed document paths being normalized, which would break wiki link functionality per ADR-0013.</search>
</search_and_replace>

## Test Categories

### 1. Text Normalization Tests

#### Basic Normalization
```python
test_cases = [
    # Input, Expected Output
    ("John Smith", "john-smith"),
    ("JOHN SMITH", "john-smith"),
    ("John  Smith", "john-smith"),  # Multiple spaces
    ("John-Smith", "john-smith"),
    ("John_Smith", "john-smith"),
    ("John@Smith", "john-smith"),
    ("John Smith!", "john-smith"),
    ("John Smith, PhD", "john-smith-phd"),
    ("John Smith Jr.", "john-smith-jr"),
    ("Café", "cafe"),  # Unicode normalization
    ("naïve", "naive"),
    ("Zürich", "zurich"),
    ("", ""),  # Empty string
    ("---", ""),  # Only special chars
    ("-John-Smith-", "john-smith"),  # Leading/trailing hyphens
]
```

#### Edge Cases
```python
edge_cases = [
    ("John Smith III", "john-smith-iii"),
    ("3M Company", "3m-company"),
    ("O'Brien", "o-brien"),
    ("McDonald's", "mcdonald-s"),
    ("AT&T", "at-t"),
    ("C++", "c"),
    ("Node.js", "node-js"),
    ("COVID-19", "covid-19"),
    ("José María", "jose-maria"),
    ("Anne-Marie", "anne-marie"),
]
```

### 2. Document ID Generation Tests

#### Standard Paths (Dual-Path Model per ADR-0013)
```python
document_tests = [
    # File Path, (Expected Normalized ID, Original Path, Path Without Extension)
    ("daily-notes/2024-11-07.md", 
     ("/Document/daily-notes/2024-11-07", "daily-notes/2024-11-07.md", "daily-notes/2024-11-07")),
    ("Daily Notes/2024-11-07.md", 
     ("/Document/daily-notes/2024-11-07", "Daily Notes/2024-11-07.md", "Daily Notes/2024-11-07")),
    ("projects/KB Processor.md", 
     ("/Document/projects/kb-processor", "projects/KB Processor.md", "projects/KB Processor")),
    ("Meeting Notes/Q4 Planning.md", 
     ("/Document/meeting-notes/q4-planning", "Meeting Notes/Q4 Planning.md", "Meeting Notes/Q4 Planning")),
    ("README.md", 
     ("/Document/readme", "README.md", "README")),
    ("docs/architecture/ADR-001.md", 
     ("/Document/docs/architecture/adr-001", "docs/architecture/ADR-001.md", "docs/architecture/ADR-001")),
]
```

#### Path Edge Cases (Dual-Path Model)
```python
path_edge_cases = [
    # File Path, (Expected Normalized ID, Original Path, Path Without Extension)
    ("file.md.md", 
     ("/Document/file-md", "file.md.md", "file.md")),  # Multiple extensions
    ("file.MD", 
     ("/Document/file", "file.MD", "file")),  # Case insensitive extension
    ("path/to/file.markdown", 
     ("/Document/path/to/file", "path/to/file.markdown", "path/to/file")),
    ("path//to///file.md", 
     ("/Document/path/to/file", "path//to///file.md", "path//to///file")),  # Multiple slashes preserved in original
    ("./path/to/file.md", 
     ("/Document/path/to/file", "./path/to/file.md", "./path/to/file")),  # Relative path preserved
    ("~/Documents/notes.md", 
     ("/Document/~/documents/notes", "~/Documents/notes.md", "~/Documents/notes")),  # Home directory preserved
]
```

### 3. Person Entity ID Tests

#### Name Variations
```python
person_tests = [
    # Name Input, Expected ID
    ("Alex Cipher", "/Person/alex-cipher"),
    ("Dr. Jane Smith", "/Person/jane-smith"),
    ("Prof. John Doe, PhD", "/Person/john-doe"),
    ("Mary Johnson-Smith", "/Person/mary-johnson-smith"),
    ("Jean-Paul Sartre", "/Person/jean-paul-sartre"),
    ("Martin Luther King Jr.", "/Person/martin-luther-king-jr"),
    ("A. B. Johnson", "/Person/a-b-johnson"),
    ("Madonna", "/Person/madonna"),  # Single name
    ("李明", "/Person/李明"),  # Non-ASCII preserved in normalized form
]
```

### 4. Organization Entity ID Tests

#### Company Names
```python
org_tests = [
    # Organization Name, Expected ID
    ("Galaxy Dynamics Co.", "/Organization/galaxy-dynamics"),
    ("Stellar Solutions Inc.", "/Organization/stellar-solutions"),
    ("The Coca-Cola Company", "/Organization/the-coca-cola-company"),
    ("AT&T Inc.", "/Organization/at-t"),
    ("3M", "/Organization/3m"),
    ("Twenty-First Century Fox", "/Organization/twenty-first-century-fox"),
    ("Ernst & Young LLP", "/Organization/ernst-young"),
    ("PricewaterhouseCoopers", "/Organization/pricewaterhousecoopers"),
]
```

### 5. Tag ID Tests

#### Hierarchical Tags
```python
tag_tests = [
    # Tag Input, Expected ID
    ("#meeting-notes", "/Tag/meeting-notes"),
    ("meeting-notes", "/Tag/meeting-notes"),  # Without hash
    ("#Meeting Notes", "/Tag/meeting-notes"),
    ("#status/in-progress", "/Tag/status/in-progress"),
    ("#person/alex-cipher", "/Tag/person/alex-cipher"),
    ("#project/KB/phase-1", "/Tag/project/kb/phase-1"),
    ("#2024/Q4", "/Tag/2024/q4"),
]
```

### 6. Document-Scoped Entity Tests

#### Todo Items
```python
todo_tests = [
    # Document ID, Todo Text, Line Number, Expected ID Pattern
    ("/Document/daily-notes/2024-11-07", "Review PR from Alex", 15, 
     r"^/Document/daily-notes/2024-11-07/TodoItem/15-[a-f0-9]{10}$"),
    ("/Document/projects/kb", "[ ] Implement ID generation", 42,
     r"^/Document/projects/kb/TodoItem/42-[a-f0-9]{10}$"),
]
```

#### Sections
```python
section_tests = [
    # Document ID, Heading, Parent Path, Expected ID
    ("/Document/readme", "Installation", None, 
     "/Document/readme/Section/installation"),
    ("/Document/readme", "Prerequisites", ["Installation"], 
     "/Document/readme/Section/installation/prerequisites"),
    ("/Document/guide", "Step 1: Setup", ["Getting Started"],
     "/Document/guide/Section/getting-started/step-1-setup"),
]
```

### 7. Wiki Link Resolution Tests

#### Link Patterns (Per ADR-0013: Wiki Link Text Preservation)
```python
wiki_link_tests = [
    # Link Text, Context, Expected Resolution (via Document Registry lookup, NOT normalization)
    ("[[Alex Cipher]]", {"in_attendees": True}, "/Person/alex-cipher"),  # Context-based entity resolution
    ("[[person:Alex Cipher]]", {}, "/Person/alex-cipher"),  # Typed entity link
    ("[[org:Galaxy Dynamics]]", {}, "/Organization/galaxy-dynamics"),  # Typed entity link  
    ("[[project:KB Processor]]", {}, "/Project/kb-processor"),  # Typed entity link
    
    # CRITICAL: Document links preserve original text for path matching
    ("[[Daily Note 2024-11-07 Thursday]]", {}, "/Document/daily-notes/2024-11-07-thursday"),  # Matches original file "Daily Note 2024-11-07 Thursday.md"
    ("[[README]]", {}, "/Document/readme"),  # Matches original file "README.md"
    ("[[Meeting Notes/Q4 Planning]]", {}, "/Document/meeting-notes/q4-planning"),  # Matches "Meeting Notes/Q4 Planning.md"
    
    # Placeholder for non-existent documents
    ("[[Non-Existent Page]]", {}, "/PlaceholderDocument/non-existent-page"),
]</search>
```

### 8. Deduplication Tests

#### Entity Deduplication
```python
dedup_tests = [
    # Test that these all resolve to the same entity
    {
        "inputs": [
            "Galaxy Dynamics Co.",
            "Galaxy Dynamics",
            "GALAXY DYNAMICS CO",
            "Galaxy Dynamics Inc."
        ],
        "expected_id": "/Organization/galaxy-dynamics",
        "expected_aliases": ["Galaxy Dynamics Co.", "Galaxy Dynamics Inc."]
    }
]
```

### 9. Collision Detection Tests

#### ID Collision Scenarios
```python
collision_tests = [
    # Different entities that might normalize to same ID
    {
        "entity1": {"type": "Person", "name": "John Smith"},
        "entity2": {"type": "Person", "name": "John Smith"},
        "same_entity": True,  # These should be the same
    },
    {
        "entity1": {"type": "Person", "name": "John Smith", "email": "john@company1.com"},
        "entity2": {"type": "Person", "name": "John Smith", "email": "john@company2.com"},
        "same_entity": False,  # Different people, need disambiguation
        "expected_ids": ["/Person/john-smith", "/Person/john-smith-1"]
    }
]
```

### 10. Property vs Entity Tests

#### Frontmatter Classification
```python
property_tests = [
    # Field, Value, Is Entity?
    ("created", "2024-11-07", False),
    ("author", "Alex Cipher", True),
    ("tags", ["meeting", "planning"], True),
    ("status", "draft", False),
    ("attendees", ["[[Alex]]", "[[Jane]]"], True),
    ("word_count", 1500, False),
    ("project", "[[KB Processor]]", True),
    ("version", "1.0.0", False),
]
```

### 11. Migration Tests

#### Old to New ID Mapping
```python
migration_tests = [
    # Old ID, New ID
    ("Organization/galaxy_dynamics_co_7a705a38", "/Organization/galaxy-dynamics"),
    ("Person/alex_cipher_42e0ac89", "/Person/alex-cipher"),
    ("DateEntity/2024_11_07t08_54_54_05_00_a3861516", None),  # Should not be entity
    ("TodoItem/todo_review_pr_abc123", "/Document/path/TodoItem/15-hash"),
]
```

### 12. Performance Tests

#### ID Generation Speed
```python
performance_requirements = {
    "single_id_generation": 1,  # < 1ms
    "bulk_generation_1000": 100,  # < 100ms for 1000 IDs
    "with_dedup_check": 5,  # < 5ms with deduplication
}
```

### 13. Integration Tests

#### End-to-End Scenarios
```python
integration_scenarios = [
    {
        "name": "Document with multiple same entities",
        "file_path": "Meeting Notes/Daily Standup 2024-11-07.md",  # Original file path
        "input": """
        ---
        author: Alex Cipher
        attendees:
          - Alex Cipher
          - Jane Smith
        ---
        
        Met with [[Alex Cipher]] and [[Jane Smith]] today.
        
        ## Action Items
        - [ ] Alex Cipher to review PR
        - [ ] Jane Smith to update docs
        """,
        "expected_entities": [
            # Document entity with dual-path model
            {
                "type": "Document",
                "kb_id": "/Document/meeting-notes/daily-standup-2024-11-07",
                "original_path": "Meeting Notes/Daily Standup 2024-11-07.md",
                "path_without_extension": "Meeting Notes/Daily Standup 2024-11-07"
            },
            # Deduplicated person entities
            "/Person/alex-cipher",  # Only one instance despite 3 mentions
            "/Person/jane-smith",   # Only one instance despite 2 mentions
            # Document-scoped entities
            "/Document/meeting-notes/daily-standup-2024-11-07/TodoItem/11-hash1",
            "/Document/meeting-notes/daily-standup-2024-11-07/TodoItem/12-hash2",
        ],
        "wiki_link_resolution": [
            # These wiki links should resolve via document registry, not normalization
            ("[[Alex Cipher]]", "context-based-person-resolution"),
            ("[[Jane Smith]]", "context-based-person-resolution")
        ]
    }
]
```

## Test Implementation Strategy

### 1. Unit Tests
- Test each ID generation function in isolation
- Verify normalization rules
- Check edge case handling

### 2. Integration Tests
- Test full pipeline from markdown to RDF
- Verify entity deduplication across documents
- Check wiki link resolution

### 3. Performance Tests
- Benchmark ID generation speed
- Test with large documents
- Measure memory usage with entity registry

### 4. Regression Tests
- Ensure old IDs can be mapped
- Verify no data loss during migration
- Check backwards compatibility

## Success Criteria

1. **100% Deterministic**: Same input always produces same ID
2. **No False Duplicates**: Different representations of same entity get same ID
3. **No False Merges**: Different entities get different IDs
4. **Performance Target**: < 1ms per ID generation
5. **Unicode Support**: Proper handling of international characters
6. **Path Safety**: Generated IDs are valid for file systems and URLs