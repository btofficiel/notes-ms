from enum import Enum, unique
from typing import (
    Any,
    Mapping
)


VALUE_ERR_MSG = '{} has invalid value {}'


@unique
class NoteType(Enum):
    personal = 1
    work = 2


class Note:
    def __init__(
        self,
        id: str,
        title: str,
        body: str,
        note_type: NoteType,
        updated_on: int
    ):
        if id is None:
            raise ValueError(VALUE_ERR_MSG.format("id", id))
        if title is None:
            raise ValueError(VALUE_ERR_MSG.format("title", title))
        if body is None:
            raise ValueError(VALUE_ERR_MSG.format("body", body))
        if note_type is None:
            raise ValueError(VALUE_ERR_MSG.format("note_type", note_type))
        if updated_on is None:
            raise ValueError(VALUE_ERR_MSG.format("updated_on", updated_on))

        self._id = id
        self._title = title
        self._body = body
        self._note_type = note_type
        self._updated_on = updated_on

    @property
    def id(self) -> str:
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        if not value:
            raise ValueError(VALUE_ERR_MSG.format('value', value))

        self._id = value

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        if not value:
            raise ValueError(VALUE_ERR_MSG.format('value', value))

        self._title = value

    @property
    def body(self) -> str:
        return self._body

    @body.setter
    def body(self, value: str) -> None:
        if not value:
            raise ValueError(VALUE_ERR_MSG.format('value', value))

        self._body = value

    @property
    def note_type(self) -> NoteType:
        return self._note_type

    @note_type.setter
    def note_type(self, value: NoteType) -> None:
        if not value:
            raise ValueError(VALUE_ERR_MSG.format('value', value))

        self._note_type = value

    @property
    def updated_on(self) -> int:
        return self._updated_on

    @updated_on.setter
    def updated_on(self, value: int) -> None:
        if not value:
            raise ValueError(VALUE_ERR_MSG.format('value', value))

        self._updated_on = value

    @classmethod
    def from_api_dm(cls, vars: Mapping[str, Any]) -> 'Note':
        return Note(
            id=vars["id"],
            title=vars["title"],
            body=vars["body"],
            note_type=NoteType[vars["note_type"]],
            updated_on=vars["updated_on"]
        )

    def to_api_dm(self) -> Mapping[str, Any]:
        d = {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "note_type": self.note_type.name,
            "updated_on": self.updated_on
        }

        return {k: v for k, v in d.items() if v is not None}
