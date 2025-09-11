# Knowledge Base Processor v2 Architecture

## 🏗️ Service-Oriented Architecture

The CLI introduces a **service-oriented architecture** that separates the user interface from business logic, making the system more testable, maintainable, and extensible.

## 📐 Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│   CLI Layer     │    │  Service Layer   │    │  Data Layer     │
│                 │    │                  │    │                 │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ • CLI Commands  │───▶│ • Orchestrator   │───▶│ • KnowledgeBase │
│ • Interactive   │    │   Service        │    │   API           │
│   Mode          │    │ • Business Logic │    │ • Processing    │
│ • Rich UI       │    │ • Configuration  │    │   Service       │
│ • Error         │    │ • State Mgmt     │    │ • SQLite DB     │
│   Handling      │    │                  │    │ • File System  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🎯 Design Principles

### 1. **Separation of Concerns**
- **CLI Layer**: User interface, input validation, output formatting
- **Service Layer**: Business logic, workflow orchestration, state management
- **Data Layer**: Data persistence, document processing, SPARQL operations

### 2. **Testability First**
- **Unit Tests**: Individual service methods
- **Integration Tests**: Service layer with real file operations
- **E2E Tests**: Full CLI workflows with mocked file system

### 3. **Single Responsibility**
- Each service class has one clear purpose
- CLI commands are thin wrappers around service calls
- Clear interfaces between layers

## 🔧 Core Components

### 📋 OrchestratorService
**Location**: `src/knowledgebase_processor/services/orchestrator.py`

**Purpose**: Main business logic orchestrator that coordinates all KB operations.

**Key Responsibilities**:
- Project initialization and configuration management
- Document processing coordination
- Search functionality
- Statistics gathering
- SPARQL synchronization
- Configuration persistence

**Key Methods**:
```python
class OrchestratorService:
    def initialize_project(...) -> ProjectConfig
    def process_documents(...) -> ProcessingResult
    def search(...) -> List[SearchResult]
    def get_project_stats() -> ProjectStats
    def sync_to_sparql(...) -> Dict[str, Any]
    def get_config_value(key) -> Any
    def set_config_value(key, value) -> bool
```

### 🖥️ CLI Commands
**Location**: `src/knowledgebase_processor/cli/commands/`

**Purpose**: Thin wrappers that provide beautiful UI around service operations.

**Architecture Pattern**:
```python
@click.command()
def command_name(ctx, ...):
    # 1. Initialize orchestrator
    orchestrator = OrchestratorService(working_dir)
    
    # 2. Validate input and show UI
    console.print("🚀 [heading]Operation Starting[/heading]")
    
    # 3. Call service layer
    try:
        result = orchestrator.service_method(...)
        
        # 4. Display results with rich formatting
        print_success("Operation completed!")
        show_formatted_results(result)
        
    except Exception as e:
        print_error(f"Operation failed: {e}")
```

### 📊 Data Models
**Location**: `src/knowledgebase_processor/services/orchestrator.py`

**Purpose**: Structured data transfer between layers.

**Key Models**:
```python
@dataclass
class ProcessingResult:
    files_processed: int
    files_failed: int
    entities_extracted: int
    todos_found: int
    processing_time: float
    error_messages: List[str]

@dataclass
class SearchResult:
    type: str
    title: str
    path: str
    snippet: str
    score: float
    metadata: Dict[str, Any]

@dataclass
class ProjectStats:
    total_documents: int
    processed_documents: int
    total_entities: int
    todos_total: int
    todos_completed: int
    # ... more stats
```

## 🧪 Testing Strategy

### 1. **Integration Tests** (Primary)
**Location**: `tests/services/test_orchestrator_integration.py`

**Scope**: 
- Test orchestrator service with real file operations
- Use temporary directories with sample documents
- Verify data persistence and configuration management
- Test error handling and edge cases

**Coverage**:
- ✅ Project initialization and configuration
- ✅ Document counting and processing
- ✅ Search functionality
- ✅ Statistics gathering
- ✅ Configuration management
- ✅ Error handling for uninitialized projects

### 2. **End-to-End Tests** (Minimal)
**Location**: `tests/cli/test_cli_e2e.py`

**Scope**:
- Test CLI interface with Click test runner
- Verify command-line argument parsing
- Test complete user workflows
- Ensure graceful error handling

**Coverage**:
- ✅ CLI help and version commands
- ✅ Init command with real configuration
- ✅ Full workflow: init → scan → search → status
- ✅ Error handling for invalid commands

### 3. **Test Philosophy**

**Testing Pyramid**:
```
     ┌─────────┐
     │  E2E    │  ← Minimal (CLI interface only)
     │  Tests  │
   ┌─┴─────────┴─┐
   │ Integration │  ← Primary (Service layer with real files)
   │    Tests    │
 ┌─┴─────────────┴─┐
 │   Unit Tests    │  ← Future (Individual methods)
 │                 │
 └─────────────────┘
```

## 🔄 Data Flow

### Typical Operation Flow:

1. **User Input** → CLI Command Parser (Click)
2. **CLI Command** → OrchestratorService method call
3. **OrchestratorService** → KnowledgeBaseAPI (existing)
4. **KnowledgeBaseAPI** → ProcessingService → Database
5. **Results** ← OrchestratorService ← CLI ← Rich UI Display

### Configuration Flow:

1. **CLI init** → OrchestratorService.initialize_project()
2. **Service** → Creates `.kbp/config.yaml`
3. **Subsequent calls** → Load config → Cache → Use in operations

## 🎨 UI Architecture

### Rich Terminal UI Components:
- **Progress Bars**: Real-time operation feedback
- **Tables**: Structured data display (search results, stats)
- **Panels**: Important information highlighting
- **Colors & Emojis**: Visual hierarchy and status indication
- **Interactive Prompts**: User-friendly input collection

### Error Handling Strategy:
```python
try:
    result = orchestrator.operation()
    print_success("Operation completed!")
    display_results(result)
except ValueError as e:
    print_error(f"Configuration error: {e}")
    suggest_solution()
except Exception as e:
    print_error(f"Unexpected error: {e}")
    if ctx.verbose:
        console.print_exception()
```

## 🚀 Benefits of This Architecture

### 1. **Testability**
- Service layer can be tested independently of CLI
- Real file operations in integration tests
- Mock-free testing with temporary directories

### 2. **Maintainability**
- Clear separation between UI and business logic
- Easy to add new commands or modify existing ones
- Centralized error handling and logging

### 3. **Extensibility**
- Easy to add new UI frontends (web UI, API server)
- Service layer can be reused across different interfaces
- Plugin architecture possible through service extension

### 4. **User Experience**
- Rich visual feedback without complexity in business logic
- Consistent error handling across all commands
- Progressive disclosure through layered architecture

## 🔮 Future Enhancements

### 1. **Service Layer Extensions**
- **CacheService**: Intelligent caching of processed documents
- **WatchService**: File system monitoring for live updates
- **PluginService**: Extension system for custom processors

### 2. **Additional UI Layers**
- **Web Interface**: Browser-based dashboard
- **API Server**: REST API for external integrations
- **Desktop App**: Electron-based GUI

### 3. **Enhanced Testing**
- **Property-based testing**: Random input validation
- **Performance benchmarks**: Service layer performance tracking
- **Mutation testing**: Test quality validation

---

This architecture transforms the CLI from a monolithic interface into a **layered, testable, and extensible system** that maintains excellent user experience while providing solid engineering foundations for future growth.