from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QIcon


@dataclass
class BookRecord:
    id: int
    title: str
    author: str | None
    year: int | None
    cover_path: Path | None
    progress: float
    file_path: Path


class LibraryModel(QAbstractTableModel):
    headers = ["Title", "Author", "Year", "Progress"]

    def __init__(self, conn: sqlite3.Connection, parent=None) -> None:  # type: ignore[override]
        super().__init__(parent)
        self._conn = conn
        self._books: list[BookRecord] = []
        self._search_text: str = ""
        self._genre_id: int | None = None
        self.refresh()

    # -- Qt model methods -----------------------------------------------------------
    def rowCount(self, parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        if parent and parent.isValid():
            return 0
        return len(self._books)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        if parent and parent.isValid():
            return 0
        return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid() or not (0 <= index.row() < len(self._books)):
            return None

        book = self._books[index.row()]
        column = index.column()

        if role in (Qt.DisplayRole, Qt.EditRole):
            if column == 0:
                return book.title
            if column == 1:
                return book.author or "Unknown"
            if column == 2:
                return book.year or "—"
            if column == 3:
                return f"{book.progress:.0%}"
        if role == Qt.DecorationRole and column == 0 and book.cover_path:
            try:
                if book.cover_path.exists():
                    return QIcon(str(book.cover_path))
            except OSError:
                return None
        if role == Qt.UserRole:
            return book
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return super().headerData(section, orientation, role)

    # -- public API -----------------------------------------------------------------
    def refresh(self) -> None:
        query = """
        SELECT b.id, b.title, b.author, b.year, b.file_path, a.cover_path, rs.percent
        FROM books b
        LEFT JOIN book_assets a ON a.book_id = b.id
        LEFT JOIN reading_state rs ON rs.book_id = b.id
        LEFT JOIN book_genres bg ON bg.book_id = b.id
        WHERE (:genre_id IS NULL OR bg.genre_id = :genre_id)
        GROUP BY b.id
        ORDER BY b.added_at DESC
        """
        records = self._conn.execute(
            query,
            {"genre_id": self._genre_id},
        ).fetchall()
        self.beginResetModel()
        self._books = [
            BookRecord(
                id=row["id"],
                title=row["title"],
                author=row["author"],
                year=row["year"],
                cover_path=Path(row["cover_path"]) if row["cover_path"] else None,
                progress=(row["percent"] or 0) / 100.0,
                file_path=Path(row["file_path"]),
            )
            for row in records
            if self._matches_filter(row["title"], row["author"])
        ]
        self.endResetModel()

    def set_search_text(self, text: str) -> None:
        self._search_text = text.lower()
        self.refresh()

    def set_genre_filter(self, genre_id: int | None) -> None:
        self._genre_id = genre_id
        self.refresh()

    def genres(self) -> list[tuple[int, str]]:
        rows = self._conn.execute(
            "SELECT id, name FROM genres ORDER BY name COLLATE NOCASE"
        ).fetchall()
        return [(row["id"], row["name"]) for row in rows]

    def book_at(self, index: QModelIndex) -> BookRecord | None:
        if not index.isValid():
            return None
        return self._books[index.row()]

    # -- helpers --------------------------------------------------------------------
    def _matches_filter(self, title: str, author: str | None) -> bool:
        if not self._search_text:
            return True
        haystack = " ".join(filter(None, [title, author or ""]))
        return self._search_text in haystack.lower()
