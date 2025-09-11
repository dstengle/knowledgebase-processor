"""RDF processing module for generating and serializing RDF graphs."""

from pathlib import Path
from typing import List, Optional

from rdflib import Graph
from rdflib.namespace import SDO as SCHEMA, RDFS, XSD

from ..models.kb_entities import KbBaseEntity, KB
from ..rdf_converter import RdfConverter
from ..utils.logging import get_logger


logger = get_logger("knowledgebase_processor.processor.rdf")


class RdfProcessor:
    """Handles RDF graph generation and serialization."""
    
    def __init__(self, rdf_converter: Optional[RdfConverter] = None):
        """Initialize RdfProcessor.
        
        Args:
            rdf_converter: Optional RdfConverter instance, creates new if not provided
        """
        self.rdf_converter = rdf_converter or RdfConverter()
    
    def create_graph(self) -> Graph:
        """Create a new RDF graph with standard namespace bindings.
        
        Returns:
            Configured RDF graph
        """
        graph = Graph()
        graph.bind("kb", KB)
        graph.bind("schema", SCHEMA)
        graph.bind("rdfs", RDFS)
        graph.bind("xsd", XSD)
        return graph
    
    def entities_to_graph(
        self,
        entities: List[KbBaseEntity],
        base_uri_str: Optional[str] = None
    ) -> Graph:
        """Convert a list of KB entities to an RDF graph.
        
        Args:
            entities: List of KB entities to convert
            base_uri_str: Optional base URI string
            
        Returns:
            RDF graph containing all entities
        """
        graph = self.create_graph()
        
        for entity in entities:
            entity_graph = self.rdf_converter.kb_entity_to_graph(
                entity,
                base_uri_str=base_uri_str or str(KB)
            )
            graph += entity_graph
        
        return graph
    
    def serialize_graph(
        self,
        graph: Graph,
        output_path: Path,
        format: str = "turtle"
    ) -> bool:
        """Serialize an RDF graph to file.
        
        Args:
            graph: RDF graph to serialize
            output_path: Path to output file
            format: Serialization format (default: turtle)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if len(graph) == 0:
                logger.debug(f"Skipping empty graph for {output_path}")
                return False
            
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Serialize graph
            graph.serialize(destination=str(output_path), format=format)
            logger.info(f"Saved RDF graph to {output_path} ({len(graph)} triples)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to serialize graph to {output_path}: {e}", exc_info=True)
            return False
    
    def process_document_to_rdf(
        self,
        entities: List[KbBaseEntity],
        output_dir: Path,
        document_path: str,
        base_uri_str: Optional[str] = None
    ) -> bool:
        """Process entities from a document and save as RDF.
        
        Args:
            entities: List of entities to process
            output_dir: Directory to save RDF files
            document_path: Original document path (for filename)
            base_uri_str: Optional base URI string
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate RDF graph from entities
            graph = self.entities_to_graph(entities, base_uri_str)
            
            if len(graph) == 0:
                logger.debug(f"No RDF triples generated for {document_path}")
                return False
            
            # Determine output filename
            output_filename = Path(document_path).with_suffix(".ttl").name
            output_path = output_dir / output_filename
            
            # Serialize to file
            return self.serialize_graph(graph, output_path)
            
        except Exception as e:
            logger.error(f"Failed to process RDF for {document_path}: {e}", exc_info=True)
            return False