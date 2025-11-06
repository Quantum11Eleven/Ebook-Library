from __future__ import annotations

import sqlite3

import pytest
from PySide6.QtWidgets import QApplication

from shelfie import database
from shelfie.models.library_model import LibraryModel


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def conn(tmp_path):
    db_path = tmp_path / "library.db"
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    database.initialize(connection)
    with connection:
        connection.execute(
            """
            INSERT INTO books (title, author, year, isbn, file_path, file_hash, pages, added_at, updated_at)
            VALUES ('Test Book', 'Author', 2023, NULL, 'file.pdf', 'hash', 10, '2023-01-01', '2023-01-01')
            """
        )
    return connection


def test_model_row_count(qapp: QApplication, conn: sqlite3.Connection) -> None:
    model = LibraryModel(conn)
    assert model.rowCount() == 1


def test_filter(qapp: QApplication, conn: sqlite3.Connection) -> None:
    model = LibraryModel(conn)
    model.set_search_text("unknown")
    assert model.rowCount() == 0
    model.set_search_text("test")
    assert model.rowCount() == 1


def test_default_genres_seeded(qapp: QApplication, conn: sqlite3.Connection) -> None:
    model = LibraryModel(conn)
    genres = dict(model.genres())
    assert "🚀 Sci-Fi Explorations" in genres.values()
