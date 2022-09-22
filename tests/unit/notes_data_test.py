import jsonschema  # type: ignore
import unittest

from notesservice import NOTES_SCHEMA
from data import notes_data_suite
import notesservice.datamodel as datamodel


class NoteDataTest(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.notes_data = notes_data_suite()

    def test_json_schema(self) -> None:
        # Validate Note Schema
        jsonschema.Draft7Validator.check_schema(NOTES_SCHEMA)

    def test_notes_data_json(self) -> None:
        # Validate Note Test Data
        for id, note in self.notes_data.items():
            # validate using application subschema
            jsonschema.validate(note, NOTES_SCHEMA)

            # Roundrtrip Test
            note_obj = datamodel.Note.from_api_dm(note)
            note_dict = note_obj.to_api_dm()
            self.assertEqual(note, note_dict)


if __name__ == '__main__':
    unittest.main()
