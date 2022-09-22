import os
import json

NOTES_SERVICE_ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

LOGGER_NAME = 'notesservice'

NOTES_SCHEMA_FILE = os.path.abspath(os.path.join(
    NOTES_SERVICE_ROOT_DIR,
    '../schema/notes-v1.0.json'
))

with open(NOTES_SCHEMA_FILE, mode='r', encoding='utf-8') as f:
    NOTES_SCHEMA = json.load(f)
