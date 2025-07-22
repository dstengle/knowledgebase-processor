"""Processing service for orchestrating document processing operations."""

from pathlib import Path
from typing import Any, List, Optional

from ..processor.processor import Processor
from ..reader.reader import Reader
from ..metadata_store.interface import MetadataStoreInterface
from ..utils.logging import get_logger

from .sparql_service import SparqlService
import tempfile
import shutil


class ProcessingService:
    """Orchestrates document processing operations."""

    def __init__(
        self,
        processor: Processor,
        reader: Reader,
        metadata_store: MetadataStoreInterface,
        config=None,
    ):
        """Initialize the ProcessingService."""
        self.processor = processor
        self.reader = reader
        self.metadata_store = metadata_store
        self.config = config
        self.logger = get_logger("knowledgebase_processor.services.processing")

    def process_documents(
        self,
        pattern: str,
        knowledge_base_path: Path,
        rdf_output_dir: Optional[Path] = None,
    ) -> int:
        """Process documents matching pattern with optional RDF generation."""
        rdf_output_dir_str = str(rdf_output_dir) if rdf_output_dir else None

        self.logger.info(
            f"Processing files matching pattern: {pattern} in knowledge base: {knowledge_base_path}"
        )
        if rdf_output_dir_str:
            self.logger.info(f"RDF output directory specified: {rdf_output_dir_str}")

            if self.config and not self.config.analyze_entities:
                self.logger.warning(
                    "Entity analysis is disabled but RDF output was requested. "
                    "Automatically enabling entity analysis for this run to generate meaningful RDF output."
                )
                self.config.analyze_entities = True
                # The processor should be re-initialized by the caller if config changes
                # This service will not re-initialize the processor itself.

        return self.processor.process_and_generate_rdf(
            reader=self.reader,
            metadata_store=self.metadata_store,
            pattern=pattern,
            knowledge_base_path=knowledge_base_path,
            rdf_output_dir_str=rdf_output_dir_str,
        )

    def process_and_load(
        self,
        pattern: str,
        knowledge_base_path: Path,
        rdf_output_dir: Optional[Path] = None,
        graph_uri: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        cleanup: bool = False,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> int:
        """
        Orchestrate processing and loading: process documents to RDF, load into SPARQL endpoint, and optionally clean up.
        """
        logger = self.logger
        temp_dir = None
        output_dir = rdf_output_dir

        if cleanup and rdf_output_dir is None:
            temp_dir = tempfile.mkdtemp(prefix="kbp_rdf_")
            output_dir = Path(temp_dir)
            logger.info(f"Using temporary directory for RDF output: {output_dir}")

        try:
            code = self.process_documents(
                pattern=pattern,
                knowledge_base_path=knowledge_base_path,
                rdf_output_dir=output_dir,
            )
            if code != 0:
                logger.error("Document processing failed.")
                return code

            if not output_dir:
                logger.error("RDF output directory is not specified for loading.")
                return 1

            sparql_service = SparqlService(config=self.config)
            rdf_files = list(Path(output_dir).glob("*.ttl"))
            if not rdf_files:
                logger.error(f"No RDF files found in {output_dir}")
                return 1

            try:
                from tqdm import tqdm
                use_progress = True
            except ImportError:
                use_progress = False

            errors = []
            successes = 0
            iterator = (
                tqdm(rdf_files, desc="Loading RDF files")
                if use_progress
                else rdf_files
            )

            for rdf_file in iterator:
                try:
                    sparql_service.load_rdf_file(
                        file_path=rdf_file,
                        graph_uri=graph_uri,
                        update_endpoint_url=endpoint_url,
                        username=username,
                        password=password,
                    )
                    logger.info(f"Loaded RDF file: {rdf_file}")
                    successes += 1
                except Exception as e:
                    logger.error(f"Failed to load {rdf_file}: {e}")
                    errors.append((str(rdf_file), str(e)))

            logger.info(
                f"RDF load complete: {successes} succeeded, {len(errors)} failed."
            )
            if errors:
                logger.error("Errors encountered during RDF loading:")
                for fname, err in errors:
                    logger.error(f"  {fname}: {err}")

            return 1 if errors else 0
        finally:
            if cleanup and temp_dir:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary RDF directory: {temp_dir}")
