"""Main CLI implementation for the Knowledge Base Processor."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from ..config import load_config
from ..main import KnowledgeBaseProcessor
from ..utils.logging import setup_logging, get_logger


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
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process knowledge base files")
    process_parser.add_argument(
        "--pattern", "-p",
        help="File pattern to process (default: **/*.md)",
        default="**/*.md"
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
    logger = get_logger("knowledgebase_processor.cli")
    
    # Load configuration
    config = load_config(parsed_args.config)
    
    # Override config with command-line arguments
    if parsed_args.knowledge_base:
        config.knowledge_base_path = parsed_args.knowledge_base
    elif not hasattr(config, 'knowledge_base_path') or not config.knowledge_base_path:
        # Default knowledge_base_path to current working directory if not set
        config.knowledge_base_path = str(Path.cwd())
        logger.info(f"Knowledge base path not specified, defaulting to current directory: {config.knowledge_base_path}")

    # Determine the metadata store directory
    db_directory_path_str: str
    if parsed_args.metadata_store:
        db_directory_path_str = parsed_args.metadata_store
        logger.info(f"Using metadata store directory from command line: {db_directory_path_str}")
    elif hasattr(config, 'metadata_store_path') and config.metadata_store_path:
        db_directory_path_str = config.metadata_store_path
        logger.info(f"Using metadata store directory from config: {db_directory_path_str}")
    else:
        # This case should ideally not be hit if config has a default for metadata_store_path
        # (which it does: ~/.kbp/metadata)
        # However, as a robust fallback:
        default_dir = Path.home() / ".kbp" / "metadata"
        db_directory_path_str = str(default_dir)
        logger.warning(
            f"Metadata store directory not specified via CLI or config, "
            f"or config value is empty. Defaulting to: {db_directory_path_str}"
        )

    # Construct the full database file path
    db_directory_path = Path(db_directory_path_str)
    db_filename = "knowledgebase.db" # Standard filename
    db_file_path = db_directory_path / db_filename
    
    logger.info(f"Final database file path: {db_file_path}")


    # Create the knowledge base processor
    # The KnowledgeBaseProcessor itself takes the full db_file_path for its metadata_store_path argument
    kb_processor = KnowledgeBaseProcessor(
        knowledge_base_dir=config.knowledge_base_path,
        metadata_store_path=str(db_file_path)
    )
    
    # Execute command
    if parsed_args.command == "process":
        return process_command(parsed_args, config, kb_processor)
    elif parsed_args.command == "query":
        return query_command(parsed_args, config, kb_processor)
    else:
        # If no command is given, ArgumentParser usually handles this.
        # If it reaches here, it means subparsers might not be required.
        # For safety, log and exit.
        logger.error("No command specified. Use 'process' or 'query'.")
        # parser.print_help() #  parse_args would have exited if no command was given and command is required.
        return 1


def process_command(args: argparse.Namespace, config, kb_processor) -> int:
    """Execute the process command.
    
    Args:
        args: Parsed arguments
        config: Configuration
        kb_processor: KnowledgeBaseProcessor instance
        
    Returns:
        Exit code
    """
    logger = get_logger("knowledgebase_processor.cli.process")
    
    # Get the file pattern
    pattern = args.pattern
    
    logger.info(f"Processing files matching pattern: {pattern}")
    logger.info(f"Knowledge base path: {config.knowledge_base_path}")
    
    # Process files
    try:
        documents = kb_processor.process_all(pattern)
        count = len(documents)
        logger.info(f"Processed {count} documents")
        return 0
    except Exception as e:
        logger.error(f"An error occurred during processing: {e}", exc_info=True)
        return 1


def query_command(args: argparse.Namespace, config, kb_processor) -> int:
    """Execute the query command.
    
    Args:
        args: Parsed arguments
        config: Configuration
        kb_processor: KnowledgeBaseProcessor instance
        
    Returns:
        Exit code
    """
    logger = get_logger("knowledgebase_processor.cli.query")
    
    # Get the query string and type
    query_string = args.query_string
    query_type = args.type
    
    logger.info(f"Querying with {query_type} query: {query_string}")
    
    # Execute the query
    try:
        if query_type == "tag":
            results = kb_processor.find_by_tag(query_string)
        elif query_type == "topic":
            # Assuming find_by_topic exists or will be added
            # results = kb_processor.find_by_topic(query_string) 
            logger.warning("Topic-based querying is not fully implemented yet.")
            results = [] # Placeholder
        else:  # text query
            results = kb_processor.search(query_string)
        
        # Print results
        if results:
            print(f"Found {len(results)} results:")
            for item in results: # Assuming results are document IDs or similar printable items
                print(f"- {item}")
        else:
            print("No results found")
        
        return 0
    except Exception as e:
        logger.error(f"An error occurred during query execution: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())