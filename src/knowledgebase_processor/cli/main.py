"""Main CLI implementation for the Knowledge Base Processor."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional
import uuid
from urllib.parse import quote
import json

from rdflib import Graph
from rdflib.namespace import SDO as SCHEMA, RDFS, XSD

from ..config import load_config
from ..main import KnowledgeBaseProcessor
from ..utils.logging import setup_logging, get_logger
from ..rdf_converter import RdfConverter
from ..models.kb_entities import KbBaseEntity, KbPerson, KbOrganization, KbLocation, KbDateEntity, KB
from ..models.entities import ExtractedEntity
from ..query_interface.sparql_interface import SparqlQueryInterface
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException
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
    source_doc_relative_path: str
) -> Optional[KbBaseEntity]:
    """Transforms an ExtractedEntity to a corresponding KbBaseEntity subclass instance."""
    kb_id_text = extracted_entity.text
    entity_label_upper = extracted_entity.label.upper()
    logger_cli.info(f"Processing entity: {kb_id_text} of type {entity_label_upper}")

    # Create a full URI for the source document
    # Replace spaces with underscores and quote for URI safety.
    # Ensure consistent path separators (/) before quoting.
    normalized_path = source_doc_relative_path.replace("\\", "/")
    safe_path_segment = quote(normalized_path.replace(" ", "_"))
    full_document_uri = str(KB[f"Document/{safe_path_segment}"])

    common_args = {
        "label": extracted_entity.text,
        "source_document_uri": full_document_uri, # Use the generated full URI
        "extracted_from_text_span": (extracted_entity.start_char, extracted_entity.end_char),
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
    
    # SPARQL command group
    sparql_parser = subparsers.add_parser("sparql", help="SPARQL operations")
    sparql_subparsers = sparql_parser.add_subparsers(dest="sparql_command", help="SPARQL command to execute", required=True)
    
    # SPARQL query command
    sparql_query_parser = sparql_subparsers.add_parser("query", help="Execute a SPARQL query")
    sparql_query_parser.add_argument(
        "sparql_query",
        help="SPARQL query string"
    )
    sparql_query_parser.add_argument(
        "--endpoint", "-e",
        help="SPARQL endpoint URL (overrides config)",
        type=str
    )
    sparql_query_parser.add_argument(
        "--timeout", "-t",
        help="Query timeout in seconds",
        type=int,
        default=30
    )
    sparql_query_parser.add_argument(
        "--format", "-f",
        help="Output format for results",
        choices=["json", "table", "turtle"],
        default="table"
    )
    
    # SPARQL load-file command
    sparql_load_parser = sparql_subparsers.add_parser("load-file", help="Load an RDF file into the SPARQL store")
    sparql_load_parser.add_argument(
        "file_path",
        help="Path to the RDF file to load"
    )
    sparql_load_parser.add_argument(
        "--graph", "-g",
        help="Named graph URI to load data into",
        type=str
    )
    sparql_load_parser.add_argument(
        "--endpoint", "-e",
        help="SPARQL endpoint URL (overrides config)",
        type=str
    )
    sparql_load_parser.add_argument(
        "--user", "-u",
        help="Username for SPARQL endpoint authentication",
        type=str
    )
    sparql_load_parser.add_argument(
        "--password", "-P",
        help="Password for SPARQL endpoint authentication",
        type=str
    )
    sparql_load_parser.add_argument(
        "--rdf-format",
        help="RDF format of the input file",
        choices=["turtle", "n3", "nt", "xml", "json-ld"],
        default="turtle"
    )
    
    return parser.parse_args(args)


def sparql_command_router(args: argparse.Namespace, config_obj, logger) -> int:
    """Route SPARQL commands to their respective handlers.
    
    Args:
        args: Parsed command-line arguments
        config_obj: Configuration object
        logger: Logger instance
        
    Returns:
        Exit code
    """
    if args.sparql_command == "query":
        return execute_sparql_query_cli_command(args, config_obj, logger)
    elif args.sparql_command == "load-file":
        return execute_sparql_load_file_cli_command(args, config_obj, logger)
    else:
        logger.error(f"Unknown SPARQL command: {args.sparql_command}")
        return 1


def execute_sparql_query_cli_command(args: argparse.Namespace, config_obj, logger) -> int:
    """Execute a SPARQL query command.
    
    Args:
        args: Parsed command-line arguments
        config_obj: Configuration object
        logger: Logger instance
        
    Returns:
        Exit code
    """
    # Determine the SPARQL query endpoint
    sparql_query_endpoint = args.endpoint if args.endpoint else config_obj.sparql_endpoint
    
    if not sparql_query_endpoint:
        logger.error("SPARQL query endpoint not specified via --endpoint or configuration.")
        return 1
    
    # Instantiate SPARQL interface
    sparql_interface = SparqlQueryInterface(endpoint_url=sparql_query_endpoint)
    
    sparql_query_string = args.sparql_query
    timeout = args.timeout
    
    try:
        # Determine query type and execute accordingly
        query_upper = sparql_query_string.upper().strip()
        
        if query_upper.startswith("SELECT") and "UPDATE" not in query_upper:
            # SELECT query
            results = sparql_interface.select(sparql_query_string, timeout=timeout)
            
            if args.format == "json":
                print(json.dumps(results, indent=2))
            elif args.format == "table":
                if results:
                    # Print headers
                    headers = list(results[0].keys())
                    print(" | ".join(headers))
                    print("-" * (len(" | ".join(headers))))
                    
                    # Print rows
                    for row in results:
                        values = [str(row.get(header, "")) for header in headers]
                        print(" | ".join(values))
                else:
                    print("No results found.")
            elif args.format == "turtle":
                logger.info("Turtle format is not applicable for SELECT queries.")
                
        elif query_upper.startswith("ASK"):
            # ASK query
            result = sparql_interface.ask(sparql_query_string, timeout=timeout)
            
            if args.format == "json":
                print(json.dumps({"boolean": result}, indent=2))
            else:  # table or turtle
                print(result)
                
        elif query_upper.startswith("CONSTRUCT"):
            # CONSTRUCT query
            graph_result = sparql_interface.construct(sparql_query_string, timeout=timeout)
            
            if args.format == "turtle":
                print(graph_result.serialize(format="turtle"))
            elif args.format == "json":
                logger.info("Direct JSON output for CONSTRUCT queries is not standard. Showing Turtle format.")
                print(graph_result.serialize(format="turtle"))
            elif args.format == "table":
                logger.info("Table format is not directly applicable for CONSTRUCT queries. Showing Turtle format.")
                print(graph_result.serialize(format="turtle"))
                
        elif query_upper.startswith("DESCRIBE"):
            # DESCRIBE query
            graph_result = sparql_interface.describe(sparql_query_string, timeout=timeout)
            
            if args.format == "turtle":
                print(graph_result.serialize(format="turtle"))
            elif args.format == "json":
                logger.info("Direct JSON output for DESCRIBE queries is not standard. Showing Turtle format.")
                print(graph_result.serialize(format="turtle"))
            elif args.format == "table":
                logger.info("Table format is not directly applicable for DESCRIBE queries. Showing Turtle format.")
                print(graph_result.serialize(format="turtle"))
                
        elif any(keyword in query_upper for keyword in ["INSERT", "DELETE", "LOAD", "CLEAR", "CREATE", "DROP"]):
            # UPDATE query
            sparql_interface.update(sparql_query_string, timeout=timeout)
            print("Update query executed successfully.")
            
        else:
            logger.error(f"Could not determine query type or query type not supported: {sparql_query_string[:50]}...")
            return 1
            
        return 0
        
    except SPARQLWrapperException as e:
        logger.error(f"SPARQL query failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during SPARQL query execution: {e}")
        return 1


def execute_sparql_load_file_cli_command(args: argparse.Namespace, config_obj, logger) -> int:
    """Execute a SPARQL load-file command.
    
    Args:
        args: Parsed command-line arguments
        config_obj: Configuration object
        logger: Logger instance
        
    Returns:
        Exit code
    """
    # Determine SPARQL endpoints
    sparql_update_endpoint_url = args.endpoint if args.endpoint else config_obj.sparql_update_endpoint
    sparql_query_endpoint = config_obj.sparql_endpoint

    if not sparql_update_endpoint_url:
        logger.error("SPARQL update endpoint not specified via --endpoint or configuration.")
        return 1

    if not sparql_query_endpoint:
        sparql_query_endpoint = sparql_update_endpoint_url.replace('/update', '/query')

    # Instantiate SPARQL interface
    sparql_interface = SparqlQueryInterface(
        endpoint_url=sparql_query_endpoint,
        update_endpoint_url=sparql_update_endpoint_url,
        username=args.user,
        password=args.password
    )
    
    file_path = args.file_path
    graph_uri = args.graph
    rdf_format = args.rdf_format
    
    try:
        sparql_interface.load_file(file_path=file_path, graph_uri=graph_uri, format=rdf_format)
        logger.info(f"Successfully loaded RDF file '{file_path}' into graph '{graph_uri}'.")
        return 0
        
    except (SPARQLWrapperException, FileNotFoundError, Exception) as e:
        logger.error(f"Failed to load RDF file '{file_path}': {e}")
        return 1


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
    
    if parsed_args.command == "process" or parsed_args.command == "query":
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
            metadata_store_path=str(db_file_path),
            config=config
        )
        
        if parsed_args.command == "process":
            return process_command(parsed_args, config, kb_processor)
        elif parsed_args.command == "query":
            return query_command(parsed_args, config, kb_processor)

    elif parsed_args.command == "sparql":
        return sparql_command_router(parsed_args, config, logger_cli)
    else:
        logger_cli.error("No command specified or unknown command. Use 'process', 'query', or 'sparql'.")
        return 1
    
    return 0


def process_command(args: argparse.Namespace, config, kb_processor: KnowledgeBaseProcessor) -> int:
    """Execute the process command."""
    logger_proc = get_logger("knowledgebase_processor.cli.process") # Renamed from logger_cli
    pattern = args.pattern
    rdf_output_dir_str = args.rdf_output_dir

    logger_proc.info(f"Processing files matching pattern: {pattern} in knowledge base: {config.knowledge_base_path}")
    if rdf_output_dir_str:
        logger_proc.info(f"RDF output directory specified: {rdf_output_dir_str}")
        
        # Auto-enable entity analysis when RDF output is requested but analysis is disabled
        if not config.analyze_entities:
            logger_proc.warning(
                "Entity analysis is disabled but RDF output was requested. "
                "Automatically enabling entity analysis for this run to generate meaningful RDF output."
            )
            config.analyze_entities = True
            # Reinitialize the processor with updated config
            from knowledgebase_processor.processor.processor import Processor
            from knowledgebase_processor.extractor.markdown import MarkdownExtractor
            from knowledgebase_processor.extractor.frontmatter import FrontmatterExtractor
            from knowledgebase_processor.extractor.heading_section import HeadingSectionExtractor
            from knowledgebase_processor.extractor.link_reference import LinkReferenceExtractor
            from knowledgebase_processor.extractor.code_quote import CodeQuoteExtractor
            from knowledgebase_processor.extractor.todo_item import TodoItemExtractor
            from knowledgebase_processor.extractor.tags import TagExtractor
            from knowledgebase_processor.extractor.list_table import ListTableExtractor
            from knowledgebase_processor.extractor.wikilink_extractor import WikiLinkExtractor
            from knowledgebase_processor.analyzer.topics import TopicAnalyzer
            from knowledgebase_processor.enricher.relationships import RelationshipEnricher
            
            kb_processor.processor = Processor(config=config)
            
            # Re-register all extractors
            kb_processor.processor.register_extractor(MarkdownExtractor())
            kb_processor.processor.register_extractor(FrontmatterExtractor())
            kb_processor.processor.register_extractor(HeadingSectionExtractor())
            kb_processor.processor.register_extractor(LinkReferenceExtractor())
            kb_processor.processor.register_extractor(CodeQuoteExtractor())
            kb_processor.processor.register_extractor(TodoItemExtractor())
            kb_processor.processor.register_extractor(TagExtractor())
            kb_processor.processor.register_extractor(ListTableExtractor())
            kb_processor.processor.register_extractor(WikiLinkExtractor())
            
            # Re-register analyzers
            kb_processor.processor.register_analyzer(TopicAnalyzer())
            
            # Re-register enrichers
            kb_processor.processor.register_enricher(RelationshipEnricher())

    # The kb_processor instance contains the reader, metadata_store, and the processor (which has the new method)
    # config.knowledge_base_path is a string, convert to Path for the method
    knowledge_base_path_obj = Path(config.knowledge_base_path)

    # Call the new method on the Processor instance within KnowledgeBaseProcessor
    return_code = kb_processor.processor.process_and_generate_rdf(
        reader=kb_processor.reader,
        metadata_store=kb_processor.metadata_store,
        pattern=pattern,
        knowledge_base_path=knowledge_base_path_obj,
        rdf_output_dir_str=rdf_output_dir_str
    )
    return return_code


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