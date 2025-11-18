#!/bin/bash
# Start the Knowledge Base Processor webapp

echo "Knowledge Base Processor - Test Webapp"
echo "======================================"
echo ""

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if main package is installed
if ! python -c "import knowledgebase_processor" 2>/dev/null; then
    echo "Installing knowledgebase-processor..."
    cd .. && pip install -e . && cd webapp
fi

echo ""
echo "Starting server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

# Start the server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
