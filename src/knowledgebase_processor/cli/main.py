"""Main CLI implementation for the Knowledge Base Processor."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional
import json
from urllib.parse import urlparse

from ..config import load_config
from ..api import KnowledgeBaseAPI
from ..utils.logging import setup_logging, get_logger
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException


logger = get_logger("knowledgebase_processor.cli")


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL."""
    if not url:
        return False
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


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
    
    parser.add_argument(
        "--log-format",
        help="Logging format",
        choices=["text", "json"],
        default="text"
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
    
    # Process-and-load command
    process_and_load_parser = subparsers.add_parser("process-and-load", help="Process and load RDF into SPARQL endpoint")
    process_and_load_parser.add_argument(
        "knowledge_base_path",
        help="Path to the knowledge base directory. If omitted, the value from the global "
             "--knowledge-base argument, the config file, or the current directory is used.",
        type=str,
        nargs="?",
        default=None,
    )
    process_and_load_parser.add_argument(
        "--pattern", "-p",
        help="File pattern to process (default: **/*.md)",
        default="**/*.md"
    )
    process_and_load_parser.add_argument(
        "--graph", "-g",
        help="Named graph URI to load data into",
        type=str,
        default=None
    )
    process_and_load_parser.add_argument(
        "--endpoint-url", "-e",
        help="SPARQL endpoint URL (overrides config)",
        type=str,
        default=None
    )
    
    process_and_load_parser.add_argument(
        "--cleanup",
        help="Remove temporary RDF files after loading",
        action="store_true"
    )
    process_and_load_parser.add_argument(
        "--rdf-output-dir",
        help="Directory to save temporary RDF output files",
        type=str,
        default=None
    )
    process_and_load_parser.add_argument(
        "--user", "-u",
        help="Username for SPARQL endpoint authentication",
        type=str
    )
    process_and_load_parser.add_argument(
        "--password", "-P",
        help="Password for SPARQL endpoint authentication",
        type=str
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
        "--endpoint-url", "-e",
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
    sparql_query_parser.add_argument(
        "--user", "-u",
        help="Username for SPARQL endpoint authentication",
        type=str
    )
    sparql_query_parser.add_argument(
        "--password", "-P",
        help="Password for SPARQL endpoint authentication",
        type=str
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
        "--endpoint-url", "-e",
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


def handle_sparql_query(api: KnowledgeBaseAPI, args: argparse.Namespace) -> int:
    """Handle SPARQL query command via API.
    
    Args:
        api: KnowledgeBaseAPI instance
        args: Parsed command-line arguments
        
    Returns:
        Exit code
    """
    try:
        result = api.sparql_query(
            query=args.sparql_query,
            endpoint_url=args.endpoint_url,
            timeout=args.timeout,
            format=args.format
        )
        
        # Format and print results based on the format
        if args.format == "json":
            print(json.dumps(result, indent=2))
        elif args.format == "table":
            if isinstance(result, list) and result:
                # Print headers
                headers = list(result[0].keys())
                print(" | ".join(headers))
                print("-" * (len(" | ".join(headers))))
                
                # Print rows
                for row in result:
                    values = [str(row.get(header, "")) for header in headers]
                    print(" | ".join(values))
            elif isinstance(result, bool):
                print(result)
            else:
                print("No results found.")
        elif args.format == "turtle":
            print(result)
        else:
            print(result)
            
        return 0
        
    except Exception as e:
        logger.error(f"SPARQL query failed: {e}")
        return 1


def handle_sparql_load(api: KnowledgeBaseAPI, args: argparse.Namespace) -> int:
    """Handle SPARQL load-file command via API.
    
    Args:
        api: KnowledgeBaseAPI instance
        args: Parsed command-line arguments
        
    Returns:
        Exit code
    """
    try:
        api.sparql_load(
            file_path=Path(args.file_path),
            graph_uri=args.graph,
            endpoint_url=args.endpoint_url,
            username=args.user,
            password=args.password,
            rdf_format=args.rdf_format
        )
        logger.info(f"Successfully loaded RDF file '{args.file_path}' into graph '{args.graph}'.")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to load RDF file '{args.file_path}': {e}")
        return 1


def handle_sparql(api: KnowledgeBaseAPI, args: argparse.Namespace) -> int:
    """Route SPARQL commands to their respective handlers.
    
    Args:
        api: KnowledgeBaseAPI instance
        args: Parsed command-line arguments
        
    Returns:
        Exit code
    """
    if args.sparql_command == "query":
        return handle_sparql_query(api, args)
    elif args.sparql_command == "load-file":
        return handle_sparql_load(api, args)
    else:
        logger.error(f"Unknown SPARQL command: {args.sparql_command}")
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
    setup_logging(parsed_args.log_level, parsed_args.log_file, parsed_args.log_format)
    
    # Load configuration
    config = load_config(parsed_args.config)
    
    # Override config with command-line arguments
    if parsed_args.knowledge_base:
        config.knowledge_base_path = parsed_args.knowledge_base
    elif not hasattr(config, 'knowledge_base_path') or not config.knowledge_base_path:
        config.knowledge_base_path = str(Path.cwd())
        logger.info(f"Knowledge base path not specified, defaulting to current directory: {config.knowledge_base_path}")

    # Handle metadata store path
    if parsed_args.metadata_store:
        db_directory_path_str = parsed_args.metadata_store
        logger.info(f"Using metadata store directory from command line: {db_directory_path_str}")
    elif hasattr(config, 'metadata_store_path') and config.metadata_store_path:
        db_directory_path_str = config.metadata_store_path
        logger.info(f"Using metadata store directory from config: {db_directory_path_str}")
    else:
        default_dir = Path.home() / ".kbp" / "metadata"
        db_directory_path_str = str(default_dir)
        logger.warning(
            f"Metadata store directory not specified via CLI or config, "
            f"or config value is empty. Defaulting to: {db_directory_path_str}"
        )

    db_directory_path = Path(db_directory_path_str)
    db_filename = "knowledgebase.db"
    db_file_path = db_directory_path / db_filename
    config.metadata_store_path = str(db_file_path)
    
    logger.info(f"Final database file path: {db_file_path}")

    # Initialize API with config
    try:
        api = KnowledgeBaseAPI(config)
    except Exception as e:
        logger.error(f"Failed to initialize KnowledgeBaseAPI: {e}")
        return 1
    
    # Route to appropriate handler
    handlers = {
        'process': handle_process,
        'process-and-load': handle_process_and_load,
        'query': handle_query,
        'sparql': handle_sparql
    }
    
    handler = handlers.get(parsed_args.command)
    if handler:
        return handler(api, parsed_args)
    else:
        logger.error("No command specified or unknown command. Use 'process', 'query', or 'sparql'.")
        return 1

def handle_process_and_load(api: KnowledgeBaseAPI, args: argparse.Namespace) -> int:
    """Handle process-and-load command via API.

    Args:
        api: KnowledgeBaseAPI instance
        args: Parsed command-line arguments

    Returns:
        Exit code
    """
    logger.info("Starting process-and-load operation")
    from ..services.processing_service import ProcessingService

    # --- Validation ---
    kb_path = args.knowledge_base_path if args.knowledge_base_path is not None else api.config.knowledge_base_path
    knowledge_base_path = Path(kb_path)
    if not knowledge_base_path.is_dir():
        logger.error(f"Invalid knowledge base path: '{knowledge_base_path}' is not a directory.")
        return 1

    endpoint_url = args.endpoint_url or api.config.sparql_endpoint_url
    if not endpoint_url:
        logger.error("SPARQL endpoint URL is required. Provide it via --endpoint-url or in the config file.")
        return 1

    if not is_valid_url(endpoint_url):
        logger.error(f"Invalid SPARQL endpoint URL: {endpoint_url}")
        return 1

    rdf_output_dir = Path(args.rdf_output_dir) if args.rdf_output_dir else None
    if rdf_output_dir:
        try:
            rdf_output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Could not create RDF output directory '{rdf_output_dir}': {e}")
            return 1

    # --- Execution ---
    try:
        processing_service = ProcessingService(api.kb_processor)
        result = processing_service.process_and_load(
            pattern=args.pattern,
            knowledge_base_path=knowledge_base_path,
            rdf_output_dir=rdf_output_dir,
            graph_uri=args.graph,
            endpoint_url=endpoint_url,
            
            cleanup=args.cleanup,
            username=args.user,
            password=args.password,
            config=api.config
        )
        if result == 0:
            logger.info("Processing and loading completed successfully.")
        else:
            logger.error(f"Processing and loading failed with exit code {result}.")
        return result
    except SPARQLWrapperException as e:
        logger.error(f"A SPARQL error occurred: {e}", exc_info=True)
        logger.error(f"Please check if the SPARQL endpoint at '{endpoint_url}' is running and accessible.")
        return 1
    except FileNotFoundError as e:
        logger.error(f"File not found during processing: {e}", exc_info=True)
        return 1
    except Exception as e:
        logger.error(f"An unexpected error occurred during process-and-load: {e}", exc_info=True)
        return 1


def handle_process(api: KnowledgeBaseAPI, args: argparse.Namespace) -> int:
    """Handle process command via API.
    
    Args:
        api: KnowledgeBaseAPI instance
        args: Parsed command-line arguments
        
    Returns:
        Exit code
    """
    try:
        pattern = args.pattern
        rdf_output_dir = Path(args.rdf_output_dir) if args.rdf_output_dir else None
        
        logger.info(f"Processing files matching pattern: {pattern}")
        if rdf_output_dir:
            logger.info(f"RDF output directory specified: {rdf_output_dir}")
        
        result = api.process_documents(
            pattern=pattern,
            rdf_output_dir=rdf_output_dir
        )
        
        if result == 0:
            logger.info("Processing completed successfully")
        else:
            logger.error("Processing failed")
            
        return result
        
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        return 1


def handle_query(api: KnowledgeBaseAPI, args: argparse.Namespace) -> int:
    """Handle query command via API.
    
    Args:
        api: KnowledgeBaseAPI instance
        args: Parsed command-line arguments
        
    Returns:
        Exit code
    """
    try:
        query_string = args.query_string
        query_type = args.type
        
        logger.info(f"Querying with {query_type} query: {query_string}")
        
        results = api.query(query_string=query_string, query_type=query_type)
        
        if results:
            print(f"Found {len(results)} results:")
            for item in results: 
                print(f"- {item}")
        else:
            print("No results found")
        
        return 0
        
    except Exception as e:
        logger.error(f"An error occurred during query execution: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())