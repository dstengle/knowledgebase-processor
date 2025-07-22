import unittest
from datetime import datetime, timezone, date, timedelta # Added timedelta

from pydantic import ValidationError

from knowledgebase_processor.models.kb_entities import KbBaseEntity, KbPerson, KbTodoItem

class TestKbEntities(unittest.TestCase):
    def test_kb_base_entity_all_fields(self):
        now = datetime.now(timezone.utc)
        entity = KbBaseEntity(
            kb_id="test_id",
            creation_timestamp=now,
            last_modified_timestamp=now,
            label="Test Label",
            source_document_uri="doc_uri_1",
            extracted_from_text_span=(0, 10)
        )
        self.assertEqual(entity.kb_id, "test_id")
        self.assertEqual(entity.creation_timestamp, now)
        self.assertEqual(entity.last_modified_timestamp, now)
        self.assertEqual(entity.label, "Test Label")
        self.assertEqual(entity.source_document_uri, "doc_uri_1")
        self.assertEqual(entity.extracted_from_text_span, (0, 10))

    def test_kb_base_entity_default_timestamps(self):
        entity = KbBaseEntity(kb_id="test_id_defaults")
        self.assertIsNotNone(entity.creation_timestamp)
        self.assertIsNotNone(entity.last_modified_timestamp)
        self.assertLessEqual(entity.creation_timestamp, datetime.now(timezone.utc))
        self.assertLessEqual(entity.last_modified_timestamp, datetime.now(timezone.utc))
        # Timestamps should be very close, if not identical
        self.assertAlmostEqual(entity.creation_timestamp, entity.last_modified_timestamp, delta=timedelta(seconds=1)) # Corrected to timedelta

    def test_kb_base_entity_minimal_fields(self):
        entity = KbBaseEntity(kb_id="minimal_id")
        self.assertEqual(entity.kb_id, "minimal_id")
        self.assertIsNotNone(entity.creation_timestamp)
        self.assertIsNotNone(entity.last_modified_timestamp)
        self.assertIsNone(entity.label)
        self.assertIsNone(entity.source_document_uri)
        self.assertIsNone(entity.extracted_from_text_span)

    def test_kb_person_all_fields(self):
        now = datetime.now(timezone.utc)
        person = KbPerson(
            kb_id="person_001",
            full_name="John Doe",
            given_name="John",
            family_name="Doe",
            aliases=["Johnny", "JD"],
            email="john.doe@example.com",
            roles=["Developer"],
            creation_timestamp=now,
            last_modified_timestamp=now
        )
        self.assertEqual(person.kb_id, "person_001")
        self.assertEqual(person.full_name, "John Doe")
        self.assertEqual(person.given_name, "John")
        self.assertEqual(person.family_name, "Doe")
        self.assertEqual(person.aliases, ["Johnny", "JD"])
        self.assertEqual(person.email, "john.doe@example.com")
        self.assertEqual(person.roles, ["Developer"])
        self.assertEqual(person.creation_timestamp, now)
        self.assertEqual(person.last_modified_timestamp, now)

    def test_kb_person_optional_fields_omitted(self):
        person = KbPerson(
            kb_id="person_002"
            # full_name is optional, so omitting it for this test of other optionals
        )
        self.assertEqual(person.kb_id, "person_002")
        self.assertIsNone(person.full_name)
        self.assertIsNone(person.given_name)
        self.assertIsNone(person.family_name)
        self.assertIsNone(person.aliases)
        self.assertIsNone(person.email)
        self.assertIsNone(person.roles)
        self.assertIsNotNone(person.creation_timestamp)
        self.assertIsNotNone(person.last_modified_timestamp)

    def test_kb_todo_item_all_fields(self):
        now = datetime.now(timezone.utc)
        due = datetime(2025, 12, 31, 10, 30, 0, tzinfo=timezone.utc) # Corrected to datetime
        todo = KbTodoItem(
            kb_id="todo_001",
            description="Finish report",
            is_completed=False,
            due_date=due,
            priority="high",
            context="Annual review",
            assigned_to_uris=["http://example.org/kb/person_001", "person_002"],
            related_project_uri="http://example.org/kb/project_alpha",
            creation_timestamp=now,
            last_modified_timestamp=now
        )
        self.assertEqual(todo.kb_id, "todo_001")
        self.assertEqual(todo.description, "Finish report")
        self.assertFalse(todo.is_completed)
        self.assertEqual(todo.due_date, due)
        self.assertEqual(todo.priority, "high")
        self.assertEqual(todo.context, "Annual review")
        self.assertEqual(todo.assigned_to_uris, ["http://example.org/kb/person_001", "person_002"])
        self.assertEqual(todo.related_project_uri, "http://example.org/kb/project_alpha")
        self.assertEqual(todo.creation_timestamp, now)
        self.assertEqual(todo.last_modified_timestamp, now)

    def test_kb_todo_item_optional_fields_omitted_and_default_is_completed(self):
        todo = KbTodoItem(
            kb_id="todo_002",
            description="Follow up email"
        )
        self.assertEqual(todo.kb_id, "todo_002")
        self.assertEqual(todo.description, "Follow up email")
        self.assertFalse(todo.is_completed) # Default value
        self.assertIsNone(todo.due_date)
        self.assertIsNone(todo.priority)
        self.assertIsNone(todo.context)
        self.assertIsNone(todo.assigned_to_uris)
        self.assertIsNone(todo.related_project_uri)
        self.assertIsNotNone(todo.creation_timestamp)
        self.assertIsNotNone(todo.last_modified_timestamp)

    def test_pydantic_validation_base_entity_missing_required(self):
        with self.assertRaises(ValidationError) as context:
            KbBaseEntity() # kb_id is required
        self.assertIn("kb_id", str(context.exception).lower())

    # test_pydantic_validation_person_missing_required removed as full_name is Optional

    def test_pydantic_validation_todo_item_missing_required(self):
        with self.assertRaises(ValidationError) as context:
            KbTodoItem(kb_id="todo_missing_desc") # description is required
        self.assertIn("description", str(context.exception).lower())

    def test_pydantic_validation_incorrect_type(self):
        with self.assertRaises(ValidationError) as context:
            KbBaseEntity(kb_id="type_error_ts", creation_timestamp="not-a-datetime")
        self.assertIn("creation_timestamp", str(context.exception).lower())

        with self.assertRaises(ValidationError) as context:
            KbTodoItem(kb_id="type_error_todo_completed", description="Test", is_completed="not-a-boolean")
        self.assertIn("is_completed", str(context.exception).lower())

        with self.assertRaises(ValidationError) as context:
            KbTodoItem(kb_id="type_error_todo_due", description="Test", due_date="not-a-datetime")
        self.assertIn("due_date", str(context.exception).lower())

if __name__ == '__main__':
    unittest.main()