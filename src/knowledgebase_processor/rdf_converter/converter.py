from datetime import datetime
from typing import Optional, List, Tuple, Union

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD

from knowledgebase_processor.models.kb_entities import KbBaseEntity, KbPerson, KbTodoItem

# Define Namespaces
KB = Namespace("http://example.org/knowledgebase/")
SCHEMA = Namespace("http://schema.org/")


class RdfConverter:
    """
    Converts Knowledge Base entities to RDF graphs.
    """

    def kb_entity_to_graph(self, entity: KbBaseEntity, base_uri_str: str = "http://example.org/kb/") -> Graph:
        """
        Converts a KB entity instance to an rdflib.Graph.

        Args:
            entity: The KbBaseEntity instance to convert.
            base_uri_str: The base URI string to use for constructing entity URIs
                          if kb_id is not already a full URI.

        Returns:
            An rdflib.Graph representing the entity.
        """
        g = Graph()
        g.bind("kb", KB)
        g.bind("schema", SCHEMA)
        g.bind("rdf", RDF)
        g.bind("rdfs", RDFS)
        g.bind("xsd", XSD)

        if "://" in entity.kb_id:
            entity_uri = URIRef(entity.kb_id)
        else:
            entity_uri = URIRef(base_uri_str.rstrip('/') + "/" + entity.kb_id.lstrip('/'))

        # Common properties for all KbBaseEntity instances
        if entity.label:
            g.add((entity_uri, RDFS.label, Literal(entity.label)))
        if entity.source_document_uri:
            g.add((entity_uri, KB.sourceDocument, URIRef(entity.source_document_uri)))
        if entity.extracted_from_text_span:
            # This could be modeled more richly, e.g., using a blank node for the span
            g.add((entity_uri, KB.extractedFromTextSpanStart, Literal(entity.extracted_from_text_span[0], datatype=XSD.integer)))
            g.add((entity_uri, KB.extractedFromTextSpanEnd, Literal(entity.extracted_from_text_span[1], datatype=XSD.integer)))
        g.add((entity_uri, KB.creationTimestamp, Literal(entity.creation_timestamp, datatype=XSD.dateTime)))
        g.add((entity_uri, KB.lastModifiedTimestamp, Literal(entity.last_modified_timestamp, datatype=XSD.dateTime)))

        if isinstance(entity, KbPerson):
            g.add((entity_uri, RDF.type, KB.Person))
            g.add((entity_uri, RDF.type, SCHEMA.Person)) # Also typing as schema:Person

            if entity.full_name:
                g.add((entity_uri, SCHEMA.name, Literal(entity.full_name)))
                g.add((entity_uri, KB.fullName, Literal(entity.full_name))) # Using KB for specific if needed
                if not entity.label: # Use full_name as rdfs:label if label is not set
                    g.add((entity_uri, RDFS.label, Literal(entity.full_name)))
            if entity.given_name:
                g.add((entity_uri, SCHEMA.givenName, Literal(entity.given_name)))
            if entity.family_name:
                g.add((entity_uri, SCHEMA.familyName, Literal(entity.family_name)))
            if entity.aliases:
                for alias in entity.aliases:
                    g.add((entity_uri, SCHEMA.alternateName, Literal(alias)))
            if entity.email:
                g.add((entity_uri, SCHEMA.email, Literal(entity.email)))
            if entity.roles:
                for role in entity.roles:
                    g.add((entity_uri, KB.role, Literal(role))) # Using KB for role, could be schema:role

        elif isinstance(entity, KbTodoItem):
            g.add((entity_uri, RDF.type, KB.TodoItem))
            g.add((entity_uri, RDF.type, SCHEMA.Action)) # Typing as schema:Action

            g.add((entity_uri, SCHEMA.description, Literal(entity.description)))
            if not entity.label: # Use description as rdfs:label if label is not set
                 g.add((entity_uri, RDFS.label, Literal(entity.description)))

            g.add((entity_uri, KB.isCompleted, Literal(entity.is_completed, datatype=XSD.boolean)))
            if entity.due_date:
                g.add((entity_uri, SCHEMA.dueDate, Literal(entity.due_date, datatype=XSD.dateTime)))
            if entity.priority:
                g.add((entity_uri, KB.priority, Literal(entity.priority))) # Could map to schema:actionPriority
            if entity.context:
                g.add((entity_uri, KB.context, Literal(entity.context))) # Could be schema:object or similar
            if entity.assigned_to_uris:
                for assignee_uri_str in entity.assigned_to_uris:
                    assignee_uri = URIRef(assignee_uri_str) if "://" in assignee_uri_str else URIRef(base_uri_str.rstrip('/') + "/" + assignee_uri_str.lstrip('/'))
                    g.add((entity_uri, SCHEMA.assignee, assignee_uri)) # schema:assignee expects schema:Person or schema:Organization
                    g.add((entity_uri, KB.assignedTo, assignee_uri))
            if entity.related_project_uri:
                project_uri = URIRef(entity.related_project_uri) if "://" in entity.related_project_uri else URIRef(base_uri_str.rstrip('/') + "/" + entity.related_project_uri.lstrip('/'))
                g.add((entity_uri, KB.relatedProject, project_uri)) # Could be schema:target or partOfProject

        return g