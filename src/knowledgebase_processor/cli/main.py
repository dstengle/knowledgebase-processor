"""Main CLI implementation for the Knowledge Base Processor."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional
import uuid

from rdflib import Graph
from rdflib.namespace import SCHEMA, RDFS, XSD

from ..config import load_config
from ..main import KnowledgeBaseProcessor
from ..utils.logging import setup_logging, get_logger
from ..rdf_converter import RDFConverter
from ..models.kb_entities import KbBaseEntity, KbPerson, KbOrganization, KbLocation, KbDateEntity, KB
from ..models.entities import ExtractedEntity
# from ..processor.processor import ProcessedDocument # For type hinting if needed


logger_cli = get_logger("knowledgebase_processor.cli") # Module level logger


def _generate_kb_id(entity_type_str: str, text: str) -> str:
    """Generates a unique knowledge base ID (URI) for an entity."""
    # Simple slugification: replace non-alphanumeric with underscore
    slug = "".join(c if c.isalnum() else "_" for c in text.lower())
    # Trim slug to avoid overly long URIs, e.g., first 50 chars
    slug = slug[:50].strip('_')
    return str(KB[f"{entity_type_str}/{slug}_{uuid.uuid4().hex[:8]}"])


def _extracted_entity_to_kb_entity(
    extracted_entity: ExtractedEntity,
    source_doc_uri: str
) -> Optional[KbBaseEntity]:
    """Transforms an ExtractedEntity to a corresponding KbBaseEntity subclass instance."""
    kb_id_text = extracted_entity.text
    entity_label_upper = extracted_entity.label.upper()

    common_args = {
        "label": extracted_entity.text,
        "source_document_uri": source_doc_uri,
        "extracted_from_text_span": (extracted_entity.span_start, extracted_entity.span_end),
    }

    if entity_label_upper == "PERSON":
        kb_id = _generate_kb_id("Person", kb_id_text)
        return KbPerson(kb_id=kb_id, full_name=extracted_entity.text, **common_args)
    elif entity_label_upper == "ORG":
        kb_id = _generate_kb_id("Organization", kb_id_text)
        return KbOrganization(kb_id=kb_id, name=extracted_entity.text, **common_args)
    elif entity_label_upper in ["LOC", "GPE"]: # GPE (Geopolitical Entity) often maps to Location
        kb_id = _generate_kb_id("Location", kb_id_text)
        return KbLocation(kb_id=kb_id, name=extracted_entity.text, **common_args)
    elif entity_label_upper == "DATE":
        kb_id = _generate_kb_id("DateEntity", kb_id_text)
        return KbDateEntity(kb_id=kb_id, date_value=extracted_entity.text, **common_args)
    else:
        logger_cli.debug(f"Unhandled entity type: {extracted_entity.label} for text: '{extracted_entity.text}'")
        return None


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.
    
    Args:
        args: Command-line arguments (optional, defaults to sys.argv[1:])
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Knowledge Base Processor - Extract and analyze knowledge base content"
    )
    
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration file",
        type=str
    )
    
    parser.add_argument(
        "--knowledge-base", "-k",
        help="Path to knowledge base directory",
        type=str
    )
    parser.add_argument(
        "--metadata-store", "-m",
        help="Path to metadata store directory (e.g., ~/.kbp/metadata). "
             "The database file 'knowledgebase.db' will be created/used within this directory. "
             "Defaults to the directory specified in the config file, or '~/.kbp/metadata' if not set.",
        type=str
    )
    
    
    parser.add_argument(
        "--log-level", "-l",
        help="Logging level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO"
    )
    
    parser.add_argument(
        "--log-file",
        help="Path to log file",
        type=str
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute", required=True)
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process knowledge base files")
    process_parser.add_argument(
        "--pattern", "-p",
        help="File pattern to process (default: **/*.md)",
        default="**/*.md"
    )
    process_parser.add_argument(
        "--rdf-output-dir",
        help="Directory to save RDF output files (e.g., output/rdf). If provided, RDF/TTL files will be generated.",
        type=str,
        default=None
    )
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the knowledge base")
    query_parser.add_argument(
        "query_string",
        help="Query string"
    )
    query_parser.add_argument(
        "--type", "-t",
        help="Query type",
        choices=["text", "tag", "topic"],
        default="text"
    )
    
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI.
    
    Args:
        args: Command-line arguments (optional, defaults to sys.argv[1:])
        
    Returns:
        Exit code
    """
    # Parse arguments
    parsed_args = parse_args(args)
    
    # Set up logging
    setup_logging(parsed_args.log_level, parsed_args.log_file)
    # Logger is already initialized at module level: logger_cli
    
    # Load configuration
    config = load_config(parsed_args.config)
    
    # Override config with command-line arguments
    if parsed_args.knowledge_base:
        config.knowledge_base_path = parsed_args.knowledge_base
    elif not hasattr(config, 'knowledge_base_path') or not config.knowledge_base_path:
        config.knowledge_base_path = str(Path.cwd())
        logger_cli.info(f"Knowledge base path not specified, defaulting to current directory: {config.knowledge_base_path}")

    db_directory_path_str: str
    if parsed_args.metadata_store:
        db_directory_path_str = parsed_args.metadata_store
        logger_cli.info(f"Using metadata store directory from command line: {db_directory_path_str}")
    elif hasattr(config, 'metadata_store_path') and config.metadata_store_path:
        db_directory_path_str = config.metadata_store_path
        logger_cli.info(f"Using metadata store directory from config: {db_directory_path_str}")
    else:
        default_dir = Path.home() / ".kbp" / "metadata"
        db_directory_path_str = str(default_dir)
        logger_cli.warning(
            f"Metadata store directory not specified via CLI or config, "
            f"or config value is empty. Defaulting to: {db_directory_path_str}"
        )

    db_directory_path = Path(db_directory_path_str)
    db_filename = "knowledgebase.db"
    db_file_path = db_directory_path / db_filename
    
    logger_cli.info(f"Final database file path: {db_file_path}")

    kb_processor = KnowledgeBaseProcessor(
        knowledge_base_dir=config.knowledge_base_path,
        metadata_store_path=str(db_file_path)
    )
    
    if parsed_args.command == "process":
        return process_command(parsed_args, config, kb_processor)
    elif parsed_args.command == "query":
        return query_command(parsed_args, config, kb_processor)
    else:
        logger_cli.error("No command specified or unknown command. Use 'process' or 'query'.")
        # parser.print_help() # Already handled by argparse if command is required
        return 1


def process_command(args: argparse.Namespace, config, kb_processor: KnowledgeBaseProcessor) -> int:
    """Execute the process command."""
    logger_proc = get_logger("knowledgebase_processor.cli.process")
    pattern = args.pattern
    rdf_output_dir_str = args.rdf_output_dir

    logger_proc.info(f"Processing files matching pattern: {pattern}")
    logger_proc.info(f"Knowledge base path: {config.knowledge_base_path}")

    rdf_converter: Optional[RDFConverter] = None
    rdf_output_path: Optional[Path] = None

    if rdf_output_dir_str:
        rdf_output_path = Path(rdf_output_dir_str)
        try:
            rdf_output_path.mkdir(parents=True, exist_ok=True)
            logger_proc.info(f"RDF output will be saved to: {rdf_output_path.resolve()}")
            rdf_converter = RDFConverter(base_uri=str(KB))
        except OSError as e:
            logger_proc.error(f"Could not create RDF output directory {rdf_output_path}: {e}", exc_info=True)
            return 1 # Exit if directory creation fails

    try:
        documents = kb_processor.process_all(pattern) # List[ProcessedDocument]
        count = len(documents)
        logger_proc.info(f"Processed {count} documents from storage.")

        if rdf_converter and rdf_output_path and documents:
            logger_proc.info(f"Starting RDF generation for {count} documents...")
            for doc_idx, doc in enumerate(documents):
                # Ensure doc.source_uri and doc.source_path are available
                if not doc.source_uri or not doc.source_path:
                    logger_proc.warning(f"Document at index {doc_idx} missing source_uri or source_path, skipping RDF generation.")
                    continue

                if not doc.metadata or not doc.metadata.entities:
                    logger_proc.debug(f"No entities to convert for document: {doc.source_uri}")
                    continue

                doc_graph = Graph()
                doc_graph.bind("kb", KB)
                doc_graph.bind("schema", SCHEMA)
                doc_graph.bind("rdfs", RDFS)
                doc_graph.bind("xsd", XSD)

                logger_proc.debug(f"Generating RDF for document: {doc.source_uri} ({doc.source_path.name})")
                entities_converted_count = 0
                for extracted_entity in doc.metadata.entities:
                    # Use doc.source_uri (which should be an absolute path string or file URI)
                    # for the source_document_uri field of the KbEntity.
                    kb_entity = _extracted_entity_to_kb_entity(extracted_entity, str(doc.source_uri))
                    if kb_entity:
                        try:
                            rdf_converter.kb_entity_to_graph(kb_entity, doc_graph)
                            entities_converted_count +=1
                            logger_proc.debug(f"Converted entity '{kb_entity.label}' ({kb_entity.kb_id}) to RDF.")
                        except Exception as e_conv:
                            logger_proc.error(f"Error converting entity '{kb_entity.label}' to RDF: {e_conv}", exc_info=True)
                
                logger_proc.debug(f"Converted {entities_converted_count} entities for {doc.source_path.name}.")

                if len(doc_graph) > 0:
                    output_filename = Path(doc.source_path.name).with_suffix(".ttl")
                    output_file_path = rdf_output_path / output_filename
                    try:
                        doc_graph.serialize(destination=str(output_file_path), format="turtle")
                        logger_proc.info(f"Saved RDF for {doc.source_path.name} to {output_file_path}")
                    except Exception as e_ser:
                        logger_proc.error(f"Error serializing RDF for {doc.source_path.name} to {output_file_path}: {e_ser}", exc_info=True)
                else:
                    logger_proc.info(f"No RDF triples generated for document: {doc.source_uri}")
        return 0
    except Exception as e:
        logger_proc.error(f"An error occurred during processing: {e}", exc_info=True)
        return 1


def query_command(args: argparse.Namespace, config, kb_processor: KnowledgeBaseProcessor) -> int:
    """Execute the query command."""
    logger_query = get_logger("knowledgebase_processor.cli.query")
    
    query_string = args.query_string
    query_type = args.type
    
    logger_query.info(f"Querying with {query_type} query: {query_string}")
    
    try:
        if query_type == "tag":
            results = kb_processor.find_by_tag(query_string)
        elif query_type == "topic":
            logger_query.warning("Topic-based querying is not fully implemented yet.")
            results = [] 
        else:  # text query
            results = kb_processor.search(query_string)
        
        if results:
            print(f"Found {len(results)} results:")
            for item in results: 
                print(f"- {item}")
        else:
            print("No results found")
        
        return 0
    except Exception as e:
        logger_query.error(f"An error occurred during query execution: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())