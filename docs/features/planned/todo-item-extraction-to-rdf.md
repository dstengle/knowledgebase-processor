# Feature Specification: Todo Item Extraction to RDF

## Revision History

| Version | Date       | Author        | Changes                              |
|---------|------------|---------------|--------------------------------------|
| 0.1     | 2025-05-18 | Roo (AI Asst) | Initial draft                        |

## Feature Name

Todo Item Extraction to RDF

## Status

Proposed

## Summary

This feature enables the extraction of todo items (tasks) from Markdown documents and their representation as structured RDF resources within the knowledge graph. This allows tasks to be queried, managed, and related to other entities in the graph.

## Motivation

Todo items are a critical piece of information in many personal knowledge bases. Representing them as first-class citizens in the RDF graph, rather than just plain text, allows for:
- Centralized querying of all tasks across the knowledge base.
- Tracking task status (open/completed).
- Linking tasks to relevant documents, projects, people, or meetings.
- Building dedicated task management views or integrations.
- Analyzing task distribution, completion rates, and contexts.

## User Stories

- As a user, I want my Markdown todo items (e.g., `- [ ] Review ADR-0009`) to be automatically identified and added to the knowledge graph, so that I can query and manage them centrally.
- As a user, I want the status of my todo items (open or completed, e.g., `- [ ]` vs. `- [x]`) to be accurately reflected as a property of the task in the RDF graph.
- As a user, I want each extracted todo item in the graph to be linked back to its source Markdown document, so I can easily find its original context.
- As a user, I want todo items that mention specific entities (e.g., `Discuss [[Project Phoenix]] with @JaneDoe`) to potentially be linked to those entities in the RDF graph, so I can see tasks related to a project or person.

## Detailed Description

The system will parse Markdown content to identify lines that represent todo items, typically formatted as:
- `- [ ] An open task`
- `- [x] A completed task`
- `* [ ] Another open task`
- `* [X] Another completed task` (case-insensitive 'x')

For each identified todo item, an RDF resource of type `kb:ToDoItem` (or a similar class from a chosen vocabulary) will be created. This resource will have properties including:
- `dcterms:title`: The textual description of the task.
- `kb:hasStatus`: A link to a resource representing its status (e.g., `kb:StatusOpen`, `kb:StatusCompleted`).
- `dcterms:source`: A link to the RDF resource representing the source Markdown document.
- Optionally, other properties like `dcterms:created` (if a creation date can be inferred or is part of the task text) or links to related entities.

## Acceptance Criteria

1.  Standard Markdown todo items (`- [ ]`, `- [x]`, `* [ ]`, `* [X]`) are correctly parsed from document content.
2.  For each todo item, an RDF resource with `rdf:type kb:ToDoItem` (or equivalent) is generated.
3.  The `kb:ToDoItem` resource has a `dcterms:title` property containing the exact text of the task.
4.  The `kb:ToDoItem` resource has a `kb:hasStatus` property linking to `kb:StatusOpen` for `[ ]` tasks and `kb:StatusCompleted` for `[x]` or `[X]` tasks.
5.  The `kb:ToDoItem` resource is linked to the RDF resource representing its source document via `dcterms:source` (or a similar provenance predicate).
6.  Extraction is robust to variations in whitespace around brackets.

## Technical Implementation

### Components Involved

| Component                             | Role                                                                                                |
|---------------------------------------|-----------------------------------------------------------------------------------------------------|
| Reader & Parser                       | Parses Markdown into a Parsed Document Model, identifying list items and their checkbox state.        |
| Extractor (Entity & Relationship)     | Specifically identifies todo items from the Parsed Document Model elements and extracts their text and status. |
| RDF Conversion & Serialization        | Maps the extracted todo item data (text, status, source document link) to RDF triples using the defined `kb:ToDoItem` class and properties. |
| RDF Triple/Quad Store                 | Stores the generated RDF triples for the todo items.                                                |
| Initial RDF Vocabulary/Ontology       | Defines `kb:ToDoItem`, `kb:hasStatus`, `kb:StatusOpen`, `kb:StatusCompleted`.                       |

### Data Model Changes

Introduction of new RDF classes and properties:
-   **Classes**:
    -   `kb:ToDoItem`: Represents a task or todo item.
    -   `kb:StatusOpen`: Represents the status of an open task.
    -   `kb:StatusCompleted`: Represents the status of a completed task.
-   **Properties**:
    -   `kb:hasStatus` (domain: `kb:ToDoItem`, range: `kb:StatusOpen` or `kb:StatusCompleted`): Links a task to its status.
    -   (Standard properties like `dcterms:title`, `dcterms:source`, `rdf:type` will be reused).

**Example RDF (Turtle):**
```turtle
@prefix kb: <http://example.org/kb/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

<urn:uuid:task-123> a kb:ToDoItem ;
    dcterms:title "Review ADR-0009" ;
    kb:hasStatus kb:StatusOpen ;
    dcterms:source <urn:uuid:document-abc> .

<urn:uuid:task-456> a kb:ToDoItem ;
    dcterms:title "Update roadmap document" ;
    kb:hasStatus kb:StatusCompleted ;
    dcterms:source <urn:uuid:document-xyz> .

kb:StatusOpen a kb:Status .
kb:StatusCompleted a kb:Status .
```
(Note: URIs for tasks, documents, and status instances would be systematically generated).

### Process Flow

1.  **Reader & Parser** processes a Markdown file, creating a Parsed Document Model. This model identifies list items and whether they contain `[ ]` or `[x]`.
2.  **Orchestrator** passes the Parsed Document Model to the **Extractor**.
3.  **Extractor** iterates through relevant elements (e.g., list items) in the Parsed Document Model.
    - If a list item is identified as a todo item (contains `[ ]` or `[x]`), its text and status are extracted.
    - A unique identifier for the todo item is generated.
4.  The list of extracted todo items (with text, status, source document ID) is passed to the **RDF Conversion & Serialization** component.
5.  **RDF Conversion & Serialization** generates RDF triples for each todo item:
    - Creates a `kb:ToDoItem` resource.
    - Adds `dcterms:title` with the task text.
    - Adds `kb:hasStatus` linking to `kb:StatusOpen` or `kb:StatusCompleted`.
    - Adds `dcterms:source` linking to the source document's RDF resource.
6.  The generated RDF triples are loaded into the **RDF Triple/Quad Store**.

## Dependencies

| Dependency                             | Type    | Status  | Notes                                                        |
|----------------------------------------|---------|---------|--------------------------------------------------------------|
| Markdown Parser to Document Model      | Feature | Planned | Essential for identifying todo structures in Markdown.         |
| Initial RDF Vocabulary/Ontology Def.   | Feature | Planned | `kb:ToDoItem`, `kb:hasStatus`, etc., must be defined.        |
| RDF Conversion & Serialization Component | Feature | Planned | Needed to transform extracted data to RDF.                   |
| RDF Store Setup & Integration          | Feature | Planned | A store must be available to persist the RDF data.           |

## Limitations and Constraints

-   Initial implementation will focus on standard Markdown task syntax (`- [ ]`, `- [x]`). Non-standard variations might not be recognized.
-   Parsing of dates, priorities, or assignees embedded within the task text (e.g., "@John due:tomorrow !High") is out of scope for the initial version but is a candidate for future enhancement.
-   Contextual linking to other entities (projects, people) based on text analysis within the todo item is a future enhancement.

## Future Enhancements

-   Parse and model due dates, creation dates, completion dates from task text or surrounding context.
-   Extract and link assignees or mentioned people/projects (e.g., `@mention`, `[[wikilink]]` within task text).
-   Support for hierarchical tasks or sub-tasks if identifiable in Markdown.
-   Allow custom task status beyond open/completed.
-   Integrate with external task management systems by mapping their task models to/from RDF.

## Related Architecture Decisions

-   [ADR-0009: Knowledge Graph and RDF Store for Enhanced Knowledge Representation](../architecture/decisions/0009-knowledge-graph-rdf-store.md) - This feature is a direct implementation of leveraging the decided RDF architecture for a key data type.