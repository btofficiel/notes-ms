from abc import ABCMeta, abstractmethod
import aiofiles  # type: ignore
import aiosqlite
import json
import os
import subprocess
from typing import AsyncIterator, Dict, Mapping, Tuple
import uuid

from notesservice.datamodel import Note


class AbstractNotesDB(metaclass=ABCMeta):
    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def stop(self):
        pass

    @abstractmethod
    async def _clear(self):
        pass

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

    async def start(self):
        pass

    async def stop(self):
        pass

    async def _clear(self):
        self.db = {}

    async def create_note(
        self,
        note: Note,
        id_: str = None
    ) -> str:
        if id_ is None:
            id_ = uuid.uuid4().hex

        if id_ in self.db:
            raise KeyError('{} already exists'.format(id_))

        self.db[id_] = note
        return id_

    async def read_note(self, id_: str) -> Note:
        return self.db[id_]

    async def update_note(self, id_: str, note: Note) -> None:
        if id_ is None or id_ not in self.db:
            raise KeyError('{} does not exist'.format(id_))

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

    async def start(self):
        pass

    async def stop(self):
        pass

    async def _clear(self):
        cmd = "rm -rf {0}/*".format(self.store)
        subprocess.check_output(cmd, shell=True)

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


class SQLiteNotesDB(AbstractNotesDB):
    def __init__(self, db_file_path: str):
        self._store = db_file_path
        self._connection = None

    @property
    def connection(self) -> aiosqlite.core.Connection:
        return self._connection

    @connection.setter
    def connection(self, conn: aiosqlite.core.Connection) -> None:
        self._connection = conn

    @property
    def store(self) -> str:
        return self._store

    @store.setter
    def store(self, store_path: str) -> None:
        self._store = store_path

    async def start(self):
        self.connection = await aiosqlite.connect(self.store)

        query = '''
        CREATE TABLE IF NOT EXISTS notes (
            id varchar(32) PRIMARY KEY,
            title varchar NOT NULL,
            body varchar NOT NULL DEFAULT '',
            note_type varchar
                CHECK( note_type IN ('personal', 'work') )
                NOT NULL,
            updated_on bigint DEFAULT 0
        );
        '''
        await self.connection.execute(query)
        await self.connection.commit()

    async def stop(self):
        await self.connection.close()

    async def _clear(self):
        query = "DELETE FROM notes;"
        await self.connection.execute(query)
        await self.connection.commit()

    async def create_note(
        self,
        note: Note,
        id_: str = None
    ) -> str:
        if id_:
            exists = await self._check_if_exists(note.id)

            if exists:
                raise KeyError("A note exists already with the given ID")

        new_note = [v for k, v in note.to_api_dm().items()]

        if not id_:
            new_note[0] = uuid.uuid4().hex

        query = '''
            INSERT INTO notes VALUES($1,$2,$3,$4,$5)
            ;
        '''

        await self.connection.execute(query, new_note)
        await self.connection.commit()

        return new_note[0]

    def dict_from_tuple(self, record):
        return {
            "id": record[0],
            "title": record[1],
            "body": record[2],
            "note_type": record[3],
            "updated_on": record[4]
        }

    async def read_note(self, id_: str) -> Note:
        exists = await self._check_if_exists(id_)

        if not exists:
            raise KeyError("No note found with given ID")

        query = '''
            SELECT * FROM notes
            WHERE id=$1
            ;
        '''

        result = {}

        cursor = await self.connection.execute(query, [id_])
        row = await cursor.fetchone()
        await cursor.close()
        result = self.dict_from_tuple(row)

        return Note.from_api_dm(result)

    async def _check_if_exists(self, id_: str) -> bool:
        query = '''
            SELECT * FROM notes
            WHERE id=$1
            ;
        '''

        cursor = await self.connection.execute(query, [id_])
        row = await cursor.fetchone()
        await cursor.close()

        if row:
            return True
        else:
            return False

    async def update_note(self, id_: str, note: Note) -> None:
        exists = await self._check_if_exists(id_)

        if not exists:
            raise KeyError("No note found with given ID")

        new_note = [v for k, v in note.to_api_dm().items()]

        query = '''
            UPDATE notes
            SET
            id=$1,
            title=$2,
            body=$3,
            note_type=$4,
            updated_on=$5
            WHERE id=$1
            ;
        '''

        await self.connection.execute(query, new_note)
        await self.connection.commit()

    async def delete_note(self, id_: str) -> None:
        exists = await self._check_if_exists(id_)

        if not exists:
            raise KeyError("No note found with given ID")

        query = '''
            DELETE FROM notes
            WHERE id=$1
        '''

        await self.connection.execute(query, [id_])
        await self.connection.commit()

    async def read_all_notes(self) -> AsyncIterator[Tuple[str, Note]]:
        query = '''
            SELECT * FROM notes;
        '''

        cursor = await self.connection.execute(query)
        rows = await cursor.fetchall()
        await cursor.close()

        notes = list(map(self.dict_from_tuple, rows))

        for note in notes:
            yield note["id"], Note.from_api_dm(note)
