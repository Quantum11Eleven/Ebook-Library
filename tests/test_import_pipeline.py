from __future__ import annotations

import sqlite3
from pathlib import Path

import fitz  # type: ignore
import pytest

from shelfie import database
from shelfie.importers.pipeline import ImportOptions, ImportPipeline


@pytest.fixture()
def temp_conn(tmp_path: Path) -> sqlite3.Connection:
    db_file = tmp_path / "shelfie.db"
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    database.initialize(conn)
    return conn


@pytest.fixture()
def sample_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Shelfie Test PDF")
    doc.save(pdf_path)
    doc.close()
    return pdf_path


def test_ingest_inserts_book(temp_conn: sqlite3.Connection, sample_pdf: Path, tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    pipeline = ImportPipeline(temp_conn, ImportOptions(library_root=library_root))

    results = pipeline.ingest([sample_pdf])

    assert len(results) == 1
    row = temp_conn.execute("SELECT COUNT(*) FROM books").fetchone()
    assert row[0] == 1


def test_duplicate_skipped(temp_conn: sqlite3.Connection, sample_pdf: Path, tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    pipeline = ImportPipeline(temp_conn, ImportOptions(library_root=library_root))

    pipeline.ingest([sample_pdf])
    results = pipeline.ingest([sample_pdf])

    assert results == []
    count = temp_conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    assert count == 1
