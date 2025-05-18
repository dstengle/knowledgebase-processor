# Knowledge Graph Architecture Documentation Plan

## Overview

This document outlines the plan for documenting the architectural shift from a document/metadata model to a knowledge graph approach using RDF and a triple/quad store. The plan includes capturing the decision, updating architectural documentation, and reflecting the new data flow and system impacts.

---

## Documentation Steps

1. **Create a new ADR**  
   - Document the decision to move to a knowledge graph/RDF-based system.
   - Include context, rationale, alternatives, and consequences.

2. **Update System Architecture Documentation**  
   - Update `data-flow.md` and system-overview docs.
   - Add a "Document Inference" step after the Document Model, before entity/relationship extraction.
   - Update or add Mermaid diagrams and revise data model sections to reflect node/edge/triple representations.

3. **Update or Add Feature Specifications**  
   - Knowledge graph extraction.
   - RDF export.
   - Querying via SPARQL or similar.

4. **Update the Evolution Roadmap**  
   - Mark this as a major architectural milestone.

---

## Revised Data Flow Diagram

```mermaid
flowchart LR
    A[Markdown Document] --> B[Document Model]
    B --> C[Document Inference (Topics/Tags)]
    C --> D[Entity & Relationship Extraction]
    D --> E[Typed Graph Nodes/Edges]
    E --> F[RDF Triple/Quad Store]
    F --> G[Graph Query Interface]
```

---

## Notes

- The "Document Inference" step enables extraction of topics and tags at the document level before entity and relationship extraction.
- This plan ensures the rationale, impact, and technical details of the architectural shift are clearly documented and traceable across the system documentation.