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

Currently working, if jank way to run processor:
```bash
poetry run kbp --knowledge-base sample_data/ process-and-loa
d  --endpoint-url http://fuseki:3030/test   --rdf-output-dir rdf-tmp/ --user $FUSEKI_USER --password $FUSEKI_PASSWORD 
```


And the processor also handles wikilinks [[A wikilink]]

### Contributing

Fork the repository, create a feature branch, and submit a pull request. Please ensure all tests pass before submitting.