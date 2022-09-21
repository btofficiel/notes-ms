# Copyright (c) 2020. All rights reserved.

import json

import tornado.testing

from notesservice.tornado.app import (
    NOTES_ENTRY_URI_FORMAT_SR, APP_VERSION
)

from tests.unit.tornado_app_handlers_test import (
    NotesServiceTornadoAppTestSetup
)


class TestNotesServiceApp(NotesServiceTornadoAppTestSetup):
    def test_notes_endpoints(self):
        # Get all addresses in the address book, must be ZERO
        r = self.fetch(
            APP_VERSION+NOTES_ENTRY_URI_FORMAT_SR.format(id=''),
            method='GET',
            headers=None,
        )
        all_notes = json.loads(r.body.decode('utf-8'))
        self.assertEqual(r.code, 200, all_notes)
        self.assertEqual(len(all_notes), 0, all_notes)

        # Add an address
        r = self.fetch(
            APP_VERSION+NOTES_ENTRY_URI_FORMAT_SR.format(id=''),
            method='POST',
            headers=self.headers,
            body=json.dumps(self.addr0),
        )
        self.assertEqual(r.code, 201)
        note_uri = r.headers['Location']

        # POST: error cases
        r = self.fetch(
            APP_VERSION + NOTES_ENTRY_URI_FORMAT_SR.format(id=''),
            method='POST',
            headers=self.headers,
            body='it is not json',
        )
        self.assertEqual(r.code, 400)
        self.assertEqual(r.reason, 'Invalid JSON body')
        # r = self.fetch(
        #     NOTES_ENTRY_URI_FORMAT_SR.format(id=''),
        #     method='POST',
        #     headers=self.headers,
        #     body=json.dumps({}),
        # )
        # self.assertEqual(r.code, 400)
        # self.assertEqual(r.reason, 'JSON Schema validation failed')

        # Get the added address
        r = self.fetch(
            note_uri,
            method='GET',
            headers=None,
        )
        self.assertEqual(r.code, 200)
        body0 = json.loads(r.body.decode('utf-8'))
        self.assertEqual(self.addr0["title"], body0["title"])
        self.assertEqual(self.addr0["body"], body0["body"])
        self.assertEqual(self.addr0["note_type"], body0["note_type"])

        # GET: error cases
        r = self.fetch(
            NOTES_ENTRY_URI_FORMAT_SR.format(id='no-such-id'),
            method='GET',
            headers=None,
        )
        self.assertEqual(r.code, 404)

        # Update that address
        r = self.fetch(
            note_uri,
            method='PUT',
            headers=self.headers,
            body=json.dumps(self.addr1),
        )
        self.assertEqual(r.code, 204)
        r = self.fetch(
            note_uri,
            method='GET',
            headers=None,
        )
        self.assertEqual(r.code, 200)
        body1 = json.loads(r.body.decode('utf-8'))
        self.assertEqual(self.addr1["title"], body1["title"])
        self.assertEqual(self.addr1["body"], body1["body"])
        self.assertEqual(self.addr1["note_type"], body1["note_type"])

        # PUT: error cases
        r = self.fetch(
            note_uri,
            method='PUT',
            headers=self.headers,
            body='it is not json',
        )
        self.assertEqual(r.code, 400)
        self.assertEqual(r.reason, 'Invalid JSON body')
        r = self.fetch(
            NOTES_ENTRY_URI_FORMAT_SR.format(id='1234'),
            method='PUT',
            headers=self.headers,
            body=json.dumps(self.addr1),
        )
        self.assertEqual(r.code, 404)
        # r = self.fetch(
        #     note_uri,
        #     method='PUT',
        #     headers=self.headers,
        #     body=json.dumps({}),
        # )
        # self.assertEqual(r.code, 400)
        # self.assertEqual(r.reason, 'JSON Schema validation failed')

        # Delete that address
        r = self.fetch(
            note_uri,
            method='DELETE',
            headers=None,
        )
        self.assertEqual(r.code, 204)
        r = self.fetch(
            note_uri,
            method='GET',
            headers=None,
        )
        self.assertEqual(r.code, 404)

        # DELETE: error cases
        r = self.fetch(
            note_uri,
            method='DELETE',
            headers=None,
        )
        self.assertEqual(r.code, 404)

        # Get all addresses in the address book, must be ZERO
        r = self.fetch(
            APP_VERSION+NOTES_ENTRY_URI_FORMAT_SR.format(id=''),
            method='GET',
            headers=None,
        )
        all_notes = json.loads(r.body.decode('utf-8'))
        self.assertEqual(r.code, 200, all_notes)
        self.assertEqual(len(all_notes), 0, all_notes)


if __name__ == '__main__':
    tornado.testing.main()
