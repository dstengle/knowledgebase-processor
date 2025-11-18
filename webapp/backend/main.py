"""
FastAPI backend for Knowledge Base Processor Test Webapp
"""
import os
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import the processor
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from knowledgebase_processor.processor import Processor
from knowledgebase_processor.utils import DocumentRegistry, EntityIdGenerator
from knowledgebase_processor.config.vocabulary import KB
from rdflib import Graph, Namespace, RDF, RDFS
from rdflib.namespace import FOAF, DCTERMS

app = FastAPI(title="Knowledge Base Processor Test Webapp")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent.parent / "frontend" / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Global state
current_graph: Optional[Graph] = None
processing_history: List[Dict[str, Any]] = []


class ProcessRequest(BaseModel):
    content: str
    document_id: Optional[str] = None


class QueryRequest(BaseModel):
    entity_type: Optional[str] = None
    property_name: Optional[str] = None
    property_value: Optional[str] = None
    limit: int = 100


@app.get("/")
async def read_root():
    """Serve the frontend HTML"""
    frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
    return FileResponse(str(frontend_path))


@app.post("/api/process")
async def process_content(request: ProcessRequest):
    """Process markdown content and generate RDF graph"""
    global current_graph, processing_history

    try:
        # Initialize processor
        processor = Processor(
            document_registry=DocumentRegistry(),
            id_generator=EntityIdGenerator()
        )

        # Generate document ID if not provided
        doc_id = request.document_id or f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Process content to graph
        graph = processor.process_content_to_graph(
            content=request.content,
            document_id=doc_id
        )

        # Store the graph globally
        current_graph = graph

        # Count entities by type
        entity_counts = {}
        for s, p, o in graph.triples((None, RDF.type, None)):
            entity_type = str(o).split('/')[-1]
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1

        # Add to history
        processing_history.append({
            "timestamp": datetime.now().isoformat(),
            "document_id": doc_id,
            "triple_count": len(graph),
            "entity_counts": entity_counts
        })

        return {
            "success": True,
            "document_id": doc_id,
            "triple_count": len(graph),
            "entity_counts": entity_counts,
            "message": f"Processed successfully. Generated {len(graph)} triples."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process/file")
async def process_file(file: UploadFile = File(...)):
    """Process uploaded markdown file"""
    try:
        content = (await file.read()).decode('utf-8')
        doc_id = Path(file.filename).stem

        return await process_content(ProcessRequest(
            content=content,
            document_id=doc_id
        ))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/entities")
async def query_entities(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (e.g., KbTodoItem, KbPerson)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results")
):
    """Query entities from the current graph"""
    global current_graph

    if current_graph is None:
        raise HTTPException(status_code=400, detail="No graph available. Process content first.")

    try:
        entities = []

        # Build SPARQL query
        if entity_type:
            # Query for specific entity type
            full_type = f"{KB}{entity_type}" if not entity_type.startswith("http") else entity_type
            triples = current_graph.triples((None, RDF.type, None))
            filtered_triples = [(s, p, o) for s, p, o in triples if str(o) == full_type]
        else:
            # Query all entities
            filtered_triples = list(current_graph.triples((None, RDF.type, None)))

        # Extract entity details
        for subject, _, entity_type_uri in filtered_triples[:limit]:
            entity = {
                "uri": str(subject),
                "type": str(entity_type_uri).split('/')[-1],
                "properties": {}
            }

            # Get all properties for this entity
            for p, o in current_graph.predicate_objects(subject):
                prop_name = str(p).split('/')[-1].split('#')[-1]
                if prop_name not in ['type']:  # Skip rdf:type
                    entity["properties"][prop_name] = str(o)

            entities.append(entity)

        return {
            "success": True,
            "count": len(entities),
            "total_in_graph": len(list(current_graph.triples((None, RDF.type, None)))),
            "entities": entities
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/entities/types")
async def get_entity_types():
    """Get all entity types in the current graph"""
    global current_graph

    if current_graph is None:
        raise HTTPException(status_code=400, detail="No graph available. Process content first.")

    try:
        entity_types = set()
        for s, p, o in current_graph.triples((None, RDF.type, None)):
            entity_types.add(str(o).split('/')[-1])

        return {
            "success": True,
            "types": sorted(list(entity_types))
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/entities/search")
async def search_entities(
    property_name: str = Query(..., description="Property name to search (e.g., label, text)"),
    property_value: str = Query(..., description="Property value to match (partial match)"),
    limit: int = Query(100, ge=1, le=1000)
):
    """Search entities by property value"""
    global current_graph

    if current_graph is None:
        raise HTTPException(status_code=400, detail="No graph available. Process content first.")

    try:
        matching_entities = []

        # Search through all triples
        for subject in set(current_graph.subjects()):
            entity_properties = {}
            entity_type = None

            # Get entity type and properties
            for p, o in current_graph.predicate_objects(subject):
                prop_name = str(p).split('/')[-1].split('#')[-1]
                if str(p) == str(RDF.type):
                    entity_type = str(o).split('/')[-1]
                else:
                    entity_properties[prop_name] = str(o)

            # Check if property matches
            if property_name in entity_properties:
                if property_value.lower() in entity_properties[property_name].lower():
                    matching_entities.append({
                        "uri": str(subject),
                        "type": entity_type,
                        "properties": entity_properties
                    })

            if len(matching_entities) >= limit:
                break

        return {
            "success": True,
            "count": len(matching_entities),
            "entities": matching_entities
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/export")
async def export_graph(format: str = Query("turtle", regex="^(turtle|json-ld|xml)$")):
    """Export the current graph in various formats"""
    global current_graph

    if current_graph is None:
        raise HTTPException(status_code=400, detail="No graph available. Process content first.")

    try:
        # Serialize graph
        serialized = current_graph.serialize(format=format)

        # Set appropriate content type
        content_types = {
            "turtle": "text/turtle",
            "json-ld": "application/ld+json",
            "xml": "application/rdf+xml"
        }

        return JSONResponse(
            content={"success": True, "data": serialized},
            media_type=content_types.get(format, "text/plain")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """Get statistics about the current graph and processing history"""
    global current_graph, processing_history

    stats = {
        "current_graph": None,
        "processing_history": processing_history
    }

    if current_graph:
        entity_types = {}
        for s, p, o in current_graph.triples((None, RDF.type, None)):
            entity_type = str(o).split('/')[-1]
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

        stats["current_graph"] = {
            "triple_count": len(current_graph),
            "entity_types": entity_types,
            "unique_subjects": len(set(current_graph.subjects())),
            "unique_predicates": len(set(current_graph.predicates())),
            "unique_objects": len(set(current_graph.objects()))
        }

    return stats


@app.delete("/api/graph")
async def clear_graph():
    """Clear the current graph"""
    global current_graph
    current_graph = None
    return {"success": True, "message": "Graph cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
