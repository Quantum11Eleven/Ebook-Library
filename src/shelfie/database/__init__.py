from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

SCHEMA_PATH = Path(__file__).with_name("schema.sql")
DEFAULT_DB_NAME = "shelfie.db"


def default_data_dir() -> Path:
    """Return the default application data directory."""
    home = Path.home()
    data_dir = home / "ShelfieLibrary" / "_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def database_path(custom_path: Path | None = None) -> Path:
    if custom_path is not None:
        custom_path.parent.mkdir(parents=True, exist_ok=True)
        return custom_path
    return default_data_dir() / DEFAULT_DB_NAME


def connect(db_file: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(database_path(db_file))
    conn.row_factory = sqlite3.Row
    return conn


def initialize(conn: sqlite3.Connection | None = None) -> sqlite3.Connection:
    close_conn = False
    if conn is None:
        conn = connect()
        close_conn = True

    with SCHEMA_PATH.open("r", encoding="utf-8") as schema_file:
        conn.executescript(schema_file.read())

    if close_conn:
        conn.commit()
        conn.close()
        conn = connect()
    return conn


def executemany(conn: sqlite3.Connection, query: str, params: Iterable[Iterable[object]]) -> None:
    with conn:
        conn.executemany(query, params)
