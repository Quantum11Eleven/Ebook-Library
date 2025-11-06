"""Helpers for loading and persisting per-book reading progress."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from shelfie.utils.filesystem import timestamp


@dataclass
class ReadingState:
    book_id: int
    last_page: int = 0
    percent: float = 0.0


def load_state(conn: sqlite3.Connection, book_id: int) -> ReadingState:
    """Return the persisted reading state for *book_id* if it exists."""

    row = conn.execute(
        "SELECT last_page, percent FROM reading_state WHERE book_id = ?",
        (book_id,),
    ).fetchone()
    if row is None:
        return ReadingState(book_id=book_id)
    return ReadingState(
        book_id=book_id,
        last_page=row["last_page"] or 0,
        percent=float(row["percent"] or 0.0) / 100.0,
    )


def save_state(conn: sqlite3.Connection, state: ReadingState) -> None:
    """Persist the reading *state* and touch the parent book row."""

    with conn:
        conn.execute(
            """
            INSERT INTO reading_state (book_id, last_page, percent, last_opened_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(book_id) DO UPDATE SET
                last_page = excluded.last_page,
                percent = excluded.percent,
                last_opened_at = excluded.last_opened_at
            """,
            (
                state.book_id,
                state.last_page,
                int(state.percent * 100),
                timestamp(),
            ),
        )

        conn.execute(
            "UPDATE books SET updated_at = ? WHERE id = ?",
            (timestamp(), state.book_id),
        )
