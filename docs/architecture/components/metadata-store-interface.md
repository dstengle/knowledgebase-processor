# Metadata Store Interface

## 1. Purpose and Scope

Defines the abstraction contract for metadata storage backends. All backends (JSON, SQLite, RDF, SPARQL, etc.) must conform to this interface.

## 2. Configuration and Runtime Selection

- **Configuration Format:**  
  - Backend type and configuration are specified in the processor config file (validated by Pydantic).
  - Example:
    ```toml
    [metadata_store]
    backend = "sqlite"
    db_path = "knowledgebase.db"
    ```
- **Runtime Selection:**  
  - The backend is selected at application startup based on configuration.
  - Environment variables or CLI arguments may override config file settings.
  - Dependency injection (constructor or DI framework) wires the selected backend.
- **Validation:**  
  - All configuration is validated before backend instantiation.
  - Backends must declare supported configuration schema and interface version.

## 3. Interface Contract

- **Core Methods:**  
  - `save(metadata: DocumentMetadata) -> str` (returns document_id)
  - `get(document_id: str) -> Optional[DocumentMetadata]`
  - `list_all() -> List[str]`
  - `search(query: Dict[str, Any]) -> List[str]`
  - `close() -> None`
- **Type Signatures:**  
  - Use Pydantic models for all metadata objects.
- **Error Handling:**  
  - All methods must raise custom exceptions for predictable failure modes.

## 4. Plugin/Backend Registration

- **Plugin Pattern:**  
  - Each backend registers itself with a central registry using a unique backend type string.
  - Discovery at runtime via entry points or registry.
  - Factory for backend instantiation.

## 5. Extensibility, Versioning, and Compliance

- **Hooks:**  
  - Allow pre/post-processing via overridable methods.
- **Versioning:**  
  - Interface and schema are versioned; backends must declare supported versions.
- **Testing:**  
  - All backends must pass an abstract test suite.

## 6. Example Usage

- Config-driven backend selection and instantiation.
- Registering a new backend.

## 7. Architecture Diagram

```mermaid
flowchart TD
    A[Config File] --> B[Backend Selector]
    B -->|Reads backend type| C[Backend Registry]
    C -->|Instantiates| D1[SQLite Backend]
    C -->|Instantiates| D2[JSON Backend]
    C -->|Instantiates| D3[RDF/SPARQL Backend]
    D1 -.->|Implements| E[MetadataStore Interface]
    D2 -.->|Implements| E
    D3 -.->|Implements| E
    E --> F[Processor Core]