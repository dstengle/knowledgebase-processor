# Knowledge Base Processor - Test Webapp

A simple web application for testing the Knowledge Base Processor. Process markdown content and query the generated RDF graph through an intuitive web interface.

## Features

- **Process Markdown**: Upload files or paste markdown content directly
- **Generate RDF Graph**: Automatically converts markdown to knowledge graph
- **Query Interface**: Search and filter entities by type and properties
- **Entity Types Supported**:
  - Documents (KbDocument)
  - Todo Items (KbTodoItem)
  - Headings (KbHeading)
  - Sections (KbSection)
  - Lists & List Items (KbList, KbListItem)
  - Tables (KbTable)
  - Code Blocks (KbCodeBlock)
  - Blockquotes (KbBlockquote)
  - Wiki Links (KbWikiLink)
  - Named Entities (KbPerson, KbOrganization, KbLocation, KbDateEntity)
- **Export Graph**: Download RDF graph in Turtle format
- **Live Statistics**: View graph metrics in real-time

## Installation

### 1. Install Dependencies

From the `webapp` directory:

```bash
cd webapp
pip install -r requirements.txt
```

### 2. Install the Knowledge Base Processor

If not already installed, install the main package:

```bash
cd ..
pip install -e .
```

## Running the Webapp

### Start the Server

From the `webapp` directory:

```bash
python backend/main.py
```

Or using uvicorn directly:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Access the Interface

Open your browser and navigate to:

```
http://localhost:8000
```

## Usage

### 1. Process Content

**Option A: Upload File**
- Click "Choose File" under "Upload Markdown File"
- Select a `.md` or `.txt` file
- File is automatically processed on selection

**Option B: Paste Content**
- Paste or type markdown content in the text area
- Optionally specify a Document ID
- Click "Process Content"

**Option C: Use Example**
- Click "Load Example Markdown" to see sample content
- Click "Process Content" to generate the graph

### 2. Query Entities

**Filter by Entity Type**
- Select an entity type from the dropdown (populated after processing)
- Click "Query Entities"

**Search by Property**
- Enter a property name (e.g., `label`, `text`, `description`)
- Enter a search value (partial matches supported)
- Click "Search by Property"

**Adjust Results**
- Change the "Result Limit" value (default: 50, max: 1000)

### 3. View Results

Results are displayed as cards showing:
- Entity type (color-coded badge)
- Entity URI
- All properties and their values

### 4. Export & Manage

- **Export Graph**: Downloads the current RDF graph as a `.ttl` file
- **Clear Graph**: Removes the current graph from memory

## API Endpoints

The webapp exposes a REST API:

### Process Content

```bash
POST /api/process
Content-Type: application/json

{
  "content": "# My Document\n\n- [ ] Todo item",
  "document_id": "optional-doc-id"
}
```

### Upload File

```bash
POST /api/process/file
Content-Type: multipart/form-data

file: <markdown file>
```

### Query Entities

```bash
GET /api/entities?entity_type=KbTodoItem&limit=100
```

### Search by Property

```bash
GET /api/entities/search?property_name=label&property_value=todo&limit=100
```

### Get Entity Types

```bash
GET /api/entities/types
```

### Export Graph

```bash
GET /api/graph/export?format=turtle
```

Supported formats: `turtle`, `json-ld`, `xml`

### Get Statistics

```bash
GET /api/stats
```

### Clear Graph

```bash
DELETE /api/graph
```

## Example Markdown

The webapp includes example markdown content demonstrating:

- Headings and sections
- Todo items with assignees and priorities
- Wiki links
- Tables
- Code blocks
- Blockquotes
- Lists (ordered and unordered)
- Dates and named entities

Click "Load Example Markdown" to see it in action.

## Architecture

### Backend (FastAPI)
- **main.py**: FastAPI application with REST API endpoints
- Uses the Knowledge Base Processor's `Processor` class directly
- Stores graph in memory for querying
- Returns JSON responses with entity data

### Frontend (HTML/JS)
- **index.html**: Bootstrap-based responsive UI
- **app.js**: Vanilla JavaScript for API interactions
- No build process required - works in any modern browser

## Development

### Run in Development Mode

```bash
uvicorn backend.main:app --reload
```

The `--reload` flag enables auto-reload on code changes.

### CORS Configuration

CORS is enabled for all origins by default for development. For production, update the CORS middleware in `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Troubleshooting

### Port Already in Use

If port 8000 is occupied, specify a different port:

```bash
uvicorn backend.main:app --port 8080
```

### Import Errors

Ensure the knowledge base processor is installed:

```bash
pip install -e ..
```

### Empty Entity Type Dropdown

Process some content first. Entity types are populated after processing.

### Graph Not Persisting

The graph is stored in memory and will be cleared when the server restarts. For persistence, consider:
- Adding a SPARQL endpoint backend
- Saving graphs to disk
- Using a triple store database

## Future Enhancements

Potential improvements:
- [ ] SPARQL query editor
- [ ] Graph visualization (D3.js, Cytoscape.js)
- [ ] Persistent storage with triple store
- [ ] Batch file processing
- [ ] Real-time processing with WebSockets
- [ ] Advanced filtering and sorting
- [ ] Export in multiple RDF formats
- [ ] Import existing RDF graphs

## License

Same as the main Knowledge Base Processor project.

## Support

For issues or questions, refer to the main project repository.
