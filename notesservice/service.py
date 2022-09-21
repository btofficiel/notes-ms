# Importing modules
import time
from typing import Dict
import uuid


# Creating NotesService class
class NotesService:
    def __init__(self, config: Dict):
        self.notes = {}

    def start(self):
        pass

    def stop(self):
        pass

    def _generate_id(self) -> str:
        # Generate UUID string
        _id = uuid.uuid4().hex
        return _id

    async def get_notes(self) -> list:
        notes = []

        # Retrieve self.notes as a list of notes
        for key in self.notes:
            note = self.notes.get(key)
            notes.append(note)
        return notes

    def _generate_note(self, id_: str, ts: int, value: Dict) -> Dict:
        note = {
            "id": id_,
            "title": value["title"],
            "body": value["body"],
            "note_type": value["note_type"],
            "updated_on": ts
        }

        return note

    async def create_note(self, value: Dict) -> Dict:
        # Generate unique id
        id_ = self._generate_id()

        # Fetch timestamp
        now_ts = int(time.time())

        # Generate note
        note = self._generate_note(id_, now_ts, value)

        # Store note
        self.notes[id_] = note

        return id_

    async def get_note(self, note_id: str) -> Dict:
        # Return note with a note id
        return self.notes[note_id]

    async def update_note(self, note_id: str, value: Dict) -> None:
        # Throws an error if not found
        self.notes[note_id]

        # Fetch timestanp`
        now_ts = int(time.time())

        # Generate note
        note = self._generate_note(note_id, now_ts, value)

        # Update note with the generated note
        self.notes[note_id] = note

    async def delete_note(self, note_id: str) -> None:
        # Check if note_id exists
        self.notes[note_id]

        # Remove note with note id
        del self.notes[note_id]
