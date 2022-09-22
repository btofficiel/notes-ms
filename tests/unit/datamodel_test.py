import unittest
import time
import uuid

from notesservice.datamodel import (Note, NoteType)


class DataModelTest(unittest.TestCase):
    def test_data_model(self) -> None:
        id = uuid.uuid4().hex
        ts = int(time.time())
        note = Note(
            id=id,
            title="Note",
            body="Note Body",
            note_type=NoteType["personal"],
            updated_on=ts
        )

        self.assertEqual(note.id, id)
        self.assertEqual(note.title, "Note")
        self.assertEqual(note.body, "Note Body")
        self.assertEqual(note.note_type, NoteType.personal)
        self.assertEqual(note.updated_on, ts)

        with self.assertRaises(ValueError):
            Note(
                id=None,
                title="Note",
                body="Note Body",
                note_type=NoteType["personal"],
                updated_on=ts
            )

        with self.assertRaises(ValueError):
            Note(
                id=id,
                title=None,
                body="Note Body",
                note_type=NoteType["personal"],
                updated_on=ts
            )

        with self.assertRaises(ValueError):
            Note(
                id=id,
                title="Note",
                body=None,
                note_type=NoteType["personal"],
                updated_on=ts
            )

        with self.assertRaises(ValueError):
            Note(
                id=id,
                title="Note",
                body="Note Body",
                note_type=None,
                updated_on=ts
            )

        with self.assertRaises(ValueError):
            Note(
                id=id,
                title="Note",
                body="Note Body",
                note_type=NoteType["personal"],
                updated_on=None
            )

        with self.assertRaises(ValueError):
            note.id = None

        with self.assertRaises(ValueError):
            note.title = None

        with self.assertRaises(ValueError):
            note.body = None

        with self.assertRaises(ValueError):
            note.note_type = None

        with self.assertRaises(ValueError):
            note.updated_on = None


if __name__ == '__main__':
    unittest.main()
