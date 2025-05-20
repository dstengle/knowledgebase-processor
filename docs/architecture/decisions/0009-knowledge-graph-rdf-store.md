# ADR Template

## ADR-0009: Knowledge Graph and RDF Store for Enhanced Knowledge Representation

**Date:** 2025-05-18

**Status:** Accepted

## Context

The current system relies on a document and metadata model, recently implemented with a SQLite-based metadata store. While functional for basic metadata and task extraction, this model presents limitations for more advanced knowledge representation and analysis. Specifically:
- Adding new kinds of knowledge (e.g., diverse entity types, complex relationships) requires significant SQL schema changes, making the system rigid.
- Performing relationship analysis beyond simple queries is difficult with the current structure.
- The goal is to create a composite view of knowledge, allowing for rich inference while retaining connections to the original markdown data.
- A more flexible approach is needed to represent various node types (meetings, people, books, topics, tasks) and their interconnections.

## Decision

We will adopt a knowledge graph approach using RDF (Resource Description Framework) and a triple/quad store for knowledge representation. The processing of markdown input will first create a document model, followed by document-level inference (e.g., topics, tags). Subsequently, typed nodes and relationships will be extracted from the document content and metadata to populate the knowledge graph.

## Rationale

This decision supports the project's goals for deeper knowledge analysis and extensibility:
- **Enhanced Flexibility**: A graph model with typed nodes (e.g., `ex:Person`, `ex:Meeting`, `ex:Topic`) and defined relationships (e.g., `ex:attends`, `ex:discusses`) is inherently more flexible than a relational schema for representing diverse and evolving knowledge structures.
- **Improved Querying and Inference**: RDF and SPARQL (the standard query language for RDF) allow for complex queries, pattern matching, and semantic inference that are difficult to achieve with SQL against the current model. This is crucial for relationship-based queries like "How do I know John Smith?" or "What tasks are related to Project Alpha meetings?".
- **Extensibility**: Adding new types of entities or relationships in a graph model typically involves defining new RDF classes and properties, rather than altering a rigid database schema.
- **Standardization**: RDF provides a W3C standard for data interchange on the Web, which can be beneficial for interoperability and leveraging existing tools and libraries.
- **Alignment with Processing Pipeline**: The planned two-stage processing (document model -> graph model) allows for initial data enrichment at the document level before transforming relevant pieces into a more structured knowledge graph.

This approach aligns with the architectural principle of "Iterative Enhancement" by providing a more robust foundation for future semantic and contextual analysis (Phase 2 and 3 of the roadmap).

## Alternatives Considered

1.  **Evolving the Existing SQLite Document/Metadata Model:**
    *   **Description:** Continue using the SQLite store and incrementally add tables/columns to support new knowledge types and relationships.
    *   **Advantages:** Builds on existing infrastructure and developer familiarity.
    *   **Disadvantages:** Becomes increasingly complex and unwieldy as more diverse knowledge types and relationships are added. Schema evolution is cumbersome and error-prone. Limited capabilities for complex graph-like queries and inference.

2.  **Using a Non-RDF Graph Database (e.g., Property Graph like Neo4j):**
    *   **Description:** Employ a native graph database that uses a property graph model (nodes, relationships, properties on both).
    *   **Advantages:** Can be simpler to set up for certain use cases, often with intuitive query languages (e.g., Cypher). Good performance for graph traversals.
    *   **Disadvantages:** While powerful, property graphs lack the formal semantics and standardization of RDF. SPARQL offers more expressive power for certain types of semantic queries and inference. RDF's schema language (RDFS/OWL) provides richer vocabulary definition capabilities. For a system focused on inferring relationships from textual data and potentially integrating diverse datasets, RDF's semantic web foundations are a better fit.

## Consequences

-   **Positive:**
    *   Significantly improved ability to represent and query complex relationships between entities.
    *   Greater flexibility in adding new types of knowledge without major schema overhauls.
    *   Clearer separation between the initial document processing stages and the structured knowledge representation.
    *   Enables more sophisticated features like semantic search and automated inference.
-   **Negative:**
    *   Introduction of new technologies (RDF, SPARQL, triple/quad store) requires a learning curve.
    *   Potential for increased complexity in the data pipeline initially.
    *   Choice of a specific triple/quad store backend will be a subsequent decision with its own implications.
    *   Performance considerations for very large knowledge graphs will need to be managed.
-   **Trade-offs:**
    *   Increased initial development effort and learning curve for the benefit of long-term flexibility, query power, and semantic richness.

## Related Decisions

-   This decision directly impacts and likely supersedes aspects of [`ADR-0008-flexible-metadata-store.md`](docs/architecture/decisions/0008-flexible-metadata-store.md), as the primary "queryable metadata" store will now be the RDF triple/quad store. The SQLite store might still be used for intermediate processing or caching, but not as the main analytical store.
-   Future ADRs will be needed for:
    *   Selection of a specific triple/quad store (e.g., Apache Jena, RDF4J, Oxigraph, etc.).
    *   Choice of RDF serialization formats (e.g., Turtle, N-Quads, JSON-LD).
    *   Definition of core ontologies/vocabularies.

## Notes

-   The processing pipeline will be: Raw Markdown -> Parsed Document Model -> Document-Level Inference (topics, tags, summaries) -> Extraction of Entities & Relationships -> RDF Triples/Quads -> Triple/Quad Store.
-   This shift emphasizes that the system is a composite view, not a system of record for the original markdown, but it will maintain links (e.g., via URIs) back to the source documents or specific sections within them.