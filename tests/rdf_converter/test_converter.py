import unittest
from datetime import datetime, timezone
from typing import List, Optional 
from pydantic import Field 

from rdflib import Graph, Literal, Namespace, URIRef, XSD, RDF, RDFS
from rdflib.namespace import SDO as SCHEMA

from knowledgebase_processor.models.kb_entities import KbPerson, KbTodoItem, KbBaseEntity
from knowledgebase_processor.rdf_converter.converter import RdfConverter, KB


# Define a dummy entity for testing generic metadata-driven conversion
KB.DummyType = KB.term("DummyType")
KB.customValue = KB.term("customValue")
if not hasattr(SCHEMA, "keywords"): # Ensure SCHEMA.keywords is usable
    SCHEMA.keywords = SCHEMA.term("keywords")

class KbDummyEntity(KbBaseEntity):
    """
    A dummy entity for testing various metadata configurations
    of the RdfConverter.
    """
    dummy_description: Optional[str] = Field(
        default=None,
        json_schema_extra={"rdf_property": SCHEMA.description, "rdf_datatype": XSD.string}
    )
    dummy_related_item: Optional[str] = Field(
        default=None,
        json_schema_extra={"rdf_property": SCHEMA.relatedLink, "is_object_property": True}
    )
    dummy_keywords: Optional[List[str]] = Field(
        default_factory=list,
        json_schema_extra={"rdf_properties": [SCHEMA.keywords], "rdf_datatype": XSD.string} 
    )
    dummy_see_also: Optional[List[str]] = Field(
        default_factory=list,
        json_schema_extra={"rdf_properties": [RDFS.seeAlso], "is_object_property": True}
    )
    dummy_count: Optional[int] = Field(
        default=None,
        json_schema_extra={"rdf_property": KB.customValue, "rdf_datatype": XSD.integer}
    )

    # model_config = {
    #     "rdf_types": [KB.DummyType],
    #     "rdfs_label_fallback_fields": ["dummy_description", "label"]
    # }

    class Config:
        json_schema_extra = {
            "rdf_types": [KB.DummyType],
            "rdfs_label_fallback_fields": ["dummy_description", "label"]
        }

class TestRdfConverter(unittest.TestCase):
    def setUp(self):
        self.converter = RdfConverter()
        self.base_uri = "http://example.org/kb/"
        self.now = datetime.now(timezone.utc)
    
    def _format_triple(self, subject, predicate, obj):
        """Format a triple in a human-readable way with clear visual formatting"""
        def short_uri(uri):
            if isinstance(uri, URIRef):
                uri_str = str(uri)
                if uri_str.startswith("http://example.org/kb/"):
                    return f"kb:{uri_str[22:]}"  # 22 is correct length for "http://example.org/kb/"
                elif uri_str.startswith("https://schema.org/"):
                    return f"schema:{uri_str[19:]}"  # 19 is correct length for "https://schema.org/"
                elif uri_str.startswith("http://schema.org/"):
                    return f"schema:{uri_str[18:]}"  # 18 is correct length for "http://schema.org/"
                elif uri_str.startswith("http://www.w3.org/1999/02/22-rdf-syntax-ns#"):
                    return f"rdf:{uri_str[43:]}"  # FIXED: 43 is correct length (was 44)
                elif uri_str.startswith("http://www.w3.org/2000/01/rdf-schema#"):
                    return f"rdfs:{uri_str[37:]}"  # FIXED: 37 is correct length (was 38)
                elif uri_str.startswith("http://www.w3.org/2001/XMLSchema#"):
                    return f"xsd:{uri_str[33:]}"  # 33 is correct length for "http://www.w3.org/2001/XMLSchema#"
                elif uri_str.startswith("http://knowledgebase.local/"):
                    return f"kb:{uri_str[27:]}"  # 27 is correct length for "http://knowledgebase.local/"
                return uri_str
            elif isinstance(uri, Literal):
                # Format literals with their datatype and value
                if uri.datatype:
                    datatype_str = short_uri(uri.datatype) if isinstance(uri.datatype, URIRef) else str(uri.datatype)
                    return f'"{uri}"^^{datatype_str}'
                elif uri.language:
                    return f'"{uri}"@{uri.language}'
                else:
                    return f'"{uri}"'
            return str(uri)
        
        # Format with better spacing and alignment (no truncation)
        s = short_uri(subject)
        p = short_uri(predicate)
        o = short_uri(obj)
        # Use wider fixed widths but don't truncate - pad shorter strings, allow longer ones
        s_formatted = f"{s:<35}" if len(s) <= 35 else s
        p_formatted = f"{p:<30}" if len(p) <= 30 else p  # Made predicate column wider
        return f"{s_formatted} {p_formatted} {o}"
    
    def _get_graph_summary(self, graph, entity_uri):
        """Get a readable summary of graph triples for a specific entity"""
        triples = [(s, p, o) for s, p, o in graph if s == entity_uri]
        if not triples:
            return f"No triples found for entity {entity_uri}"
        
        lines = [f"\nGraph contains {len(triples)} triples for {self._format_triple(entity_uri, '...', '...')}:"]
        lines.append("-" * 80)
        
        # Group triples by predicate for better organization
        predicates = {}
        for s, p, o in triples:
            if p not in predicates:
                predicates[p] = []
            predicates[p].append(o)
        
        # Sort predicates for consistent output
        for predicate in sorted(predicates.keys(), key=str):
            objects = predicates[predicate]
            if len(objects) == 1:
                lines.append(f"  {self._format_triple(entity_uri, predicate, objects[0])}")
            else:
                # Multiple objects for same predicate
                for i, obj_item in enumerate(objects): # Renamed obj to obj_item to avoid conflict
                    if i == 0:
                        lines.append(f"  {self._format_triple(entity_uri, predicate, obj_item)}")
                    else:
                        lines.append(f"  {'':<35} {'':<30} {self._format_triple('', '', obj_item).strip()}") # Adjusted spacing
        
        return "\n".join(lines)
    
    def _compare_expected_vs_actual(self, graph, entity_uri, expected_triples, missing_triples=None):
        """Compare expected vs actual triples and show differences clearly"""
        actual_triples = set((s, p, o) for s, p, o in graph if s == entity_uri)
        expected_set = set(expected_triples)
        
        missing = expected_set - actual_triples
        unexpected = actual_triples - expected_set
        
        if missing_triples: # missing_triples is a list of triples
            missing.update(set(missing_triples)) # Ensure it's a set for update
        
        lines = [f"\nTriple comparison for {self._format_triple(entity_uri, '...', '...')}:"]
        lines.append("=" * 80)
        
        if missing:
            lines.append(f"\n❌ MISSING ({len(missing)} triples):")
            for s_m, p_m, o_m in sorted(missing, key=lambda x: str(x[1])): # Renamed s,p,o
                lines.append(f"  {self._format_triple(s_m, p_m, o_m)}")
        
        if unexpected:
            lines.append(f"\n⚠️  UNEXPECTED ({len(unexpected)} triples):")
            for s_u, p_u, o_u in sorted(unexpected, key=lambda x: str(x[1])): # Renamed s,p,o
                lines.append(f"  {self._format_triple(s_u, p_u, o_u)}")
        
        if not missing and not unexpected:
            lines.append("\n✅ All expected triples found!")
        
        # Show all actual triples for context
        lines.append(f"\n📋 ACTUAL GRAPH ({len(actual_triples)} triples):")
        lines.append("-" * 40)
        for s_a, p_a, o_a in sorted(actual_triples, key=lambda x: str(x[1])): # Renamed s,p,o
            status = "✅" if (s_a, p_a, o_a) in expected_set else "⚠️"
            lines.append(f"  {status} {self._format_triple(s_a, p_a, o_a)}")
        
        return "\n".join(lines)
    
    def _assert_triple_in_graph(self, graph, subject, predicate, obj, custom_msg=None):
        """Assert that a triple exists in the graph with better error messages"""
        triple = (subject, predicate, obj)
        if triple not in graph:
            msg = f"Expected triple not found: {self._format_triple(subject, predicate, obj)}\n"
            if custom_msg:
                msg += f"{custom_msg}\n"
            
            # Show comparison between expected and actual
            msg += self._compare_expected_vs_actual(graph, subject, [triple])
            self.fail(msg)
    
    def _assert_triple_not_in_graph(self, graph, subject, predicate, obj_pattern_val=None, custom_msg=None): # Renamed obj_pattern
        """Assert that no matching triple exists in the graph"""
        if obj_pattern_val is None: # Indicates checking for any object for this subject and predicate
            matching_triples = [(s, p, o) for s, p, o in graph if s == subject and p == predicate]
            if matching_triples:
                msg = f"Unexpected triples found with predicate {self._format_triple(subject, predicate, '...')}\n"
                if custom_msg:
                    msg += f"{custom_msg}\n"
                for s_match, p_match, o_match in matching_triples:
                    msg += f"  Found: {self._format_triple(s_match, p_match, o_match)}\n"
                self.fail(msg)
        else: # Check for a specific triple (subject, predicate, obj_pattern_val)
            triple_to_check = (subject, predicate, obj_pattern_val)
            if triple_to_check in graph:
                msg = f"Unexpected triple found: {self._format_triple(subject, predicate, obj_pattern_val)}\n"
                if custom_msg:
                    msg += f"{custom_msg}\n"
                msg += self._get_graph_summary(graph, subject)
                self.fail(msg)

    def _assert_triples_in_graph(self, graph, entity_uri, expected_triples, custom_msg=None):
        """Assert multiple triples exist in the graph with comprehensive comparison"""
        actual_triples = set((s, p, o) for s, p, o in graph if s == entity_uri)
        expected_set = set(expected_triples)
        
        missing = expected_set - actual_triples
        
        if missing:
            msg = f"Some expected triples are missing!\n"
            if custom_msg:
                msg += f"{custom_msg}\n"
            msg += self._compare_expected_vs_actual(graph, entity_uri, expected_triples)
            self.fail(msg)

    # Unittest-compatible assertion methods for better test readability
    def assertTripleExists(self, graph, subject, predicate, obj, msg=None):
        """Assert that a specific triple exists in the graph with detailed error message"""
        self._assert_triple_in_graph(graph, subject, predicate, obj, msg)
    
    def assertTripleNotExists(self, graph, subject, predicate, obj=None, msg=None):
        """Assert that a triple does not exist in the graph.
        If obj is None, asserts that no triple (subject, predicate, *) exists.
        Otherwise, asserts that the specific triple (subject, predicate, obj) does not exist.
        """
        if obj is None: # Check for any object for this subject and predicate
            self._assert_triple_not_in_graph(graph, subject, predicate, obj_pattern_val=None, custom_msg=msg)
        else: # Check for a specific triple
            self._assert_triple_not_in_graph(graph, subject, predicate, obj_pattern_val=obj, custom_msg=msg)

    def assertTripleCount(self, graph, subject, expected_count, msg=None):
        """Assert that the entity has the expected number of triples"""
        actual_triples = list(graph.triples((subject, None, None)))
        actual_count = len(actual_triples)
        if actual_count != expected_count:
            error_msg = f"\nExpected {expected_count} triples but found {actual_count}\n"
            error_msg += self._get_graph_summary(graph, subject)
            if msg:
                error_msg = f"{msg}\n{error_msg}"
            self.fail(error_msg)
    
    def assertGraphContainsExpectedTriples(self, graph, entity_uri, expected_triples, exact_match=False, msg=None):
        """
        Assert that the graph contains all expected triples for an entity.
        If exact_match=True, also asserts no extra triples exist.
        """
        missing_triples_list = [] # Renamed from missing_triples to avoid conflict
        for triple_item in expected_triples: # Renamed triple to triple_item
            s_item, p_item, o_item = triple_item # Renamed s,p,o
            if (s_item, p_item, o_item) not in graph:
                missing_triples_list.append(triple_item)
        
        actual_triples_list = list(graph.triples((entity_uri, None, None))) # Renamed actual_triples
        
        if missing_triples_list or (exact_match and len(actual_triples_list) != len(expected_triples)):
            error_msg = self._compare_expected_vs_actual(graph, entity_uri, expected_triples, missing_triples_list)
            if msg:
                error_msg = f"{msg}\n{error_msg}"
            
            if missing_triples_list:
                self.fail(f"Missing {len(missing_triples_list)} expected triples. {error_msg}")
            if exact_match and len(actual_triples_list) != len(expected_triples):
                self.fail(f"Expected exactly {len(expected_triples)} triples but found {len(actual_triples_list)}. {error_msg}")

    def test_kb_id_as_full_uri(self):
        person = KbPerson(kb_id="http://custom.uri/person/123", full_name="Full URI Person")
        graph = self.converter.kb_entity_to_graph(person, base_uri_str=self.base_uri)
        entity_uri = URIRef("http://custom.uri/person/123")
        
        # Use improved assertion methods
        self.assertTripleExists(graph, entity_uri, RDF.type, KB.Person)
        self.assertTripleExists(graph, entity_uri, KB.fullName, Literal("Full URI Person", datatype=XSD.string))

    def test_kb_id_appended_to_base_uri(self):
        person = KbPerson(kb_id="person/456", full_name="Appended URI Person")
        graph = self.converter.kb_entity_to_graph(person, base_uri_str=self.base_uri)
        entity_uri = URIRef(self.base_uri + "person/456")
        
        # Use improved assertion methods with descriptive messages
        self.assertTripleExists(graph, entity_uri, RDF.type, KB.Person, 
                               "Person should have correct RDF type")
        self.assertTripleExists(graph, entity_uri, KB.fullName, 
                               Literal("Appended URI Person", datatype=XSD.string),
                               "Person should have correct full name")

    def test_kb_person_serialization_all_fields(self):
        person = KbPerson(
            kb_id="person_001",
            label="John D.",
            source_document_uri="http://example.org/docs/doc1",
            # extracted_from_text_span is not directly mapped in KbBaseEntity
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

        expected_triples = [
            (entity_uri, RDF.type, KB.Entity),
            (entity_uri, RDF.type, KB.Person),
            (entity_uri, RDFS.label, Literal("John D.", datatype=XSD.string)),
            (entity_uri, KB.sourceDocument, URIRef("http://example.org/docs/doc1")),
            (entity_uri, SCHEMA.dateCreated, Literal(self.now, datatype=XSD.dateTime)),
            (entity_uri, SCHEMA.dateModified, Literal(self.now, datatype=XSD.dateTime)),
            (entity_uri, KB.fullName, Literal("John Doe", datatype=XSD.string)),
            (entity_uri, SCHEMA.givenName, Literal("John", datatype=XSD.string)),
            (entity_uri, SCHEMA.familyName, Literal("Doe", datatype=XSD.string)),
            (entity_uri, SCHEMA.alternateName, Literal("Johnny", datatype=XSD.string)),
            (entity_uri, SCHEMA.alternateName, Literal("JD", datatype=XSD.string)),
            (entity_uri, SCHEMA.email, Literal("john.doe@example.com", datatype=XSD.string)),
            (entity_uri, SCHEMA.roleName, Literal("Developer", datatype=XSD.string)),
            (entity_uri, SCHEMA.roleName, Literal("Lead", datatype=XSD.string))
        ]
        
        # Use the comprehensive assertion method that shows detailed comparison
        self.assertGraphContainsExpectedTriples(graph, entity_uri, expected_triples, 
                                               msg="Testing complete person serialization with all fields")

    def test_kb_person_serialization_minimal_fields(self):
        person = KbPerson(kb_id="person_002", full_name="Jane Minimal")
        graph = self.converter.kb_entity_to_graph(person, base_uri_str=self.base_uri)
        entity_uri = URIRef(self.base_uri + "person_002")

        self.assertTripleExists(graph, entity_uri, RDF.type, KB.Entity)
        self.assertTripleExists(graph, entity_uri, RDF.type, KB.Person)
        self.assertTripleExists(graph, entity_uri, KB.fullName, Literal("Jane Minimal", datatype=XSD.string)) 
        self.assertTripleExists(graph, entity_uri, RDFS.label, Literal("Jane Minimal", datatype=XSD.string))
        self.assertTripleNotExists(graph, entity_uri, SCHEMA.givenName) # Check no givenName triple exists

    def test_kb_todo_item_serialization_all_fields(self):
        due_date = datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        todo = KbTodoItem(
            kb_id="todo_001",
            label="Urgent Task",
            source_document_uri="http://example.org/docs/doc2",
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

        self.assertTripleExists(graph, entity_uri, RDF.type, KB.Entity)
        self.assertTripleExists(graph, entity_uri, RDF.type, KB.TodoItem)
        self.assertTripleExists(graph, entity_uri, RDF.type, SCHEMA.Action)

        self.assertTripleExists(graph, entity_uri, RDFS.label, Literal("Urgent Task", datatype=XSD.string))
        self.assertTripleExists(graph, entity_uri, KB.sourceDocument, URIRef("http://example.org/docs/doc2"))
        self.assertTripleExists(graph, entity_uri, SCHEMA.dateCreated, Literal(self.now, datatype=XSD.dateTime))
        self.assertTripleExists(graph, entity_uri, SCHEMA.dateModified, Literal(self.now, datatype=XSD.dateTime))
        self.assertTripleExists(graph, entity_uri, SCHEMA.description, Literal("Complete the project report.", datatype=XSD.string))
        self.assertTripleExists(graph, entity_uri, KB.isCompleted, Literal(False, datatype=XSD.boolean))
        self.assertTripleExists(graph, entity_uri, KB.dueDate, Literal(due_date, datatype=XSD.dateTime))
        self.assertTripleExists(graph, entity_uri, KB.priority, Literal("High", datatype=XSD.string))
        self.assertTripleExists(graph, entity_uri, KB.context, Literal("Project Alpha", datatype=XSD.string))
        self.assertTripleExists(graph, entity_uri, KB.assignee, URIRef(self.base_uri + "person_001"))
        self.assertTripleExists(graph, entity_uri, KB.assignee, URIRef("http://example.org/kb/person_002"))
        self.assertTripleExists(graph, entity_uri, KB.relatedProject, URIRef(self.base_uri + "project_alpha_id"))

    def test_kb_todo_item_serialization_minimal_fields(self):
        todo = KbTodoItem(kb_id="todo_002", description="Minimal todo item")
        graph = self.converter.kb_entity_to_graph(todo, base_uri_str=self.base_uri)
        entity_uri = URIRef(self.base_uri + "todo_002")

        self.assertTripleExists(graph, entity_uri, RDF.type, KB.Entity)
        self.assertTripleExists(graph, entity_uri, RDF.type, KB.TodoItem)
        self.assertTripleExists(graph, entity_uri, SCHEMA.description, Literal("Minimal todo item", datatype=XSD.string))
        self.assertTripleExists(graph, entity_uri, RDFS.label, Literal("Minimal todo item", datatype=XSD.string))
        self.assertTripleExists(graph, entity_uri, KB.isCompleted, Literal(False, datatype=XSD.boolean))
        self.assertTripleNotExists(graph, entity_uri, KB.dueDate) # Check no dueDate triple exists

    def test_optional_fields_none_not_in_graph(self):
        person = KbPerson(kb_id="person_003", full_name="Optional Test", email=None, given_name=None)
        graph = self.converter.kb_entity_to_graph(person, base_uri_str=self.base_uri)
        entity_uri = URIRef(self.base_uri + "person_003")

        self.assertTripleNotExists(graph, entity_uri, SCHEMA.email)
        self.assertTripleNotExists(graph, entity_uri, SCHEMA.givenName)
        self.assertTripleNotExists(graph, entity_uri, SCHEMA.roleName)
        self.assertTripleNotExists(graph, entity_uri, SCHEMA.alternateName)

    # --- Tests for KbDummyEntity ---

    def test_kb_dummy_entity_serialization(self):
        dummy = KbDummyEntity(
            kb_id="dummy_001",
            label="Explicit Dummy Label",
            source_document_uri="http://example.org/docs/dummy_doc",
            creation_timestamp=self.now,
            dummy_description="This is a dummy entity description.",
            dummy_related_item="http://example.org/related/other_dummy",
            dummy_keywords=["test", "dummy", "metadata"],
            dummy_see_also=["http://example.org/see/dummy1", "relative_dummy_id"],
            dummy_count=42
        )
        graph = self.converter.kb_entity_to_graph(dummy, base_uri_str=self.base_uri)
        entity_uri = URIRef(self.base_uri + "dummy_001")

        # Use the new comprehensive assertion method
        expected_triples = [
            (entity_uri, RDF.type, KB.Entity),
            (entity_uri, RDF.type, KB.DummyType),
            (entity_uri, RDFS.label, Literal("Explicit Dummy Label", datatype=XSD.string)),
            (entity_uri, KB.sourceDocument, URIRef("http://example.org/docs/dummy_doc")),
            (entity_uri, SCHEMA.dateCreated, Literal(self.now, datatype=XSD.dateTime)),
            (entity_uri, SCHEMA.description, Literal("This is a dummy entity description.", datatype=XSD.string)),
            (entity_uri, SCHEMA.relatedLink, URIRef("http://example.org/related/other_dummy")),
            (entity_uri, SCHEMA.keywords, Literal("test", datatype=XSD.string)),
            (entity_uri, SCHEMA.keywords, Literal("dummy", datatype=XSD.string)),
            (entity_uri, SCHEMA.keywords, Literal("metadata", datatype=XSD.string)),
            (entity_uri, RDFS.seeAlso, URIRef("http://example.org/see/dummy1")),
            (entity_uri, RDFS.seeAlso, URIRef(self.base_uri + "relative_dummy_id")),
            (entity_uri, KB.customValue, Literal(42, datatype=XSD.integer))
        ]
        
        self._assert_triples_in_graph(graph, entity_uri, expected_triples, 
                                    "Testing comprehensive dummy entity serialization")

    def test_kb_dummy_entity_label_fallback(self):
        # Test case 1: Fallback to dummy_description
        dummy1 = KbDummyEntity(kb_id="dummy_fb_1", dummy_description="Fallback from description.")
        graph1 = self.converter.kb_entity_to_graph(dummy1, base_uri_str=self.base_uri)
        entity_uri1 = URIRef(self.base_uri + "dummy_fb_1")
        self.assertTripleExists(graph1, entity_uri1, RDFS.label, 
                                Literal("Fallback from description.", datatype=XSD.string),
                                "Label should fallback to dummy_description.")

        # Test case 2: Fallback to explicit label field (which is also in rdfs_label_fallback_fields)
        dummy2 = KbDummyEntity(kb_id="dummy_fb_2", label="Fallback from explicit label field.")
        graph2 = self.converter.kb_entity_to_graph(dummy2, base_uri_str=self.base_uri)
        entity_uri2 = URIRef(self.base_uri + "dummy_fb_2")
        self.assertTripleExists(graph2, entity_uri2, RDFS.label, 
                                Literal("Fallback from explicit label field.", datatype=XSD.string),
                                "Label should use the explicit 'label' field.")

        # Test case 3: No explicit label, no dummy_description.
        # kb_id is NOT in rdfs_label_fallback_fields for KbDummyEntity.
        # Thus, no rdfs:label should be generated.
        dummy3 = KbDummyEntity(kb_id="dummy_fb_3")
        graph3 = self.converter.kb_entity_to_graph(dummy3, base_uri_str=self.base_uri)
        entity_uri3 = URIRef(self.base_uri + "dummy_fb_3")
        
        # Assert that no RDFS.label triple exists for entity_uri3
        self.assertTripleNotExists(graph3, entity_uri3, RDFS.label, 
                                   msg=(f"RDFS.label should not be present for {entity_uri3} when all configured "
                                        f"fallback fields (['dummy_description', 'label']) are None and "
                                        f"kb_id is not an explicit fallback in KbDummyEntity's config."))


    def test_kb_dummy_entity_minimal(self):
        dummy = KbDummyEntity(kb_id="dummy_minimal_001")
        graph = self.converter.kb_entity_to_graph(dummy, base_uri_str=self.base_uri)
        entity_uri = URIRef(self.base_uri + "dummy_minimal_001")
        
        expected_triples = [
            (entity_uri, RDF.type, KB.Entity),
            (entity_uri, RDF.type, KB.DummyType),
        ]
        
        for triple_to_check in expected_triples: # Renamed triple to triple_to_check
            self._assert_triple_in_graph(graph, *triple_to_check, f"Testing minimal dummy entity RDF types")

        should_not_exist_predicates = [
            SCHEMA.description,
            SCHEMA.relatedLink,
            SCHEMA.keywords,
            KB.customValue,
        ]
        
        for predicate_to_check in should_not_exist_predicates: # Renamed predicate to predicate_to_check
            self.assertTripleNotExists(graph, entity_uri, predicate_to_check,
                                       msg=f"Unexpected property {self._format_triple(entity_uri, predicate_to_check, '...')} found.")
        
        self.assertTripleNotExists(graph, entity_uri, RDFS.label,
                                   msg="RDFS.label should not be present for minimal KbDummyEntity due to its specific fallback config.")


if __name__ == '__main__':
    unittest.main()