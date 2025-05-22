import unittest
from datetime import datetime, timezone
from rdflib import Graph, Literal, Namespace, URIRef, XSD, RDF, RDFS

from knowledgebase_processor.models.kb_entities import KbPerson, KbTodoItem
from knowledgebase_processor.rdf_converter.converter import RdfConverter, KB, SCHEMA


class TestRdfConverter(unittest.TestCase):
    def setUp(self):
        self.converter = RdfConverter() # Instantiate without arguments
        self.base_uri = "http://example.org/kb/"
        self.now = datetime.now(timezone.utc)

    def test_kb_id_as_full_uri(self):
        person = KbPerson(kb_id="http://custom.uri/person/123", full_name="Full URI Person")
        graph = self.converter.kb_entity_to_graph(person, base_uri_str=self.base_uri)
        entity_uri = URIRef("http://custom.uri/person/123")
        self.assertIn((entity_uri, RDF.type, KB.Person), graph)
        self.assertIn((entity_uri, SCHEMA.name, Literal("Full URI Person")), graph)

    def test_kb_id_appended_to_base_uri(self):
        person = KbPerson(kb_id="person/456", full_name="Appended URI Person")
        graph = self.converter.kb_entity_to_graph(person, base_uri_str=self.base_uri)
        entity_uri = URIRef(self.base_uri + "person/456")
        self.assertIn((entity_uri, RDF.type, KB.Person), graph)
        self.assertIn((entity_uri, SCHEMA.name, Literal("Appended URI Person")), graph)

    def test_kb_person_serialization_all_fields(self):
        person = KbPerson(
            kb_id="person_001",
            label="John D.",
            source_document_uri="http://example.org/docs/doc1",
            extracted_from_text_span=(10, 20),
            creation_timestamp=self.now,
            last_modified_timestamp=self.now,
            full_name="John Doe",
            given_name="John",
            family_name="Doe",
            aliases=["Johnny", "JD"],
            email="john.doe@example.com",
            roles=["Developer", "Lead"]
        )
        graph = self.converter.kb_entity_to_graph(person, base_uri_str=self.base_uri)
        entity_uri = URIRef(self.base_uri + "person_001")

        self.assertIn((entity_uri, RDF.type, KB.Person), graph)
        self.assertIn((entity_uri, RDF.type, SCHEMA.Person), graph)
        self.assertIn((entity_uri, RDFS.label, Literal("John D.")), graph) # Explicit label
        self.assertIn((entity_uri, KB.sourceDocument, URIRef("http://example.org/docs/doc1")), graph)
        self.assertIn((entity_uri, KB.extractedFromTextSpanStart, Literal(10, datatype=XSD.integer)), graph)
        self.assertIn((entity_uri, KB.extractedFromTextSpanEnd, Literal(20, datatype=XSD.integer)), graph)
        self.assertIn((entity_uri, KB.creationTimestamp, Literal(self.now, datatype=XSD.dateTime)), graph)
        self.assertIn((entity_uri, KB.lastModifiedTimestamp, Literal(self.now, datatype=XSD.dateTime)), graph)
        self.assertIn((entity_uri, SCHEMA.name, Literal("John Doe")), graph)
        self.assertIn((entity_uri, KB.fullName, Literal("John Doe")), graph)
        self.assertIn((entity_uri, SCHEMA.givenName, Literal("John")), graph)
        self.assertIn((entity_uri, SCHEMA.familyName, Literal("Doe")), graph)
        self.assertIn((entity_uri, SCHEMA.alternateName, Literal("Johnny")), graph)
        self.assertIn((entity_uri, SCHEMA.alternateName, Literal("JD")), graph)
        self.assertIn((entity_uri, SCHEMA.email, Literal("john.doe@example.com")), graph)
        self.assertIn((entity_uri, KB.role, Literal("Developer")), graph)
        self.assertIn((entity_uri, KB.role, Literal("Lead")), graph)

    def test_kb_person_serialization_minimal_fields(self):
        person = KbPerson(kb_id="person_002", full_name="Jane Minimal") # full_name will be used as label
        graph = self.converter.kb_entity_to_graph(person, base_uri_str=self.base_uri)
        entity_uri = URIRef(self.base_uri + "person_002")

        self.assertIn((entity_uri, RDF.type, KB.Person), graph)
        self.assertIn((entity_uri, SCHEMA.name, Literal("Jane Minimal")), graph)
        self.assertIn((entity_uri, RDFS.label, Literal("Jane Minimal")), graph) # Label from full_name
        self.assertNotIn((entity_uri, SCHEMA.givenName, None), graph) # Check optional fields are not present

    def test_kb_todo_item_serialization_all_fields(self):
        due_date = datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        todo = KbTodoItem(
            kb_id="todo_001",
            label="Urgent Task",
            source_document_uri="http://example.org/docs/doc2",
            extracted_from_text_span=(5, 15),
            creation_timestamp=self.now,
            last_modified_timestamp=self.now,
            description="Complete the project report.",
            is_completed=False,
            due_date=due_date,
            priority="High",
            context="Project Alpha",
            assigned_to_uris=["person_001", "http://example.org/kb/person_002"],
            related_project_uri="project_alpha_id"
        )
        graph = self.converter.kb_entity_to_graph(todo, base_uri_str=self.base_uri)
        entity_uri = URIRef(self.base_uri + "todo_001")

        self.assertIn((entity_uri, RDF.type, KB.TodoItem), graph)
        self.assertIn((entity_uri, RDF.type, SCHEMA.Action), graph)
        self.assertIn((entity_uri, RDFS.label, Literal("Urgent Task")), graph) # Explicit label
        self.assertIn((entity_uri, KB.sourceDocument, URIRef("http://example.org/docs/doc2")), graph)
        self.assertIn((entity_uri, KB.extractedFromTextSpanStart, Literal(5, datatype=XSD.integer)), graph)
        self.assertIn((entity_uri, KB.extractedFromTextSpanEnd, Literal(15, datatype=XSD.integer)), graph)
        self.assertIn((entity_uri, KB.creationTimestamp, Literal(self.now, datatype=XSD.dateTime)), graph)
        self.assertIn((entity_uri, KB.lastModifiedTimestamp, Literal(self.now, datatype=XSD.dateTime)), graph)
        self.assertIn((entity_uri, SCHEMA.description, Literal("Complete the project report.")), graph)
        self.assertIn((entity_uri, KB.isCompleted, Literal(False, datatype=XSD.boolean)), graph)
        self.assertIn((entity_uri, SCHEMA.dueDate, Literal(due_date, datatype=XSD.dateTime)), graph)
        self.assertIn((entity_uri, KB.priority, Literal("High")), graph)
        self.assertIn((entity_uri, KB.context, Literal("Project Alpha")), graph)
        self.assertIn((entity_uri, SCHEMA.assignee, URIRef(self.base_uri + "person_001")), graph)
        self.assertIn((entity_uri, SCHEMA.assignee, URIRef("http://example.org/kb/person_002")), graph)
        self.assertIn((entity_uri, KB.relatedProject, URIRef(self.base_uri + "project_alpha_id")), graph)

    def test_kb_todo_item_serialization_minimal_fields(self):
        todo = KbTodoItem(kb_id="todo_002", description="Minimal todo item") # description will be used as label
        graph = self.converter.kb_entity_to_graph(todo, base_uri_str=self.base_uri)
        entity_uri = URIRef(self.base_uri + "todo_002")

        self.assertIn((entity_uri, RDF.type, KB.TodoItem), graph)
        self.assertIn((entity_uri, SCHEMA.description, Literal("Minimal todo item")), graph)
        self.assertIn((entity_uri, RDFS.label, Literal("Minimal todo item")), graph) # Label from description
        self.assertIn((entity_uri, KB.isCompleted, Literal(False, datatype=XSD.boolean)), graph) # Default value
        self.assertNotIn((entity_uri, SCHEMA.dueDate, None), graph)

    def test_optional_fields_none_not_in_graph(self):
        person = KbPerson(kb_id="person_003", full_name="Optional Test", email=None, given_name=None)
        graph = self.converter.kb_entity_to_graph(person, base_uri_str=self.base_uri)
        entity_uri = URIRef(self.base_uri + "person_003")

        # Check that fields explicitly set to None or not provided are not in the graph
        self.assertNotIn((entity_uri, SCHEMA.email, None), graph)
        self.assertFalse(any(s == entity_uri and p == SCHEMA.email for s, p, o in graph))
        self.assertFalse(any(s == entity_uri and p == SCHEMA.givenName for s, p, o in graph))
        self.assertFalse(any(s == entity_uri and p == KB.role for s, p, o in graph))


if __name__ == '__main__':
    unittest.main()