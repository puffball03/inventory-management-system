import pytest
import sqlite3
from pathlib import Path

import inventory.db as db

PROJECT_FOLDER = Path(__file__).parent.parent

@pytest.fixture
def connection():
    con = db.connect("memory")
    con.executescript((PROJECT_FOLDER / "schema.sql").read_text(encoding="utf-8"))