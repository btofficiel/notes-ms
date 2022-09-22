# Copyright (c) 2020. All rights reserved.

from abc import ABCMeta, abstractmethod
import asynctest  # type: ignore
from io import StringIO
import os
import subprocess
import tempfile
from typing import Dict
import unittest
import yaml

from notesservice.database.notes_db import (
    AbstractNotesDB,
    InMemoryNotesDB,
    FilesystemNotesDB,
    SQLiteNotesDB
)
from notesservice.database.db_engines import create_notes_db
from notesservice.datamodel import Note
from tests.integration.notesservice_test import run_coroutine

from data import notes_data_suite


class AbstractNotesDBTest(unittest.TestCase):
    def read_config(self, txt: str) -> Dict:
        with StringIO(txt) as f:
            cfg = yaml.load(f.read(), Loader=yaml.SafeLoader)
        return cfg

    def test_in_memory_db_config(self):
        cfg = self.read_config('''
notes-db:
  memory: null
        ''')

        self.assertIn('memory', cfg['notes-db'])
        db = create_notes_db(cfg['notes-db'])
        self.assertEqual(type(db), InMemoryNotesDB)

    def test_file_system_db_config(self):
        cfg = self.read_config('''
notes-db:
  fs: /tmp
        ''')

        self.assertIn('fs', cfg['notes-db'])
        db = create_notes_db(cfg['notes-db'])
        self.assertEqual(type(db), FilesystemNotesDB)
        self.assertEqual(db.store, '/tmp')

    def test_sqlite_db_config(self):
        cfg = self.read_config('''
notes-db:
  sql: ./tests/tmp/store.db
        ''')

        self.assertIn('sql', cfg['notes-db'])
        db = create_notes_db(cfg['notes-db'])
        self.assertEqual(type(db), SQLiteNotesDB)
        self.assertEqual(db.store, './tests/tmp/store.db')


class AbstractNotesDBTestCase(metaclass=ABCMeta):
    def setUp(self) -> None:
        self.notes_data = {
            k: Note.from_api_dm(v)
            for k, v in notes_data_suite().items()
        }
        self.notes_db = self.make_notes_db()
        run_coroutine(self.notes_db._clear())

    @abstractmethod
    def make_notes_db(self) -> AbstractNotesDB:
        raise NotImplementedError()

    @abstractmethod
    async def notes_count(self) -> int:
        raise NotImplementedError()

    @asynctest.fail_on(active_handles=True)
    async def test_crud_lifecycle(self) -> None:
        # Nothing in the database
        for id in self.notes_data:
            with self.assertRaises(KeyError):  # type: ignore
                await self.notes_db.read_note(id)

        # Create then Read, again Create(fail)
        for id, note in self.notes_data.items():
            await self.notes_db.create_note(note, id)
            await self.notes_db.read_note(id)
            with self.assertRaises(KeyError):  # type: ignore
                await self.notes_db.create_note(note, id)

        self.assertEqual(await self.notes_count(), 2)  # type: ignore

        # First data in test set
        first_id = list(self.notes_data.keys())[0]
        first_note = self.notes_data[first_id]

        # Update
        await self.notes_db.update_note(first_id, first_note)
        with self.assertRaises(KeyError):  # type: ignore
            await self.notes_db.update_note('does not exist', first_note)

        # Create without giving id
        new_id = await self.notes_db.create_note(note)
        self.assertIsNotNone(new_id)  # type: ignore
        self.assertEqual(await self.notes_count(), 3)  # type: ignore

        # Get All Notes
        notes = {}
        async for id, note in self.notes_db.read_all_notes():
            notes[id] = note

        self.assertEqual(len(notes), 3)  # type: ignore

        # Delete then Read, and the again Delete
        for id in self.notes_data:
            await self.notes_db.delete_note(id)
            with self.assertRaises(KeyError):  # type: ignore
                await self.notes_db.read_note(id)
            with self.assertRaises(KeyError):  # type: ignore
                await self.notes_db.delete_note(id)

        self.assertEqual(await self.notes_count(), 1)  # type: ignore

        await self.notes_db.delete_note(new_id)
        self.assertEqual(await self.notes_count(), 0)  # type: ignore


class InMemoryNotesDBTest(
    AbstractNotesDBTestCase,
    asynctest.TestCase
):
    def make_notes_db(self) -> AbstractNotesDB:
        self.mem_db = InMemoryNotesDB()
        return self.mem_db

    async def notes_count(self) -> int:
        return len(self.mem_db.db)


class FilesystemNotesDBTest(
    AbstractNotesDBTestCase,
    asynctest.TestCase
):
    def make_notes_db(self) -> AbstractNotesDB:
        self.tmp_dir = tempfile.TemporaryDirectory(prefix='notesbook-fsdb')
        self.store_dir = self.tmp_dir.name
        self.fs_db = FilesystemNotesDB(self.store_dir)
        return self.fs_db

    async def notes_count(self) -> int:
        return len([
            name for name in os.listdir(self.store_dir)
            if os.path.isfile(os.path.join(self.store_dir, name))
        ])

    def tearDown(self):
        self.tmp_dir.cleanup()
        super().tearDown()

    async def test_db_creation(self):
        with tempfile.TemporaryDirectory(prefix='notesbook-fsdb') as tempdir:
            store_dir = os.path.join(tempdir, 'abc')
            FilesystemNotesDB(store_dir)
            tmpfilename = os.path.join(tempdir, 'xyz.txt')
            with open(tmpfilename, 'w') as f:
                f.write('this is a file and not a dir')
            with self.assertRaises(ValueError):
                FilesystemNotesDB(tmpfilename)


class SQLiteNotesDBTest(
    AbstractNotesDBTestCase,
    asynctest.TestCase
):
    def make_notes_db(self) -> AbstractNotesDB:
        self.db_path = "./tests/tmp/store.db"
        self.sql_db = SQLiteNotesDB(self.db_path)
        run_coroutine(self.sql_db.start())
        return self.sql_db

    async def notes_count(self) -> int:
        count = 0
        async for id_, note in self.sql_db.read_all_notes():
            count += 1

        return count

    def remove_db(self) -> None:
        cmd = "rm -rf {0}".format(self.db_path)
        subprocess.check_output(cmd, shell=True)

    def tearDown(self):
        run_coroutine(self.sql_db.stop())
        self.remove_db()
        super().tearDown()

    async def test_db_creation(self):
        self.assertTrue(os.path.isfile(self.db_path))


if __name__ == '__main__':
    unittest.main()
