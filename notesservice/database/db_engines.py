from typing import Dict

from notesservice.database.notes_db import (
    AbstractNotesDB, InMemoryNotesDB, FilesystemNotesDB
)


def create_notes_db(notes_db_config: Dict) -> AbstractNotesDB:
    db_type = list(notes_db_config.keys())[0]
    db_config = notes_db_config[db_type]

    return {
        'memory': lambda cfg: InMemoryNotesDB(),
        'fs': lambda cfg: FilesystemNotesDB(cfg)
    }[db_type](db_config)
