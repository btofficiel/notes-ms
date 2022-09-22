from abc import ABCMeta, abstractmethod
import aiofiles  # type: ignore
import json
import os
from typing import AsyncIterator, Dict, Mapping, Tuple
import uuid

from notesservice.datamodel import Note


class AbstractNotesDB(metaclass=ABCMeta):
    def start(self):
        pass

    def stop(self):
        pass

    # CRUD

    @abstractmethod
    async def create_note(
        self,
        note: Note,
        id_: str = None
    ) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def read_note(self, id_: str) -> Note:
        raise NotImplementedError()

    @abstractmethod
    async def update_note(self, id_: str, note: Note) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def delete_note(self, id_: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def read_all_notes(self) -> AsyncIterator[Tuple[str, Note]]:
        raise NotImplementedError()


class InMemoryNotesDB(AbstractNotesDB):
    def __init__(self):
        self.db: Dict[str, Note] = {}

    async def create_note(
        self,
        note: Note,
        id_: str = None
    ) -> str:
        if id_ is None:
            id_ = uuid.uuid_4().hex

        if id_ in self.db:
            raise KeyError('{} already exists'.format(id_))

        self.db[id_] = note
        return id_

    async def read_note(self, id_: str) -> Note:
        return self.db[id_]

    async def update_note(self, id_: str, note: Note) -> None:
        if id_ is None or id_ not in self.db:
            raise KeyError('{} does not exist'.format(id_))

        print(note.title)

        self.db[id_] = note

    async def delete_note(self, id_: str) -> None:
        if id_ is None or id_ not in self.db:
            raise KeyError('{} does not exist'.format(id_))

        del self.db[id_]

    async def read_all_notes(
        self
    ) -> AsyncIterator[Tuple[str, Note]]:
        for id_, note in self.db.items():
            yield id_, note


class FilesystemNotesDB(AbstractNotesDB):
    def __init__(self, store_dir_path: str):
        store_dir = os.path.abspath(store_dir_path)
        if not os.path.exists(store_dir):
            os.makedirs(store_dir)
        if not (os.path.isdir(store_dir) and os.access(store_dir, os.W_OK)):
            raise ValueError(
                'String store "{}" is not a writable directory'.format(
                    store_dir
                )
            )
        self._store = store_dir

    @property
    def store(self) -> str:
        return self._store

    def _file_name(self, id_: str) -> str:
        return os.path.join(
            self.store,
            id_ + '.json'
        )

    def _file_exists(self, id_: str) -> bool:
        return os.path.exists(self._file_name(id_))

    async def _file_read(self, id_: str) -> Dict:
        try:
            async with aiofiles.open(
                self._file_name(id_),
                encoding='utf-8',
                mode='r'
            ) as f:
                contents = await f.read()
                return json.loads(contents)
        except FileNotFoundError:
            raise KeyError(id_)

    async def _file_write(self, id_: str, note: Mapping) -> None:
        async with aiofiles.open(
            self._file_name(id_),
            mode='w',
            encoding='utf-8'
        ) as f:
            await f.write(json.dumps(note))

    async def _file_delete(self, id_: str) -> None:
        os.remove(self._file_name(id_))

    async def _file_read_all(self) -> AsyncIterator[Tuple[str, Dict]]:
        all_files = os.listdir(self.store)
        extn_end = '.json'
        extn_len = len(extn_end)
        for f in all_files:
            if f.endswith(extn_end):
                id_ = f[:-extn_len]
                note = await self._file_read(id_)
                yield id_, note

    async def create_note(
        self,
        note: Note,
        id_: str = None
    ) -> str:
        if id_ is None:
            id_ = uuid.uuid4().hex

        if self._file_exists(id_):
            raise KeyError('{} already exists'.format(id_))

        await self._file_write(id_, note.to_api_dm())
        return id_

    async def read_note(self, id_: str) -> Note:
        note = await self._file_read(id_)
        return Note.from_api_dm(note)

    async def update_note(self, id_: str, note: Note) -> None:
        if self._file_exists(id_):
            await self._file_write(id_, note.to_api_dm())
        else:
            raise KeyError(id_)

    async def delete_note(self, id_: str) -> None:
        if self._file_exists(id_):
            await self._file_delete(id_)
        else:
            raise KeyError(id_)

    async def read_all_notes(
        self
    ) -> AsyncIterator[Tuple[str, Note]]:
        async for id_, note in self._file_read_all():
            yield id_, Note.from_api_dm(note)
