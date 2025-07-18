# Knowledge Base Processor

A Python tool for extracting, analyzing, and managing metadata from Markdown-based knowledge bases. The processor parses Markdown files to extract tags, headings, links, and other structured information, supporting advanced knowledge management workflows.

## Features

- Extracts metadata, tags, and structural elements from Markdown files
- Modular architecture for analyzers, extractors, and enrichers
- Easily extensible for new metadata types or processing logic
- Command-line interface for batch processing
- Comprehensive test suite

## Developing

### Setup

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

### Running Tests

Run all tests using the provided script:
```bash
poetry run python scripts/run_tests.py
```

### Running the Processor

To process your knowledge base, use:
```bash
poetry run python scripts/run_processor.py
```
For available options and arguments, run:
```bash
poetry run python scripts/run_processor.py --help
```

### Process and Load Knowledgebase into SPARQL Endpoint

The `process-and-load` command processes all files in a knowledgebase directory, generates RDF data, and loads it into a SPARQL endpoint in a single step.

**Basic usage:**
```bash
poetry run python -m knowledgebase_processor.cli.main process-and-load /path/to/knowledgebase
```

**Options:**
- `--pattern PATTERN`
  Only process files matching the given glob pattern (e.g., `*.md`).

- `--graph GRAPH_URI`
  Specify the named graph URI to load data into.

- `--endpoint ENDPOINT_URL`
  Override the default SPARQL endpoint URL.

- `--update-endpoint UPDATE_ENDPOINT_URL`
  Specify a separate SPARQL update endpoint.

- `--cleanup`
  Remove temporary RDF files after loading.

**Example invocations:**
```bash
# Process all Markdown files and load into default endpoint
poetry run python -m knowledgebase_processor.cli.main process-and-load ./sample_data

# Process only daily notes and load into a specific named graph
poetry run python -m knowledgebase_processor.cli.main process-and-load ./sample_data --pattern "daily-note-*.md" --graph "http://example.org/graph/daily"

# Specify a custom SPARQL endpoint and cleanup temporary files
poetry run python -m knowledgebase_processor.cli.main process-and-load ./sample_data --endpoint http://localhost:3030/ds --cleanup
```

Progress and errors will be reported in the console. For more options, run:
```bash
poetry run python -m knowledgebase_processor.cli.main process-and-load --help
```

And the processor also handles wikilinks [[A wikilink]]

### Contributing

Fork the repository, create a feature branch, and submit a pull request. Please ensure all tests pass before submitting.