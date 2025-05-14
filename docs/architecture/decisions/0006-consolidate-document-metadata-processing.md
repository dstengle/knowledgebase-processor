# ADR 0006: Consolidate Document and Metadata Processing

**Date**: 2025-05-14

**Status**: Proposed

## Context

The current implementation of the `Processor` in [`src/knowledgebase_processor/processor/processor.py`](src/knowledgebase_processor/processor/processor.py) has separate pathways for generating `Document` objects and `DocumentMetadata` objects. The `process_document` method internally creates a comprehensive `DocumentMetadata` instance (including document-level entities and entities within wikilinks) but only returns the `Document` object. If calling code (like the test suite) then calls `extract_metadata` separately, a new `DocumentMetadata` object is created. This new object correctly processes wikilink entities but lacks the document-level entities from the initial internal processing, leading to inconsistencies and test failures (e.g., `test_entities_in_doc_not_link_fixture` in [`tests/processor/test_wikilink_entity_processing.py`](tests/processor/test_wikilink_entity_processing.py)).

Additionally, two structurally identical Pydantic models exist for representing entities:
1.  `Entity` in [`src/knowledgebase_processor/models/metadata.py`](src/knowledgebase_processor/models/metadata.py)
2.  `ExtractedEntity` in [`src/knowledgebase_processor/models/entities.py`](src/knowledgebase_processor/models/entities.py)

This redundancy can lead to confusion and unnecessary complexity.

## Decision

To resolve these issues, we will:

1.  **Consolidate Entity Models**:
    *   Standardize on the `ExtractedEntity` model from [`src/knowledgebase_processor/models/entities.py`](src/knowledgebase_processor/models/entities.py) as the single source of truth for recognized entities.
    *   Remove the redundant `Entity` model definition from [`src/knowledgebase_processor/models/metadata.py`](src/knowledgebase_processor/models/metadata.py).
    *   Update all references, including the `entities` field in the `Document` model ([`src/knowledgebase_processor/models/content.py`](src/knowledgebase_processor/models/content.py)), to use `ExtractedEntity`.

2.  **Centralize Metadata Creation and Association**:
    *   The `Processor.process_document()` method will become the sole source for creating and populating a comprehensive `DocumentMetadata` object.
    *   This fully populated `DocumentMetadata` object will be attached directly to the `Document` object it describes.
    *   Modify the `Document` model ([`src/knowledgebase_processor/models/content.py`](src/knowledgebase_processor/models/content.py)) to include a field: `metadata: Optional[DocumentMetadata] = None`.

3.  **Refactor `Processor.process_document()`**:
    *   The method will orchestrate all extraction, analysis (including entity recognition for both document content and wikilink display text), and metadata population.
    *   The final step within `process_document()` will be to assign the created and populated `DocumentMetadata` instance to the `document.metadata` field.

4.  **Deprecate/Remove `Processor.extract_metadata()`**:
    *   With `process_document()` handling all metadata creation and association, the separate `extract_metadata()` method becomes redundant and the source of the inconsistency. Its logic for populating metadata from document elements will be integrated into `process_document()`.

5.  **Update Tests**:
    *   Test helpers (like `_process_fixture` in [`tests/processor/test_wikilink_entity_processing.py`](tests/processor/test_wikilink_entity_processing.py)) will be updated to retrieve metadata from `processed_document.metadata` after calling `process_document()`.

## Detailed Plan for `Processor.process_document()` Refactoring

The refactored `process_document(self, document: Document) -> Document` method in [`src/knowledgebase_processor/processor/processor.py`](src/knowledgebase_processor/processor/processor.py) will follow this sequence:

1.  **Run Extractors**: Iterate through `self.extractors` to populate `document.elements`.
2.  **Update Document Title**: Set `document.title` (e.g., from frontmatter in `document.elements` or filename).
3.  **Preserve Content**: Call `document.preserve_content()`.
4.  **Initialize `doc_metadata`**: Create `doc_metadata = DocumentMetadata(document_id=document.id, title=document.title, path=document.path)`.
5.  **Populate `doc_metadata` from `document.elements`**:
    *   Iterate through `document.elements`.
    *   For `frontmatter` elements: Parse and populate `doc_metadata.frontmatter` and `doc_metadata.tags`.
    *   For `tag` elements: Add to `doc_metadata.tags`.
    *   For `link` elements: Add the `Link` object to `doc_metadata.links`.
    *   For `wikilink` elements (which are `WikiLink` model instances):
        *   Use `self.entity_recognizer.analyze_text_for_entities(wikilink_element.display_text)` (using the `Processor`'s `entity_recognizer` instance) to get `ExtractedEntity` objects.
        *   Set `wikilink_element.entities` with the result.
        *   Add the updated `wikilink_element` (now containing its entities) to `doc_metadata.wikilinks`.
    *   Populate `doc_metadata.structure` with `document.content`, `document.title`, and a summary of `document.elements`.
6.  **Run Analyzers**:
    *   Iterate through `self.analyzers`.
    *   If an analyzer is an `EntityRecognizer` instance: Call `analyzer.analyze(document.content, doc_metadata)`. This populates `doc_metadata.entities` with document-wide `ExtractedEntity` objects.
    *   For other analyzers: Call them as appropriate (e.g., `analyzer.analyze(document)`).
7.  **Run Enrichers**: Iterate through `self.enrichers` and call `enricher.enrich(document)`.
8.  **Attach Metadata**: Set `document.metadata = doc_metadata`.
9.  **Return**: Return the `document` object.

### Visual Flow

```mermaid
graph TD
    A[Start process_document(document)] --> B[Run Extractors (populates document.elements)];
    B --> C[Update document.title];
    C --> D[document.preserve_content()];
    D --> E[Initialize doc_metadata = DocumentMetadata(...)];
    E --> F{Iterate document.elements (to populate doc_metadata based on elements)};
    F -- frontmatter --> G[Parse frontmatter, update doc_metadata.frontmatter, doc_metadata.tags];
    F -- tag --> H[Add tag to doc_metadata.tags];
    F -- link --> I[Add link to doc_metadata.links];
    F -- wikilink --> J[Use self.entity_recognizer.analyze_text_for_entities(wikilink.display_text) -> List[ExtractedEntity]];
    J --> K[Populate wikilink_element.entities];
    K --> L[Add wikilink_element to doc_metadata.wikilinks];
    F -- done iterating elements --> M[Populate doc_metadata.structure];
    M --> N{Iterate self.analyzers};
    N -- EntityRecognizer instance --> O[Call analyzer.analyze(document.content, doc_metadata) to populate doc_metadata.entities with List[ExtractedEntity]];
    N -- Other analyzers --> P[Call analyzer.analyze(document) or similar];
    N -- done iterating analyzers --> Q[Run Enrichers on document];
    Q --> R[Set document.metadata = doc_metadata];
    R --> S[Return document];
```

## Consequences

**Positive**:
*   Resolves the inconsistency in metadata generation, ensuring that a single, comprehensive `DocumentMetadata` object is created and associated with the `Document`.
*   Simplifies the data model by removing the redundant `Entity` class and standardizing on `ExtractedEntity`.
*   Makes metadata access more straightforward for consumers of the `Processor`, as it will be directly available via `document.metadata`.
*   Should fix the underlying issue causing `test_entities_in_doc_not_link_fixture` to fail.

**Negative**:
*   Requires changes in multiple files: `processor.py`, `models/content.py`, `models/metadata.py`, `models/entities.py` (potentially just for imports if `ExtractedEntity` is already well-defined), and test files.
*   Callers currently relying on `extract_metadata()` will need to update their code to access metadata from `document.metadata` after calling `process_document()`.

**Neutral**:
*   The `EntityRecognizer`'s dual methods (`analyze` for document content and `analyze_text_for_entities` for specific strings) fit well into this revised processing flow.

This change will lead to a more robust and predictable way of handling document processing and metadata extraction.