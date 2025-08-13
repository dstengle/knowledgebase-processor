# ADR-0014: Vocabulary Reference Strategy

**Date:** 2025-08-13

**Status:** Proposed

## Context

The knowledgebase-processor requires a stable reference to the KB vocabulary defined in the external repository at https://github.com/dstengle/knowledgebase-vocabulary/. This vocabulary defines the RDF ontology used for knowledge graph representation.

Currently, the project:
- Has a temporary copy at `/tmp-vocab/kb.ttl`
- Uses hardcoded namespace `http://example.org/kb/` in the code
- Needs to ensure all processing uses the correct vocabulary
- Must make the vocabulary reference easy for LLM agent coders to understand and use

## Decision

We will implement a **hybrid approach** combining local caching with remote reference documentation:

### 1. Local Vocabulary Cache
- Maintain a local copy of the vocabulary at `/vocabulary/kb.ttl`
- Track this file in version control for deterministic builds
- Include version metadata in the file header

### 2. Source Reference Documentation
- Create `/vocabulary/README.md` documenting:
  - Source repository URL
  - Last sync date and commit hash
  - Update instructions
  - Namespace URI to use

### 3. Configuration-Based Namespace
- Define vocabulary namespace in configuration file
- Allow override via environment variable
- Default to the canonical namespace from the vocabulary

### 4. Sync Mechanism
- Provide a script `/scripts/sync-vocabulary.sh` to update from source
- Document the sync process for maintainers
- Include validation to ensure vocabulary compatibility

## Implementation Plan

### Directory Structure
```
vocabulary/
├── kb.ttl              # Local copy of vocabulary
├── README.md           # Documentation and source reference
├── VERSION.json        # Version metadata
└── .gitignore         # (empty - track all files)
```

### Version Metadata Format
```json
{
  "source_repository": "https://github.com/dstengle/knowledgebase-vocabulary",
  "source_commit": "sha-hash",
  "sync_date": "2025-08-13T14:00:00Z",
  "namespace": "http://example.org/kb/vocab#",
  "version": "0.1.0-dev"
}
```

### Configuration Integration
```python
# src/knowledgebase_processor/config/vocabulary.py
import json
from pathlib import Path
from rdflib import Namespace

def get_kb_namespace():
    """Get the KB namespace from vocabulary metadata."""
    vocab_dir = Path(__file__).parent.parent.parent.parent / "vocabulary"
    version_file = vocab_dir / "VERSION.json"
    
    if version_file.exists():
        with open(version_file) as f:
            metadata = json.load(f)
            return Namespace(metadata["namespace"])
    
    # Fallback to default
    return Namespace("http://example.org/kb/vocab#")

KB = get_kb_namespace()
```

## Rationale

This approach provides:

### For Development
- **Deterministic builds**: Local vocabulary ensures consistent behavior
- **Version control**: Track vocabulary changes with code changes
- **Offline development**: No runtime dependency on external repository

### For LLM Agents
- **Clear documentation**: README explains the vocabulary source and usage
- **Simple imports**: `from knowledgebase_processor.config.vocabulary import KB`
- **Explicit versioning**: VERSION.json shows exactly what vocabulary version is used
- **Update instructions**: Clear process for keeping vocabulary current

### For Maintenance
- **Traceable updates**: Git history shows when vocabulary was updated
- **Validation possible**: Can add tests to ensure vocabulary compatibility
- **Manual control**: Updates are intentional, not automatic

## Alternatives Considered

### 1. Git Submodule
- **Pros**: Automatic tracking of source repository
- **Cons**: Complex for LLM agents, requires git submodule knowledge

### 2. Runtime Fetching
- **Pros**: Always up-to-date
- **Cons**: Network dependency, non-deterministic, harder to debug

### 3. Direct Copy Only
- **Pros**: Simplest approach
- **Cons**: Loses connection to source, no version tracking

### 4. Package Dependency
- **Pros**: Standard Python approach
- **Cons**: Vocabulary repo not published as package

## Consequences

### Positive
- Clear provenance of vocabulary
- Deterministic builds
- Easy for LLM agents to understand
- Simple to update when needed
- Works offline

### Negative
- Manual sync required for updates
- Potential for drift from source
- Duplicate storage of vocabulary

### Mitigations
- Regular sync schedule (monthly or on major updates)
- CI check to warn if vocabulary is outdated
- Clear documentation of update process

## Related Decisions

- [ADR-0009: Knowledge Graph and RDF Store](0009-knowledge-graph-rdf-store.md)
- [ADR-0010: Entity Modeling for RDF Serialization](0010-entity-modeling-for-rdf-serialization.md)
- [ADR-0012: Entity Modeling with Wiki-Based Architecture](0012-entity-modeling-with-wiki-based-architecture.md)

## Notes

The vocabulary should be treated as a critical dependency. Any updates should be tested thoroughly to ensure compatibility with existing RDF data and queries.