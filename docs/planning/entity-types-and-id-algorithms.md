# Entity Types and ID Generation Algorithms

## Entity Type Definitions

### 1. Document Entity

**Purpose**: Represents a markdown file in the knowledge base

**Properties**:
- `path`: Original file path relative to KB root
- `title`: Document title (from frontmatter or first heading)
- `type`: Document type (note, person, project, etc.)
- `created`: Creation timestamp
- `modified`: Last modification timestamp
- `content_hash`: Hash of document content for change detection

**ID Generation Algorithm**:
```python
def generate_document_id(file_path: str) -> str:
    # Remove file extension
    path_without_ext = file_path.rsplit('.', 1)[0]
    
    # Normalize path components
    parts = path_without_ext.split('/')
    normalized_parts = [normalize_text(part) for part in parts]
    
    # Join with forward slashes
    normalized_path = '/'.join(normalized_parts)
    
    return f"/Document/{normalized_path}"

# Example:
# "Daily Notes/2024-11-07 Thursday.md" → "/Document/daily-notes/2024-11-07-thursday"
```

### 2. Tag Entity

**Purpose**: Represents a tag used across documents

**Properties**:
- `name`: Tag name
- `category`: Optional tag category (from hierarchical tags)
- `color`: Optional display color
- `description`: Optional tag description

**ID Generation Algorithm**:
```python
def generate_tag_id(tag_text: str) -> str:
    # Remove # prefix if present
    tag = tag_text.lstrip('#')
    
    # Split hierarchical tags
    if '/' in tag:
        parts = tag.split('/')
        normalized_parts = [normalize_text(part) for part in parts]
        normalized_tag = '/'.join(normalized_parts)
    else:
        normalized_tag = normalize_text(tag)
    
    return f"/Tag/{normalized_tag}"

# Examples:
# "#meeting-notes" → "/Tag/meeting-notes"
# "#status/in-progress" → "/Tag/status/in-progress"
```

### 3. Person Entity

**Purpose**: Represents a person referenced in the knowledge base

**Properties**:
- `canonical_name`: Primary name for the person
- `aliases`: Alternative names or nicknames
- `email`: Email addresses
- `roles`: Roles or titles
- `organization`: Associated organization
- `social_profiles`: Links to social media profiles

**ID Generation Algorithm**:
```python
def generate_person_id(name: str) -> str:
    normalized_name = normalize_person_name(name)
    return f"/Person/{normalized_name}"

def normalize_person_name(name: str) -> str:
    # Handle common name patterns
    # "John Smith, PhD" → "john-smith"
    # "Dr. Jane Doe" → "jane-doe"
    # "A. B. Johnson" → "a-b-johnson"
    
    # Remove titles and suffixes
    name = remove_titles_and_suffixes(name)
    
    # Normalize spacing and case
    name = normalize_text(name)
    
    return name

# Examples:
# "Alex Cipher" → "/Person/alex-cipher"
# "Dr. Jane Smith, PhD" → "/Person/jane-smith"
```

### 4. Organization Entity

**Purpose**: Represents a company, team, or organization

**Properties**:
- `name`: Official organization name
- `aliases`: Alternative names or abbreviations
- `type`: Organization type (company, non-profit, team, etc.)
- `website`: Organization website
- `location`: Headquarters location

**ID Generation Algorithm**:
```python
def generate_organization_id(name: str) -> str:
    normalized_name = normalize_organization_name(name)
    return f"/Organization/{normalized_name}"

def normalize_organization_name(name: str) -> str:
    # Remove common suffixes
    suffixes = ['Inc.', 'Inc', 'LLC', 'Ltd.', 'Ltd', 'Co.', 'Co', 'Corp.', 'Corp']
    for suffix in suffixes:
        if name.endswith(f' {suffix}'):
            name = name[:-len(suffix)-1]
    
    return normalize_text(name)

# Examples:
# "Galaxy Dynamics Co." → "/Organization/galaxy-dynamics"
# "Stellar Solutions Inc." → "/Organization/stellar-solutions"
```

### 5. Location Entity

**Purpose**: Represents a geographical location

**Properties**:
- `name`: Location name
- `type`: Location type (city, building, room, etc.)
- `address`: Street address if applicable
- `coordinates`: GPS coordinates if known
- `parent_location`: Containing location (e.g., city for a building)

**ID Generation Algorithm**:
```python
def generate_location_id(name: str, parent: Optional[str] = None) -> str:
    normalized_name = normalize_text(name)
    
    if parent:
        normalized_parent = normalize_text(parent)
        return f"/Location/{normalized_parent}/{normalized_name}"
    
    return f"/Location/{normalized_name}"

# Examples:
# "San Francisco" → "/Location/san-francisco"
# "Conference Room A" in "Building 1" → "/Location/building-1/conference-room-a"
```

### 6. Project Entity

**Purpose**: Represents a project or initiative

**Properties**:
- `name`: Project name
- `status`: Current status
- `start_date`: Project start date
- `end_date`: Project end date or deadline
- `team_members`: Associated people
- `repository`: Code repository link if applicable

**ID Generation Algorithm**:
```python
def generate_project_id(name: str) -> str:
    normalized_name = normalize_text(name)
    return f"/Project/{normalized_name}"

# Examples:
# "Knowledge Base Processor" → "/Project/knowledge-base-processor"
# "Q4 2024 Planning" → "/Project/q4-2024-planning"
```

### 7. TodoItem Entity (Document-Scoped)

**Purpose**: Represents a todo item within a document

**Properties**:
- `description`: Todo text (without checkbox)
- `completed`: Boolean completion status
- `due_date`: Optional due date
- `assignees`: Optional assigned people
- `priority`: Optional priority level

**ID Generation Algorithm**:
```python
def generate_todo_id(document_id: str, todo_text: str, line_number: int) -> str:
    # Use first 10 chars of text hash + line number for stability
    text_hash = hashlib.sha256(todo_text.encode()).hexdigest()[:10]
    
    return f"{document_id}/TodoItem/{line_number}-{text_hash}"

# Example:
# Document: "/Document/daily-notes/2024-11-07"
# Todo: "Review PR from Alex"
# Line: 15
# → "/Document/daily-notes/2024-11-07/TodoItem/15-a3f5b2c8d1"
```

### 8. Section Entity (Document-Scoped)

**Purpose**: Represents a section within a document based on heading structure

**Properties**:
- `heading`: Section heading text
- `level`: Heading level (1-6)
- `content`: Section content
- `parent_section`: Parent section ID if nested

**ID Generation Algorithm**:
```python
def generate_section_id(document_id: str, heading: str, parent_path: List[str] = None) -> str:
    normalized_heading = normalize_text(heading)
    
    if parent_path:
        path_parts = [normalize_text(p) for p in parent_path]
        section_path = '/'.join(path_parts + [normalized_heading])
    else:
        section_path = normalized_heading
    
    return f"{document_id}/Section/{section_path}"

# Example:
# Document: "/Document/architecture/readme"
# Heading: "## Installation"
# Parent: "Getting Started"
# → "/Document/architecture/readme/Section/getting-started/installation"
```

### 9. PlaceholderDocument Entity

**Purpose**: Represents a wiki link target that doesn't exist yet

**Properties**:
- `title`: Original link text
- `referenced_by`: List of documents that link to this placeholder
- `created`: When first referenced
- `suggested_type`: Inferred entity type based on context

**ID Generation Algorithm**:
```python
def generate_placeholder_id(link_text: str) -> str:
    normalized_text = normalize_text(link_text)
    return f"/PlaceholderDocument/{normalized_text}"

# Example:
# "[[Future Project Ideas]]" → "/PlaceholderDocument/future-project-ideas"
```

## Common Normalization Function

```python
def normalize_text(text: str) -> str:
    """
    Standard text normalization for ID generation
    """
    # Unicode normalization (NFKD)
    text = unicodedata.normalize('NFKD', text)
    
    # Lowercase
    text = text.lower()
    
    # Replace spaces and special chars with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)
    
    # Remove consecutive hyphens
    text = re.sub(r'-+', '-', text)
    
    # Trim hyphens from start/end
    text = text.strip('-')
    
    return text
```

## ID Validation Rules

1. **Format Compliance**:
   - Must start with entity type prefix
   - Use forward slashes for hierarchy
   - Only lowercase alphanumeric and hyphens in segments

2. **Length Limits**:
   - Maximum total ID length: 256 characters
   - Maximum segment length: 64 characters

3. **Reserved Words**:
   - Cannot use: "admin", "api", "system", "internal"
   - Cannot start with underscore or number

4. **Uniqueness**:
   - Must be unique within entity type
   - Case-insensitive uniqueness check

## Collision Handling

When ID collisions occur (rare with proper normalization):

1. **Check for existing entity**
2. **If same content**: Use existing ID (deduplication)
3. **If different content**: 
   - Add minimal numeric suffix
   - Log warning for manual review
   - Consider if entities should be merged

Example:
```
/Person/john-smith (exists)
/Person/john-smith-1 (different person)
/Person/john-smith-2 (another different person)