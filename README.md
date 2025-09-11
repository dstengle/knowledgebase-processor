# Knowledge Base Processor

A Python tool for extracting, analyzing, and managing metadata from Markdown-based knowledge bases. The processor parses Markdown files to extract tags, headings, links, and other structured information, supporting advanced knowledge management workflows.

## Features

- 🔍 Extracts metadata, tags, and structural elements from Markdown files
- 🏗️ Modular architecture for analyzers, extractors, and enrichers
- 🔌 Easily extensible for new metadata types or processing logic
- 🎨 Modern command-line interface with rich terminal UI
- 📊 Interactive mode for guided workflows
- 🔄 Real-time file watching and continuous processing
- 🧪 Comprehensive test suite

## Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/knowledgebase-processor.git
   cd knowledgebase-processor
   ```

2. **Install Poetry (if not already installed):**
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies:**
   ```bash
   poetry install
   ```

### Basic Usage

The Knowledge Base Processor provides a modern CLI interface with two command aliases: `kb` and `kbp`.

```bash
# Initialize a new knowledge base in the current directory
kb init

# Process documents in the current directory
kb scan

# Search for content
kb search "todo items"

# Process and sync to SPARQL endpoint in one command
kb publish --endpoint http://localhost:3030/kb

# Enter interactive mode (just run kb without arguments)
kb
```

## CLI Commands

### 🚀 `kb init` - Initialize Knowledge Base
Configure the processor for your documents:
```bash
kb init                    # Interactive setup
kb init ~/Documents        # Initialize specific directory
kb init --name "My KB"     # Set project name
```

### 📁 `kb scan` - Process Documents
Process documents and extract knowledge entities:
```bash
kb scan                           # Scan current directory
kb scan ~/Documents              # Scan specific directory
kb scan --pattern "*.md"         # Only process Markdown files
kb scan --watch                  # Watch for changes
kb scan --sync --endpoint <url>  # Process + sync to SPARQL
```

### 🔍 `kb search` - Search Knowledge Base
Search your processed knowledge base:
```bash
kb search "machine learning"     # Full-text search
kb search --type todo "project"  # Search specific entity types
kb search --tag important        # Search by tags
```

### 📤 `kb publish` - Publish to SPARQL
Process and sync to SPARQL endpoint in one command:
```bash
kb publish                       # Use default endpoint
kb publish --endpoint <url>      # Specify endpoint
kb publish --watch               # Continuous publishing mode
kb publish --graph <uri>         # Specify named graph
```

### 🔄 `kb sync` - Sync to SPARQL
Sync already processed data to SPARQL endpoint:
```bash
kb sync                          # Sync to default endpoint
kb sync --endpoint <url>         # Specify endpoint
kb sync --clear                  # Clear endpoint before sync
```

### 📊 `kb status` - Show Status
Display knowledge base statistics and status:
```bash
kb status                        # Show current status
kb status --detailed             # Show detailed statistics
```

### ⚙️ `kb config` - Manage Configuration
View and manage configuration:
```bash
kb config show                   # Display current config
kb config set endpoint <url>    # Set SPARQL endpoint
kb config reset                  # Reset to defaults
```

## Advanced Usage

### Interactive Mode
Run `kb` without any arguments to enter interactive mode with a guided interface:
```bash
kb
```

### Process with RDF Output
Generate RDF/TTL files during processing:
```bash
kb scan --rdf-output ./rdf_output
```

### Continuous Processing
Watch for file changes and automatically process:
```bash
kb scan --watch
kb publish --watch
```

### Using as a Python Module
```bash
# Run CLI as a module
python -m knowledgebase_processor.cli --help
```

## Development

### Running Tests
Run all tests using the provided script:
```bash
poetry run python scripts/run_tests.py
```

Or use pytest directly:
```bash
poetry run pytest
poetry run pytest tests/cli/  # Test CLI specifically
```

### Architecture
The processor uses a service-oriented architecture with clear separation between:
- **CLI Layer**: User interface and command handling
- **Service Layer**: Business logic and orchestration
- **Data Layer**: Document processing and persistence

See [ARCHITECTURE_V2.md](ARCHITECTURE_V2.md) for detailed architecture documentation.

## Configuration

The processor can be configured via:
1. Command-line arguments (highest priority)
2. Configuration file (`.kbp/config.yaml`)
3. Environment variables
4. Default values

Example configuration file:
```yaml
knowledge_base:
  path: /path/to/documents
  patterns:
    - "*.md"
    - "*.markdown"
sparql:
  endpoint: http://localhost:3030/kb
  graph: http://example.org/kb
processing:
  batch_size: 100
  parallel: true
```

## Wikilinks Support
The processor handles wikilinks [[A wikilink]] and extracts them as relationships between documents.

## Contributing
Fork the repository, create a feature branch, and submit a pull request. Please ensure all tests pass before submitting.

## License
[Add your license information here]