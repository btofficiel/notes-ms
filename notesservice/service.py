# Importing modules
import time
import jsonschema
from typing import Dict, Mapping
import logging
import uuid
from notesservice.database.db_engines import create_notes_db
from notesservice import NOTES_SCHEMA
from notesservice.datamodel import Note


# Creating NotesService class
class NotesService:
    def __init__(
        self,
        config: Dict,
        logger: logging.Logger
    ) -> None:
        self.notes_db = create_notes_db(config['notes-db'])
        self.logger = logger
        self.notes = {}

    def start(self):
        pass

    def stop(self):
        pass

    def _generate_id(self) -> str:
        # Generate UUID string
        _id = uuid.uuid4().hex
        return _id

    def _generate_note(self, id_: str, ts: int, value: Dict) -> Dict:
        note = {
            "id": id_,
            "title": value["title"],
            "body": value["body"],
            "note_type": value["note_type"],
            "updated_on": ts
        }

        return note

    def validate_note(self, note: Mapping) -> None:
        try:
            jsonschema.validate(note, NOTES_SCHEMA)
        except jsonschema.exceptions.ValidationError:
            raise ValueError('JSON Schema validation failed')

    async def get_notes(self) -> list:
        async for id_, note in self.notes_db.read_all_notes():
            yield id_, note.to_api_dm()

    async def create_note(self, value: Dict) -> Dict:
        # Validate payload
        self.validate_note(value)

        # Generate unique id
        id_ = self._generate_id()

        # Fetch timestamp
        now_ts = int(time.time())

        # Generate note
        note_ = self._generate_note(id_, now_ts, value)

        note = Note.from_api_dm(note_)

        # Store note
        key = await self.notes_db.create_note(note, id_)

        return key

    async def get_note(self, note_id: str) -> Dict:
        # Return note with a note id
        note = await self.notes_db.read_note(note_id)
        return note.to_api_dm()

    async def update_note(self, note_id: str, value: Dict) -> None:
        # Validate payload
        self.validate_note(value)
        # Fetch timestanp`
        now_ts = int(time.time())

        # Generate note
        note_ = self._generate_note(note_id, now_ts, value)

        note = Note.from_api_dm(note_)

        # Update note with the generated note
        await self.notes_db.update_note(note_id, note)

    async def delete_note(self, note_id: str) -> None:
        # Remove note with note id
        await self.notes_db.delete_note(note_id)
