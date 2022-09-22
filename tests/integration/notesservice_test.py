# Copyright (c) 2020. All rights reserved.

import asynctest  # type: ignore
import aiotask_context as context  # type: ignore
from io import StringIO
import logging
import logging.config
import unittest
import asyncio
import yaml

from notesservice import LOGGER_NAME
from notesservice.datamodel import Note
from notesservice.service import NotesService
from data import notes_data_suite


def run_coroutine(coro):
    asyncio.get_event_loop().set_task_factory(context.task_factory)
    return asyncio.get_event_loop().run_until_complete(coro)


IN_MEMORY_CFG_TXT = '''
service:
  name: Notes

notes-db:
  memory: null

logging:
  version: 1
  root:
    level: ERROR
'''

with StringIO(IN_MEMORY_CFG_TXT) as f:
    TEST_CONFIG = yaml.load(f.read(), Loader=yaml.SafeLoader)


class NotesServiceWithInMemoryDBTest(asynctest.TestCase):
    def setUp(self) -> None:
        logging.config.dictConfig(TEST_CONFIG['logging'])
        logger = logging.getLogger(LOGGER_NAME)

        self.service = NotesService(
            config=TEST_CONFIG,
            logger=logger
        )
        self.service.start()

        self.notes_data = notes_data_suite()
        run_coroutine(self.service.notes_db._clear())
        for id, val in self.notes_data.items():
            notes = Note.from_api_dm(val)
            run_coroutine(self.service.notes_db.create_note(notes, id))

    def tearDown(self) -> None:
        run_coroutine(self.service.notes_db._clear())
        self.service.stop()

    def test_get_note(self) -> None:
        for id, note in self.notes_data.items():
            value = run_coroutine(self.service.get_note(id))
            self.assertEqual(note, value)

    @asynctest.fail_on(active_handles=True)
    async def test_get_all_notes(self) -> None:
        all_notes = {}
        async for id, note in self.service.get_notes():
            all_notes[id] = note
        self.assertEqual(len(all_notes), 2)

    def test_crud_notes(self) -> None:
        ids = list(self.notes_data.keys())
        self.assertGreaterEqual(len(ids), 2)

        note0 = self.notes_data[ids[0]]
        key = run_coroutine(self.service.create_note(note0))
        val = run_coroutine(self.service.get_note(key))
        self.assertEqual(note0["title"], val["title"])
        self.assertEqual(note0["body"], val["body"])
        self.assertEqual(note0["note_type"], val["note_type"])

        note1 = self.notes_data[ids[1]]
        run_coroutine(self.service.update_note(key, note1))
        val = run_coroutine(self.service.get_note(key))
        self.assertEqual(note1["title"], val["title"])
        self.assertEqual(note1["body"], val["body"])
        self.assertEqual(note1["note_type"], val["note_type"])

        run_coroutine(self.service.delete_note(key))

        with self.assertRaises(KeyError):
            run_coroutine(self.service.get_note(key))


IN_FS_CFG_TXT = '''
service:
  name: Notes

notes-db:
  fs: ./tests/dump

logging:
  version: 1
  root:
    level: ERROR
'''

with StringIO(IN_FS_CFG_TXT) as f_fs:
    FS_TEST_CONFIG = yaml.load(f_fs.read(), Loader=yaml.SafeLoader)


class NotesServiceWithFilesystemDBTest(asynctest.TestCase):
    def setUp(self) -> None:
        logging.config.dictConfig(FS_TEST_CONFIG['logging'])
        logger = logging.getLogger(LOGGER_NAME)

        self.service = NotesService(
            config=FS_TEST_CONFIG,
            logger=logger
        )
        self.service.start()

        self.notes_data = notes_data_suite()
        run_coroutine(self.service.notes_db._clear())
        for id, val in self.notes_data.items():
            notes = Note.from_api_dm(val)
            run_coroutine(self.service.notes_db.create_note(notes, id))

    def tearDown(self) -> None:
        run_coroutine(self.service.notes_db._clear())
        self.service.stop()

    def test_get_note(self) -> None:
        for id, note in self.notes_data.items():
            value = run_coroutine(self.service.get_note(id))
            self.assertEqual(note, value)

    @asynctest.fail_on(active_handles=True)
    async def test_get_all_notes(self) -> None:
        all_notes = {}
        async for id, note in self.service.get_notes():
            all_notes[id] = note
        self.assertEqual(len(all_notes), 2)

    def test_crud_notes(self) -> None:
        ids = list(self.notes_data.keys())
        self.assertGreaterEqual(len(ids), 2)

        note0 = self.notes_data[ids[0]]
        key = run_coroutine(self.service.create_note(note0))
        val = run_coroutine(self.service.get_note(key))
        self.assertEqual(note0["title"], val["title"])
        self.assertEqual(note0["body"], val["body"])
        self.assertEqual(note0["note_type"], val["note_type"])

        note1 = self.notes_data[ids[1]]
        run_coroutine(self.service.update_note(key, note1))
        val = run_coroutine(self.service.get_note(key))
        self.assertEqual(note1["title"], val["title"])
        self.assertEqual(note1["body"], val["body"])
        self.assertEqual(note1["note_type"], val["note_type"])

        run_coroutine(self.service.delete_note(key))

        with self.assertRaises(KeyError):
            run_coroutine(self.service.get_note(key))


IN_SQL_CFG_TXT = '''
service:
  name: Notes

notes-db:
  sql: ./tests/db/store.db

logging:
  version: 1
  root:
    level: ERROR
'''

with StringIO(IN_SQL_CFG_TXT) as f_sql:
    SQL_TEST_CONFIG = yaml.load(f_sql.read(), Loader=yaml.SafeLoader)


class NotesServiceWithSQLiteDBTest(asynctest.TestCase):
    def setUp(self) -> None:
        logging.config.dictConfig(SQL_TEST_CONFIG['logging'])
        logger = logging.getLogger(LOGGER_NAME)

        self.service = NotesService(
            config=SQL_TEST_CONFIG,
            logger=logger
        )
        self.service.start()

        self.notes_data = notes_data_suite()
        run_coroutine(self.service.notes_db._clear())
        for id, val in self.notes_data.items():
            notes = Note.from_api_dm(val)
            run_coroutine(self.service.notes_db.create_note(notes, id))

    def tearDown(self) -> None:
        run_coroutine(self.service.notes_db._clear())
        self.service.stop()

    def test_get_note(self) -> None:
        for id, note in self.notes_data.items():
            value = run_coroutine(self.service.get_note(id))
            self.assertEqual(note, value)

    @asynctest.fail_on(active_handles=True)
    async def test_get_all_notes(self) -> None:
        all_notes = {}
        async for id, note in self.service.get_notes():
            all_notes[id] = note
        self.assertEqual(len(all_notes), 2)

    def test_crud_notes(self) -> None:
        ids = list(self.notes_data.keys())
        self.assertGreaterEqual(len(ids), 2)

        note0 = self.notes_data[ids[0]]
        key = run_coroutine(self.service.create_note(note0))
        val = run_coroutine(self.service.get_note(key))
        self.assertEqual(note0["title"], val["title"])
        self.assertEqual(note0["body"], val["body"])
        self.assertEqual(note0["note_type"], val["note_type"])

        note1 = self.notes_data[ids[1]]
        run_coroutine(self.service.update_note(key, note1))
        val = run_coroutine(self.service.get_note(key))
        self.assertEqual(note1["title"], val["title"])
        self.assertEqual(note1["body"], val["body"])
        self.assertEqual(note1["note_type"], val["note_type"])

        run_coroutine(self.service.delete_note(key))

        with self.assertRaises(KeyError):
            run_coroutine(self.service.get_note(key))


if __name__ == '__main__':
    unittest.main()
