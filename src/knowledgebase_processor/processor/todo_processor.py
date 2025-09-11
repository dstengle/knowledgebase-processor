"""Todo item processing module for handling todo item extraction and conversion."""

from typing import List

from ..models.content import Document
from ..models.markdown import TodoItem
from ..models.kb_entities import KbTodoItem
from ..utils.id_generator import EntityIdGenerator
from ..utils.logging import get_logger


logger = get_logger("knowledgebase_processor.processor.todo")


class TodoProcessor:
    """Handles todo item extraction and conversion to KB entities."""
    
    def __init__(self, id_generator: EntityIdGenerator):
        """Initialize TodoProcessor with required dependencies.
        
        Args:
            id_generator: Generator for entity IDs
        """
        self.id_generator = id_generator
    
    def extract_todos_from_elements(
        self,
        document_elements: List,
        document_id: str
    ) -> List[KbTodoItem]:
        """Extract todo items from document elements.
        
        Args:
            document_elements: List of document elements to search
            document_id: ID of source document
            
        Returns:
            List of KbTodoItem entities
        """
        todo_entities = []
        
        for element in document_elements:
            if isinstance(element, TodoItem):
                kb_todo = self._convert_todo_to_entity(element, document_id)
                todo_entities.append(kb_todo)
        
        logger.debug(f"Extracted {len(todo_entities)} todo items from document {document_id}")
        return todo_entities
    
    def _convert_todo_to_entity(
        self,
        todo_item: TodoItem,
        document_id: str
    ) -> KbTodoItem:
        """Convert a TodoItem to a KbTodoItem entity.
        
        Args:
            todo_item: TodoItem to convert
            document_id: ID of source document
            
        Returns:
            KbTodoItem entity
        """
        todo_id = self.id_generator.generate_todo_id(document_id, todo_item.text)
        
        return KbTodoItem(
            kb_id=todo_id,
            label=todo_item.text,
            description=todo_item.text,
            is_completed=todo_item.is_checked,
            source_document_uri=document_id,
            extracted_from_text_span=(
                todo_item.position.get("start", 0),
                todo_item.position.get("end", 0)
            ) if todo_item.position else None
        )
    
    def find_incomplete_todos(
        self,
        todo_entities: List[KbTodoItem]
    ) -> List[KbTodoItem]:
        """Find all incomplete todo items from a list.
        
        Args:
            todo_entities: List of todo entities to filter
            
        Returns:
            List of incomplete todo entities
        """
        incomplete = [todo for todo in todo_entities if not todo.is_completed]
        logger.debug(f"Found {len(incomplete)} incomplete todos out of {len(todo_entities)} total")
        return incomplete
    
    def get_todo_statistics(
        self,
        todo_entities: List[KbTodoItem]
    ) -> dict:
        """Get statistics about todo items.
        
        Args:
            todo_entities: List of todo entities to analyze
            
        Returns:
            Dictionary with todo statistics
        """
        if not todo_entities:
            return {
                'total': 0,
                'completed': 0,
                'incomplete': 0,
                'completion_rate': 0.0
            }
        
        total = len(todo_entities)
        completed = sum(1 for todo in todo_entities if todo.is_completed)
        incomplete = total - completed
        completion_rate = completed / total if total > 0 else 0.0
        
        return {
            'total': total,
            'completed': completed,
            'incomplete': incomplete,
            'completion_rate': completion_rate
        }