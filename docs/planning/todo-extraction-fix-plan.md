# Plan to Fix Todo Item Extraction Issue

## Problem Summary

The TodoItemExtractor is not finding todo items in markdown files when they have leading whitespace. The current regex pattern `^-\s+\[([ xX])\]\s+(.+)$` expects the hyphen to be at the very start of a line (due to the `^` anchor), but the sample files have todo items with leading spaces.

### Example of the Issue

Current regex expects:
```markdown
- [ ] Todo item
- [x] Completed item
```

But the actual format in files is:
```markdown
 - [ ] Todo item
 - [x] Completed item
```

## Root Cause Analysis

1. **Regex Pattern Issue**: The `^` anchor in the regex pattern matches only at the start of a line, not allowing for any leading whitespace.
2. **Markdown Formatting**: In markdown, list items are often indented for readability or to indicate nesting levels.

## Proposed Solution

### Option 1: Update Regex Pattern (Recommended)
Modify the regex pattern to allow optional leading whitespace:

**Current pattern:**
```python
self.todo_pattern = re.compile(r'^-\s+\[([ xX])\]\s+(.+)$', re.MULTILINE)
```

**Updated pattern:**
```python
self.todo_pattern = re.compile(r'^\s*-\s+\[([ xX])\]\s+(.+)$', re.MULTILINE)
```

The change is adding `\s*` after `^` to match zero or more whitespace characters at the start of the line.

### Option 2: Use a More Flexible Pattern
For even more flexibility, we could remove the line anchor entirely:
```python
self.todo_pattern = re.compile(r'\s*-\s+\[([ xX])\]\s+(.+)', re.MULTILINE)
```

However, this might match todo items in code blocks or other contexts where they shouldn't be extracted.

## Implementation Steps

1. **Update TodoItemExtractor**
   - Modify the regex pattern in `src/knowledgebase_processor/extractor/todo_item.py`
   - Update the position calculation to account for leading whitespace

2. **Add Test Cases**
   - Add test cases in `tests/extractor/test_todo_item_extractor.py` for:
     - Todo items with no leading whitespace (existing case)
     - Todo items with single space indentation
     - Todo items with multiple spaces/tabs
     - Nested todo items (if applicable)

3. **Test with Sample Data**
   - Run the processor on `sample_data/daily-note-2024-11-07-Thursday.md`
   - Verify that all 6 todo items are extracted correctly

4. **Update Documentation**
   - Document the supported todo item formats
   - Add examples showing indented todo items

## Test Plan

### Unit Tests
```python
def test_extract_todos_with_leading_whitespace(self):
    """Test extracting todo items with leading whitespace."""
    content = """# Test Document
    
 - [ ] Single space indent
  - [x] Two space indent
    - [ ] Four space indent
\t- [x] Tab indent
"""
    # Test that all 4 items are extracted
```

### Integration Test
- Process the actual sample file and verify RDF generation includes all todo items

## Verification Steps

1. Run existing todo extractor tests to ensure no regression
2. Run new tests to confirm leading whitespace support
3. Process sample files and check RDF output contains todo items
4. Verify position tracking is still accurate with indented items

## Alternative Considerations

- Should we preserve indentation level information for nested todo lists?
- Should we have different handling for tabs vs spaces?
- Do we need to handle edge cases like mixed indentation?

## Risks and Mitigation

- **Risk**: Pattern might become too permissive and match non-todo content
  - **Mitigation**: Keep the hyphen and bracket structure requirements strict
  
- **Risk**: Position tracking might be off due to whitespace
  - **Mitigation**: Carefully test position calculation with various indentation levels

## Next Steps

1. Get approval for this plan
2. Switch to code mode to implement the changes
3. Run comprehensive tests
4. Update documentation