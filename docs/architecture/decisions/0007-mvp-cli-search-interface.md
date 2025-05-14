# 0007. MVP CLI Search Interface and Datastore Choice

*   Status: Proposed
*   Date: 2025-05-14
*   Deciders: Roo (Architect AI), User
*   Consulted: N/A
*   Informed: N/A

## Context and Problem Statement

The project requires a search interface to query processed knowledge, as outlined in Phase 3 of the [Evolution Plan](../../roadmap/evolution-plan.md). The initial focus is on a Minimum Viable Product (MVP) delivered as a Command Line Interface (CLI). This requires selecting an appropriate datastore and defining a basic plan for implementation. The current `MetadataStore` uses individual JSON files and is not suitable for the complex queries identified in the [Core Use Cases](../../../use-cases.md).

## Decision Drivers

*   Support for structured queries based on entities, dates, tags, task status, and relationships.
*   Ease of integration with a Python-based CLI application.
*   Rapid development for an MVP.
*   Manageable complexity and dependencies for a personal knowledge base tool.
*   Ability to evolve the schema and query capabilities.

## Considered Options

1.  **SQLite:** Relational, serverless, file-based, good Python support.
2.  **NoSQL (Document Store like TinyDB):** Flexible schema, pure Python options available.
3.  **NoSQL (Graph Database like Neo4j):** Excellent for relationship-heavy queries, but potentially overkill and higher learning curve for MVP.
4.  **Search Engine (like Whoosh):** Optimized for full-text search, but less ideal as a primary store for structured relational data.
5.  **In-memory Store / Process Files on Demand:** Simplest start, but not persistent and scales poorly.

## Decision Outcome

Chosen option: **SQLite**, because it provides a good balance of structured query capabilities, ease of use for a CLI tool, good Python integration, and manageable lock-in for an MVP. It directly supports the relational nature of the data (documents, entities, tasks, links, and their connections) as identified in the use cases.

## Plan for MVP CLI Search Interface

1.  **Datastore Selection & Setup:**
    *   **Decision:** Adopt SQLite as the datastore for the MVP.
    *   **Action:**
        *   Modify or replace the existing `MetadataStore` to use SQLite.
        *   Define an initial database schema.

2.  **Database Schema Design (Initial):**
    *   Based on `DocumentMetadata` and the query use cases.
    *   **Core Tables & Relationships (Mermaid Diagram):**

    ```mermaid
    erDiagram
        documents {
            TEXT document_id PK
            TEXT file_path
            TEXT title
            TEXT created_at
            TEXT modified_at
            TEXT raw_content
        }

        entities {
            INTEGER entity_id PK
            TEXT name
            TEXT type
        }

        document_entities {
            TEXT document_id FK
            INTEGER entity_id FK
            PRIMARY KEY (document_id, entity_id)
        }

        tags {
            INTEGER tag_id PK
            TEXT name UNIQUE
        }

        document_tags {
            TEXT document_id FK
            INTEGER tag_id FK
            PRIMARY KEY (document_id, tag_id)
        }

        tasks {
            INTEGER task_id PK
            TEXT document_id FK
            TEXT description
            TEXT status
            TEXT due_date
            TEXT context
        }

        links {
            INTEGER link_id PK
            TEXT source_document_id FK
            TEXT target_document_id NULL
            TEXT target_url NULL
            TEXT link_text
            TEXT type
        }

        documents ||--o{ document_entities : "has"
        entities ||--o{ document_entities : "appears in"
        documents ||--o{ document_tags : "has"
        tags ||--o{ document_tags : "applied to"
        documents ||--o{ tasks : "contains"
        documents ||--o{ links : "originates from (source)"
    ```

3.  **Data Ingestion/Population:**
    *   **Action:** Modify the existing processing pipeline so that after a document is processed by the `Processor`, its extracted metadata, entities, tasks, etc., are saved into the new SQLite database via the updated `MetadataStore`.

4.  **CLI Interface Design:**
    *   **Tool:** Utilize a library like `click` or `argparse` within `src/knowledgebase_processor/cli/main.py` (or a new CLI entry point for search).
    *   **Initial Commands (examples):**
        *   `poetry run knowledgebase-processor search --entity "Jane Doe"`
        *   `poetry run knowledgebase-processor search --tag "meeting"`
        *   `poetry run knowledgebase-processor search --task-status "open"`
        *   `poetry run knowledgebase-processor search --after-date "YYYY-MM-DD" --before-date "YYYY-MM-DD"`
        *   `poetry run knowledgebase-processor search --text "keyword"` (simple text search for now)

5.  **Query Logic Implementation:**
    *   **Action:** Implement functions within the `MetadataStore` (or a new `QueryInterface` module) that take search parameters from the CLI and construct/execute the appropriate SQL queries against the SQLite database.

6.  **Output Formatting:**
    *   **Action:** Define how search results are presented to the user in the CLI (e.g., list of document paths, titles, relevant snippets).

## Consequences

*   The `MetadataStore` will need significant refactoring or replacement.
*   The processing pipeline will need to be updated to populate the SQLite database.
*   New CLI commands and underlying query logic will need to be developed.
*   This introduces a new dependency (SQLite, though often available with Python).
*   The schema is an initial proposal and may evolve as more complex query needs arise.

## Next Steps

*   Begin implementation of the SQLite-backed `MetadataStore`.
*   Develop the data ingestion logic.
*   Implement the initial CLI commands and query functionality.