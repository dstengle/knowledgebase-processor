# Entity Hierarchy Architecture

## Overview

This document presents the architectural design for the new entity hierarchy that supports wiki-based knowledge graphs with deterministic entity ID generation.

## Entity Hierarchy Diagram

```mermaid
graph TD
    subgraph "Root Level Entities"
        Document["📄 Document<br/>ID: /Document/{path}"]
        Tag["🏷️ Tag<br/>ID: /Tag/{name}"]
        Person["👤 Person<br/>ID: /Person/{name}"]
        Organization["🏢 Organization<br/>ID: /Organization/{name}"]
        Location["📍 Location<br/>ID: /Location/{name}"]
        Project["📁 Project<br/>ID: /Project/{name}"]
    end

    subgraph "Document-Scoped Entities"
        Section["📑 Section<br/>ID: /Document/{path}/Section/{heading}"]
        TodoItem["☑️ TodoItem<br/>ID: /Document/{path}/TodoItem/{hash}"]
        CodeBlock["💻 CodeBlock<br/>ID: /Document/{path}/CodeBlock/{hash}"]
        Table["📊 Table<br/>ID: /Document/{path}/Table/{hash}"]
    end

    subgraph "Virtual Entities"
        PlaceholderDoc["📄 PlaceholderDocument<br/>ID: /PlaceholderDocument/{name}"]
    end

    Document --> Section
    Document --> TodoItem
    Document --> CodeBlock
    Document --> Table
    Document -.->|"wiki link"| Document
    Document -.->|"references"| Person
    Document -.->|"references"| Organization
    Document -.->|"references"| Location
    Document -.->|"references"| Project
    Document -.->|"has tag"| Tag
    Document -.->|"links to missing"| PlaceholderDoc
```

## Entity ID Generation Flow

```mermaid
flowchart LR
    subgraph "Input Processing"
        Input["Raw Text/Link"]
        Context["Context Analysis"]
        Type["Type Detection"]
    end

    subgraph "Normalization"
        Normalize["Text Normalization<br/>• Lowercase<br/>• Replace spaces<br/>• Remove special chars"]
        Dedupe["Deduplication Check<br/>• Check existing entities<br/>• Resolve aliases"]
    end

    subgraph "ID Generation"
        GenID["Generate ID<br/>Based on entity type<br/>and normalized name"]
        Validate["Validate ID<br/>• Check uniqueness<br/>• Format compliance"]
    end

    Input --> Context
    Context --> Type
    Type --> Normalize
    Normalize --> Dedupe
    Dedupe --> GenID
    GenID --> Validate
    Validate --> EntityID["Entity ID"]
```

## Wiki Link Resolution Process

```mermaid
flowchart TD
    WikiLink["[[Wiki Link]]"]
    
    WikiLink --> Parse["Parse Link"]
    Parse --> TypeCheck{"Has Type Prefix?"}
    
    TypeCheck -->|"Yes"| TypedEntity["Create Typed Entity<br/>e.g., person:Name"]
    TypeCheck -->|"No"| ContextCheck{"Check Context"}
    
    ContextCheck --> DocExists{"Document Exists?"}
    DocExists -->|"Yes"| DocEntity["Link to Document"]
    DocExists -->|"No"| EntityExists{"Named Entity Exists?"}
    
    EntityExists -->|"Yes"| NamedEntity["Link to Entity"]
    EntityExists -->|"No"| CreatePlaceholder["Create Placeholder Document"]
    
    TypedEntity --> ResolvedEntity["Resolved Entity"]
    DocEntity --> ResolvedEntity
    NamedEntity --> ResolvedEntity
    CreatePlaceholder --> ResolvedEntity
```

## Data Model Relationships

```mermaid
erDiagram
    Document ||--o{ Section : contains
    Document ||--o{ TodoItem : contains
    Document ||--o{ CodeBlock : contains
    Document ||--o{ Table : contains
    Document }o--o{ Tag : "tagged with"
    Document }o--o{ Document : "links to"
    Document }o--o{ Person : references
    Document }o--o{ Organization : references
    Document }o--o{ Location : references
    Document }o--o{ Project : references
    Document }o--|| PlaceholderDocument : "may link to"
    
    Person ||--o{ Alias : "known as"
    Organization ||--o{ Alias : "known as"
    Location ||--o{ Alias : "known as"
    
    Document {
        string id PK "Deterministic from path"
        string path
        string title
        datetime created
        datetime modified
        string type "note|person|project|etc"
    }
    
    Person {
        string id PK "Deterministic from name"
        string canonical_name
        string[] roles
        string[] emails
    }
    
    TodoItem {
        string id PK "Parent doc + content hash"
        string description
        boolean completed
        datetime due_date
        string[] assignees
    }
```

## Entity Type Detection Pipeline

```mermaid
flowchart TD
    subgraph "Detection Sources"
        FM["Frontmatter<br/>type: person"]
        Tags["Tags<br/>#person/name"]
        Context["Context<br/>Attendees: [[Name]]"]
        WikiPrefix["Wiki Prefix<br/>[[person:Name]]"]
    end
    
    subgraph "Processing"
        Analyze["Analyze Source"]
        Priority["Apply Priority<br/>1. Wiki Prefix<br/>2. Frontmatter<br/>3. Tags<br/>4. Context"]
        Determine["Determine Type"]
    end
    
    FM --> Analyze
    Tags --> Analyze
    Context --> Analyze
    WikiPrefix --> Analyze
    
    Analyze --> Priority
    Priority --> Determine
    Determine --> EntityType["Entity Type"]
```

## Properties vs Entities Decision Tree

```mermaid
flowchart TD
    DataPoint["Data Point in Document"]
    
    DataPoint --> IsIndependent{"Independent<br/>Concept?"}
    
    IsIndependent -->|"Yes"| HasIdentity{"Has Own<br/>Identity?"}
    IsIndependent -->|"No"| Property["Document Property"]
    
    HasIdentity -->|"Yes"| MultiRef{"Referenced<br/>Multiple Places?"}
    HasIdentity -->|"No"| Property
    
    MultiRef -->|"Yes"| Entity["Create Entity"]
    MultiRef -->|"No"| Embedded{"Complex<br/>Structure?"}
    
    Embedded -->|"Yes"| SubEntity["Document-Scoped Entity"]
    Embedded -->|"No"| Property
    
    Property --> Examples1["Examples:<br/>• created date<br/>• word count<br/>• author (single)"]
    Entity --> Examples2["Examples:<br/>• Person<br/>• Organization<br/>• Project"]
    SubEntity --> Examples3["Examples:<br/>• Todo Item<br/>• Section<br/>• Code Block"]
```

## Implementation Architecture

```mermaid
graph TB
    subgraph "ID Generation Layer"
        IDGen["ID Generator"]
        Normalizer["Text Normalizer"]
        TypeDetector["Type Detector"]
        AliasResolver["Alias Resolver"]
    end
    
    subgraph "Entity Management"
        EntityRegistry["Entity Registry<br/>(In-Memory Cache)"]
        EntityStore["Entity Store<br/>(Persistent)"]
        PlaceholderMgr["Placeholder Manager"]
    end
    
    subgraph "Integration Points"
        MarkdownParser["Markdown Parser"]
        WikiLinkParser["WikiLink Parser"]
        RDFConverter["RDF Converter"]
    end
    
    MarkdownParser --> TypeDetector
    WikiLinkParser --> TypeDetector
    TypeDetector --> Normalizer
    Normalizer --> IDGen
    IDGen --> AliasResolver
    AliasResolver --> EntityRegistry
    EntityRegistry --> EntityStore
    EntityRegistry --> PlaceholderMgr
    EntityStore --> RDFConverter
```

## Key Design Decisions

1. **Deterministic IDs**: All entity IDs are generated deterministically from their content
2. **Document-First**: Documents are the primary entities, everything else relates to them
3. **Wiki Compatibility**: Full support for wiki-style linking conventions
4. **Type Safety**: Clear entity type hierarchy with distinct ID patterns
5. **Placeholder Support**: Unresolved links create placeholder documents for future resolution
6. **Alias Management**: Entities can have multiple names that resolve to the same ID
7. **Scoped Entities**: Sub-document entities include parent document ID for uniqueness