"""Element extraction processing module for handling document element extraction."""

from typing import List, Dict, Any

from ..models.content import Document
from ..models.metadata import DocumentMetadata
from ..utils.logging import get_logger


logger = get_logger("knowledgebase_processor.processor.element_extraction")


class ElementExtractionProcessor:
    """Handles element extraction from documents using registered extractors."""
    
    def __init__(self):
        """Initialize ElementExtractionProcessor."""
        self.extractors = []
    
    def register_extractor(self, extractor):
        """Register an element extractor.
        
        Args:
            extractor: Extractor component to register
        """
        self.extractors.append(extractor)
        logger.debug(f"Registered extractor: {type(extractor).__name__}")
    
    def extract_all_elements(
        self,
        document: Document,
        doc_metadata: DocumentMetadata
    ) -> List[Any]:
        """Extract all elements from document using registered extractors.
        
        Args:
            document: Document to extract from
            doc_metadata: Document metadata to update with extraction info
            
        Returns:
            List of all extracted elements
        """
        all_elements = []
        extraction_stats = {}
        
        for extractor in self.extractors:
            try:
                extractor_name = type(extractor).__name__
                elements = extractor.extract(document)
                
                if elements:
                    all_elements.extend(elements)
                    document.elements.extend(elements)
                    extraction_stats[extractor_name] = len(elements)
                    
                    # Update metadata if extractor supports it
                    if hasattr(extractor, "update_metadata"):
                        extractor.update_metadata(elements, doc_metadata)
                        
                    logger.debug(f"Extractor {extractor_name} found {len(elements)} elements")
                else:
                    extraction_stats[extractor_name] = 0
                    
            except Exception as e:
                extractor_name = type(extractor).__name__
                logger.error(f"Error in extractor {extractor_name}: {e}", exc_info=True)
                extraction_stats[extractor_name] = 0
        
        # Store extraction statistics in metadata
        if hasattr(doc_metadata, 'extraction_stats'):
            doc_metadata.extraction_stats = extraction_stats
        
        logger.info(f"Extracted {len(all_elements)} total elements from document")
        return all_elements
    
    def extract_by_type(
        self,
        document: Document,
        element_type: str
    ) -> List[Any]:
        """Extract elements of a specific type from document.
        
        Args:
            document: Document to extract from
            element_type: Type of elements to extract (e.g., 'heading', 'list', 'todo')
            
        Returns:
            List of elements of the specified type
        """
        matching_elements = []
        
        for extractor in self.extractors:
            # Check if extractor handles the requested type
            if self._extractor_handles_type(extractor, element_type):
                try:
                    elements = extractor.extract(document)
                    if elements:
                        # Filter for specific type if elements have type info
                        filtered = self._filter_elements_by_type(elements, element_type)
                        matching_elements.extend(filtered)
                        
                except Exception as e:
                    extractor_name = type(extractor).__name__
                    logger.error(f"Error in {extractor_name} for type {element_type}: {e}")
        
        logger.debug(f"Found {len(matching_elements)} elements of type '{element_type}'")
        return matching_elements
    
    def _extractor_handles_type(self, extractor, element_type: str) -> bool:
        """Check if an extractor handles a specific element type.
        
        Args:
            extractor: Extractor to check
            element_type: Element type to check for
            
        Returns:
            True if extractor handles the type, False otherwise
        """
        extractor_name = type(extractor).__name__.lower()
        element_type_lower = element_type.lower()
        
        # Simple heuristic based on extractor name
        return element_type_lower in extractor_name
    
    def _filter_elements_by_type(self, elements: List[Any], element_type: str) -> List[Any]:
        """Filter elements by type if they have type information.
        
        Args:
            elements: List of elements to filter
            element_type: Type to filter for
            
        Returns:
            Filtered list of elements
        """
        filtered = []
        
        for element in elements:
            # Check various ways elements might store type information
            if hasattr(element, 'element_type'):
                if element.element_type == element_type:
                    filtered.append(element)
            elif hasattr(element, 'type'):
                if element.type == element_type:
                    filtered.append(element)
            elif hasattr(element, '__class__'):
                # Check class name
                class_name = element.__class__.__name__.lower()
                if element_type.lower() in class_name:
                    filtered.append(element)
            else:
                # If no type info available, include all elements
                filtered.append(element)
        
        return filtered
    
    def get_extraction_summary(
        self,
        document: Document
    ) -> Dict[str, Any]:
        """Get a summary of extracted elements from a document.
        
        Args:
            document: Document to summarize
            
        Returns:
            Dictionary with extraction summary
        """
        summary = {
            'total_elements': len(document.elements),
            'element_types': {},
            'extractor_stats': {}
        }
        
        # Count elements by type
        for element in document.elements:
            element_type = 'unknown'
            
            if hasattr(element, 'element_type'):
                element_type = element.element_type
            elif hasattr(element, 'type'):
                element_type = element.type
            elif hasattr(element, '__class__'):
                element_type = element.__class__.__name__
            
            if element_type not in summary['element_types']:
                summary['element_types'][element_type] = 0
            summary['element_types'][element_type] += 1
        
        # Add extractor statistics if available
        if hasattr(document, 'metadata') and hasattr(document.metadata, 'extraction_stats'):
            summary['extractor_stats'] = document.metadata.extraction_stats
        
        return summary
    
    def validate_extracted_elements(
        self,
        elements: List[Any]
    ) -> Dict[str, Any]:
        """Validate extracted elements for completeness and correctness.
        
        Args:
            elements: List of elements to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'total_elements': len(elements),
            'valid_elements': 0,
            'invalid_elements': 0,
            'validation_errors': []
        }
        
        for i, element in enumerate(elements):
            try:
                # Basic validation checks
                is_valid = True
                
                # Check if element has required attributes
                if not hasattr(element, '__dict__') and not hasattr(element, '__slots__'):
                    validation_results['validation_errors'].append(
                        f"Element {i}: No accessible attributes"
                    )
                    is_valid = False
                
                # Check for position information if available
                if hasattr(element, 'position'):
                    if not isinstance(element.position, dict):
                        validation_results['validation_errors'].append(
                            f"Element {i}: Invalid position format"
                        )
                        is_valid = False
                
                # Check for content if available
                if hasattr(element, 'content'):
                    if not element.content or not isinstance(element.content, str):
                        validation_results['validation_errors'].append(
                            f"Element {i}: Missing or invalid content"
                        )
                        is_valid = False
                
                if is_valid:
                    validation_results['valid_elements'] += 1
                else:
                    validation_results['invalid_elements'] += 1
                    
            except Exception as e:
                validation_results['validation_errors'].append(
                    f"Element {i}: Validation error - {str(e)}"
                )
                validation_results['invalid_elements'] += 1
        
        validation_results['validity_rate'] = (
            validation_results['valid_elements'] / len(elements) 
            if elements else 0.0
        )
        
        return validation_results