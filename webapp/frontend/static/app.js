// Knowledge Base Processor - Frontend Application

const API_BASE = '';

// Example markdown content
const EXAMPLE_MARKDOWN = `# Project Planning Document

## Overview
This is a sample document to demonstrate the Knowledge Base Processor.

## Tasks
- [ ] Design the database schema @john
- [x] Set up development environment @jane !high
- [ ] Implement user authentication !critical
- [ ] Write unit tests @team
- [x] Create API documentation

## Team Members
Contact [[John Smith]] or [[Jane Doe]] for more information.

## Features
1. User authentication with JWT
2. RESTful API endpoints
3. Real-time data synchronization
4. Advanced search capabilities

## Technical Specs

| Component | Technology | Status |
|-----------|-----------|--------|
| Backend | Python/FastAPI | In Progress |
| Frontend | React | Planned |
| Database | PostgreSQL | Completed |

## Code Example

\`\`\`python
def process_document(content: str):
    """Process markdown content"""
    processor = Processor()
    return processor.process(content)
\`\`\`

## Important Dates
- Project kickoff: 2024-01-15
- Alpha release: 2024-03-01
- Beta testing: 2024-04-15

> Note: This is a high-priority project. All deadlines are firm.

## Related Documents
- [[Architecture Design]]
- [[API Specification]]
- [[Testing Strategy]]
`;

// DOM Elements
let processBtn, queryBtn, searchBtn, exportBtn, clearBtn, loadExampleBtn;
let markdownInput, fileInput, docIdInput, entityTypeFilter, propertyName, propertyValue, resultLimit;
let resultsContainer, processResult, processingSpinner;
let tripleCount, entityCount, typeCount, docCount, resultCount;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    attachEventListeners();
    loadEntityTypes();
    updateStats();
});

function initializeElements() {
    // Buttons
    processBtn = document.getElementById('processBtn');
    queryBtn = document.getElementById('queryBtn');
    searchBtn = document.getElementById('searchBtn');
    exportBtn = document.getElementById('exportBtn');
    clearBtn = document.getElementById('clearBtn');
    loadExampleBtn = document.getElementById('loadExample');

    // Inputs
    markdownInput = document.getElementById('markdownInput');
    fileInput = document.getElementById('fileInput');
    docIdInput = document.getElementById('docId');
    entityTypeFilter = document.getElementById('entityTypeFilter');
    propertyName = document.getElementById('propertyName');
    propertyValue = document.getElementById('propertyValue');
    resultLimit = document.getElementById('resultLimit');

    // Display elements
    resultsContainer = document.getElementById('resultsContainer');
    processResult = document.getElementById('processResult');
    processingSpinner = document.getElementById('processingSpinner');

    // Stats
    tripleCount = document.getElementById('tripleCount');
    entityCount = document.getElementById('entityCount');
    typeCount = document.getElementById('typeCount');
    docCount = document.getElementById('docCount');
    resultCount = document.getElementById('resultCount');
}

function attachEventListeners() {
    processBtn.addEventListener('click', processContent);
    queryBtn.addEventListener('click', queryEntities);
    searchBtn.addEventListener('click', searchEntities);
    exportBtn.addEventListener('click', exportGraph);
    clearBtn.addEventListener('click', clearGraph);
    loadExampleBtn.addEventListener('click', loadExample);
    fileInput.addEventListener('change', handleFileUpload);
}

async function processContent() {
    const content = markdownInput.value.trim();

    if (!content) {
        showAlert('Please enter some markdown content.', 'warning');
        return;
    }

    try {
        // Show spinner
        processingSpinner.style.display = 'block';
        processBtn.disabled = true;

        const response = await fetch(`${API_BASE}/api/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                content: content,
                document_id: docIdInput.value || null
            })
        });

        const data = await response.json();

        if (data.success) {
            showAlert(data.message, 'success');
            displayProcessingResult(data);
            await loadEntityTypes();
            await updateStats();
        } else {
            showAlert('Processing failed: ' + (data.detail || 'Unknown error'), 'danger');
        }
    } catch (error) {
        showAlert('Error: ' + error.message, 'danger');
    } finally {
        processingSpinner.style.display = 'none';
        processBtn.disabled = false;
    }
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    try {
        processingSpinner.style.display = 'block';
        processBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/api/process/file`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showAlert(`File processed: ${data.message}`, 'success');
            displayProcessingResult(data);
            await loadEntityTypes();
            await updateStats();
        } else {
            showAlert('File processing failed: ' + (data.detail || 'Unknown error'), 'danger');
        }
    } catch (error) {
        showAlert('Error: ' + error.message, 'danger');
    } finally {
        processingSpinner.style.display = 'none';
        processBtn.disabled = false;
        fileInput.value = '';
    }
}

async function queryEntities() {
    const entityType = entityTypeFilter.value;
    const limit = parseInt(resultLimit.value) || 100;

    try {
        queryBtn.disabled = true;
        const params = new URLSearchParams();
        if (entityType) params.append('entity_type', entityType);
        params.append('limit', limit);

        const response = await fetch(`${API_BASE}/api/entities?${params}`);
        const data = await response.json();

        if (data.success) {
            displayEntities(data.entities, data.count, data.total_in_graph);
        } else {
            showAlert('Query failed: ' + (data.detail || 'Unknown error'), 'danger');
        }
    } catch (error) {
        showAlert('Error: ' + error.message, 'danger');
    } finally {
        queryBtn.disabled = false;
    }
}

async function searchEntities() {
    const propName = propertyName.value.trim();
    const propValue = propertyValue.value.trim();
    const limit = parseInt(resultLimit.value) || 100;

    if (!propName || !propValue) {
        showAlert('Please enter both property name and value to search.', 'warning');
        return;
    }

    try {
        searchBtn.disabled = true;
        const params = new URLSearchParams({
            property_name: propName,
            property_value: propValue,
            limit: limit
        });

        const response = await fetch(`${API_BASE}/api/entities/search?${params}`);
        const data = await response.json();

        if (data.success) {
            displayEntities(data.entities, data.count);
        } else {
            showAlert('Search failed: ' + (data.detail || 'Unknown error'), 'danger');
        }
    } catch (error) {
        showAlert('Error: ' + error.message, 'danger');
    } finally {
        searchBtn.disabled = false;
    }
}

async function loadEntityTypes() {
    try {
        const response = await fetch(`${API_BASE}/api/entities/types`);
        const data = await response.json();

        if (data.success) {
            // Update dropdown
            entityTypeFilter.innerHTML = '<option value="">All Types</option>';
            data.types.forEach(type => {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type;
                entityTypeFilter.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load entity types:', error);
    }
}

async function updateStats() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        const data = await response.json();

        if (data.current_graph) {
            tripleCount.textContent = data.current_graph.triple_count;
            entityCount.textContent = data.current_graph.unique_subjects;
            typeCount.textContent = Object.keys(data.current_graph.entity_types).length;
        }

        if (data.processing_history) {
            docCount.textContent = data.processing_history.length;
        }
    } catch (error) {
        console.error('Failed to update stats:', error);
    }
}

async function exportGraph() {
    try {
        exportBtn.disabled = true;
        const response = await fetch(`${API_BASE}/api/graph/export?format=turtle`);
        const data = await response.json();

        if (data.success) {
            // Download the RDF data
            const blob = new Blob([data.data], { type: 'text/turtle' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `kb_graph_${new Date().toISOString()}.ttl`;
            a.click();
            window.URL.revokeObjectURL(url);
            showAlert('Graph exported successfully!', 'success');
        } else {
            showAlert('Export failed: ' + (data.detail || 'Unknown error'), 'danger');
        }
    } catch (error) {
        showAlert('Error: ' + error.message, 'danger');
    } finally {
        exportBtn.disabled = false;
    }
}

async function clearGraph() {
    if (!confirm('Are you sure you want to clear the current graph?')) {
        return;
    }

    try {
        clearBtn.disabled = true;
        const response = await fetch(`${API_BASE}/api/graph`, {
            method: 'DELETE'
        });
        const data = await response.json();

        if (data.success) {
            showAlert('Graph cleared successfully!', 'success');
            resultsContainer.innerHTML = '<p class="text-muted text-center">Graph cleared. Process content to create a new graph.</p>';
            resultCount.textContent = '0';
            await updateStats();
            await loadEntityTypes();
        }
    } catch (error) {
        showAlert('Error: ' + error.message, 'danger');
    } finally {
        clearBtn.disabled = false;
    }
}

function loadExample() {
    markdownInput.value = EXAMPLE_MARKDOWN;
    showAlert('Example markdown loaded! Click "Process Content" to generate the graph.', 'info');
}

function displayProcessingResult(data) {
    let html = `
        <div class="alert alert-success">
            <h6><i class="bi bi-check-circle"></i> Processing Complete</h6>
            <ul class="mb-0">
                <li>Document ID: <code>${data.document_id}</code></li>
                <li>Total Triples: <strong>${data.triple_count}</strong></li>
                <li>Entity Types: <strong>${Object.keys(data.entity_counts).length}</strong></li>
            </ul>
        </div>
    `;

    if (data.entity_counts && Object.keys(data.entity_counts).length > 0) {
        html += '<div class="mt-2"><h6>Entity Breakdown:</h6>';
        for (const [type, count] of Object.entries(data.entity_counts)) {
            html += `<span class="property-badge"><strong>${type}:</strong> ${count}</span> `;
        }
        html += '</div>';
    }

    processResult.innerHTML = html;
}

function displayEntities(entities, count, total = null) {
    if (!entities || entities.length === 0) {
        resultsContainer.innerHTML = '<p class="text-muted text-center">No entities found.</p>';
        resultCount.textContent = '0';
        return;
    }

    let html = '';

    if (total !== null) {
        html += `<div class="alert alert-info">Showing ${count} of ${total} entities</div>`;
    } else {
        html += `<div class="alert alert-info">Found ${count} matching entities</div>`;
    }

    entities.forEach(entity => {
        html += `
            <div class="card entity-card mb-2">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <span class="entity-type">${entity.type}</span>
                        <small class="entity-uri">${entity.uri}</small>
                    </div>
                    <div class="properties">
        `;

        // Display properties
        for (const [key, value] of Object.entries(entity.properties)) {
            const displayValue = value.length > 100 ? value.substring(0, 100) + '...' : value;
            html += `
                <div class="property-badge">
                    <strong>${key}:</strong> ${escapeHtml(displayValue)}
                </div>
            `;
        }

        html += `
                    </div>
                </div>
            </div>
        `;
    });

    resultsContainer.innerHTML = html;
    resultCount.textContent = count;
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    processResult.innerHTML = '';
    processResult.appendChild(alertDiv);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 300);
    }, 5000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
