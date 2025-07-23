"""SPARQL service for high-level SPARQL operations."""

import json
from pathlib import Path
from typing import Any, Optional

from rdflib import Graph
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException

from ..query_interface.sparql_interface import SparqlQueryInterface
from ..utils.logging import get_logger


class SparqlService:
    """High-level SPARQL operations service."""
    
    def __init__(self, config=None):
        """Initialize the SparqlService.
        
        Args:
            config: Configuration object containing SPARQL endpoint settings
        """
        self.config = config
        self.logger = get_logger("knowledgebase_processor.services.sparql")
        
        endpoint_url = getattr(config, 'sparql_endpoint_url', None)
        update_endpoint_url = getattr(config, 'sparql_update_endpoint_url', None)

        if not endpoint_url and update_endpoint_url and '/update' in update_endpoint_url:
            endpoint_url = update_endpoint_url.replace('/update', '/query')

        self.sparql_interface = SparqlQueryInterface(
            endpoint_url=endpoint_url,
            update_endpoint_url=update_endpoint_url
        )
    
    def execute_query(self, query: str, endpoint_url: Optional[str] = None, 
                     timeout: int = 30, format: str = "json") -> Any:
        """Execute a SPARQL query and return formatted results.
        
        Args:
            query: SPARQL query string
            endpoint_url: SPARQL endpoint URL (overrides config if provided)
            timeout: Query timeout in seconds
            format: Output format ("json", "table", "turtle")
            
        Returns:
            Query results in the requested format
            
        Raises:
            SPARQLWrapperException: If the SPARQL query fails
            Exception: For other unexpected errors
        """
        # Determine the SPARQL query endpoint
        sparql_query_endpoint = endpoint_url if endpoint_url else self.sparql_interface.endpoint_url
        
        if not sparql_query_endpoint:
            raise ValueError("SPARQL query endpoint not specified via parameter or configuration.")
        
        # Instantiate SPARQL interface if endpoint is different from config
        sparql_interface = self.sparql_interface
        if endpoint_url and endpoint_url != self.sparql_interface.endpoint_url:
            sparql_interface = SparqlQueryInterface(endpoint_url=endpoint_url, update_endpoint_url=self.sparql_interface.update_endpoint_url)
        
        try:
            # Determine query type and execute accordingly
            query_upper = query.upper().strip()
            
            if query_upper.startswith("SELECT") and "UPDATE" not in query_upper:
                # SELECT query
                results = sparql_interface.select(query, timeout=timeout)
                
                if format == "json":
                    return json.dumps(results, indent=2)
                elif format == "table":
                    if results:
                        # Format as table
                        headers = list(results[0].keys())
                        table_output = " | ".join(headers) + "\n"
                        table_output += "-" * (len(" | ".join(headers))) + "\n"
                        
                        for row in results:
                            values = [str(row.get(header, "")) for header in headers]
                            table_output += " | ".join(values) + "\n"
                        return table_output
                    else:
                        return "No results found."
                elif format == "turtle":
                    self.logger.info("Turtle format is not applicable for SELECT queries.")
                    return str(results)
                    
            elif query_upper.startswith("ASK"):
                # ASK query
                result = sparql_interface.ask(query, timeout=timeout)
                
                if format == "json":
                    return json.dumps({"boolean": result}, indent=2)
                else:  # table or turtle
                    return str(result)
                    
            elif query_upper.startswith("CONSTRUCT"):
                # CONSTRUCT query
                graph_result = sparql_interface.construct(query, timeout=timeout)
                
                if format == "turtle":
                    return graph_result.serialize(format="turtle")
                elif format == "json":
                    self.logger.info("Direct JSON output for CONSTRUCT queries is not standard. Showing Turtle format.")
                    return graph_result.serialize(format="turtle")
                elif format == "table":
                    self.logger.info("Table format is not directly applicable for CONSTRUCT queries. Showing Turtle format.")
                    return graph_result.serialize(format="turtle")
                    
            elif query_upper.startswith("DESCRIBE"):
                # DESCRIBE query
                graph_result = sparql_interface.describe(query, timeout=timeout)
                
                if format == "turtle":
                    return graph_result.serialize(format="turtle")
                elif format == "json":
                    self.logger.info("Direct JSON output for DESCRIBE queries is not standard. Showing Turtle format.")
                    return graph_result.serialize(format="turtle")
                elif format == "table":
                    self.logger.info("Table format is not directly applicable for DESCRIBE queries. Showing Turtle format.")
                    return graph_result.serialize(format="turtle")
                    
            elif any(keyword in query_upper for keyword in ["INSERT", "DELETE", "LOAD", "CLEAR", "CREATE", "DROP"]):
                # UPDATE query
                sparql_interface.update(query, timeout=timeout)
                return "Update query executed successfully."
                
            else:
                raise ValueError(f"Could not determine query type or query type not supported: {query[:50]}...")
                
        except SPARQLWrapperException as e:
            self.logger.error(f"SPARQL query failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during SPARQL query execution: {e}")
            raise
    
    def load_rdf_file(self, file_path: Path, graph_uri: Optional[str] = None,
                     endpoint_url: Optional[str] = None, update_endpoint_url: Optional[str] = None,
                     username: Optional[str] = None, password: Optional[str] = None,
                     rdf_format: str = "turtle", upsert: bool = False) -> None:
        """Load an RDF file into the SPARQL store.
        
        Args:
            file_path: Path to the RDF file to load
            graph_uri: Named graph URI to load data into
            endpoint_url: SPARQL endpoint URL (overrides config if provided)
            update_endpoint_url: SPARQL update endpoint URL (overrides config if provided)
            username: Username for authentication
            password: Password for authentication
            rdf_format: Format of the RDF file
            upsert: If True, performs upsert to avoid duplicates (default: False)
            
        Raises:
            ValueError: If required endpoints are not configured
            SPARQLWrapperException: If the load operation fails
            FileNotFoundError: If the RDF file doesn't exist
            Exception: For other unexpected errors
        """
        # Determine SPARQL endpoints
        sparql_update_endpoint_url = update_endpoint_url if update_endpoint_url else self.sparql_interface.update_endpoint_url
        sparql_query_endpoint = endpoint_url if endpoint_url else self.sparql_interface.endpoint_url

        if not sparql_update_endpoint_url:
            raise ValueError("SPARQL update endpoint not specified via parameter or configuration.")

        # Instantiate SPARQL interface
        sparql_interface = self.sparql_interface
        if (endpoint_url and endpoint_url != self.sparql_interface.endpoint_url) or \
           (update_endpoint_url and update_endpoint_url != self.sparql_interface.update_endpoint_url) or \
           (username and password):
            sparql_interface = SparqlQueryInterface(
                endpoint_url=sparql_query_endpoint,
                update_endpoint_url=sparql_update_endpoint_url,
                username=username,
                password=password
            )
        
        try:
            sparql_interface.load_file(file_path=str(file_path), graph_uri=graph_uri, format=rdf_format, upsert=upsert)
            operation = "upserted" if upsert else "loaded"
            self.logger.info(f"Successfully {operation} RDF file '{file_path}' into graph '{graph_uri}'.")
            
        except (SPARQLWrapperException, FileNotFoundError, Exception) as e:
            operation = "upsert" if upsert else "load"
            self.logger.error(f"Failed to {operation} RDF file '{file_path}': {e}")
            raise
    def load_rdf_files_batch(
        self,
        file_paths: list[Path],
        graph_uri: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        update_endpoint_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        rdf_format: str = "turtle",
        batch_size: int = 10,
        upsert: bool = False,
    ) -> None:
        """
        Efficiently load a large number of RDF files into the SPARQL store in batches.

        Args:
            file_paths: List of RDF file paths to load
            graph_uri: Named graph URI to load data into
            endpoint_url: SPARQL endpoint URL (overrides config if provided)
            update_endpoint_url: SPARQL update endpoint URL (overrides config if provided)
            username: Username for authentication
            password: Password for authentication
            rdf_format: Format of the RDF files
            batch_size: Number of files to load per batch
            upsert: If True, performs upsert to avoid duplicates (default: False)

        Raises:
            Exception: If any batch fails to load
        """
        from time import time

        total_files = len(file_paths)
        errors = []
        operation = "Upserting" if upsert else "Loading"
        
        for i in range(0, total_files, batch_size):
            batch = file_paths[i : i + batch_size]
            self.logger.info(
                f"{operation} RDF batch {i // batch_size + 1} ({len(batch)} files: {i + 1}-{min(i + batch_size, total_files)})"
            )
            start_time = time()
            for file_path in batch:
                try:
                    self.load_rdf_file(
                        file_path=file_path,
                        graph_uri=graph_uri,
                        endpoint_url=endpoint_url,
                        update_endpoint_url=update_endpoint_url,
                        username=username,
                        password=password,
                        rdf_format=rdf_format,
                        upsert=upsert,
                    )
                except Exception as e:
                    errors.append((str(file_path), str(e)))
            elapsed = time() - start_time
            operation_past = "upserted" if upsert else "loaded"
            self.logger.info(
                f"Batch {i // batch_size + 1} {operation_past} in {elapsed:.2f}s"
            )
        if errors:
            operation_lower = "upserting" if upsert else "loading"
            self.logger.error(
                f"Batch {operation_lower} completed with {len(errors)} errors. See log for details."
            )
            for file_path, err in errors:
                self.logger.error(f"File: {file_path} | Error: {err}")