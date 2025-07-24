# 🐳 Docker Usage Guide

This guide shows you how to run the Knowledge Base Processor in different Docker scenarios.

## 🚀 Quick Start

### Option 1: Docker Run Script (Recommended)

Use the provided wrapper script for easy Docker usage:

```bash
# Make script executable (first time only)
chmod +x scripts/docker-run.sh

# Show help
./scripts/docker-run.sh --help

# Initialize in current directory
./scripts/docker-run.sh init

# Process documents in specific directory
./scripts/docker-run.sh -w ~/Documents scan

# Use custom config file
./scripts/docker-run.sh -c ./my-config.json publish --watch

# Search your knowledge base
./scripts/docker-run.sh search "todo items"
```

### Option 2: Docker Compose

For persistent services and easier management:

```bash
# Build and run interactively
docker-compose -f docker-compose.app.yml up kbp

# Run in watch mode (continuous processing)
docker-compose -f docker-compose.app.yml --profile watch up kbp-watch

# Run with SPARQL server
docker-compose -f docker-compose.app.yml up fuseki kbp
```

### Option 3: Direct Docker Commands

For full control over the container:

```bash
# Build the image
docker build -t knowledgebase-processor:latest .

# Run with volume mounts
docker run --rm -it \
  -v "$(pwd):/workspace" \
  -e KBP_WORK_DIR=/workspace \
  -e KBP_HOME=/workspace/.kbp \
  -w /workspace \
  knowledgebase-processor:latest kb --help
```

## 📁 Directory Structure

The Docker setup creates this structure in your mounted directory:

```
your-documents/
├── .kbp/                    # KBP configuration directory
│   ├── config.yaml          # Configuration file
│   ├── metadata/            # Document metadata and cache
│   └── cache/               # Processing cache
├── your-files.md            # Your existing documents (unchanged)
└── kbp_config.json         # Optional: custom config file
```

## 🔧 Environment Variables

Configure the tool's behavior with environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `KBP_WORK_DIR` | Working directory path | `/workspace` |
| `KBP_HOME` | KBP configuration directory | `$KBP_WORK_DIR/.kbp` |
| `KBP_KNOWLEDGE_BASE_PATH` | Documents directory | `$KBP_WORK_DIR` |
| `KBP_METADATA_STORE_PATH` | Metadata storage path | `$KBP_HOME/metadata` |
| `KBP_CONFIG_PATH` | Custom config file path | *(auto-detected)* |

## 📋 Common Use Cases

### 1. Initialize New Project

```bash
# Using wrapper script
./scripts/docker-run.sh -w ~/my-docs init

# Using docker directly
docker run --rm -it \
  -v ~/my-docs:/workspace \
  -e KBP_WORK_DIR=/workspace \
  -e KBP_HOME=/workspace/.kbp \
  -w /workspace \
  knowledgebase-processor:latest kb init
```

### 2. Process Existing Documents

```bash
# Scan and process all documents
./scripts/docker-run.sh -w ~/my-docs scan

# With custom patterns
./scripts/docker-run.sh -w ~/my-docs scan --pattern "**/*.md" --pattern "**/*.txt"
```

### 3. Continuous Monitoring

```bash
# Watch for changes and auto-process
./scripts/docker-run.sh -w ~/my-docs publish --watch

# Or using docker-compose
docker-compose -f docker-compose.app.yml --profile watch up
```

### 4. Search Knowledge Base

```bash
# Search for content
./scripts/docker-run.sh -w ~/my-docs search "project tasks"

# Advanced search with filters
./scripts/docker-run.sh -w ~/my-docs search --type todo "deadlines"
```

### 5. Custom Configuration

Create a `kbp_config.json` file:

```json
{
  "file_patterns": ["**/*.md", "**/*.txt"],
  "extract_frontmatter": true,
  "sparql_endpoint_url": "http://localhost:3030/ds/query",
  "sparql_update_endpoint_url": "http://localhost:3030/ds/update"
}
```

Then use it:

```bash
./scripts/docker-run.sh -c ./kbp_config.json -w ~/my-docs scan
```

## 🔗 Integration with SPARQL

### Using Fuseki Server

1. Start Fuseki with docker-compose:
```bash
docker-compose -f docker-compose.app.yml up fuseki
```

2. Configure KBP to use Fuseki:
```bash
./scripts/docker-run.sh init --sparql-endpoint http://fuseki:3030/ds
```

3. Publish your knowledge base:
```bash
./scripts/docker-run.sh publish --sync
```

### Using External SPARQL Endpoint

Set environment variables:

```bash
docker run --rm -it \
  -v "$(pwd):/workspace" \
  -e KBP_WORK_DIR=/workspace \
  -e SPARQL_ENDPOINT=http://your-sparql-server/query \
  -e SPARQL_UPDATE_ENDPOINT=http://your-sparql-server/update \
  knowledgebase-processor:latest kb publish --sync
```

## 🛠️ Development & Debugging

### Enable Verbose Output

```bash
# With wrapper script
VERBOSE=1 ./scripts/docker-run.sh -w ~/my-docs scan --verbose

# Direct docker command
docker run --rm -it \
  -v "$(pwd):/workspace" \
  -e KBP_WORK_DIR=/workspace \
  -w /workspace \
  knowledgebase-processor:latest kb scan --verbose
```

### Access Container Shell

```bash
docker run --rm -it \
  -v "$(pwd):/workspace" \
  -e KBP_WORK_DIR=/workspace \
  -w /workspace \
  knowledgebase-processor:latest /bin/bash
```

### Build Custom Image

```bash
# Build with custom tag
docker build -t my-kbp:latest .

# Use custom image
./scripts/docker-run.sh -i my-kbp:latest scan
```

## 🔍 Troubleshooting

### Permission Issues

If you encounter permission errors:

```bash
# Fix ownership (Linux/macOS)
sudo chown -R $(id -u):$(id -g) ./.kbp

# Or run container with your user ID
docker run --rm -it \
  --user $(id -u):$(id -g) \
  -v "$(pwd):/workspace" \
  knowledgebase-processor:latest kb scan
```

### Config Not Found

Ensure you're mounting the right directory:

```bash
# Check what's mounted
./scripts/docker-run.sh ls -la

# Verify config path
./scripts/docker-run.sh config show
```

### Volume Mount Issues

On Windows, use full paths:

```powershell
# PowerShell
./scripts/docker-run.sh -w "C:\Users\YourName\Documents" init

# Or use WSL paths
./scripts/docker-run.sh -w "/mnt/c/Users/YourName/Documents" init
```

## 📊 Performance Tips

1. **Use volume mounts** instead of copying files
2. **Persist the .kbp directory** to avoid reprocessing
3. **Use watch mode** for continuous updates
4. **Configure exclusion patterns** for large directories

Example optimized setup:

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  kbp:
    volumes:
      - ./docs:/workspace/docs
      - ./.kbp:/workspace/.kbp
      - /node_modules  # Exclude from processing
    environment:
      - KBP_EXCLUDE_PATTERNS=["**/node_modules/**", "**/.git/**"]
```