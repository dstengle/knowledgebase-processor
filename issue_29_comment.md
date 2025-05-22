## Implementation Plan for Issue #29: Implement knowledgebase models for KbPerson and KbTodoItem

This plan outlines the steps to define `KbPerson` and `KbTodoItem` Pydantic models and implement their RDF serialization, as per [`docs/architecture/decisions/0010-entity-modeling-for-rdf-serialization.md`](docs/architecture/decisions/0010-entity-modeling-for-rdf-serialization.md:1).

### 1. Define Base Knowledge Base (KB) Entity Model

*   **Objective:** Create a common base Pydantic model for all KB entities.
*   **Tasks:**
    *   Identify common attributes for all KB Entities. Suggested attributes:
        *   `kb_id: str` (Unique identifier within the knowledge base, potentially a URI)
        *   `label: Optional[str]` (A human-readable label for the entity)
        *   `source_document_uri: Optional[str]` (URI of the source document from which this entity was derived/mentioned)
        *   `extracted_from_text_span: Optional[Tuple[int, int]]` (Character offsets in the source document if applicable)
        *   `creation_timestamp: datetime = Field(default_factory=datetime.utcnow)`
        *   `last_modified_timestamp: datetime = Field(default_factory=datetime.utcnow)`
    *   Create a Pydantic model named `KbBaseEntity`.
*   **File:** [`src/knowledgebase_processor/models/kb_entities.py`](src/knowledgebase_processor/models/kb_entities.py) (new file)

### 2. Implement `KbTodoItem` Model

*   **Objective:** Define the Pydantic model for to-do items.
*   **Tasks:**
    *   Define attributes specific to a to-do item, inheriting from `KbBaseEntity`. Suggested attributes:
        *   `description: str`
        *   `is_completed: bool = False`
        *   `due_date: Optional[datetime] = None`
        *   `priority: Optional[str] = None` (e.g., "high", "medium", "low")
        *   `context: Optional[str] = None` (Brief context or link to context)
        *   `assigned_to_uris: Optional[List[str]] = None` (List of URIs pointing to `KbPerson` entities)
        *   `related_project_uri: Optional[str] = None` (URI pointing to a `KbProject` entity - Note: `KbProject` is out of scope for this issue but the field can be included for future use)
    *   Create the `KbTodoItem(KbBaseEntity)` Pydantic model.
*   **File:** [`src/knowledgebase_processor/models/kb_entities.py`](src/knowledgebase_processor/models/kb_entities.py)

### 3. Implement `KbPerson` Model

*   **Objective:** Define the Pydantic model for person entities.
*   **Tasks:**
    *   Define attributes specific to a person, inheriting from `KbBaseEntity`. Suggested attributes:
        *   `full_name: Optional[str] = None`
        *   `given_name: Optional[str] = None`
        *   `family_name: Optional[str] = None`
        *   `aliases: Optional[List[str]] = None`
        *   `email: Optional[str] = None`
        *   `roles: Optional[List[str]] = None` (e.g., "Developer", "Manager")
    *   Create the `KbPerson(KbBaseEntity)` Pydantic model.
*   **File:** [`src/knowledgebase_processor/models/kb_entities.py`](src/knowledgebase_processor/models/kb_entities.py)

### 4. Implement RDF Serialization Logic

*   **Objective:** Create a component to convert `KbPerson` and `KbTodoItem` instances into RDF triples.
*   **Tasks:**
    *   **Define RDF Namespace and Prefixes:**
        *   Establish a project-specific namespace (e.g., `kb: <http://example.org/knowledgebase/>`).
        *   Include common namespaces like `rdf:`, `rdfs:`, `schema: <http://schema.org/>`, `xsd:`.
        *   This can be defined within the RDF converter module or a shared configuration.
    *   **Develop Mapping Strategy:**
        *   For `KbPerson` -> `kb:Person` (or `schema:Person`). Map fields like `full_name` to `rdfs:label`, `schema:name`, or `kb:fullName`. `email` to `schema:email`.
        *   For `KbTodoItem` -> `kb:TodoItem` (or `schema:Action`). Map fields like `description` to `rdfs:label` or `schema:description`, `is_completed` to `kb:isCompleted` (with `xsd:boolean`), `due_date` to `schema:dueDate` (with `xsd:dateTime`).
        *   Relationships like `assigned_to_uris` will be RDF properties linking to other entity URIs.
    *   **Create RDF Serialization Component:**
        *   Implement a module (e.g., `RdfConverter`) with functions:
            *   `def kb_entity_to_graph(entity: KbBaseEntity, base_uri: str = "http://example.org/kb/") -> Graph:`
            *   This function will take a KB entity instance and generate an RDFLib `Graph` containing the corresponding triples.
            *   The `base_uri` will be used to construct URIs for new entities if `kb_id` is not already a full URI.
*   **Files:**
    *   [`src/knowledgebase_processor/rdf_converter/converter.py`](src/knowledgebase_processor/rdf_converter/converter.py) (new file)
    *   [`src/knowledgebase_processor/rdf_converter/__init__.py`](src/knowledgebase_processor/rdf_converter/__init__.py) (new file)

### 5. Implement Unit Tests

*   **Objective:** Ensure the correctness of the new models and RDF serialization.
*   **Tasks:**
    *   **Model Tests:**
        *   Test instantiation of `KbBaseEntity`, `KbPerson`, `KbTodoItem` with valid data.
        *   Test Pydantic validation for required fields and data types.
        *   Test default value generation (e.g., timestamps).
    *   **RDF Serialization Tests:**
        *   Create sample `KbPerson` and `KbTodoItem` instances.
        *   Serialize them to RDF using the `RdfConverter`.
        *   Assert the correctness of the generated RDF graph:
            *   Verify the entity's RDF type (e.g., `<entity_uri> rdf:type kb:Person`).
            *   Verify literal properties (e.g., `<entity_uri> kb:fullName "John Doe"^^xsd:string`).
            *   Verify relationships (e.g., `<todo_uri> kb:assignedTo <person_uri>`).
            *   Test serialization with and without optional fields.
*   **Files:**
    *   [`tests/models/test_kb_entities.py`](tests/models/test_kb_entities.py) (new file)
    *   [`tests/rdf_converter/__init__.py`](tests/rdf_converter/__init__.py) (new file)
    *   [`tests/rdf_converter/test_converter.py`](tests/rdf_converter/test_converter.py) (new file)

### Diagram: New Components and Models

```mermaid
graph TD
    subgraph "Pydantic Models ([`src/knowledgebase_processor/models`](src/knowledgebase_processor/models))"
        KbBaseEntity["KbBaseEntity.py\n(kb_id, label, timestamps)"]
        KbTodoItem["KbTodoItem(KbBaseEntity)\n(description, is_completed, due_date)"]
        KbPerson["KbPerson(KbBaseEntity)\n(full_name, email, roles)"]
    end

    subgraph "RDF Conversion ([`src/knowledgebase_processor/rdf_converter`](src/knowledgebase_processor/rdf_converter))"
        RdfConverter["converter.py\n(kb_entity_to_graph())"]
        RdfNamespaces["(Namespaces: kb, schema, rdf, rdfs)"]
    end

    subgraph "Unit Tests"
        TestKbEntities["[`tests/models/test_kb_entities.py`](tests/models/test_kb_entities.py)"]
        TestRdfConverter["[`tests/rdf_converter/test_converter.py`](tests/rdf_converter/test_converter.py)"]
    end

    KbBaseEntity --> KbTodoItem
    KbBaseEntity --> KbPerson

    KbTodoItem -- Consumed by --> RdfConverter
    KbPerson -- Consumed by --> RdfConverter
    RdfNamespaces -- Used by --> RdfConverter

    RdfConverter -- Produces --> RDFGraph[(RDFLib Graph)]

    KbTodoItem -- Tested by --> TestKbEntities
    KbPerson -- Tested by --> TestKbEntities
    RdfConverter -- Tested by --> TestRdfConverter

    style KbBaseEntity fill:#f9f,stroke:#333,stroke-width:2px
    style KbTodoItem fill:#f9f,stroke:#333,stroke-width:2px
    style KbPerson fill:#f9f,stroke:#333,stroke-width:2px
    style RdfConverter fill:#ccf,stroke:#333,stroke-width:2px
    style RdfNamespaces fill:#ccf,stroke:#333,stroke-width:2px
    style TestKbEntities fill:#cfc,stroke:#333,stroke-width:2px
    style TestRdfConverter fill:#cfc,stroke:#333,stroke-width:2px