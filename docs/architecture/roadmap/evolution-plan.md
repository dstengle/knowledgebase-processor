# System Evolution Plan

## Revision History

| Version | Date       | Author        | Changes                                                                          |
|---------|------------|---------------|----------------------------------------------------------------------------------|
| 0.2     | 2025-05-18 | Roo (AI Asst) | Aligned roadmap with Knowledge Graph/RDF architecture (ADR-0009). Updated phases, features, and metrics. |
| 0.1     | YYYY-MM-DD | [Name]        | Initial draft                                                                    |

## Overview

This document outlines the planned evolution of the Knowledge Base Processor system. It provides a roadmap for incremental development, focusing on delivering value at each stage while maintaining alignment with the architectural principles, particularly the shift towards an RDF-based knowledge graph as detailed in [ADR-0009](../decisions/0009-knowledge-graph-rdf-store.md).

## Core Use Cases

The development and prioritization of features in this evolution plan are significantly guided by a set of core use cases and target questions the system aims to address. These are detailed in the [Core Use Cases and Desired Outcomes document](../use-cases.md). The RDF knowledge graph is intended to provide a powerful backend for addressing these use cases.

## Expanded Concept of Knowledge Representation (RDF Focus)

With the shift to RDF, "knowledge" is represented as a graph of interconnected resources:
1.  **Document Structure as RDF**: Headings, sections, lists become part of the graph, linked to their source.
2.  **Explicit Metadata as RDF Properties**: Tags, categories, dates, frontmatter become RDF properties of document or entity resources.
3.  **Content Elements as RDF**: Key content snippets, quotes, and todo items can be represented as resources or literals within the graph.
4.  **Relationships as RDF Predicates**: Links, mentions, and conceptual connections (e.g., `meeting:discussesTopic`) become explicit RDF predicates.
5.  **Semantic Entities as RDF Resources**: Topics, persons, organizations, projects, meetings are first-class citizens (typed resources) in the graph.
6.  **Context via Graph Structure**: Proximity, co-occurrence, and provenance (e.g., source document for a triple) are modeled within the graph structure or using quads.

The goal is to transform the knowledge base content into a rich, queryable RDF knowledge graph.

## Development Phases

### Phase 1: Foundational Knowledge Graph & Core Extraction

**Focus**: Establish the basic RDF infrastructure, parse Markdown, and extract core structural elements and explicit metadata into an initial RDF graph. Todo item extraction is a key deliverable.

**Goals**:
- Set up the basic RDF triple/quad store.
- Define an initial RDF vocabulary/ontology for core concepts (documents, sections, persons, tasks, basic relationships).
- Implement Reader & Parser for Markdown to Parsed Document Model.
- Extract document structure (headings, sections), frontmatter, and explicit tags into RDF.
- Identify and extract todo items with their status and context, representing them as RDF resources with appropriate properties.
- Extract basic links and references, representing them as RDF relationships.
- Ensure the Parsed Document Model is robust for subsequent, more detailed analysis.

**Success Criteria**:
- System can read Markdown and produce a Parsed Document Model.
- An RDF store is operational and can be populated.
- Basic document structure, frontmatter, and tags are represented in the RDF graph.
- Todo items are correctly extracted and represented as queryable RDF resources with status and textual content.
- Simple SPARQL queries can retrieve documents, their sections, and associated todo items.

**Timeframe**: [Estimated timeframe]

### Phase 2: Semantic Enrichment & Deeper Graph Modeling

**Focus**: Enhance the RDF graph with richer semantic information through document-level inference and more detailed entity/relationship extraction.

**Goals**:
- Implement Analyzer for document-level inference (topics, inferred tags, summaries) from the Parsed Document Model, adding this information to the RDF graph.
- Implement Extractor for detailed entity recognition (persons, organizations, projects, meetings) and relationship extraction (e.g., person attends meeting, document mentions project), populating the RDF graph.
- Refine and expand the RDF vocabulary/ontology to support these new entities and relationships.
- Model contextual information (e.g., source of a statement using quads/named graphs).
- Analyze todo items within their graph context (e.g., linked projects, mentioned people).

**Success Criteria**:
- The RDF graph contains typed entities (persons, meetings, topics) linked by meaningful relationships.
- Document-level inferences (topics, tags) are attached to document resources in the graph.
- Todo items are linked to relevant entities (e.g., projects, people mentioned in the task).
- SPARQL queries can retrieve information based on semantic relationships (e.g., "find all meetings discussing Topic X attended by Person Y").

**Timeframe**: [Estimated timeframe]

### Phase 3: Advanced Querying, Integration & Representation

**Focus**: Leverage the rich RDF knowledge graph through advanced SPARQL querying, develop useful representations, and enable integrations.

**Goals**:
- Develop a comprehensive suite of SPARQL queries to address the [Core Use Cases](../use-cases.md).
- Implement a robust Graph Query Interface (SPARQL endpoint).
- Create specialized views and dashboards, particularly for todo items and task management, powered by SPARQL queries.
- Explore RDF graph visualization techniques.
- Enable integration with external tools by exposing query capabilities or RDF data.

**Success Criteria**:
- A significant portion of the target questions from the Core Use Cases can be answered via SPARQL queries.
- Todo items can be effectively viewed, filtered, and managed across the knowledge base using graph-derived views.
- The knowledge graph structure provides intuitive navigation and discovery paths.
- At least one meaningful integration with an external tool or workflow is demonstrated.

**Timeframe**: [Estimated timeframe]

### Phase 4: Refinement, Optimization & Extension

**Focus**: Refine the system based on usage, optimize performance, and extend capabilities, including the ontology and query patterns.

**Goals**:
- Optimize SPARQL query performance and RDF store efficiency.
- Refine and expand the RDF ontology based on emergent patterns and user needs.
- Add advanced analytical capabilities using graph algorithms or RDF inferencing (e.g., RDFS/OWL reasoning).
- Enhance todo item tracking with more sophisticated status models or dependencies within the graph.
- Ensure long-term maintainability of the RDF model and processing pipeline.

**Success Criteria**:
- System performs well with the user's full knowledge base.
- Advanced graph features (e.g., inference, pathfinding) provide additional value.
- Todo management features are robust and enhance productivity.
- The RDF model is well-documented and maintainable.

**Timeframe**: [Estimated timeframe]

## Feature Roadmap

| Feature                                         | Phase | Priority | Status  | Dependencies                                       | Notes (RDF Context)                                     |
|-------------------------------------------------|-------|----------|---------|----------------------------------------------------|---------------------------------------------------------|
| Markdown Parser to Document Model               | 1     | High     | Planned | None                                               | Foundation for all RDF generation                       |
| Initial RDF Vocabulary/Ontology Definition      | 1     | High     | Planned | None                                               | Core classes (Document, Section, Task) & properties     |
| RDF Store Setup & Integration                   | 1     | High     | Planned | None                                               | Choose and integrate a triple/quad store                |
| Heading & Section Extraction to RDF             | 1     | High     | Planned | Parser, RDF Vocab                                  | `kb:Document hasSection kb:SectionX`                    |
| Frontmatter & Explicit Tag Extraction to RDF    | 1     | High     | Planned | Parser, RDF Vocab                                  | `kb:Document dcterms:title "X"; dcterms:subject "tagY"` |
| **Todo Item Extraction to RDF**                 | 1     | High     | Planned | Parser, RDF Vocab                                  | `kb:TaskX a kb:ToDoItem; dcterms:title "..."; kb:hasStatus kb:StatusOpen` |
| Basic Link & Reference Extraction to RDF        | 1     | Medium   | Planned | Parser, RDF Vocab                                  | `kb:DocumentA dcterms:references kb:DocumentB`          |
| Document-Level Inference (Topics, Tags) to RDF  | 2     | High     | Planned | Parser, RDF Vocab, Analyzer Component              | `kb:DocumentA kb:hasTopic kb:TopicZ`                    |
| Entity Recognition (Person, Org, Project) to RDF| 2     | High     | Planned | Enriched Doc Model, RDF Vocab, Extractor Component | `kb:PersonX a foaf:Person; foaf:name "J. Doe"`          |
| Relationship Extraction to RDF                  | 2     | High     | Planned | Entity Reco., RDF Vocab, Extractor Component       | `kb:PersonX kb:attends kb:MeetingY`                     |
| **Todo Item Contextual Linking in RDF**         | 2     | High     | Planned | Todo RDF, Entity RDF                               | `kb:TaskX kb:relatedToProject kb:ProjectAlpha`          |
| Advanced RDF Vocabulary/Ontology Expansion      | 2     | Medium   | Planned | Initial RDF Vocab, Phase 2 Learnings               | More specific relationships, classes                    |
| SPARQL Endpoint Implementation                  | 3     | High     | Planned | RDF Store, Phase 2 Graph Data                      | Core query capability                                   |
| SPARQL Queries for Core Use Cases               | 3     | High     | Planned | SPARQL Endpoint, Rich Graph                        | Answering user questions                                |
| **Todo Management View (SPARQL-driven)**        | 3     | High     | Planned | SPARQL Queries, Todo RDF                           | Centralized task overview                               |
| RDF Graph Visualization (Exploratory)           | 3     | Medium   | Planned | SPARQL Endpoint / RDF Store Access                 | Understanding graph structure                           |
| External Tool Integration via SPARQL/RDF        | 3     | Medium   | Planned | SPARQL Endpoint                                    | Exporting/linking knowledge                             |
| Performance Optimization (Store & Queries)      | 4     | High     | Planned | Populated Graph, Usage Patterns                    | Scalability and responsiveness                          |
| RDF Inferencing (RDFS/OWL Basics)               | 4     | Medium   | Planned | Stable Ontology, RDF Store with Inf. Support       | Deriving new knowledge                                  |
| **Advanced Todo Tracking in RDF**               | 4     | Medium   | Planned | Todo View, Ontology                                | Dependencies, sub-tasks in graph                        |
| Ontology Refinement & Documentation             | 4     | High     | Planned | Usage Feedback                                     | Maintainability, clarity                                |

## Technical Debt Management
(As previously stated, with emphasis on RDF model and ontology documentation)

## Adaptation Strategy
(As previously stated, feedback will inform ontology evolution and SPARQL query development)

## Success Metrics

1.  **Knowledge Graph Fidelity & Richness**:
    *   How accurately and comprehensively does the RDF graph represent the structure, content, and semantics of the knowledge base?
    *   Are todo items correctly modeled in RDF with their status, context, and relevant links (e.g., to projects, people)?
    *   Does the ontology effectively capture the key concepts and relationships?

2.  **Querying & Inferential Power**:
    *   Can SPARQL queries effectively retrieve complex information and answer the target questions from the [Core Use Cases document](../use-cases.md)?
    *   Does the graph structure (and any basic inferencing) reveal connections and insights not obvious in the original format?
    *   Is todo management enhanced by the ability to query and relate tasks within the graph?

3.  **Practical Utility & Integration**:
    *   Does the RDF knowledge graph enable more effective use and navigation of the knowledge base?
    *   Do SPARQL-driven views (especially for todo items) improve task management?
    *   Can the RDF data be integrated with or exported for use in other tools?

4.  **Personal Value**:
    *   Does the system, with its RDF backend, provide significant value in managing personal knowledge and tasks?