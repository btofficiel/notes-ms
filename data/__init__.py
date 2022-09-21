# Copyright (c) 2020. All rights reserved.

import glob
import json
import os
from typing import Dict, Sequence

NOTES_SERVICE_TEST_DATA_DIR = os.path.abspath(os.path.dirname(__file__))


NOTES_DATA_DIR = os.path.abspath(os.path.join(
    NOTES_SERVICE_TEST_DATA_DIR,
    'notes'
))

NOTES_FILES = glob.glob(NOTES_DATA_DIR + '/*.json')

def notes_data_suite(
    json_files: Sequence[str] = NOTES_FILES
) -> Dict[str, Dict]:
    note_data_suite = {}

    for id_ in json_files:
        note_id = os.path.splitext(os.path.basename(id_))[0]
        with open(id_, mode='r', encoding='utf-8') as f:
            note_json = json.load(f)
            note_data_suite[note_id] = note_json

    return note_data_suite
