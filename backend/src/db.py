from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from src.config import settings


def connect():
    return psycopg.connect(settings.database_url, row_factory=dict_row, connect_timeout=4)


def migrate():
    with connect() as db:
        db.execute("SELECT pg_advisory_xact_lock(107800)")
        for path in sorted(Path("migrations").glob("*.sql")):
            db.execute(path.read_text(encoding="utf-8"))
